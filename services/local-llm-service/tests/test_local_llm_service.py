"""
Local LLM Service Integration Tests

TDD RED PHASE - Comprehensive failing tests for local LLM service.

These tests define the expected behavior for:
- Ollama client initialization
- Simple query generation using Llama 3.1 8B
- Prompt formatting (Llama 3.1 format)
- Response caching for repeated queries
- RAG context summarization
- Conversation history compression
- Structured output/function parameter extraction
- Error handling and retries
- Latency requirements (<300ms for simple queries)

All tests will fail initially until service is implemented (GREEN phase).
"""

import pytest
import asyncio
import time
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock


@pytest.fixture
def sample_simple_query() -> str:
    """Simple query that should be routed to local LLM"""
    return "What is Python?"


@pytest.fixture
def sample_complex_query() -> str:
    """Complex query that requires GPT-4"""
    return "Explain the differences between thread-based parallelism and process-based parallelism in Python, including GIL implications, use cases for each, and how to choose between multiprocessing, threading, and asyncio for a data pipeline that processes 10GB of JSON files."


@pytest.fixture
def sample_rag_context() -> str:
    """Sample RAG context to be summarized"""
    return """
    Course Management API Documentation:

    POST /api/v1/courses - Create a new course
    Request body: {"title": "string", "description": "string", "organization_id": "int"}
    Response: {"course_id": "int", "status": "created"}

    GET /api/v1/courses/{course_id} - Get course details
    Response: {"course_id": "int", "title": "string", "description": "string"}

    PUT /api/v1/courses/{course_id} - Update course
    Request body: {"title": "string", "description": "string"}
    Response: {"status": "updated"}

    DELETE /api/v1/courses/{course_id} - Delete course
    Response: {"status": "deleted"}
    """


@pytest.fixture
def sample_conversation_history() -> List[Dict[str, str]]:
    """Sample conversation history to be compressed"""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hello! How can I help you today?"},
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": "Python is a high-level programming language known for simplicity and readability."},
        {"role": "user", "content": "Tell me about Python features"},
        {"role": "assistant", "content": "Python features include dynamic typing, automatic memory management, rich standard library, and support for multiple programming paradigms."},
        {"role": "user", "content": "How do I create a list in Python?"},
        {"role": "assistant", "content": "You can create a list using square brackets: my_list = [1, 2, 3] or using the list() constructor."},
    ]


@pytest.fixture
def sample_function_schema() -> Dict[str, Any]:
    """Sample function schema for structured output"""
    return {
        "name": "create_course",
        "description": "Create a new course in the platform",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Course title"},
                "description": {"type": "string", "description": "Course description"},
                "organization_id": {"type": "integer", "description": "Organization ID"}
            },
            "required": ["title", "organization_id"]
        }
    }


@pytest.mark.asyncio
class TestLocalLLMServiceInitialization:
    """Test suite for service initialization and health checks"""

    async def test_service_initialization_with_ollama(self):
        """Test that service initializes with Ollama connection"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService(
            base_url="http://localhost:11434",
            model_name="llama3.1:8b-instruct-q4_K_M"
        )

        assert service.base_url == "http://localhost:11434"
        assert service.model_name == "llama3.1:8b-instruct-q4_K_M"
        assert service.client is not None

    async def test_health_check_success(self):
        """Test health check returns True when Ollama is running"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()
        health = await service.health_check()

        assert health is True

    async def test_health_check_failure(self):
        """Test health check returns False when Ollama is not running"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService(base_url="http://localhost:99999")
        health = await service.health_check()

        assert health is False

    async def test_list_available_models(self):
        """Test listing available Ollama models"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()
        models = await service.list_models()

        assert isinstance(models, list)
        assert len(models) > 0
        assert any("llama3.1" in model for model in models)


