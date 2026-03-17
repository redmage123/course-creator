"""
MetadataService - Integration with Metadata Service

BUSINESS PURPOSE:
Provides fuzzy search capability for courses and content, enabling
students to find materials even with typos or partial matches.

TECHNICAL IMPLEMENTATION:
HTTP client integration with metadata-service (port 8014).
Uses pg_trgm for similarity-based fuzzy matching.

USAGE:
    metadata_service = MetadataService(base_url="https://metadata-service:8014")
    results = await metadata_service.fuzzy_search(
        query="pyton programming",  # Typo intentional
        entity_types=["course"],
        similarity_threshold=0.3
    )
"""

import logging
from typing import List, Dict, Any, Optional
import httpx


logger = logging.getLogger(__name__)


class MetadataService:
    """
    Integration with Metadata Service for fuzzy search

    RESPONSIBILITIES:
    - Fuzzy search for courses and content with typo tolerance
    - Filter by entity types (course, content, etc.)
    - Format results for LLM context
    - Health check metadata service

    ATTRIBUTES:
        base_url: Base URL of metadata service
        client: HTTP client for API calls
    """

    def __init__(self, base_url: str):
        """
        Initialize Metadata Service client

        Args:
            base_url: Base URL of metadata service (e.g., "https://metadata-service:8014")
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            timeout=10.0,
            verify=False  # Skip SSL verification for self-signed certs
        )

        logger.info(f"Initialized MetadataService: {self.base_url}")

    async def fuzzy_search(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        similarity_threshold: float = 0.3,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fuzzy search for courses and content

        BUSINESS VALUE:
        Students can find courses even with typos:
        - "pyton" → "python"
        - "prog" → "programming"
        - "machne lerning" → "machine learning"

        Args:
            query: Search query (typos allowed!)
            entity_types: Filter by entity types (course, content, etc.)
            similarity_threshold: Minimum similarity (0.0-1.0, default 0.3)
            limit: Maximum results (default 10)

        Returns:
            List of matching entities with similarity scores

        Example:
            results = await metadata_service.fuzzy_search(
                query="pyton basics",
                entity_types=["course"],
                similarity_threshold=0.3
            )
            # [
            #   {
            #     "entity_id": "...",
            #     "entity_type": "course",
            #     "title": "Python Basics",
            #     "description": "...",
            #     "similarity_score": 0.85
            #   }
            # ]
        """
        try:
            # Build request parameters
            params = {
                "query": query,
                "similarity_threshold": similarity_threshold,
                "limit": limit
            }

            if entity_types:
                params["entity_types"] = entity_types

            # Call metadata service API
            response = await self.client.get(
                f"{self.base_url}/api/v1/metadata/fuzzy-search",
                params=params
            )

            if response.status_code == 200:
                results = response.json()
                logger.info(
                    f"Fuzzy search found {len(results)} results for query: '{query}'"
                )
                return results
            else:
                logger.warning(
                    f"Metadata service returned {response.status_code} "
                    f"for query: '{query}'"
                )
                return []

        except Exception as e:
            logger.error(f"Metadata service fuzzy search failed: {e}")
            # Return empty results instead of failing - graceful degradation
            return []

    async def health_check(self) -> bool:
        """
        Check if metadata service is healthy

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/health",
                timeout=2.0
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Metadata service health check failed: {e}")
            return False

    def format_metadata_context(self, results: List[Dict[str, Any]]) -> str:
        """
        Format metadata search results for LLM context

        BUSINESS PURPOSE:
        Converts metadata search results into readable text that LLM
        can use to provide better answers about courses and content.

        Args:
            results: List of metadata search results

        Returns:
            Formatted context string for LLM

        Example:
            context = service.format_metadata_context(results)
            # "METADATA CONTEXT:
            # - Course: 'Python Programming' (similarity: 0.85)
            #   Learn Python basics and fundamentals
            # - Content: 'Python Functions Tutorial' (similarity: 0.72)
            #   Deep dive into Python functions"
        """
        if not results:
            return ""

        context_lines = ["METADATA CONTEXT:"]

        for result in results[:5]:  # Limit to top 5 for conciseness
            entity_type = result.get("entity_type", "unknown")
            title = result.get("title", "Untitled")
            description = result.get("description", "No description")
            similarity = result.get("similarity_score", 0.0)

            # Capitalize entity type for readability
            entity_type_display = entity_type.title()

            context_lines.append(
                f"- {entity_type_display}: '{title}' (similarity: {similarity:.2f})"
            )

            # Add description if available (truncated)
            if description and description != "No description":
                desc_truncated = (
                    description[:100] + "..."
                    if len(description) > 100
                    else description
                )
                context_lines.append(f"  {desc_truncated}")

        return "\n".join(context_lines) + "\n"

    async def close(self):
        """
        Close HTTP client

        CLEANUP:
        Call this when shutting down the service to release resources
        """
        await self.client.aclose()
        logger.info("Metadata service client closed")
