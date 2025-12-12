#!/usr/bin/env python3
"""
RAG Database Ingestion Script - Docker Container Version

Runs inside the RAG service Docker container for direct ChromaDB access.
"""

import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
import uuid

import chromadb
from sentence_transformers import SentenceTransformer

# Configuration - paths for Docker container
PROJECT_ROOT = Path("/app/codebase")  # Will mount codebase here
CHROMADB_PATH = "/app/chromadb_data"  # Docker volume mount
CHUNK_SIZE = 3000
CHUNK_OVERLAP = 300
BATCH_SIZE = 50

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
    type_map = {
        ".py": "python", ".ts": "typescript", ".tsx": "typescript_react",
        ".js": "javascript", ".jsx": "javascript_react", ".md": "markdown",
        ".yml": "yaml", ".yaml": "yaml", ".json": "json", ".sql": "sql",
        ".css": "css", ".sh": "shell", ".d2": "diagram", ".html": "html",
    }
    return type_map.get(suffix, "text")


def get_domain_for_file(file_path: Path) -> str:
    path_str = str(file_path)
    if "user-guide" in path_str or "docs/" in path_str or "CLAUDE" in path_str:
        return "demo_tour_guide"
    if "lab-manager" in path_str or "lab" in path_str.lower():
        return "lab_assistant"
    if any(x in path_str for x in ["course-generator", "content-management"]):
        return "content_generation"
    return "course_knowledge"


def extract_metadata(file_path: Path, content: str) -> Dict[str, Any]:
    try:
        rel_path = str(file_path.relative_to(PROJECT_ROOT))
    except ValueError:
        rel_path = str(file_path)

    metadata = {
        "file_path": rel_path,
        "file_name": file_path.name,
        "file_type": get_file_type(file_path),
        "file_size": len(content),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }

    if "/services/" in rel_path:
        parts = rel_path.split("/")
        try:
            idx = parts.index("services")
            if idx + 1 < len(parts):
                metadata["service"] = parts[idx + 1]
        except ValueError:
            pass

    if "frontend-react" in rel_path:
        if "/components/" in rel_path:
            metadata["component_type"] = "react_component"
        elif "/pages/" in rel_path:
            metadata["component_type"] = "page"
        elif "/features/" in rel_path:
            metadata["component_type"] = "feature"
        elif "/hooks/" in rel_path:
            metadata["component_type"] = "hook"

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
    if len(content) <= CHUNK_SIZE:
        return [(content, 0, 1)]

    chunks = []
    start = 0
    chunk_idx = 0

    while start < len(content):
        end = start + CHUNK_SIZE
        if end < len(content):
            para_break = content.rfind('\n\n', start + CHUNK_SIZE - 500, end)
            if para_break > start:
                end = para_break + 2
            else:
                newline = content.rfind('\n', start + CHUNK_SIZE - 300, end)
                if newline > start:
                    end = newline + 1

        chunk_text = content[start:end].strip()
        if chunk_text:
            chunks.append((chunk_text, chunk_idx, -1))
            chunk_idx += 1

        start = end - CHUNK_OVERLAP

    total = len(chunks)
    return [(text, idx, total) for text, idx, _ in chunks]


def collect_files() -> List[Path]:
    files = []
    extensions = {'.py', '.ts', '.tsx', '.js', '.jsx', '.md', '.yml', '.yaml', '.sql', '.sh', '.d2', '.css'}

    for subdir in ["docs", "services", "frontend-react/src", "tests", "scripts", "migrations", ".claude", "claude.md"]:
        path = PROJECT_ROOT / subdir
        if path.exists():
            if path.is_file():
                files.append(path)
            else:
                for ext in extensions:
                    for f in path.rglob(f"*{ext}"):
                        if f.is_file() and not should_exclude_path(f):
                            files.append(f)

    return list(set(files))


def process_file(file_path: Path) -> List[Dict[str, Any]]:
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        logger.warning(f"Failed to read {file_path}: {e}")
        return []

    if not content.strip() or len(content) > 200000:
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
    logger.info("=" * 60)
    logger.info("RAG Database Ingestion (Docker)")
    logger.info("=" * 60)

    # Check codebase mount
    if not PROJECT_ROOT.exists():
        logger.error(f"Codebase not mounted at {PROJECT_ROOT}")
        return

    logger.info("\nLoading embedding model...")
    try:
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Model loaded")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return

    logger.info("\nConnecting to ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMADB_PATH)
    logger.info(f"ChromaDB at {CHROMADB_PATH}")

    collections = {}
    for name in ["course_knowledge", "content_generation", "lab_assistant", "demo_tour_guide"]:
        collections[name] = client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
        logger.info(f"  {name}: {collections[name].count()} existing")

    logger.info("\nCollecting files...")
    files = collect_files()
    logger.info(f"Found {len(files)} files")

    logger.info("\nProcessing files...")
    all_documents = []
    for i, file_path in enumerate(files):
        docs = process_file(file_path)
        all_documents.extend(docs)
        if (i + 1) % 100 == 0:
            logger.info(f"  {i + 1}/{len(files)} files ({len(all_documents)} chunks)")

    logger.info(f"\nTotal: {len(all_documents)} documents")

    by_domain = {}
    for doc in all_documents:
        domain = doc["domain"]
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(doc)

    for domain, docs in by_domain.items():
        logger.info(f"  {domain}: {len(docs)}")

    logger.info("\nIngesting...")
    total = 0

    for domain, docs in by_domain.items():
        collection = collections[domain]
        logger.info(f"\n{domain}: {len(docs)} docs...")

        for i in range(0, len(docs), BATCH_SIZE):
            batch = docs[i:i + BATCH_SIZE]
            texts = [d["content"] for d in batch]
            embeddings = embedding_model.encode(texts, show_progress_bar=False).tolist()

            try:
                collection.add(
                    ids=[d["id"] for d in batch],
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=[d["metadata"] for d in batch]
                )
                total += len(batch)
            except Exception as e:
                logger.error(f"Batch failed: {e}")

    logger.info("\n" + "=" * 60)
    logger.info(f"Done! Ingested {total} documents")
    for name, col in collections.items():
        logger.info(f"  {name}: {col.count()}")


if __name__ == "__main__":
    main()
