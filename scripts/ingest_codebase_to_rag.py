#!/usr/bin/env python3
"""
Codebase RAG Ingestion Script

Ingests the entire codebase into the RAG database via HTTP API.
Uses rate limiting and batch processing to avoid overwhelming the service.
"""

import os
import sys
import hashlib
import logging
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
RAG_SERVICE_URL = "https://localhost:8009"
PROJECT_ROOT = Path("/home/bbrelin/course-creator")
CHUNK_SIZE = 2500
CHUNK_OVERLAP = 200
CONCURRENT_REQUESTS = 3  # Limit concurrent requests
DELAY_BETWEEN_BATCHES = 0.5  # Seconds

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EXCLUDE_DIRS = {
    "node_modules", "__pycache__", ".git", ".venv", "venv",
    "dist", "build", ".next", "coverage", ".pytest_cache",
    ".mypy_cache", "chromadb_data", ".cache", "logs",
    "htmlcov", ".tox", "eggs"
}


def should_exclude_path(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
        if part.startswith('.') and part not in ['.claude']:
            return True
    return False


def get_file_type(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    return {
        ".py": "python", ".ts": "typescript", ".tsx": "typescript_react",
        ".js": "javascript", ".jsx": "javascript_react", ".md": "markdown",
        ".yml": "yaml", ".yaml": "yaml", ".json": "json", ".sql": "sql",
        ".css": "css", ".sh": "shell", ".d2": "diagram",
    }.get(suffix, "text")


def get_domain_for_file(file_path: Path) -> str:
    path_str = str(file_path)
    if "user-guide" in path_str or "CLAUDE" in path_str.upper():
        return "demo_tour_guide"
    if "lab-manager" in path_str:
        return "lab_assistant"
    if any(x in path_str for x in ["course-generator", "content-management"]):
        return "content_generation"
    return "course_knowledge"


def extract_metadata(file_path: Path, content: str) -> Dict[str, Any]:
    try:
        rel_path = str(file_path.relative_to(PROJECT_ROOT))
    except:
        rel_path = str(file_path)

    metadata = {
        "file_path": rel_path,
        "file_name": file_path.name,
        "file_type": get_file_type(file_path),
        "file_size": len(content),
    }

    if "/services/" in rel_path:
        parts = rel_path.split("/")
        try:
            idx = parts.index("services")
            if idx + 1 < len(parts):
                metadata["service"] = parts[idx + 1]
        except:
            pass

    if "frontend-react" in rel_path:
        if "/components/" in rel_path:
            metadata["component_type"] = "react_component"
        elif "/pages/" in rel_path:
            metadata["component_type"] = "page"
        elif "/features/" in rel_path:
            metadata["component_type"] = "feature"

    if file_path.suffix == ".py":
        if "test_" in file_path.name:
            metadata["is_test"] = True
        if "dao" in file_path.name.lower():
            metadata["layer"] = "data_access"
        elif "service" in file_path.name.lower():
            metadata["layer"] = "application"
        elif "entit" in file_path.name.lower():
            metadata["layer"] = "domain"
        elif "endpoint" in file_path.name.lower():
            metadata["layer"] = "api"

    return metadata


def chunk_content(content: str) -> List[Tuple[str, int, int]]:
    if len(content) <= CHUNK_SIZE:
        return [(content, 0, 1)]

    chunks = []
    start = 0
    chunk_idx = 0

    while start < len(content):
        end = start + CHUNK_SIZE
        if end < len(content):
            para = content.rfind('\n\n', start + 1500, end)
            if para > start:
                end = para + 2
            else:
                nl = content.rfind('\n', start + 1800, end)
                if nl > start:
                    end = nl + 1

        chunk = content[start:end].strip()
        if chunk:
            chunks.append((chunk, chunk_idx, -1))
            chunk_idx += 1
        start = end - CHUNK_OVERLAP

    total = len(chunks)
    return [(t, i, total) for t, i, _ in chunks]


def ingest_chunk(payload: Dict[str, Any]) -> bool:
    """Send a single chunk to RAG service."""
    try:
        resp = requests.post(
            f"{RAG_SERVICE_URL}/api/v1/rag/add-document",
            json=payload,
            verify=False,
            timeout=30
        )
        return resp.status_code == 200
    except Exception as e:
        return False


def process_file(file_path: Path) -> List[Dict[str, Any]]:
    """Process a file into payloads for RAG ingestion."""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except:
        return []

    if not content.strip() or len(content) > 150000:
        return []

    metadata = extract_metadata(file_path, content)
    domain = get_domain_for_file(file_path)
    chunks = chunk_content(content)

    payloads = []
    for chunk_text, idx, total in chunks:
        payloads.append({
            "content": chunk_text,
            "domain": domain,
            "source": "codebase",
            "metadata": {
                **metadata,
                "chunk_index": idx,
                "total_chunks": total,
            }
        })

    return payloads


def collect_files() -> List[Path]:
    """Collect files from priority directories."""
    files = []
    extensions = {'.py', '.ts', '.tsx', '.md', '.yml', '.yaml', '.sql', '.sh'}

    priority_dirs = [
        "docs",
        ".claude",
        "claude.md",
        "services/rag-service",
        "services/ai-assistant-service",
        "services/lab-manager",
        "services/course-management",
        "services/course-generator",
        "services/user-management",
        "services/organization-management",
        "services/content-management",
        "services/analytics",
        "frontend-react/src/features",
        "frontend-react/src/components",
        "frontend-react/src/hooks",
        "frontend-react/src/services",
        "frontend-react/src/pages",
        "tests/e2e",
        "tests/unit",
        "scripts",
        "migrations",
    ]

    for subdir in priority_dirs:
        path = PROJECT_ROOT / subdir
        if path.exists():
            if path.is_file() and path.suffix in extensions:
                files.append(path)
            elif path.is_dir():
                for ext in extensions:
                    for f in path.rglob(f"*{ext}"):
                        if f.is_file() and not should_exclude_path(f):
                            files.append(f)

    # Add root CLAUDE.md
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    if claude_md.exists():
        files.append(claude_md)

    return list(set(files))


def main():
    logger.info("=" * 60)
    logger.info("Codebase RAG Ingestion")
    logger.info("=" * 60)

    # Collect files
    logger.info("\nCollecting files...")
    files = collect_files()
    logger.info(f"Found {len(files)} files")

    # Process into payloads
    logger.info("\nProcessing files into chunks...")
    all_payloads = []
    domain_counts = {}

    for i, f in enumerate(files):
        payloads = process_file(f)
        for p in payloads:
            domain = p["domain"]
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        all_payloads.extend(payloads)

        if (i + 1) % 100 == 0:
            logger.info(f"  Processed {i + 1}/{len(files)} files")

    logger.info(f"\nTotal payloads: {len(all_payloads)}")
    for domain, count in sorted(domain_counts.items()):
        logger.info(f"  {domain}: {count}")

    # Ingest with rate limiting
    logger.info("\nIngesting to RAG service...")
    success = 0
    failure = 0

    with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        futures = []
        for i, payload in enumerate(all_payloads):
            futures.append(executor.submit(ingest_chunk, payload))

            # Rate limiting
            if (i + 1) % 10 == 0:
                time.sleep(DELAY_BETWEEN_BATCHES)

            # Progress update
            if (i + 1) % 100 == 0:
                # Check completed futures
                done = sum(1 for f in futures if f.done())
                logger.info(f"  Submitted: {i + 1}/{len(all_payloads)}, Completed: {done}")

        # Wait for all to complete
        logger.info("\nWaiting for completion...")
        for future in as_completed(futures):
            try:
                if future.result():
                    success += 1
                else:
                    failure += 1
            except:
                failure += 1

    logger.info("\n" + "=" * 60)
    logger.info("Ingestion Complete!")
    logger.info("=" * 60)
    logger.info(f"Success: {success}")
    logger.info(f"Failure: {failure}")
    logger.info(f"Rate: {100*success//(success+failure) if (success+failure) > 0 else 0}%")

    # Verify
    logger.info("\nFinal RAG stats:")
    try:
        resp = requests.get(f"{RAG_SERVICE_URL}/api/v1/rag/stats", verify=False)
        if resp.status_code == 200:
            stats = resp.json()
            for col, data in stats.get("statistics", {}).items():
                logger.info(f"  {col}: {data.get('document_count', 0)} documents")
    except:
        pass


if __name__ == "__main__":
    main()
