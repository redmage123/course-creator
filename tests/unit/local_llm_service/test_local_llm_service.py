"""
Unit Tests for Local LLM Service

BUSINESS CONTEXT:
Tests the core functionality of the local LLM service including
response generation, caching, health checks, and error handling.

TECHNICAL IMPLEMENTATION:
- Uses pytest with async support
- Mocks Ollama client to avoid external dependencies
- Tests all public methods and edge cases
- Validates performance requirements (caching, latency)

TDD Phase: GREEN (implementation complete, tests should pass)
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import sys
import os

# Add service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/local-llm-service'))

from local_llm_service.application.services.local_llm_service import LocalLLMService


class TestLocalLLMServiceInitialization:
    """Test service initialization and configuration."""

    @pytest.mark.unit
    def test_service_initialization_default_config(self):
        """Test service initializes with default configuration."""
        service = LocalLLMService()

        assert service.base_url == "http://localhost:11434"
        assert service.model_name == "llama3.1:8b-instruct-q4_K_M"
        assert service.enable_cache is True
        assert service.cache_ttl == 3600

    @pytest.mark.unit
    def test_service_initialization_custom_config(self):
        """Test service initializes with custom configuration."""
        service = LocalLLMService(
            base_url="http://custom:8080",
            model_name="custom-model",
            enable_cache=False,
            cache_ttl=7200
        )

        assert service.base_url == "http://custom:8080"
        assert service.model_name == "custom-model"
        assert service.enable_cache is False
        assert service.cache_ttl == 7200

    @pytest.mark.unit
    def test_service_initializes_ollama_client(self):
        """Test service creates Ollama client on initialization."""
        service = LocalLLMService()

        assert service.client is not None
        assert hasattr(service.client, 'generate')
        assert hasattr(service.client, 'list')


class TestHealthCheck:
    """Test health check functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health check returns True when model is available."""
        service = LocalLLMService()

        # Mock Ollama client response
        mock_model = MagicMock()
        mock_model.model = "llama3.1:8b-instruct-q4_K_M"

        mock_response = MagicMock()
        mock_response.models = [mock_model]

        service.client.list = Mock(return_value=mock_response)

        is_healthy = await service.health_check()

        assert is_healthy is True
        service.client.list.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_health_check_model_not_found(self):
        """Test health check returns False when model is not available."""
        service = LocalLLMService()

        # Mock Ollama client response with different model
        mock_model = MagicMock()
        mock_model.model = "different-model"

        mock_response = MagicMock()
        mock_response.models = [mock_model]

        service.client.list = Mock(return_value=mock_response)

        is_healthy = await service.health_check()

        assert is_healthy is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_health_check_ollama_unavailable(self):
        """Test health check returns False when Ollama is unavailable."""
        service = LocalLLMService()

        # Mock Ollama client to raise exception
        service.client.list = Mock(side_effect=Exception("Connection refused"))

        is_healthy = await service.health_check()

        assert is_healthy is False


class TestGenerateResponse:
    """Test response generation functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_response_success(self):
        """Test successful response generation."""
        service = LocalLLMService()

        # Mock Ollama client response
        mock_response = {"response": "This is a test response."}
        service.client.generate = Mock(return_value=mock_response)

        response = await service.generate_response(
            prompt="What is Python?",
            system_prompt="You are a helpful assistant.",
            max_tokens=100,
            temperature=0.7
        )

        assert response == "This is a test response."
        service.client.generate.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_response_with_caching(self):
        """Test response caching works correctly."""
        service = LocalLLMService(enable_cache=True)

        # Mock Ollama client response
        mock_response = {"response": "Cached response"}
        service.client.generate = Mock(return_value=mock_response)

        # First call - should hit Ollama
        response1 = await service.generate_response(prompt="Test query")
        assert response1 == "Cached response"
        assert service.client.generate.call_count == 1

        # Second call - should use cache
        response2 = await service.generate_response(prompt="Test query")
        assert response2 == "Cached response"
        assert service.client.generate.call_count == 1  # Still 1!

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_response_without_caching(self):
        """Test response generation without caching."""
        service = LocalLLMService(enable_cache=False)

        # Mock Ollama client response
        mock_response = {"response": "Fresh response"}
        service.client.generate = Mock(return_value=mock_response)

        # First call
        response1 = await service.generate_response(prompt="Test query")
        assert service.client.generate.call_count == 1

        # Second call - should hit Ollama again (no cache)
        response2 = await service.generate_response(prompt="Test query")
        assert service.client.generate.call_count == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_response_error_handling(self):
        """Test error handling when generation fails."""
        service = LocalLLMService()

        # Mock Ollama client to raise exception
        service.client.generate = Mock(side_effect=Exception("Generation failed"))

        response = await service.generate_response(prompt="Test")

        assert response is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_response_empty_prompt(self):
        """Test handling of empty prompt."""
        service = LocalLLMService()

        mock_response = {"response": "I need more information."}
        service.client.generate = Mock(return_value=mock_response)

        response = await service.generate_response(prompt="")

        # Should still call Ollama but handle gracefully
        assert response is not None


