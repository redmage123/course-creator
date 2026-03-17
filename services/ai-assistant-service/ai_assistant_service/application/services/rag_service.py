"""
RAG Service Client - Application Layer

BUSINESS PURPOSE:
Integrates with existing RAG service (port 8009) to retrieve relevant
codebase context for AI assistant. Enables AI to answer questions about
platform architecture, APIs, and workflows.

TECHNICAL IMPLEMENTATION:
HTTP client for RAG service API. Queries vector database for semantic
search results. Provides context to LLM for informed responses.
"""

import httpx
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG Service client for codebase context retrieval

    BUSINESS PURPOSE:
    Connects AI assistant to indexed codebase knowledge. Enables AI
    to provide accurate answers about platform features, APIs, and
    technical implementation details.

    TECHNICAL IMPLEMENTATION:
    HTTP client for RAG service at port 8009. Uses demo_tour_guide
    collection for platform knowledge. Performs semantic search and
    returns ranked results with source citations.

    ATTRIBUTES:
        base_url: RAG service base URL (https://localhost:8009)
        collection: Collection name to query (demo_tour_guide)
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        base_url: str = "https://localhost:8009",
        collection: str = "demo_tour_guide",
        timeout: float = 30.0
    ):
        """
        Initialize RAG service client

        BUSINESS PURPOSE:
        Configures connection to existing RAG service. Sets up HTTP
        client with SSL verification disabled for local development.

        TECHNICAL IMPLEMENTATION:
        Creates httpx async client with timeout and SSL settings.
        Validates RAG service is reachable on initialization.

        ARGS:
            base_url: RAG service base URL
            collection: ChromaDB collection to query
            timeout: Request timeout seconds
        """
        self.base_url = base_url.rstrip('/')
        self.collection = collection
        self.timeout = timeout

        # Create HTTP client with SSL disabled for localhost
        self.client = httpx.AsyncClient(
            timeout=timeout,
            verify=False  # Disable SSL verification for localhost
        )

        logger.info(
            f"RAG Service client initialized: "
            f"base_url={base_url}, collection={collection}"
        )

    async def query(
        self,
        query: str,
        n_results: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query RAG service for relevant context

        BUSINESS PURPOSE:
        Retrieves relevant codebase documentation, API specs, and
        workflow descriptions based on user query. Provides context
        for AI to generate accurate responses.

        TECHNICAL IMPLEMENTATION:
        POSTs to RAG service /api/v1/rag/query endpoint. Returns
        ranked results with content, metadata, and relevance scores.
        Handles errors gracefully with empty results fallback.

        ARGS:
            query: User's question or search query
            n_results: Number of results to return (default 5)
            metadata_filter: Optional metadata filters

        RETURNS:
            List of result dictionaries with 'content', 'metadata', 'score'

        EXAMPLE:
            results = await rag_service.query(
                "How do I create a project?",
                n_results=3
            )
            # Returns: [
            #     {
            #         "content": "To create a project, call POST /api/v1/projects...",
            #         "metadata": {"source": "API_DOCUMENTATION.md"},
            #         "score": 0.89
            #     },
            #     ...
            # ]
        """
        try:
            url = f"{self.base_url}/api/v1/rag/query"

            payload = {
                "query": query,
                "domain": self.collection,
                "n_results": n_results
            }

            if metadata_filter:
                payload["metadata_filter"] = metadata_filter

            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()

            # Extract results from response
            # RAG service returns: {"results": [...], "metadata": {...}}
            results = data.get("results", [])

            logger.info(
                f"RAG query completed: "
                f"query='{query[:50]}...', results={len(results)}"
            )

            return results

        except httpx.HTTPError as e:
            logger.error(f"RAG query failed: {e}")
            return []  # Return empty results on error
        except Exception as e:
            logger.error(f"RAG query error: {e}")
            return []

    async def add_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        document_id: Optional[str] = None
    ) -> bool:
        """
        Add document to RAG service

        BUSINESS PURPOSE:
        Indexes new documentation or code into RAG system. Used during
        codebase indexing phase to populate vector database.

        TECHNICAL IMPLEMENTATION:
        POSTs to RAG service /api/v1/rag/add-document endpoint.
        Document is embedded and stored in ChromaDB collection.

        ARGS:
            content: Document text content
            metadata: Document metadata (source, category, etc.)
            document_id: Optional unique document ID

        RETURNS:
            True if document added successfully, False otherwise

        EXAMPLE:
            success = await rag_service.add_document(
                content="API endpoint: POST /api/v1/projects",
                metadata={"source": "API_DOCS", "category": "projects"}
            )
        """
        try:
            url = f"{self.base_url}/api/v1/rag/add-document"

            payload = {
                "content": content,
                "metadata": metadata,
                "domain": self.collection
            }

            if document_id:
                payload["document_id"] = document_id

            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            logger.info(
                f"Document added to RAG: "
                f"content_length={len(content)}, "
                f"source={metadata.get('source', 'unknown')}"
            )

            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to add document to RAG: {e}")
            return False
        except Exception as e:
            logger.error(f"Error adding document to RAG: {e}")
            return False

    async def hybrid_search(
        self,
        query: str,
        n_results: int = 5,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (vector + BM25)

        BUSINESS PURPOSE:
        Combines semantic search with keyword matching for better
        results. Useful for queries with specific technical terms.

        TECHNICAL IMPLEMENTATION:
        POSTs to RAG service /api/v1/rag/hybrid-search endpoint.
        Combines dense vector search with sparse BM25 retrieval.
        Alpha parameter controls semantic vs keyword weighting.

        ARGS:
            query: Search query
            n_results: Number of results to return
            alpha: Semantic weight (0.0=keyword only, 1.0=semantic only)

        RETURNS:
            List of search results
        """
        try:
            url = f"{self.base_url}/api/v1/rag/hybrid-search"

            payload = {
                "query": query,
                "domain": self.collection,
                "n_results": n_results,
                "alpha": alpha
            }

            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            logger.info(
                f"Hybrid search completed: "
                f"query='{query[:50]}...', results={len(results)}"
            )

            return results

        except httpx.HTTPError as e:
            logger.error(f"Hybrid search failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get RAG service statistics

        BUSINESS PURPOSE:
        Retrieves indexing stats for monitoring and debugging.
        Shows number of indexed documents per collection.

        TECHNICAL IMPLEMENTATION:
        GETs RAG service /api/v1/rag/stats endpoint.

        RETURNS:
            Statistics dictionary with collection counts
        """
        try:
            url = f"{self.base_url}/api/v1/rag/stats"
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get RAG stats: {e}")
            return {}

    async def health_check(self) -> bool:
        """
        Check RAG service health

        BUSINESS PURPOSE:
        Verifies RAG service is running and accessible. Used for
        startup validation and health monitoring.

        TECHNICAL IMPLEMENTATION:
        GETs RAG service /api/v1/rag/health endpoint.

        RETURNS:
            True if service is healthy, False otherwise
        """
        try:
            url = f"{self.base_url}/api/v1/rag/health"
            response = await self.client.get(url)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"RAG health check failed: {e}")
            return False

    async def close(self) -> None:
        """
        Close HTTP client

        BUSINESS PURPOSE:
        Cleanup method for graceful shutdown. Closes HTTP connections.

        TECHNICAL IMPLEMENTATION:
        Closes httpx AsyncClient to release resources.
        """
        await self.client.aclose()
        logger.info("RAG Service client closed")

    def format_context_for_llm(self, results: List[Dict[str, Any]]) -> str:
        """
        Format RAG results for LLM prompt

        BUSINESS PURPOSE:
        Converts RAG search results into structured context for LLM.
        Provides source citations and relevance scores.

        TECHNICAL IMPLEMENTATION:
        Formats each result with numbered headings, content, and metadata.
        Truncates long content to fit within LLM token limits.

        ARGS:
            results: List of RAG search results

        RETURNS:
            Formatted context string for LLM system prompt

        EXAMPLE:
            context = rag_service.format_context_for_llm(results)
            # Returns:
            # \"\"\"
            # RELEVANT CONTEXT FROM CODEBASE:
            #
            # [1] Source: API_DOCUMENTATION.md (Relevance: 0.89)
            # To create a project, call POST /api/v1/projects...
            #
            # [2] Source: WORKFLOWS.md (Relevance: 0.85)
            # Project creation workflow requires...
            # \"\"\"
        """
        if not results:
            return "No relevant context found in codebase."

        context_parts = ["RELEVANT CONTEXT FROM CODEBASE:\n"]

        for i, result in enumerate(results, 1):
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            score = result.get("score", 0.0)

            source = metadata.get("source", "Unknown")

            # Truncate long content
            if len(content) > 500:
                content = content[:500] + "..."

            context_parts.append(
                f"[{i}] Source: {source} (Relevance: {score:.2f})\n"
                f"{content}\n"
            )

        return "\n".join(context_parts)
