#!/usr/bin/env python3
"""
RAG Database Ingestion Script

Ingests the User Guide and codebase into the RAG database for AI assistant
context retrieval. Supports chunking, metadata extraction, and batch ingestion.

BUSINESS CONTEXT:
This script populates the RAG knowledge base with platform documentation and
source code, enabling the AI assistant to provide accurate, context-aware
responses about the Course Creator Platform.

TECHNICAL IMPLEMENTATION:
- Reads markdown, Python, TypeScript, and configuration files
- Chunks large documents into manageable segments
- Extracts metadata (file type, path, component, etc.)
- Sends documents to RAG service via HTTP API
- Supports incremental updates and full re-indexing
"""

import os
import sys
import json
import hashlib
import asyncio
import aiohttp
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Configuration
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "https://localhost:8009")
PROJECT_ROOT = Path("/home/bbrelin/course-creator")
CHUNK_SIZE = 1500  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks
BATCH_SIZE = 10  # Documents per batch request

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File patterns to include
INCLUDE_PATTERNS = {
    "python": ["**/*.py"],
    "typescript": ["**/*.ts", "**/*.tsx"],
    "javascript": ["**/*.js", "**/*.jsx"],
    "markdown": ["**/*.md"],
    "yaml": ["**/*.yml", "**/*.yaml"],
    "json": ["**/package.json", "**/tsconfig.json"],
    "sql": ["**/*.sql"],
    "css": ["**/*.css", "**/*.module.css"],
    "shell": ["**/*.sh"],
    "d2": ["**/*.d2"],
}

# Directories to exclude
EXCLUDE_DIRS = {
    "node_modules", "__pycache__", ".git", ".venv", "venv",
    "dist", "build", ".next", "coverage", ".pytest_cache",
    ".mypy_cache", "chromadb_data", ".cache", "logs",
    "htmlcov", ".tox", "eggs", "*.egg-info"
}

# Files to exclude
EXCLUDE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    ".DS_Store", "Thumbs.db", "*.pyc", "*.pyo"
}


@dataclass
class DocumentChunk:
    """
    Represents a chunk of a document for RAG ingestion.

    WHY DATACLASS:
    - Clean data structure for document representation
    - Automatic __init__, __repr__, __eq__ generation
    - Type hints for better code clarity
    """
    content: str
    metadata: Dict[str, Any]
    domain: str
    source: str
    chunk_index: int
    total_chunks: int
    file_path: str
    content_hash: str


def should_exclude_path(path: Path) -> bool:
    """
    Check if a path should be excluded from ingestion.

    WHY THIS APPROACH:
    - Avoids ingesting generated files, dependencies, and caches
    - Focuses on source code and documentation
    - Improves RAG quality by excluding noise
    """
    parts = path.parts
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
        if part.startswith('.') and part not in ['.claude']:
            return True

    if path.name in EXCLUDE_FILES:
        return True

    return False


def get_file_type(file_path: Path) -> str:
    """
    Determine the file type based on extension.

    Returns category for metadata tagging.
    """
    suffix = file_path.suffix.lower()

    type_map = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript_react",
        ".js": "javascript",
        ".jsx": "javascript_react",
        ".md": "markdown",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".json": "json",
        ".sql": "sql",
        ".css": "css",
        ".sh": "shell",
        ".d2": "diagram",
        ".html": "html",
    }

    return type_map.get(suffix, "text")


def get_domain_for_file(file_path: Path) -> str:
    """
    Determine the RAG domain (collection) for a file.

    WHY DOMAIN MAPPING:
    - Routes documents to appropriate knowledge bases
    - Enables domain-specific retrieval
    - Improves query relevance
    """
    path_str = str(file_path)

    # User Guide and documentation -> demo_tour_guide
    if "user-guide" in path_str or "docs/" in path_str:
        return "demo_tour_guide"

    # Lab-related code -> lab_assistant
    if "lab-manager" in path_str or "lab" in path_str.lower():
        return "lab_assistant"

    # Course and content generation -> content_generation
    if any(x in path_str for x in ["course-generator", "content-management", "course-management"]):
        return "content_generation"

    # Default to course_knowledge for general codebase
    return "course_knowledge"


