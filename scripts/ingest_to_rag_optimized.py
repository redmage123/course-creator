#!/usr/bin/env python3
"""
Optimized RAG Database Ingestion Script

Direct ChromaDB ingestion with batch processing for high throughput.
Ingests User Guide and key codebase files into the RAG database.

OPTIMIZATIONS:
- Direct ChromaDB access (bypasses HTTP overhead)
- Large batch processing (100+ documents per batch)
- Larger chunk sizes (3000 chars) to reduce total chunks
- Focuses on essential files first
- Uses SentenceTransformers for local embeddings
"""

import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
import uuid

# Add services to path
sys.path.insert(0, '/home/bbrelin/course-creator/services/rag-service')

import chromadb
from sentence_transformers import SentenceTransformer

# Configuration
PROJECT_ROOT = Path("/home/bbrelin/course-creator")
CHROMADB_PATH = "/home/bbrelin/course-creator/services/rag-service/chromadb_data"
CHUNK_SIZE = 3000  # Larger chunks = fewer total documents
CHUNK_OVERLAP = 300
BATCH_SIZE = 50  # Documents per ChromaDB batch

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directories to exclude
EXCLUDE_DIRS = {
    "node_modules", "__pycache__", ".git", ".venv", "venv",
    "dist", "build", ".next", "coverage", ".pytest_cache",
    ".mypy_cache", "chromadb_data", ".cache", "logs",
    "htmlcov", ".tox", "eggs"
}

# Priority files/directories (ingest these first)
PRIORITY_PATHS = [
    "docs/user-guide/USER_GUIDE.md",
    "CLAUDE.md",
    "claude.md/",
    ".claude/",
    "services/rag-service/",
    "services/ai-assistant-service/",
    "services/lab-manager/",
    "services/course-management/",
    "services/course-generator/",
    "services/user-management/",
    "services/organization-management/",
    "frontend-react/src/features/",
    "frontend-react/src/components/",
    "frontend-react/src/hooks/",
    "frontend-react/src/services/",
]


def should_exclude_path(path: Path) -> bool:
    """Check if path should be excluded."""
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
        if part.startswith('.') and part not in ['.claude']:
            return True
    return False


def get_file_type(file_path: Path) -> str:
    """Get file type from extension."""
    suffix = file_path.suffix.lower()
    type_map = {
        ".py": "python", ".ts": "typescript", ".tsx": "typescript_react",
        ".js": "javascript", ".jsx": "javascript_react", ".md": "markdown",
        ".yml": "yaml", ".yaml": "yaml", ".json": "json", ".sql": "sql",
        ".css": "css", ".sh": "shell", ".d2": "diagram", ".html": "html",
    }
    return type_map.get(suffix, "text")


def get_domain_for_file(file_path: Path) -> str:
    """Map file to RAG collection/domain."""
    path_str = str(file_path)

    if "user-guide" in path_str or "docs/" in path_str or "CLAUDE" in path_str:
        return "demo_tour_guide"
    if "lab-manager" in path_str or "lab" in path_str.lower():
        return "lab_assistant"
    if any(x in path_str for x in ["course-generator", "content-management"]):
        return "content_generation"
    return "course_knowledge"


def extract_metadata(file_path: Path, content: str) -> Dict[str, Any]:
    """Extract rich metadata from file."""
    rel_path = str(file_path.relative_to(PROJECT_ROOT)) if file_path.is_relative_to(PROJECT_ROOT) else str(file_path)

    metadata = {
        "file_path": rel_path,
        "file_name": file_path.name,
        "file_type": get_file_type(file_path),
        "file_size": len(content),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }

    # Extract service name
    if "/services/" in rel_path:
        parts = rel_path.split("/")
        try:
            idx = parts.index("services")
            if idx + 1 < len(parts):
                metadata["service"] = parts[idx + 1]
        except ValueError:
            pass

    # Extract component info for frontend
    if "frontend-react" in rel_path:
        if "/components/" in rel_path:
            metadata["component_type"] = "react_component"
        elif "/pages/" in rel_path:
            metadata["component_type"] = "page"
        elif "/features/" in rel_path:
            metadata["component_type"] = "feature"
        elif "/hooks/" in rel_path:
            metadata["component_type"] = "hook"

    # Python layer detection
    if file_path.suffix == ".py":
        if "test_" in file_path.name:
            metadata["is_test"] = True
        if "main.py" == file_path.name:
            metadata["is_entry_point"] = True
        if "dao" in file_path.name.lower():
            metadata["layer"] = "data_access"
        elif "service" in file_path.name.lower():
            metadata["layer"] = "application"
        elif "entit" in file_path.name.lower():
            metadata["layer"] = "domain"
        elif "api/" in rel_path or "endpoint" in file_path.name.lower():
            metadata["layer"] = "api"

    return metadata


def chunk_content(content: str) -> List[Tuple[str, int, int]]:
    """Split content into overlapping chunks."""
    if len(content) <= CHUNK_SIZE:
        return [(content, 0, 1)]

    chunks = []
    start = 0
    chunk_idx = 0

    while start < len(content):
        end = start + CHUNK_SIZE

        # Try to break at natural boundaries
        if end < len(content):
            # Look for double newline (paragraph break)
            para_break = content.rfind('\n\n', start + CHUNK_SIZE - 500, end)
            if para_break > start:
                end = para_break + 2
            else:
                # Look for single newline
                newline = content.rfind('\n', start + CHUNK_SIZE - 300, end)
                if newline > start:
                    end = newline + 1

        chunk_text = content[start:end].strip()
        if chunk_text:
            chunks.append((chunk_text, chunk_idx, -1))
            chunk_idx += 1

        start = end - CHUNK_OVERLAP

    # Update total chunks
    total = len(chunks)
    return [(text, idx, total) for text, idx, _ in chunks]