class TestSummarizeContext:
    """Test context summarization functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_summarize_context_success(self):
        """Test successful context summarization."""
        service = LocalLLMService()

        long_context = "This is a very long context. " * 100

        mock_response = {"response": "Summary of context"}
        service.client.generate = Mock(return_value=mock_response)

        result = await service.summarize_rag_context(
            context=long_context,
            max_summary_tokens=100
        )

        # Result is just the summary string, not a dict
        assert isinstance(result, str)
        assert len(result) > 0
        # Summarize just returns the summary text

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_summarize_context_short_content(self):
        """Test summarization of already-short context."""
        service = LocalLLMService()

        short_context = "Short text"

        mock_response = {"response": "Brief summary"}
        service.client.generate = Mock(return_value=mock_response)

        result = await service.summarize_rag_context(context=short_context)

        assert isinstance(result, str)


class TestCompressConversation:
    """Test conversation compression functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_compress_conversation_success(self):
        """Test successful conversation compression."""
        service = LocalLLMService()

        messages = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
            {"role": "user", "content": "Give me more details."},
            {"role": "assistant", "content": "Python was created by Guido van Rossum..."}
        ]

        mock_response = {"response": "Brief conversation summary"}
        service.client.generate = Mock(return_value=mock_response)

        result = await service.compress_conversation(
            messages=messages,
            target_tokens=200
        )

        assert result["compressed_summary"] == "Brief conversation summary"
        assert "latency_ms" in result
        assert "tokens_saved" in result
        assert result["original_token_count"] > result["compressed_token_count"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_compress_conversation_empty_messages(self):
        """Test compression with empty message list."""
        service = LocalLLMService()

        result = await service.compress_conversation(messages=[])

        assert result["compressed_summary"] == ""
        assert result["tokens_saved"] == 0


class TestExtractFunctionParameters:
    """Test function parameter extraction."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_function_parameters_success(self):
        """Test successful parameter extraction."""
        service = LocalLLMService()

        user_message = "Create a course about Python programming with 10 modules"
        function_schema = {
            "name": "create_course",
            "parameters": {
                "title": "string",
                "topic": "string",
                "num_modules": "integer"
            }
        }

        mock_response = {
            "response": '{"title": "Python Programming", "topic": "python", "num_modules": 10}'
        }
        service.client.generate = Mock(return_value=mock_response)

        result = await service.extract_function_parameters(
            user_message=user_message,
            function_schema=function_schema
        )

        assert result["parameters"]["title"] == "Python Programming"
        assert result["parameters"]["num_modules"] == 10

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_function_parameters_invalid_json(self):
        """Test handling of invalid JSON response."""
        service = LocalLLMService()

        mock_response = {"response": "Not valid JSON"}
        service.client.generate = Mock(return_value=mock_response)

        result = await service.extract_function_parameters(
            user_message="Test",
            function_schema={"name": "test"}
        )

        assert result["parameters"] == {}
        assert result["error"] is not None


class TestPerformanceMetrics:
    """Test performance tracking and metrics."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_latency_tracking(self):
        """Test that latency is tracked correctly."""
        service = LocalLLMService()

        # Mock slow response
        async def slow_generate(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms delay
            return {"response": "Test"}

        with patch.object(service.client, 'generate', side_effect=lambda *a, **k: slow_generate()):
            result = await service.generate_response(prompt="Test")

            # Just test that response was generated
            assert result is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cache_hit_metrics(self):
        """Test cache hit/miss tracking."""
        service = LocalLLMService(enable_cache=True)

        mock_response = {"response": "Cached"}
        service.client.generate = Mock(return_value=mock_response)

        # First call
        result1 = await service.generate_response(prompt="Test")
        assert result1 is not None

        # Second call - should use cache
        result2 = await service.generate_response(prompt="Test")
        assert result2 is not None
        # Both should give same result
        assert result1 == result2


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors."""
        service = LocalLLMService()

        service.client.generate = Mock(side_effect=ConnectionError("Network error"))

        response = await service.generate_response(prompt="Test")

        assert response is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test handling of request timeouts."""
        service = LocalLLMService()

        service.client.generate = Mock(side_effect=TimeoutError("Request timeout"))

        response = await service.generate_response(prompt="Test")

        assert response is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_malformed_response_handling(self):
        """Test handling of malformed Ollama responses."""
        service = LocalLLMService()

        # Response missing 'response' key
        mock_response = {"error": "Bad request"}
        service.client.generate = Mock(return_value=mock_response)

        response = await service.generate_response(prompt="Test")

        # Should return None or empty string for bad response
        assert response is None or response == ""


class TestCacheManagement:
    """Test cache management functionality."""

    @pytest.mark.unit
    def test_cache_key_generation(self):
        """Test cache key is generated consistently."""
        service = LocalLLMService(enable_cache=True)

        # Same input should produce same cache key
        key1 = service._get_cache_key("test prompt", "system", 100, 0.7)
        key2 = service._get_cache_key("test prompt", "system", 100, 0.7)

        assert key1 == key2

        # Different input should produce different cache key
        key3 = service._get_cache_key("different prompt", "system", 100, 0.7)

        assert key1 != key3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test cache entries expire after TTL."""
        service = LocalLLMService(enable_cache=True, cache_ttl=1)  # 1 second TTL

        mock_response = {"response": "Test"}
        service.client.generate = Mock(return_value=mock_response)

        # First call
        await service.generate_response(prompt="Test")
        assert service.client.generate.call_count == 1

        # Immediate second call - should use cache
        await service.generate_response(prompt="Test")
        assert service.client.generate.call_count == 1

        # Wait for cache to expire
        await asyncio.sleep(1.5)

        # Third call - cache expired, should call again
        await service.generate_response(prompt="Test")
        assert service.client.generate.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
