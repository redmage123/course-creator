#!/usr/bin/env python3
"""
Fast Async RAG Ingestion Script

Uses aiohttp for high-throughput parallel ingestion.
"""

import os
import sys
import hashlib
import logging
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
import ssl

# Configuration
RAG_SERVICE_URL = "https://localhost:8009"
PROJECT_ROOT = Path("/home/bbrelin/course-creator")
CHUNK_SIZE = 2500
CHUNK_OVERLAP = 200
CONCURRENT_LIMIT = 20  # Higher concurrency
BATCH_SIZE = 50

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EXCLUDE_DIRS = {"node_modules", "__pycache__", ".git", ".venv", "venv", "dist", "build", ".next", "coverage", ".pytest_cache", ".mypy_cache", "chromadb_data", ".cache", "logs", "htmlcov"}


def should_exclude_path(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS or (part.startswith('.') and part not in ['.claude']):
            return True
    return False


def get_file_type(file_path: Path) -> str:
    return {".py": "python", ".ts": "typescript", ".tsx": "typescript_react", ".js": "javascript", ".jsx": "javascript_react", ".md": "markdown", ".yml": "yaml", ".yaml": "yaml", ".sql": "sql", ".sh": "shell"}.get(file_path.suffix.lower(), "text")


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

    metadata = {"file_path": rel_path, "file_name": file_path.name, "file_type": get_file_type(file_path)}

    if "/services/" in rel_path:
        parts = rel_path.split("/")
        try:
            idx = parts.index("services")
            if idx + 1 < len(parts):
                metadata["service"] = parts[idx + 1]
        except:
            pass

    if file_path.suffix == ".py":
        if "test_" in file_path.name:
            metadata["is_test"] = True
        if "dao" in file_path.name.lower():
            metadata["layer"] = "data_access"
        elif "service" in file_path.name.lower():
            metadata["layer"] = "application"

    return metadata


def chunk_content(content: str) -> List[Tuple[str, int, int]]:
    if len(content) <= CHUNK_SIZE:
        return [(content, 0, 1)]

    chunks = []
    start = 0
    idx = 0

    while start < len(content):
        end = start + CHUNK_SIZE
        if end < len(content):
            nl = content.rfind('\n', start + 1800, end)
            if nl > start:
                end = nl + 1
        chunk = content[start:end].strip()
        if chunk:
            chunks.append((chunk, idx, -1))
            idx += 1
        start = end - CHUNK_OVERLAP

    total = len(chunks)
    return [(t, i, total) for t, i, _ in chunks]


def collect_files() -> List[Path]:
    files = []
    extensions = {'.py', '.ts', '.tsx', '.md', '.yml', '.yaml', '.sql', '.sh'}

    for subdir in ["docs", ".claude", "claude.md", "services", "frontend-react/src", "tests", "scripts", "migrations"]:
        path = PROJECT_ROOT / subdir
        if path.exists():
            if path.is_file() and path.suffix in extensions:
                files.append(path)
            elif path.is_dir():
                for ext in extensions:
                    for f in path.rglob(f"*{ext}"):
                        if f.is_file() and not should_exclude_path(f):
                            files.append(f)

    claude_md = PROJECT_ROOT / "CLAUDE.md"
    if claude_md.exists():
        files.append(claude_md)

    return list(set(files))


def process_file(file_path: Path) -> List[Dict[str, Any]]:
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
            "metadata": {**metadata, "chunk_index": idx, "total_chunks": total}
        })

    return payloads


async def ingest_batch(session: aiohttp.ClientSession, payloads: List[Dict], semaphore: asyncio.Semaphore) -> int:
    """Ingest a batch of payloads with rate limiting."""
    success = 0
    tasks = []

    for payload in payloads:
        task = asyncio.create_task(ingest_one(session, payload, semaphore))
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    success = sum(1 for r in results if r is True)
    return success


async def ingest_one(session: aiohttp.ClientSession, payload: Dict, semaphore: asyncio.Semaphore) -> bool:
    """Ingest a single document with semaphore for rate limiting."""
    async with semaphore:
        try:
            async with session.post(
                f"{RAG_SERVICE_URL}/api/v1/rag/add-document",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                return resp.status == 200
        except Exception:
            return False


async def main():
    logger.info("=" * 60)
    logger.info("Fast Async RAG Ingestion")
    logger.info("=" * 60)

    logger.info("\nCollecting files...")
    files = collect_files()
    logger.info(f"Found {len(files)} files")

    logger.info("\nProcessing into chunks...")
    all_payloads = []
    domain_counts = {}

    for i, f in enumerate(files):
        payloads = process_file(f)
        for p in payloads:
            domain = p["domain"]
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        all_payloads.extend(payloads)
        if (i + 1) % 200 == 0:
            logger.info(f"  Processed {i + 1}/{len(files)} files")

    logger.info(f"\nTotal: {len(all_payloads)} documents")
    for domain, count in sorted(domain_counts.items()):
        logger.info(f"  {domain}: {count}")

    logger.info("\nIngesting to RAG...")

    # Create SSL context that doesn't verify
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    connector = aiohttp.TCPConnector(ssl=ssl_ctx, limit=CONCURRENT_LIMIT)
    semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)

    total_success = 0

    async with aiohttp.ClientSession(connector=connector) as session:
        for i in range(0, len(all_payloads), BATCH_SIZE):
            batch = all_payloads[i:i + BATCH_SIZE]
            success = await ingest_batch(session, batch, semaphore)
            total_success += success

            progress = min(i + BATCH_SIZE, len(all_payloads))
            if progress % 500 == 0 or progress == len(all_payloads):
                logger.info(f"  Progress: {progress}/{len(all_payloads)} ({100*progress//len(all_payloads)}%)")

    logger.info("\n" + "=" * 60)
    logger.info("Ingestion Complete!")
    logger.info("=" * 60)
    logger.info(f"Ingested: {total_success}/{len(all_payloads)}")

    # Final stats
    import requests
    import urllib3
    urllib3.disable_warnings()
    try:
        resp = requests.get(f"{RAG_SERVICE_URL}/api/v1/rag/stats", verify=False, timeout=10)
        if resp.status_code == 200:
            stats = resp.json()
            logger.info("\nFinal RAG stats:")
            for col, data in stats.get("statistics", {}).items():
                logger.info(f"  {col}: {data.get('document_count', 0)}")
    except:
        pass


if __name__ == "__main__":
    asyncio.run(main())