def extract_component_info(file_path: Path, content: str) -> Dict[str, Any]:
    """
    Extract component/module information from file content.

    WHY METADATA EXTRACTION:
    - Enables filtered searches by component type
    - Provides context for AI responses
    - Improves retrieval precision
    """
    metadata = {
        "file_path": str(file_path.relative_to(PROJECT_ROOT)),
        "file_name": file_path.name,
        "file_type": get_file_type(file_path),
        "file_size": len(content),
    }

    # Extract service name for backend files
    if "/services/" in str(file_path):
        parts = file_path.parts
        try:
            services_idx = parts.index("services")
            if services_idx + 1 < len(parts):
                metadata["service"] = parts[services_idx + 1]
        except ValueError:
            pass

    # Extract component type for frontend files
    if "frontend-react" in str(file_path):
        if "/components/" in str(file_path):
            metadata["component_type"] = "react_component"
        elif "/pages/" in str(file_path):
            metadata["component_type"] = "page"
        elif "/features/" in str(file_path):
            metadata["component_type"] = "feature"
        elif "/hooks/" in str(file_path):
            metadata["component_type"] = "hook"
        elif "/services/" in str(file_path):
            metadata["component_type"] = "service"

    # Check for specific patterns
    if file_path.suffix == ".py":
        if "test_" in file_path.name or "_test.py" in file_path.name:
            metadata["is_test"] = True
        if "main.py" in file_path.name:
            metadata["is_entry_point"] = True
        if "dao" in file_path.name.lower():
            metadata["layer"] = "data_access"
        elif "service" in file_path.name.lower():
            metadata["layer"] = "application"
        elif "entity" in file_path.name.lower() or "entities" in str(file_path):
            metadata["layer"] = "domain"
        elif "api/" in str(file_path) or "endpoints" in file_path.name.lower():
            metadata["layer"] = "api"

    return metadata


def chunk_content(content: str, file_path: Path) -> List[Tuple[str, int, int]]:
    """
    Split content into overlapping chunks.

    WHY CHUNKING:
    - Large files exceed embedding model limits
    - Smaller chunks improve retrieval precision
    - Overlap preserves context across boundaries

    Returns list of (chunk_text, chunk_index, total_chunks)
    """
    if len(content) <= CHUNK_SIZE:
        return [(content, 0, 1)]

    chunks = []
    start = 0
    chunk_index = 0

    while start < len(content):
        end = start + CHUNK_SIZE

        # Try to break at natural boundaries
        if end < len(content):
            # Look for newline near the end
            newline_pos = content.rfind('\n', start + CHUNK_SIZE - 200, end)
            if newline_pos > start:
                end = newline_pos + 1

        chunk_text = content[start:end].strip()
        if chunk_text:
            chunks.append((chunk_text, chunk_index, -1))  # -1 as placeholder
            chunk_index += 1

        start = end - CHUNK_OVERLAP

    # Update total_chunks in all tuples
    total = len(chunks)
    chunks = [(text, idx, total) for text, idx, _ in chunks]

    return chunks


def create_document_chunks(file_path: Path) -> List[DocumentChunk]:
    """
    Read a file and create document chunks for ingestion.

    WHY THIS APPROACH:
    - Handles different file encodings gracefully
    - Extracts rich metadata for each chunk
    - Creates content hashes for deduplication
    """
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        logger.warning(f"Failed to read {file_path}: {e}")
        return []

    if not content.strip():
        return []

    # Skip very large files (likely generated)
    if len(content) > 500000:  # 500KB
        logger.warning(f"Skipping large file: {file_path} ({len(content)} bytes)")
        return []

    metadata = extract_component_info(file_path, content)
    domain = get_domain_for_file(file_path)
    chunks = chunk_content(content, file_path)

    document_chunks = []
    for chunk_text, chunk_idx, total_chunks in chunks:
        # Create content hash for deduplication
        content_hash = hashlib.md5(chunk_text.encode()).hexdigest()

        chunk_metadata = {
            **metadata,
            "chunk_index": chunk_idx,
            "total_chunks": total_chunks,
            "ingested_at": datetime.utcnow().isoformat(),
        }

        document_chunks.append(DocumentChunk(
            content=chunk_text,
            metadata=chunk_metadata,
            domain=domain,
            source="codebase_ingestion",
            chunk_index=chunk_idx,
            total_chunks=total_chunks,
            file_path=str(file_path),
            content_hash=content_hash,
        ))

    return document_chunks