@pytest.mark.asyncio
class TestSimpleQueryGeneration:
    """Test suite for simple query generation"""

    async def test_generate_response_for_simple_query(self, sample_simple_query):
        """Test generating response for simple query"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()
        response = await service.generate_response(
            prompt=sample_simple_query,
            max_tokens=150,
            temperature=0.7
        )

        assert isinstance(response, str)
        assert len(response) > 0
        assert "python" in response.lower()

    async def test_response_latency_under_300ms(self, sample_simple_query):
        """Test that simple queries return in <300ms"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()

        start_time = time.time()
        response = await service.generate_response(prompt=sample_simple_query)
        latency = (time.time() - start_time) * 1000  # Convert to ms

        assert latency < 300, f"Expected <300ms, got {latency}ms"
        assert len(response) > 0

    async def test_generate_response_with_system_prompt(self, sample_simple_query):
        """Test generating response with custom system prompt"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()
        system_prompt = "You are a concise programming assistant. Answer in 1-2 sentences."

        response = await service.generate_response(
            prompt=sample_simple_query,
            system_prompt=system_prompt,
            max_tokens=100
        )

        assert isinstance(response, str)
        assert len(response) > 0
        assert len(response.split()) < 50  # Should be concise

    async def test_generate_response_with_conversation_context(self):
        """Test generating response with conversation history"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()
        conversation = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
            {"role": "user", "content": "What are its main features?"}
        ]

        response = await service.generate_response_with_context(
            messages=conversation,
            max_tokens=200
        )

        assert isinstance(response, str)
        assert len(response) > 0
        # Response should mention features based on context


@pytest.mark.asyncio
class TestPromptFormatting:
    """Test suite for Llama 3.1 prompt formatting"""

    async def test_format_llama_prompt_simple(self, sample_simple_query):
        """Test formatting simple query in Llama 3.1 format"""
        from local_llm_service.infrastructure.repositories.prompt_formatter import PromptFormatter

        formatter = PromptFormatter()
        formatted = formatter.format_llama_prompt(
            user_message=sample_simple_query,
            system_prompt="You are a helpful assistant."
        )

        assert "<|begin_of_text|>" in formatted
        assert "<|start_header_id|>system<|end_header_id|>" in formatted
        assert "<|start_header_id|>user<|end_header_id|>" in formatted
        assert sample_simple_query in formatted

    async def test_format_llama_prompt_with_conversation_history(self, sample_conversation_history):
        """Test formatting conversation history in Llama 3.1 format"""
        from local_llm_service.infrastructure.repositories.prompt_formatter import PromptFormatter

        formatter = PromptFormatter()
        formatted = formatter.format_conversation(
            messages=sample_conversation_history,
            system_prompt="You are a helpful assistant."
        )

        assert "<|begin_of_text|>" in formatted
        assert formatted.count("<|start_header_id|>user<|end_header_id|>") == 4
        assert formatted.count("<|start_header_id|>assistant<|end_header_id|>") == 4

    async def test_format_function_calling_prompt(self, sample_function_schema):
        """Test formatting prompt for function calling"""
        from local_llm_service.infrastructure.repositories.prompt_formatter import PromptFormatter

        formatter = PromptFormatter()
        formatted = formatter.format_function_calling_prompt(
            user_message="Create a Python course for my organization",
            functions=[sample_function_schema]
        )

        assert "create_course" in formatted
        assert "title" in formatted
        assert "organization_id" in formatted


