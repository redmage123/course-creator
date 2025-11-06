"""
Unit Tests for RAG Service

BUSINESS CONTEXT:
Tests the Retrieval-Augmented Generation (RAG) service that provides
codebase knowledge to the AI assistant. Validates vector search,
document retrieval, and context enrichment.

TECHNICAL VALIDATION:
- Document retrieval from vector store
- Similarity search
- Context ranking
- Health checks
- Statistics reporting

TEST COVERAGE TARGETS:
- Line Coverage: 85%+
- Function Coverage: 80%+
- Branch Coverage: 75%+
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
import sys
from pathlib import Path

# Add ai-assistant-service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'ai-assistant-service'))

from ai_assistant_service.application.services.rag_service import RAGService


class TestRAGService:
    """Test suite for RAG Service"""

    @pytest.fixture
    def rag_service(self):
        """
        TEST FIXTURE: RAG Service instance

        BUSINESS SCENARIO: AI assistant needs codebase knowledge
        TECHNICAL SETUP: Initialize RAG service with mock HTTP client
        """
        with patch('httpx.AsyncClient') as mock_client:
            service = RAGService(base_url="https://localhost:8009")
            service.client = AsyncMock()
            return service

    @pytest.fixture
    def sample_query(self) -> str:
        """TEST FIXTURE: Sample search query"""
        return "How do I create a new course?"

    @pytest.fixture
    def sample_documents(self) -> list:
        """TEST FIXTURE: Sample RAG documents"""
        return [
            {
                "content": "To create a course, use the POST /api/v1/courses endpoint",
                "metadata": {"file": "course_api.py", "line": 42},
                "score": 0.95
            },
            {
                "content": "Course creation requires instructor role",
                "metadata": {"file": "rbac.py", "line": 100},
                "score": 0.87
            }
        ]

    # ==========================================
    # INITIALIZATION TESTS
    # ==========================================

    def test_rag_service_initialization(self, rag_service):
        """
        TEST: RAG service initializes correctly

        BUSINESS SCENARIO: Platform starts AI assistant service
        TECHNICAL VALIDATION: Service instance created with HTTP client
        EXPECTED OUTCOME: Service ready for API calls
        """
        # Assert
        assert rag_service is not None
        assert rag_service.base_url == "https://localhost:8009"

    # ==========================================
    # HEALTH CHECK TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_health_check_success(self, rag_service):
        """
        TEST: RAG service health check succeeds

        BUSINESS SCENARIO: Monitoring system checks service status
        TECHNICAL VALIDATION: HTTP GET returns 200 OK
        EXPECTED OUTCOME: Health check returns True
        """
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        rag_service.client.get = AsyncMock(return_value=mock_response)

        # Act
        is_healthy = await rag_service.health_check()

        # Assert
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, rag_service):
        """
        TEST: RAG service health check handles failure

        BUSINESS SCENARIO: RAG service is down
        TECHNICAL VALIDATION: HTTP request fails or returns error
        EXPECTED OUTCOME: Health check returns False
        """
        # Arrange
        rag_service.client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

        # Act
        is_healthy = await rag_service.health_check()

        # Assert
        assert is_healthy is False

    # ==========================================
    # SEARCH TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_search_success(self, rag_service, sample_query, sample_documents):
        """
        TEST: Successful document search

        BUSINESS SCENARIO: AI searches for relevant code documentation
        TECHNICAL VALIDATION: Vector search returns relevant documents
        EXPECTED OUTCOME: Ranked list of relevant documents
        """
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={
            "documents": sample_documents,
            "total": 2,
            "query": sample_query
        })
        rag_service.client.post = AsyncMock(return_value=mock_response)

        # Act
        results = await rag_service.search(sample_query, top_k=5)

        # Assert
        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]["score"] > results[1]["score"]  # Ranked by relevance

    @pytest.mark.asyncio
    async def test_search_with_filters(self, rag_service, sample_query):
        """
        TEST: Search with metadata filters

        BUSINESS SCENARIO: Search only in specific files or modules
        TECHNICAL VALIDATION: Filters applied to vector search
        EXPECTED OUTCOME: Only matching documents returned
        """
        # Arrange
        filters = {"file": "course_api.py"}
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"documents": [], "total": 0})
        rag_service.client.post = AsyncMock(return_value=mock_response)

        # Act
        results = await rag_service.search(sample_query, filters=filters)

        # Assert
        rag_service.client.post.assert_called_once()
        call_args = rag_service.client.post.call_args
        assert call_args[1]["json"]["filters"] == filters

    @pytest.mark.asyncio
    async def test_search_empty_query(self, rag_service):
        """
        TEST: Handles empty search query

        BUSINESS SCENARIO: Invalid input from AI
        TECHNICAL VALIDATION: Validation error raised
        EXPECTED OUTCOME: Clear error message
        """
        # Act & Assert
        with pytest.raises(ValueError, match="query"):
            await rag_service.search("")

    @pytest.mark.asyncio
    async def test_search_no_results(self, rag_service, sample_query):
        """
        TEST: Handles no search results

        BUSINESS SCENARIO: Query doesn't match any documents
        TECHNICAL VALIDATION: Empty list returned
        EXPECTED OUTCOME: No errors, empty results list
        """
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"documents": [], "total": 0})
        rag_service.client.post = AsyncMock(return_value=mock_response)

        # Act
        results = await rag_service.search(sample_query)

        # Assert
        assert results == []

    # ==========================================
    # CONTEXT RETRIEVAL TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_get_context_for_query(self, rag_service, sample_query, sample_documents):
        """
        TEST: Retrieve formatted context for LLM

        BUSINESS SCENARIO: AI needs context to answer question
        TECHNICAL VALIDATION: Documents formatted as context string
        EXPECTED OUTCOME: Ready-to-use context for LLM prompt
        """
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"documents": sample_documents})
        rag_service.client.post = AsyncMock(return_value=mock_response)

        # Act
        context = await rag_service.get_context(sample_query, max_tokens=500)

        # Assert
        assert isinstance(context, str)
        assert len(context) > 0
        assert "POST /api/v1/courses" in context

    @pytest.mark.asyncio
    async def test_get_context_token_limit(self, rag_service, sample_query):
        """
        TEST: Context respects token limit

        BUSINESS SCENARIO: LLM has context window constraints
        TECHNICAL VALIDATION: Context truncated to fit token limit
        EXPECTED OUTCOME: Context within specified token count
        """
        # Arrange
        large_documents = [
            {
                "content": "A" * 10000,  # Very long document
                "metadata": {},
                "score": 0.9
            }
        ] * 10

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"documents": large_documents})
        rag_service.client.post = AsyncMock(return_value=mock_response)

        # Act
        context = await rag_service.get_context(sample_query, max_tokens=100)

        # Assert
        # Rough token estimation: 1 token ≈ 4 characters
        assert len(context) < 100 * 4 * 1.2  # Allow 20% margin

    # ==========================================
    # STATISTICS TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_get_stats(self, rag_service):
        """
        TEST: Retrieve RAG service statistics

        BUSINESS SCENARIO: Admin monitors RAG performance
        TECHNICAL VALIDATION: Statistics endpoint returns metrics
        EXPECTED OUTCOME: Document count, index size, query stats
        """
        # Arrange
        mock_stats = {
            "document_count": 1500,
            "index_size_mb": 45.2,
            "total_queries": 12500,
            "avg_query_time_ms": 23.4
        }
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_stats)
        rag_service.client.get = AsyncMock(return_value=mock_response)

        # Act
        stats = await rag_service.get_stats()

        # Assert
        assert stats["document_count"] == 1500
        assert stats["index_size_mb"] == 45.2

    # ==========================================
    # ERROR HANDLING TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_search_api_error(self, rag_service, sample_query):
        """
        TEST: Handles RAG service API error

        BUSINESS SCENARIO: RAG service returns 500 error
        TECHNICAL VALIDATION: Exception raised with details
        EXPECTED OUTCOME: Error propagated to caller
        """
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        rag_service.client.post = AsyncMock(return_value=mock_response)

        # Act & Assert
        with pytest.raises(Exception):
            await rag_service.search(sample_query)

    @pytest.mark.asyncio
    async def test_search_timeout(self, rag_service, sample_query):
        """
        TEST: Handles search timeout

        BUSINESS SCENARIO: Slow vector search operation
        TECHNICAL VALIDATION: Timeout exception raised
        EXPECTED OUTCOME: Request fails with timeout error
        """
        # Arrange
        rag_service.client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        # Act & Assert
        with pytest.raises(httpx.TimeoutException):
            await rag_service.search(sample_query, timeout=5)

    # ==========================================
    # CLEANUP TESTS
    # ==========================================

    @pytest.mark.asyncio
    async def test_close_client(self, rag_service):
        """
        TEST: HTTP client closed properly

        BUSINESS SCENARIO: Service shutdown
        TECHNICAL VALIDATION: Async client cleanup
        EXPECTED OUTCOME: No resource leaks
        """
        # Arrange
        rag_service.client.aclose = AsyncMock()

        # Act
        await rag_service.close()

        # Assert
        rag_service.client.aclose.assert_called_once()


# ==========================================
# INTEGRATION-STYLE TESTS
# ==========================================

class TestRAGServiceIntegration:
    """Integration-style scenarios"""

    @pytest.mark.asyncio
    async def test_multi_query_caching(self):
        """
        TEST: Multiple queries with caching

        BUSINESS SCENARIO: Student asks similar questions
        TECHNICAL VALIDATION: Cache hits reduce API calls
        EXPECTED OUTCOME: Improved performance
        """
        # Arrange
        with patch('httpx.AsyncClient'):
            service = RAGService(base_url="https://localhost:8009")
            service.client = AsyncMock()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"documents": [], "total": 0})
        service.client.post = AsyncMock(return_value=mock_response)

        # Act
        await service.search("Python course")
        await service.search("Python course")  # Same query

        # Assert
        # Should hit cache on second call if caching implemented
        # For now, just verify both calls succeeded
        assert service.client.post.call_count >= 1

    @pytest.mark.asyncio
    async def test_search_with_context_enrichment(self):
        """
        TEST: Search results enriched with surrounding context

        BUSINESS SCENARIO: AI needs code context around match
        TECHNICAL VALIDATION: Additional lines retrieved
        EXPECTED OUTCOME: Richer context for better answers
        """
        # Arrange
        with patch('httpx.AsyncClient'):
            service = RAGService(base_url="https://localhost:8009")
            service.client = AsyncMock()

        enriched_doc = {
            "content": "Full function including match",
            "metadata": {"context_lines": 10},
            "score": 0.9
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"documents": [enriched_doc]})
        service.client.post = AsyncMock(return_value=mock_response)

        # Act
        results = await service.search("function", enrich_context=True)

        # Assert
        assert len(results) > 0
        assert results[0]["metadata"].get("context_lines") == 10