async def ingest_document(
    session: aiohttp.ClientSession,
    chunk: DocumentChunk
) -> bool:
    """
    Send a document chunk to the RAG service.

    WHY ASYNC:
    - Enables concurrent ingestion for performance
    - Non-blocking I/O for better throughput
    - Handles network latency efficiently
    """
    payload = {
        "content": chunk.content,
        "domain": chunk.domain,
        "source": chunk.source,
        "metadata": chunk.metadata,
    }

    try:
        async with session.post(
            f"{RAG_SERVICE_URL}/api/v1/rag/add-document",
            json=payload,
            ssl=False,  # Skip SSL verification for localhost
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status == 200:
                return True
            else:
                error_text = await response.text()
                logger.error(f"Failed to ingest {chunk.file_path}: {error_text}")
                return False
    except Exception as e:
        logger.error(f"Error ingesting {chunk.file_path}: {e}")
        return False


async def ingest_batch(
    session: aiohttp.ClientSession,
    chunks: List[DocumentChunk]
) -> Tuple[int, int]:
    """
    Ingest a batch of document chunks concurrently.

    Returns (success_count, failure_count)
    """
    tasks = [ingest_document(session, chunk) for chunk in chunks]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success = sum(1 for r in results if r is True)
    failure = len(results) - success

    return success, failure


def collect_files(directories: List[Path], file_types: List[str]) -> List[Path]:
    """
    Collect all files matching the specified patterns.

    WHY GENERATOR PATTERN:
    - Memory efficient for large codebases
    - Lazy evaluation of file paths
    - Flexible pattern matching
    """
    files = []

    for directory in directories:
        if not directory.exists():
            logger.warning(f"Directory not found: {directory}")
            continue

        for file_type in file_types:
            patterns = INCLUDE_PATTERNS.get(file_type, [])
            for pattern in patterns:
                for file_path in directory.glob(pattern):
                    if file_path.is_file() and not should_exclude_path(file_path):
                        files.append(file_path)

    return list(set(files))  # Remove duplicates


async def main():
    """
    Main ingestion workflow.

    WORKFLOW:
    1. Collect files from codebase
    2. Create document chunks
    3. Batch ingest to RAG service
    4. Report statistics
    """
    logger.info("=" * 60)
    logger.info("RAG Database Ingestion Script")
    logger.info("=" * 60)

    # Define directories to scan
    directories = [
        PROJECT_ROOT / "docs" / "user-guide",
        PROJECT_ROOT / "services",
        PROJECT_ROOT / "frontend-react" / "src",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "scripts",
        PROJECT_ROOT / "migrations",
        PROJECT_ROOT / ".claude",
        PROJECT_ROOT / "claude.md",
    ]

    # File types to ingest
    file_types = ["python", "typescript", "markdown", "yaml", "sql", "shell", "d2"]

    logger.info(f"Scanning directories: {len(directories)}")
    logger.info(f"File types: {file_types}")

    # Collect files
    logger.info("\nCollecting files...")
    files = collect_files(directories, file_types)
    logger.info(f"Found {len(files)} files to process")

    # Create document chunks
    logger.info("\nCreating document chunks...")
    all_chunks = []
    for file_path in files:
        chunks = create_document_chunks(file_path)
        all_chunks.extend(chunks)
        if chunks:
            logger.debug(f"  {file_path.name}: {len(chunks)} chunks")

    logger.info(f"Created {len(all_chunks)} total chunks")

    # Group chunks by domain for reporting
    domain_counts = {}
    for chunk in all_chunks:
        domain_counts[chunk.domain] = domain_counts.get(chunk.domain, 0) + 1

    logger.info("\nChunks by domain:")
    for domain, count in sorted(domain_counts.items()):
        logger.info(f"  {domain}: {count}")

    # Ingest to RAG service
    logger.info("\nIngesting to RAG service...")

    total_success = 0
    total_failure = 0

    connector = aiohttp.TCPConnector(limit=10)  # Limit concurrent connections
    async with aiohttp.ClientSession(connector=connector) as session:
        # Process in batches
        for i in range(0, len(all_chunks), BATCH_SIZE):
            batch = all_chunks[i:i + BATCH_SIZE]
            success, failure = await ingest_batch(session, batch)
            total_success += success
            total_failure += failure

            # Progress update
            progress = min(i + BATCH_SIZE, len(all_chunks))
            logger.info(f"  Progress: {progress}/{len(all_chunks)} ({100*progress//len(all_chunks)}%)")

    # Final report
    logger.info("\n" + "=" * 60)
    logger.info("Ingestion Complete!")
    logger.info("=" * 60)
    logger.info(f"Total files processed: {len(files)}")
    logger.info(f"Total chunks created: {len(all_chunks)}")
    logger.info(f"Successfully ingested: {total_success}")
    logger.info(f"Failed: {total_failure}")
    logger.info(f"Success rate: {100*total_success//(total_success+total_failure) if (total_success+total_failure) > 0 else 0}%")

    # Verify with stats
    logger.info("\nVerifying RAG database stats...")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{RAG_SERVICE_URL}/api/v1/rag/stats",
            ssl=False
        ) as response:
            if response.status == 200:
                stats = await response.json()
                logger.info(f"RAG Stats: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
