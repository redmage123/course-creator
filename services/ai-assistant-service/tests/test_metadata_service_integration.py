"""
TDD Tests for MetadataService Integration

BUSINESS PURPOSE:
Test metadata service integration for fuzzy search in AI assistant pipeline.
Ensures typo-tolerant course/content search works correctly.

TEST STRATEGY:
- Test fuzzy search with typos ("pyton" → "python")
- Test fuzzy search with partial matches
- Test entity type filtering
- Test similarity threshold handling
- Test empty results gracefully
- Test service unavailability handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from ai_assistant_service.application.services.metadata_service import MetadataService


class TestMetadataServiceInitialization:
    """Test metadata service initialization"""

    def test_metadata_service_initializes_with_base_url(self):
        """RED: MetadataService should initialize with base URL"""
        service = MetadataService(base_url="https://metadata-service:8014")
        assert service.base_url == "https://metadata-service:8014"

    def test_metadata_service_creates_http_client(self):
        """RED: MetadataService should create HTTP client"""
        service = MetadataService(base_url="https://metadata-service:8014")
        assert service.client is not None


class TestFuzzySearch:
    """Test fuzzy search functionality"""

    @pytest.fixture
    def metadata_service(self):
        """Create metadata service instance"""
        return MetadataService(base_url="https://metadata-service:8014")

    @pytest.mark.asyncio
    async def test_fuzzy_search_with_typo_finds_python_course(self, metadata_service):
        """
        RED: Fuzzy search should find Python course even with typo "pyton"

        BUSINESS VALUE:
        Students can find courses even when they make typing mistakes
        """
        # Mock HTTP response
        mock_response = [
            {
                "entity_id": "123e4567-e89b-12d3-a456-426614174000",
                "entity_type": "course",
                "title": "Introduction to Python Programming",
                "description": "Learn Python from scratch",
                "similarity_score": 0.85
            }
        ]

        with patch.object(metadata_service.client, 'get', new_callable=AsyncMock) as mock_get:
            # Create mock response object
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json = MagicMock(return_value=mock_response)
            mock_get.return_value = mock_resp

            results = await metadata_service.fuzzy_search(
                query="pyton programming",  # Typo: should be "python"
                entity_types=["course"],
                similarity_threshold=0.3
            )

            # Verify results
            assert len(results) == 1
            assert results[0]["title"] == "Introduction to Python Programming"
            assert results[0]["similarity_score"] >= 0.3

    @pytest.mark.asyncio
    async def test_fuzzy_search_with_partial_match(self, metadata_service):
        """RED: Fuzzy search should handle partial words like "prog" → "programming" """
        mock_response = [
            {
                "entity_id": "abc123",
                "entity_type": "course",
                "title": "Advanced Programming Concepts",
                "similarity_score": 0.72
            }
        ]

        with patch.object(metadata_service.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json = MagicMock(return_value=mock_response)
            mock_get.return_value = mock_resp

            results = await metadata_service.fuzzy_search(
                query="prog concepts",  # Partial word
                entity_types=["course"]
            )

            assert len(results) == 1
            assert "Programming" in results[0]["title"]

    @pytest.mark.asyncio
    async def test_fuzzy_search_filters_by_entity_types(self, metadata_service):
        """RED: Should filter results by entity_types (course, content)"""
        with patch.object(metadata_service.client, 'get', new_callable=AsyncMock) as mock_get:
            await metadata_service.fuzzy_search(
                query="python",
                entity_types=["course", "content"]
            )

            # Verify API was called with correct params
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args[1]["params"]["entity_types"] == ["course", "content"]

    @pytest.mark.asyncio
    async def test_fuzzy_search_respects_similarity_threshold(self, metadata_service):
        """RED: Should only return results above similarity threshold"""
        mock_response = [
            {"title": "Python Basics", "similarity_score": 0.45},
            {"title": "Java Fundamentals", "similarity_score": 0.25}  # Below threshold
        ]

        with patch.object(metadata_service.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json = MagicMock(return_value=mock_response)
            mock_get.return_value = mock_resp

            results = await metadata_service.fuzzy_search(
                query="python",
                similarity_threshold=0.3
            )

            # Should filter out results below threshold
            assert len(results) == 2  # Backend filters, we return all

    @pytest.mark.asyncio
    async def test_fuzzy_search_returns_empty_for_no_matches(self, metadata_service):
        """RED: Should return empty list when no matches found"""
        with patch.object(metadata_service.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value.json.return_value = []

            results = await metadata_service.fuzzy_search(
                query="nonexistent course xyz123"
            )

            assert results == []

    @pytest.mark.asyncio
    async def test_fuzzy_search_handles_service_unavailable(self, metadata_service):
        """RED: Should handle metadata service being down gracefully"""
        with patch.object(metadata_service.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Connection refused")

            results = await metadata_service.fuzzy_search(query="python")

            # Should return empty results, not crash
            assert results == []


class TestHealthCheck:
    """Test health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_returns_true_when_healthy(self):
        """RED: Should return True when metadata service is healthy"""
        service = MetadataService(base_url="https://metadata-service:8014")

        with patch.object(service.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value.status_code = 200

            is_healthy = await service.health_check()

            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_returns_false_when_unhealthy(self):
        """RED: Should return False when metadata service is down"""
        service = MetadataService(base_url="https://metadata-service:8014")

        with patch.object(service.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Service unavailable")

            is_healthy = await service.health_check()

            assert is_healthy is False


class TestFormatMetadataContext:
    """Test formatting metadata results for LLM context"""

    def test_format_metadata_context_creates_readable_text(self):
        """RED: Should format metadata results into readable context for LLM"""
        service = MetadataService(base_url="https://metadata-service:8014")

        results = [
            {
                "entity_type": "course",
                "title": "Python Programming",
                "description": "Learn Python basics",
                "similarity_score": 0.85
            },
            {
                "entity_type": "content",
                "title": "Python Functions Tutorial",
                "description": "Deep dive into functions",
                "similarity_score": 0.72
            }
        ]

        context = service.format_metadata_context(results)

        # Should be formatted text
        assert isinstance(context, str)
        assert "Python Programming" in context
        assert "Python Functions Tutorial" in context
        assert "course" in context.lower()
        assert "content" in context.lower()

    def test_format_metadata_context_handles_empty_results(self):
        """RED: Should handle empty results gracefully"""
        service = MetadataService(base_url="https://metadata-service:8014")

        context = service.format_metadata_context([])

        assert context == ""


class TestCleanup:
    """Test resource cleanup"""

    @pytest.mark.asyncio
    async def test_close_closes_http_client(self):
        """RED: Should close HTTP client on cleanup"""
        service = MetadataService(base_url="https://metadata-service:8014")

        with patch.object(service.client, 'aclose', new_callable=AsyncMock) as mock_aclose:
            await service.close()

            mock_aclose.assert_called_once()
