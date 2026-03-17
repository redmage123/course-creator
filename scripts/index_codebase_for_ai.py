#!/usr/bin/env python3
"""
Codebase Indexing Script for AI Assistant

BUSINESS PURPOSE:
Indexes Course Creator Platform codebase and documentation into RAG service.
Enables AI assistant to answer questions about platform architecture, APIs,
workflows, and implementation details.

TECHNICAL IMPLEMENTATION:
- Scans documentation files (*.md)
- Extracts API endpoint documentation
- Indexes key code files with summaries
- Uploads to RAG service demo_tour_guide collection

USAGE:
    python3 scripts/index_codebase_for_ai.py
"""

import os
import sys
import httpx
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# RAG service configuration
RAG_SERVICE_URL = "https://localhost:8009"
RAG_COLLECTION = "demo_tour_guide"


class CodebaseIndexer:
    """
    Codebase indexer for RAG service

    BUSINESS PURPOSE:
    Prepares codebase knowledge for AI assistant. Extracts relevant
    documentation, API specs, and code summaries for RAG indexing.

    TECHNICAL IMPLEMENTATION:
    - Discovers documentation files
    - Parses API endpoint definitions
    - Chunks large files for embedding
    - Uploads to RAG service via HTTP API

    ATTRIBUTES:
        rag_url: RAG service base URL
        collection: ChromaDB collection name
        client: HTTP client for RAG API
        indexed_count: Number of documents indexed
    """

    def __init__(self, rag_url: str = RAG_SERVICE_URL, collection: str = RAG_COLLECTION):
        """Initialize indexer with RAG service URL"""
        self.rag_url = rag_url.rstrip('/')
        self.collection = collection
        self.client = httpx.AsyncClient(verify=False, timeout=30.0)
        self.indexed_count = 0

    async def index_all(self) -> None:
        """
        Index entire codebase

        BUSINESS PURPOSE:
        Complete indexing pipeline for AI assistant knowledge base.
        Processes all documentation and code summaries.

        TECHNICAL IMPLEMENTATION:
        1. Index markdown documentation
        2. Index API documentation
        3. Index service summaries
        4. Index workflow documentation
        """
        logger.info("=" * 80)
        logger.info("Starting Codebase Indexing for AI Assistant")
        logger.info("=" * 80)

        try:
            # Check RAG service health
            if not await self.check_rag_health():
                logger.error("RAG service not reachable. Aborting.")
                return

            # Index documentation files
            await self.index_markdown_docs()

            # Index API documentation
            await self.index_api_documentation()

            # Index service summaries
            await self.index_service_summaries()

            # Index workflow documentation
            await self.index_workflows()

            logger.info("=" * 80)
            logger.info(f"✓ Indexing Complete: {self.indexed_count} documents indexed")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            raise
        finally:
            await self.client.aclose()

    async def check_rag_health(self) -> bool:
        """Check RAG service health"""
        try:
            url = f"{self.rag_url}/api/v1/rag/health"
            response = await self.client.get(url)
            if response.status_code == 200:
                logger.info("✓ RAG service is healthy")
                return True
            else:
                logger.error(f"RAG service returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to RAG service: {e}")
            return False

    async def index_markdown_docs(self) -> None:
        """
        Index all markdown documentation

        BUSINESS PURPOSE:
        Indexes comprehensive platform documentation for AI assistant.
        Enables answering questions about features, architecture, and usage.

        TECHNICAL IMPLEMENTATION:
        Discovers all .md files in docs/ and claude.md/ directories.
        Chunks large files and indexes with metadata.
        """
        logger.info("\n--- Indexing Markdown Documentation ---")

        doc_paths = [
            project_root / "docs",
            project_root / "claude.md",
            project_root / "tests"
        ]

        markdown_files = []
        for doc_path in doc_paths:
            if doc_path.exists():
                markdown_files.extend(doc_path.rglob("*.md"))

        logger.info(f"Found {len(markdown_files)} markdown files")

        for md_file in markdown_files:
            try:
                content = md_file.read_text(encoding='utf-8')

                # Skip if file is too small
                if len(content) < 50:
                    continue

                # Chunk large files
                if len(content) > 5000:
                    chunks = self.chunk_text(content, chunk_size=3000)
                    for i, chunk in enumerate(chunks):
                        await self.add_document(
                            content=chunk,
                            source=str(md_file.relative_to(project_root)),
                            metadata={
                                "category": "documentation",
                                "chunk": i + 1,
                                "total_chunks": len(chunks)
                            }
                        )
                else:
                    await self.add_document(
                        content=content,
                        source=str(md_file.relative_to(project_root)),
                        metadata={
                            "category": "documentation"
                        }
                    )

                logger.info(f"✓ Indexed: {md_file.relative_to(project_root)}")

            except Exception as e:
                logger.warning(f"Failed to index {md_file}: {e}")

    async def index_api_documentation(self) -> None:
        """
        Index API endpoint documentation

        BUSINESS PURPOSE:
        Indexes API endpoint specifications for AI assistant.
        Enables answering questions about available APIs and parameters.

        TECHNICAL IMPLEMENTATION:
        Extracts API routes from service main.py and API files.
        Parses endpoint paths, methods, and descriptions.
        """
        logger.info("\n--- Indexing API Documentation ---")

        # Index CLAUDE.md which contains API information
        claude_md = project_root / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text(encoding='utf-8')

            # Extract API-related sections
            api_sections = re.findall(
                r'## .*API.*\n(.*?)(?=\n##|\Z)',
                content,
                re.DOTALL | re.IGNORECASE
            )

            for i, section in enumerate(api_sections):
                if len(section.strip()) > 100:
                    await self.add_document(
                        content=section.strip(),
                        source="CLAUDE.md",
                        metadata={
                            "category": "api_documentation",
                            "section": i + 1
                        }
                    )

        # Index service API files
        services_dir = project_root / "services"
        if services_dir.exists():
            for service_dir in services_dir.iterdir():
                if service_dir.is_dir():
                    api_dir = service_dir / "api"
                    if api_dir.exists():
                        for api_file in api_dir.rglob("*.py"):
                            await self.index_api_file(api_file)

        logger.info("✓ API documentation indexed")

    async def index_api_file(self, api_file: Path) -> None:
        """Index single API file"""
        try:
            content = api_file.read_text(encoding='utf-8')

            # Extract API routes using regex
            routes = re.findall(
                r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']\)',
                content
            )

            if routes:
                route_summary = f"API File: {api_file.name}\n\n"
                route_summary += "Endpoints:\n"
                for method, path in routes:
                    route_summary += f"- {method.upper()} {path}\n"

                # Extract docstrings
                docstrings = re.findall(
                    r'"""(.*?)"""',
                    content,
                    re.DOTALL
                )

                if docstrings:
                    route_summary += "\n\nEndpoint Descriptions:\n"
                    route_summary += "\n\n".join(docstrings[:5])  # Limit to first 5

                await self.add_document(
                    content=route_summary,
                    source=str(api_file.relative_to(project_root)),
                    metadata={
                        "category": "api_routes",
                        "service": api_file.parts[-3]  # Service name
                    }
                )

        except Exception as e:
            logger.debug(f"Could not parse {api_file}: {e}")

    async def index_service_summaries(self) -> None:
        """
        Index service summaries

        BUSINESS PURPOSE:
        Indexes high-level service descriptions for AI assistant.
        Enables explaining platform architecture and service responsibilities.

        TECHNICAL IMPLEMENTATION:
        Extracts service docstrings and README files.
        Creates summaries of each microservice.
        """
        logger.info("\n--- Indexing Service Summaries ---")

        services_dir = project_root / "services"
        if not services_dir.exists():
            logger.warning("Services directory not found")
            return

        for service_dir in services_dir.iterdir():
            if service_dir.is_dir() and not service_dir.name.startswith('.'):
                service_name = service_dir.name

                # Check for README
                readme = service_dir / "README.md"
                if readme.exists():
                    content = readme.read_text(encoding='utf-8')
                    await self.add_document(
                        content=content,
                        source=f"services/{service_name}/README.md",
                        metadata={
                            "category": "service_documentation",
                            "service": service_name
                        }
                    )
                    logger.info(f"✓ Indexed service: {service_name}")
                else:
                    # Extract from main.py docstring
                    main_py = service_dir / "main.py"
                    if main_py.exists():
                        content = main_py.read_text(encoding='utf-8')
                        docstring = re.search(r'"""(.*?)"""', content, re.DOTALL)
                        if docstring:
                            await self.add_document(
                                content=f"Service: {service_name}\n\n{docstring.group(1)}",
                                source=f"services/{service_name}/main.py",
                                metadata={
                                    "category": "service_documentation",
                                    "service": service_name
                                }
                            )
                            logger.info(f"✓ Indexed service: {service_name}")

    async def index_workflows(self) -> None:
        """
        Index workflow documentation

        BUSINESS PURPOSE:
        Indexes business process workflows for AI assistant.
        Enables explaining multi-step processes like course creation.

        TECHNICAL IMPLEMENTATION:
        Parses workflow markdown files and extracts step-by-step processes.
        """
        logger.info("\n--- Indexing Workflows ---")

        workflow_files = [
            "docs/WORKFLOWS.md",
            "docs/RBAC_DOCUMENTATION.md",
            "docs/GUEST_SESSION_PRIVACY_COMPLIANCE.md",
            "tests/COMPREHENSIVE_E2E_TEST_PLAN.md"
        ]

        for workflow_file in workflow_files:
            workflow_path = project_root / workflow_file
            if workflow_path.exists():
                content = workflow_path.read_text(encoding='utf-8')

                # Chunk if large
                if len(content) > 4000:
                    chunks = self.chunk_text(content, chunk_size=3000)
                    for i, chunk in enumerate(chunks):
                        await self.add_document(
                            content=chunk,
                            source=workflow_file,
                            metadata={
                                "category": "workflows",
                                "chunk": i + 1,
                                "total_chunks": len(chunks)
                            }
                        )
                else:
                    await self.add_document(
                        content=content,
                        source=workflow_file,
                        metadata={
                            "category": "workflows"
                        }
                    )

                logger.info(f"✓ Indexed workflow: {workflow_file}")

    async def add_document(
        self,
        content: str,
        source: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add document to RAG service

        BUSINESS PURPOSE:
        Uploads single document to RAG for embedding and indexing.

        TECHNICAL IMPLEMENTATION:
        POSTs to RAG service /api/v1/rag/add-document endpoint.

        ARGS:
            content: Document text content
            source: Document source identifier
            metadata: Additional document metadata

        RETURNS:
            True if successful, False otherwise
        """
        try:
            url = f"{self.rag_url}/api/v1/rag/add-document"

            payload = {
                "content": content,
                "source": source,
                "domain": self.collection,
                "metadata": metadata or {}
            }

            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            self.indexed_count += 1
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to add document: {e}")
            return False

    def chunk_text(self, text: str, chunk_size: int = 3000, overlap: int = 200) -> List[str]:
        """
        Chunk text into smaller pieces

        BUSINESS PURPOSE:
        Splits large documents for better embedding and retrieval.
        Maintains context with overlapping chunks.

        TECHNICAL IMPLEMENTATION:
        Splits on paragraph boundaries with overlap for context preservation.

        ARGS:
            text: Text to chunk
            chunk_size: Maximum chunk size in characters
            overlap: Overlap between chunks

        RETURNS:
            List of text chunks
        """
        # Split on paragraph boundaries
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # Start new chunk with overlap
                if len(para) > chunk_size:
                    # Split large paragraph
                    for i in range(0, len(para), chunk_size - overlap):
                        chunks.append(para[i:i + chunk_size])
                    current_chunk = ""
                else:
                    current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks


async def main():
    """
    Main entry point

    BUSINESS PURPOSE:
    Runs complete codebase indexing process for AI assistant.

    TECHNICAL IMPLEMENTATION:
    Creates indexer and processes all documentation and code.
    """
    indexer = CodebaseIndexer()
    await indexer.index_all()


if __name__ == "__main__":
    asyncio.run(main())