def collect_files() -> List[Path]:
    """Collect all relevant files from the codebase."""
    files = []
    extensions = {'.py', '.ts', '.tsx', '.js', '.jsx', '.md', '.yml', '.yaml', '.sql', '.sh', '.d2', '.css'}

    # Priority paths first
    for priority in PRIORITY_PATHS:
        path = PROJECT_ROOT / priority
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            for ext in extensions:
                for f in path.rglob(f"*{ext}"):
                    if f.is_file() and not should_exclude_path(f):
                        files.append(f)

    # Then scan remaining directories
    for subdir in ["services", "frontend-react/src", "tests", "scripts", "migrations"]:
        path = PROJECT_ROOT / subdir
        if path.exists():
            for ext in extensions:
                for f in path.rglob(f"*{ext}"):
                    if f.is_file() and not should_exclude_path(f) and f not in files:
                        files.append(f)

    return files


def process_file(file_path: Path) -> List[Dict[str, Any]]:
    """Process a single file into document chunks."""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        logger.warning(f"Failed to read {file_path}: {e}")
        return []

    if not content.strip():
        return []

    # Skip very large files
    if len(content) > 200000:  # 200KB
        logger.warning(f"Skipping large file: {file_path}")
        return []

    metadata = extract_metadata(file_path, content)
    domain = get_domain_for_file(file_path)
    chunks = chunk_content(content)

    documents = []
    for chunk_text, chunk_idx, total_chunks in chunks:
        doc_id = str(uuid.uuid4())
        content_hash = hashlib.md5(chunk_text.encode()).hexdigest()

        doc_metadata = {
            **metadata,
            "chunk_index": chunk_idx,
            "total_chunks": total_chunks,
            "content_hash": content_hash,
        }

        documents.append({
            "id": doc_id,
            "content": chunk_text,
            "metadata": doc_metadata,
            "domain": domain,
        })

    return documents


def main():
    """Main ingestion workflow with direct ChromaDB access."""
    logger.info("=" * 60)
    logger.info("Optimized RAG Database Ingestion")
    logger.info("=" * 60)

    # Initialize embedding model
    logger.info("\nLoading embedding model...")
    try:
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("SentenceTransformer model loaded")
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return

    # Initialize ChromaDB
    logger.info("\nConnecting to ChromaDB...")
    os.makedirs(CHROMADB_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMADB_PATH)
    logger.info(f"ChromaDB initialized at {CHROMADB_PATH}")

    # Get or create collections
    collections = {}
    collection_names = ["course_knowledge", "content_generation", "lab_assistant", "demo_tour_guide"]

    for name in collection_names:
        try:
            collections[name] = client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"  Collection '{name}': {collections[name].count()} existing documents")
        except Exception as e:
            logger.error(f"Failed to create collection {name}: {e}")
            return

    # Collect and process files
    logger.info("\nCollecting files...")
    files = collect_files()
    logger.info(f"Found {len(files)} files to process")

    # Process files into documents
    logger.info("\nProcessing files into chunks...")
    all_documents = []
    for i, file_path in enumerate(files):
        docs = process_file(file_path)
        all_documents.extend(docs)
        if (i + 1) % 100 == 0:
            logger.info(f"  Processed {i + 1}/{len(files)} files ({len(all_documents)} chunks)")

    logger.info(f"\nTotal documents to ingest: {len(all_documents)}")

    # Group by domain
    by_domain = {}
    for doc in all_documents:
        domain = doc["domain"]
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(doc)

    logger.info("\nDocuments by domain:")
    for domain, docs in by_domain.items():
        logger.info(f"  {domain}: {len(docs)}")

    # Ingest to ChromaDB
    logger.info("\nIngesting to ChromaDB...")
    total_ingested = 0

    for domain, docs in by_domain.items():
        collection = collections[domain]
        logger.info(f"\nIngesting {len(docs)} documents to '{domain}'...")

        # Process in batches
        for i in range(0, len(docs), BATCH_SIZE):
            batch = docs[i:i + BATCH_SIZE]

            # Generate embeddings
            texts = [d["content"] for d in batch]
            embeddings = embedding_model.encode(texts, show_progress_bar=False).tolist()

            # Prepare batch data
            ids = [d["id"] for d in batch]
            documents = texts
            metadatas = [d["metadata"] for d in batch]

            # Add to collection
            try:
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
                total_ingested += len(batch)

                if (i + BATCH_SIZE) % 200 == 0 or i + BATCH_SIZE >= len(docs):
                    progress = min(i + BATCH_SIZE, len(docs))
                    logger.info(f"  Progress: {progress}/{len(docs)} ({100*progress//len(docs)}%)")
            except Exception as e:
                logger.error(f"  Failed to ingest batch: {e}")

    # Final statistics
    logger.info("\n" + "=" * 60)
    logger.info("Ingestion Complete!")
    logger.info("=" * 60)
    logger.info(f"Total files processed: {len(files)}")
    logger.info(f"Total chunks ingested: {total_ingested}")

    logger.info("\nFinal collection sizes:")
    for name, collection in collections.items():
        logger.info(f"  {name}: {collection.count()} documents")


if __name__ == "__main__":
    main()