@pytest.mark.asyncio
class TestResponseCaching:
    """Test suite for response caching"""

    async def test_cache_hit_for_identical_query(self, sample_simple_query):
        """Test that identical query returns cached response"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService(enable_cache=True)

        # First call
        response1 = await service.generate_response(prompt=sample_simple_query)

        # Second call - should hit cache
        start_time = time.time()
        response2 = await service.generate_response(prompt=sample_simple_query)
        cache_latency = (time.time() - start_time) * 1000

        assert response1 == response2
        assert cache_latency < 10, f"Cache should return <10ms, got {cache_latency}ms"

    async def test_cache_miss_for_different_query(self, sample_simple_query):
        """Test that different query doesn't hit cache"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService(enable_cache=True)

        response1 = await service.generate_response(prompt=sample_simple_query)
        response2 = await service.generate_response(prompt="What is Java?")

        assert response1 != response2

    async def test_cache_ttl_expiration(self, sample_simple_query):
        """Test that cache expires after TTL"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService(enable_cache=True, cache_ttl=1)  # 1 second TTL

        # First request - just to populate cache
        _ = await service.generate_response(prompt=sample_simple_query)

        # Wait for cache to expire
        await asyncio.sleep(2)

        # Should generate new response
        response2 = await service.generate_response(prompt=sample_simple_query)

        # Can't assert they're different (might be same answer), but cache should have missed
        assert isinstance(response2, str)

    async def test_cache_statistics(self, sample_simple_query):
        """Test cache hit/miss statistics"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService(enable_cache=True)

        # First call - miss
        await service.generate_response(prompt=sample_simple_query)

        # Second call - hit
        await service.generate_response(prompt=sample_simple_query)

        stats = service.get_cache_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


@pytest.mark.asyncio
class TestRAGContextSummarization:
    """Test suite for RAG context summarization"""

    async def test_summarize_rag_context(self, sample_rag_context):
        """Test summarizing RAG context to reduce tokens"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()
        summary = await service.summarize_rag_context(
            context=sample_rag_context,
            max_summary_tokens=100
        )

        assert isinstance(summary, str)
        assert len(summary) < len(sample_rag_context)
        assert "course" in summary.lower()
        assert "api" in summary.lower()

    async def test_summarization_preserves_key_information(self, sample_rag_context):
        """Test that summarization preserves important facts"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()
        summary = await service.summarize_rag_context(context=sample_rag_context)

        # Should mention CRUD operations
        summary_lower = summary.lower()
        assert any(word in summary_lower for word in ["create", "get", "update", "delete", "post", "put"])

    async def test_batch_summarization(self):
        """Test summarizing multiple RAG contexts in batch"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()
        contexts = [
            "Long text about Python course creation...",
            "Long text about student enrollment...",
            "Long text about analytics dashboard..."
        ]

        summaries = await service.batch_summarize(contexts=contexts, max_tokens=50)

        assert len(summaries) == 3
        assert all(isinstance(s, str) for s in summaries)
        assert all(len(s) < len(c) for s, c in zip(summaries, contexts))


@pytest.mark.asyncio
class TestConversationHistoryCompression:
    """Test suite for conversation history compression"""

    async def test_compress_conversation_history(self, sample_conversation_history):
        """Test compressing conversation history"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()
        compressed = await service.compress_conversation(
            messages=sample_conversation_history,
            target_tokens=200
        )

        assert isinstance(compressed, str)
        assert len(compressed) < sum(len(m["content"]) for m in sample_conversation_history)
        assert "python" in compressed.lower()

    async def test_compression_preserves_conversation_flow(self, sample_conversation_history):
        """Test that compression preserves logical flow"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()
        compressed = await service.compress_conversation(
            messages=sample_conversation_history
        )

        # Should mention the topic (Python) and maintain coherence
        compressed_lower = compressed.lower()
        assert "python" in compressed_lower
        assert any(word in compressed_lower for word in ["programming", "language", "list", "features"])

    async def test_compression_ratio(self, sample_conversation_history):
        """Test that compression achieves significant token reduction"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()

        original_length = sum(len(m["content"]) for m in sample_conversation_history)
        compressed = await service.compress_conversation(messages=sample_conversation_history)
        compressed_length = len(compressed)

        compression_ratio = compressed_length / original_length

        assert compression_ratio < 0.5, f"Expected >50% compression, got {compression_ratio * 100}%"


@pytest.mark.asyncio
class TestStructuredOutputExtraction:
    """Test suite for structured output and function parameter extraction"""

    async def test_extract_function_parameters(self, sample_function_schema):
        """Test extracting function parameters from user message"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()
        user_message = "Create a Python Fundamentals course for organization 5"

        parameters = await service.extract_function_parameters(
            user_message=user_message,
            function_schema=sample_function_schema
        )

        assert isinstance(parameters, dict)
        assert "title" in parameters
        assert "python" in parameters["title"].lower()
        assert "organization_id" in parameters
        assert parameters["organization_id"] == 5

    async def test_structured_json_output(self):
        """Test generating structured JSON output"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()
        prompt = "Extract key information: John Doe enrolled in Python course on 2024-01-15"

        schema = {
            "type": "object",
            "properties": {
                "student_name": {"type": "string"},
                "course_name": {"type": "string"},
                "enrollment_date": {"type": "string"}
            }
        }

        result = await service.generate_structured_output(
            prompt=prompt,
            schema=schema
        )

        assert isinstance(result, dict)
        assert result["student_name"] == "John Doe"
        assert "python" in result["course_name"].lower()
        assert result["enrollment_date"] == "2024-01-15"

    async def test_function_parameter_validation(self, sample_function_schema):
        """Test that extracted parameters match schema requirements"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()
        user_message = "Create a Java course"  # Missing organization_id (required)

        with pytest.raises(ValueError, match="Missing required parameter"):
            await service.extract_function_parameters(
                user_message=user_message,
                function_schema=sample_function_schema
            )


@pytest.mark.asyncio
class TestErrorHandling:
    """Test suite for error handling and retries"""

    async def test_retry_on_connection_error(self, sample_simple_query):
        """Test that service retries on connection errors"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService(max_retries=3, retry_delay=0.1)

        # This will succeed after Ollama is running
        response = await service.generate_response(prompt=sample_simple_query)

        assert isinstance(response, str)

    async def test_timeout_handling(self, sample_complex_query):
        """Test that service times out for long-running queries"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService(timeout=1)  # 1 second timeout

        # Complex query might timeout
        with pytest.raises(asyncio.TimeoutError):
            await service.generate_response(
                prompt=sample_complex_query,
                max_tokens=2000
            )

    async def test_graceful_degradation_on_ollama_down(self, sample_simple_query):
        """Test graceful handling when Ollama is not available"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService(base_url="http://localhost:99999")

        # Should return None or raise specific exception
        result = await service.generate_response(prompt=sample_simple_query)

        assert result is None or isinstance(result, str)

    async def test_invalid_model_handling(self):
        """Test handling of invalid model name"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService(model_name="invalid-model-xyz")

        with pytest.raises(ValueError, match="Model not found"):
            await service.generate_response(prompt="test")


@pytest.mark.asyncio
class TestPerformanceMetrics:
    """Test suite for performance tracking and metrics"""

    async def test_track_response_latency(self, sample_simple_query):
        """Test that service tracks response latency"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()

        await service.generate_response(prompt=sample_simple_query)

        metrics = service.get_metrics()

        assert "avg_latency_ms" in metrics
        assert "total_requests" in metrics
        assert metrics["total_requests"] == 1
        assert metrics["avg_latency_ms"] > 0

    async def test_track_token_usage(self, sample_simple_query):
        """Test that service tracks token usage"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()

        await service.generate_response(prompt=sample_simple_query, max_tokens=100)

        metrics = service.get_metrics()

        assert "total_tokens_generated" in metrics
        assert metrics["total_tokens_generated"] > 0

    async def test_track_cost_savings(self, sample_simple_query):
        """Test that service calculates cost savings vs GPT-4"""
        from local_llm_service.application.services.local_llm_service import LocalLLMService

        service = LocalLLMService()

        # Generate 10 responses
        for _ in range(10):
            await service.generate_response(prompt=sample_simple_query)

        metrics = service.get_metrics()

        assert "estimated_gpt4_cost_usd" in metrics
        assert "cost_savings_usd" in metrics
        assert metrics["cost_savings_usd"] > 0
