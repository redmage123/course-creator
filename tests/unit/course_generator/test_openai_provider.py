"""
Unit Tests for OpenAI LLM Provider

BUSINESS CONTEXT:
Tests the OpenAI provider implementation's ability to:
- Analyze images using GPT-5.2 and GPT-4o vision models
- Generate text completions with proper error handling
- Handle rate limiting, authentication errors, and API failures
- Estimate token costs accurately
- Provide health check functionality

TECHNICAL IMPLEMENTATION:
- Uses pytest with async support via pytest.mark.asyncio
- Mocks httpx AsyncClient for API calls
- Tests error handling and retry logic
- Validates request formatting and response parsing
- Tests token counting and cost estimation

WHY:
The OpenAI provider is the primary LLM provider for screenshot-to-course
generation. Comprehensive testing ensures reliable operation, proper error
handling, and accurate cost tracking.
"""

import asyncio
import base64
import json
import pytest
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4

import httpx

from course_generator.infrastructure.llm_providers.openai_provider import OpenAIProvider
from course_generator.infrastructure.llm_providers.base_provider import (
    LLMProviderCapabilities,
    LLMResponse,
    VisionAnalysisResult
)
from shared.exceptions import (
    LLMProviderException,
    LLMProviderConnectionException,
    LLMProviderAuthenticationException,
    LLMProviderRateLimitException,
    LLMProviderResponseException
)


class TestOpenAIProviderInitialization:
    """
    Test Suite for OpenAI Provider Initialization

    BUSINESS CONTEXT:
    Tests that the provider initializes correctly with various configuration
    options, enabling organization-specific LLM configurations.
    """

    def test_initialization_with_defaults(self):
        """Test provider initialization with default configuration"""
        provider = OpenAIProvider(api_key="test-key")

        assert provider.api_key == "test-key"
        assert provider.base_url == OpenAIProvider.DEFAULT_BASE_URL
        assert provider.model == OpenAIProvider.DEFAULT_MODEL
        assert provider.timeout == 120.0
        assert provider.max_retries == 3
        assert provider._client is not None

    def test_initialization_with_custom_config(self):
        """Test provider initialization with custom configuration"""
        org_id = uuid4()
        provider = OpenAIProvider(
            api_key="custom-key",
            base_url="https://custom.openai.com/v1",
            model="gpt-4o",
            organization_id=org_id,
            timeout=60.0,
            max_retries=5
        )

        assert provider.api_key == "custom-key"
        assert provider.base_url == "https://custom.openai.com/v1"
        assert provider.model == "gpt-4o"
        assert provider.organization_id == org_id
        assert provider.timeout == 60.0
        assert provider.max_retries == 5

    def test_provider_name(self):
        """Test provider_name property returns correct value"""
        provider = OpenAIProvider(api_key="test-key")
        assert provider.provider_name == "openai"

    def test_default_model_property(self):
        """Test default_model property returns correct value"""
        provider = OpenAIProvider(api_key="test-key")
        assert provider.default_model == "gpt-5.2"

    def test_default_vision_model_property(self):
        """Test default_vision_model property returns correct value"""
        provider = OpenAIProvider(api_key="test-key")
        assert provider.default_vision_model == "gpt-5.2"

    def test_http_client_initialization(self):
        """Test that HTTP client is initialized with correct headers"""
        provider = OpenAIProvider(api_key="test-key-123")

        assert provider._client is not None
        assert provider._client.headers["Authorization"] == "Bearer test-key-123"
        assert provider._client.headers["Content-Type"] == "application/json"
        assert provider._client.timeout.connect == 120.0


class TestOpenAIProviderCapabilities:
    """
    Test Suite for OpenAI Provider Capabilities

    BUSINESS CONTEXT:
    Tests capability detection for feature availability, enabling the system
    to select appropriate providers based on required features.
    """

    def test_get_capabilities_structure(self):
        """Test that get_capabilities returns correct structure"""
        provider = OpenAIProvider(api_key="test-key")
        capabilities = provider.get_capabilities()

        assert isinstance(capabilities, LLMProviderCapabilities)
        assert capabilities.supports_vision is True
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is True
        assert capabilities.supports_json_mode is True

    def test_capabilities_token_limits(self):
        """Test that capabilities include correct token limits"""
        provider = OpenAIProvider(api_key="test-key")
        capabilities = provider.get_capabilities()

        assert capabilities.max_tokens == 128000
        assert capabilities.context_window == 128000

    def test_capabilities_image_support(self):
        """Test that capabilities include correct image support"""
        provider = OpenAIProvider(api_key="test-key")
        capabilities = provider.get_capabilities()

        assert capabilities.max_image_size_mb == 20.0
        assert "image/png" in capabilities.supported_image_formats
        assert "image/jpeg" in capabilities.supported_image_formats
        assert "image/webp" in capabilities.supported_image_formats
        assert "image/gif" in capabilities.supported_image_formats

    def test_capabilities_rate_limits(self):
        """Test that capabilities include rate limit information"""
        provider = OpenAIProvider(api_key="test-key")
        capabilities = provider.get_capabilities()

        assert capabilities.rate_limit_requests_per_minute == 500


class TestOpenAIProviderImageAnalysis:
    """
    Test Suite for OpenAI Provider Image Analysis

    BUSINESS CONTEXT:
    Tests the core screenshot-to-course functionality, ensuring accurate
    image analysis and content extraction with GPT-5.2 vision models.
    """

    @pytest.mark.asyncio
    async def test_analyze_image_with_bytes(self):
        """Test image analysis with raw image bytes"""
        provider = OpenAIProvider(api_key="test-key")

        # Create sample PNG image bytes (PNG magic bytes)
        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        # Mock response
        mock_response_data = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "extracted_text": "Test course content",
                        "detected_language": "en",
                        "confidence_score": 0.95,
                        "title": "Test Course",
                        "description": "A test course description",
                        "topics": ["Topic 1", "Topic 2"],
                        "difficulty": "intermediate",
                        "duration_hours": 10
                    })
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 1000,
                "completion_tokens": 500,
                "total_tokens": 1500
            }
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Analyze this screenshot"
            )

        assert isinstance(result, VisionAnalysisResult)
        assert result.extracted_text == "Test course content"
        assert result.detected_language == "en"
        assert result.confidence_score == 0.95
        assert result.suggested_title == "Test Course"
        assert result.suggested_description == "A test course description"
        assert result.suggested_topics == ["Topic 1", "Topic 2"]
        assert result.suggested_difficulty == "intermediate"
        assert result.suggested_duration_hours == 10
        assert result.model_used == "gpt-5.2"
        assert result.provider_used == "openai"
        assert result.tokens_used == 1500

    @pytest.mark.asyncio
    async def test_analyze_image_with_base64_string(self):
        """Test image analysis with base64-encoded string"""
        provider = OpenAIProvider(api_key="test-key")

        # Create base64 string
        image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        mock_response_data = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "extracted_text": "Base64 test content",
                        "confidence_score": 0.9
                    })
                }
            }],
            "usage": {"total_tokens": 1000}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            result = await provider.analyze_image(
                image_data=image_base64,
                prompt="Analyze"
            )

        assert result.extracted_text == "Base64 test content"
        assert result.confidence_score == 0.9

    @pytest.mark.asyncio
    async def test_analyze_image_with_custom_model(self):
        """Test image analysis with custom vision model"""
        provider = OpenAIProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response_data = {
            "choices": [{"message": {"content": json.dumps({"extracted_text": "Test"})}}],
            "usage": {"total_tokens": 100}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Analyze",
                model="gpt-4o"
            )

        # Verify custom model was used
        call_args = mock_request.call_args
        request_body = call_args[0][1]
        assert request_body["model"] == "gpt-4o"
        assert result.model_used == "gpt-4o"

    @pytest.mark.asyncio
    async def test_analyze_image_request_format(self):
        """Test that image analysis request is formatted correctly"""
        provider = OpenAIProvider(api_key="test-key")

        image_bytes = b'\xff\xd8\xff\xe0'  # JPEG magic bytes
        prompt = "Extract course content from this screenshot"

        mock_response_data = {
            "choices": [{"message": {"content": json.dumps({"extracted_text": "Test"})}}],
            "usage": {"total_tokens": 100}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            await provider.analyze_image(
                image_data=image_bytes,
                prompt=prompt,
                max_tokens=2048,
                temperature=0.5
            )

        # Verify request structure
        call_args = mock_request.call_args
        endpoint, request_body = call_args[0]

        assert endpoint == "/chat/completions"
        assert request_body["model"] == "gpt-5.2"
        assert request_body["max_tokens"] == 2048
        assert request_body["temperature"] == 0.5
        assert request_body["response_format"] == {"type": "json_object"}

        # Verify message structure
        messages = request_body["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert len(messages[0]["content"]) == 2

        # Verify text content
        text_content = messages[0]["content"][0]
        assert text_content["type"] == "text"
        assert text_content["text"] == prompt

        # Verify image content
        image_content = messages[0]["content"][1]
        assert image_content["type"] == "image_url"
        assert image_content["image_url"]["detail"] == "high"
        assert "data:image/jpeg;base64," in image_content["image_url"]["url"]

    @pytest.mark.asyncio
    async def test_analyze_image_with_default_prompt(self):
        """Test that default prompt is used when none provided"""
        provider = OpenAIProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response_data = {
            "choices": [{"message": {"content": json.dumps({"extracted_text": "Test"})}}],
            "usage": {"total_tokens": 100}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            await provider.analyze_image(image_data=image_bytes, prompt="")

        call_args = mock_request.call_args
        request_body = call_args[0][1]

        # Verify default prompt contains expected keywords
        text_content = request_body["messages"][0]["content"][0]["text"]
        assert "Course Title" in text_content
        assert "Topics/Sections" in text_content
        assert "JSON format" in text_content

    @pytest.mark.asyncio
    async def test_analyze_image_handles_non_json_response(self):
        """Test that non-JSON responses are handled gracefully"""
        provider = OpenAIProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        # Response is plain text, not JSON
        mock_response_data = {
            "choices": [{
                "message": {
                    "content": "This is plain text, not JSON"
                }
            }],
            "usage": {"total_tokens": 100}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Analyze"
            )

        # Should wrap plain text in extracted_text field
        assert result.extracted_text == "This is plain text, not JSON"

    @pytest.mark.asyncio
    async def test_analyze_image_calculates_processing_time(self):
        """Test that processing time is calculated"""
        provider = OpenAIProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response_data = {
            "choices": [{"message": {"content": json.dumps({"extracted_text": "Test"})}}],
            "usage": {"total_tokens": 100}
        }

        async def delayed_request(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate 100ms delay
            return mock_response_data

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = delayed_request

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Analyze"
            )

        # Processing time should be approximately 100ms
        assert result.processing_time_ms >= 100
        assert result.processing_time_ms < 200


class TestOpenAIProviderTextGeneration:
    """
    Test Suite for OpenAI Provider Text Generation

    BUSINESS CONTEXT:
    Tests text completion functionality for course content generation,
    quiz creation, and other AI-powered features.
    """

    @pytest.mark.asyncio
    async def test_generate_text_basic(self):
        """Test basic text generation"""
        provider = OpenAIProvider(api_key="test-key")

        mock_response_data = {
            "choices": [{
                "message": {
                    "content": "Generated course content here"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 200,
                "total_tokens": 300
            }
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            result = await provider.generate_text(
                prompt="Generate a course outline"
            )

        assert isinstance(result, LLMResponse)
        assert result.content == "Generated course content here"
        assert result.model == "gpt-5.2"
        assert result.provider == "openai"
        assert result.input_tokens == 100
        assert result.output_tokens == 200
        assert result.total_tokens == 300
        assert result.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_generate_text_with_system_prompt(self):
        """Test text generation with system prompt"""
        provider = OpenAIProvider(api_key="test-key")

        mock_response_data = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {"total_tokens": 100}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            await provider.generate_text(
                prompt="Create a quiz",
                system_prompt="You are a helpful course creation assistant"
            )

        call_args = mock_request.call_args
        request_body = call_args[0][1]

        messages = request_body["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful course creation assistant"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Create a quiz"

    @pytest.mark.asyncio
    async def test_generate_text_with_json_mode(self):
        """Test text generation with JSON mode enabled"""
        provider = OpenAIProvider(api_key="test-key")

        mock_response_data = {
            "choices": [{"message": {"content": '{"quiz": "content"}'}}],
            "usage": {"total_tokens": 100}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            await provider.generate_text(
                prompt="Generate quiz JSON",
                json_mode=True
            )

        call_args = mock_request.call_args
        request_body = call_args[0][1]

        assert request_body["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_generate_text_with_custom_model(self):
        """Test text generation with custom model"""
        provider = OpenAIProvider(api_key="test-key", model="gpt-5.2")

        mock_response_data = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {"total_tokens": 100}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            result = await provider.generate_text(
                prompt="Test",
                model="gpt-4o-mini"
            )

        call_args = mock_request.call_args
        request_body = call_args[0][1]

        assert request_body["model"] == "gpt-4o-mini"
        assert result.model == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_generate_text_request_parameters(self):
        """Test that text generation request includes all parameters"""
        provider = OpenAIProvider(api_key="test-key")

        mock_response_data = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {"total_tokens": 100}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            await provider.generate_text(
                prompt="Test prompt",
                max_tokens=2048,
                temperature=0.9
            )

        call_args = mock_request.call_args
        endpoint, request_body = call_args[0]

        assert endpoint == "/chat/completions"
        assert request_body["max_tokens"] == 2048
        assert request_body["temperature"] == 0.9

    @pytest.mark.asyncio
    async def test_generate_text_includes_cost_metadata(self):
        """Test that response includes cost estimation metadata"""
        provider = OpenAIProvider(api_key="test-key")

        mock_response_data = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {
                "prompt_tokens": 1000,
                "completion_tokens": 2000,
                "total_tokens": 3000
            }
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            result = await provider.generate_text(prompt="Test")

        assert "input_cost_per_million" in result.metadata
        assert "output_cost_per_million" in result.metadata
        assert result.metadata["input_cost_per_million"] == 5.00  # GPT-5.2 input price
        assert result.metadata["output_cost_per_million"] == 15.00  # GPT-5.2 output price


class TestOpenAIProviderTokenCounting:
    """
    Test Suite for Token Counting and Cost Estimation

    BUSINESS CONTEXT:
    Tests accurate token counting and cost estimation for budget tracking
    and billing purposes across organizations.
    """

    @pytest.mark.asyncio
    async def test_token_counts_in_response(self):
        """Test that token counts are correctly extracted from API response"""
        provider = OpenAIProvider(api_key="test-key")

        mock_response_data = {
            "choices": [{"message": {"content": "Test"}}],
            "usage": {
                "prompt_tokens": 150,
                "completion_tokens": 250,
                "total_tokens": 400
            }
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            result = await provider.generate_text(prompt="Test")

        assert result.input_tokens == 150
        assert result.output_tokens == 250
        assert result.total_tokens == 400

    def test_cost_estimation_for_gpt52(self):
        """Test cost estimation for GPT-5.2 model"""
        response = LLMResponse(
            content="Test",
            model="gpt-5.2",
            provider="openai",
            input_tokens=1_000_000,  # 1M input tokens
            output_tokens=500_000,   # 500K output tokens
            metadata={
                "input_cost_per_million": 5.00,
                "output_cost_per_million": 15.00
            }
        )

        # Cost = (1M * $5.00) + (0.5M * $15.00) = $5.00 + $7.50 = $12.50
        assert response.estimated_cost == 12.50

    def test_cost_estimation_for_gpt4o_mini(self):
        """Test cost estimation for GPT-4o-mini model"""
        response = LLMResponse(
            content="Test",
            model="gpt-4o-mini",
            provider="openai",
            input_tokens=1_000_000,  # 1M input tokens
            output_tokens=1_000_000,  # 1M output tokens
            metadata={
                "input_cost_per_million": 0.15,
                "output_cost_per_million": 0.60
            }
        )

        # Cost = (1M * $0.15) + (1M * $0.60) = $0.15 + $0.60 = $0.75
        assert response.estimated_cost == 0.75


class TestOpenAIProviderErrorHandling:
    """
    Test Suite for Error Handling

    BUSINESS CONTEXT:
    Tests proper error handling for authentication failures, rate limits,
    API errors, and network issues. Critical for reliable service operation
    and graceful degradation.
    """

    @pytest.mark.asyncio
    async def test_authentication_error_401(self):
        """Test handling of 401 authentication errors"""
        provider = OpenAIProvider(api_key="invalid-key")

        mock_response = Mock()
        mock_response.status_code = 401

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderAuthenticationException) as exc_info:
                await provider._make_request("/chat/completions", {})

            assert "Invalid API key" in str(exc_info.value) or "authentication" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rate_limit_error_429(self):
        """Test handling of 429 rate limit errors"""
        provider = OpenAIProvider(api_key="test-key", max_retries=0)

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "30"}

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderRateLimitException) as exc_info:
                await provider._make_request("/chat/completions", {})

            # Verify rate limit exception was raised with retry_after info
            assert "rate limit" in str(exc_info.value).lower() or "retry" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rate_limit_retry_with_backoff(self):
        """Test that rate limit triggers retry with exponential backoff"""
        provider = OpenAIProvider(api_key="test-key", max_retries=2)

        # First two calls return 429, third succeeds
        mock_rate_limit_response = Mock()
        mock_rate_limit_response.status_code = 429
        mock_rate_limit_response.headers = {"Retry-After": "1"}

        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {"result": "success"}

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = [
                mock_rate_limit_response,
                mock_rate_limit_response,
                mock_success_response
            ]

            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await provider._make_request("/chat/completions", {})

            assert result == {"result": "success"}
            assert mock_post.call_count == 3
            assert mock_sleep.call_count == 2  # Two retry sleeps

    @pytest.mark.asyncio
    async def test_server_error_500_with_retry(self):
        """Test handling of 500 server errors with retry logic"""
        provider = OpenAIProvider(api_key="test-key", max_retries=2)

        # First call returns 500, second succeeds
        mock_error_response = Mock()
        mock_error_response.status_code = 500

        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {"result": "success"}

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = [mock_error_response, mock_success_response]

            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await provider._make_request("/chat/completions", {})

            assert result == {"result": "success"}
            assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_server_error_exhausted_retries(self):
        """Test that server errors raise exception after max retries"""
        provider = OpenAIProvider(api_key="test-key", max_retries=1)

        mock_error_response = Mock()
        mock_error_response.status_code = 503

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_error_response

            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(LLMProviderResponseException) as exc_info:
                    await provider._make_request("/chat/completions", {})

            # Verify server error exception was raised
            assert "error" in str(exc_info.value).lower() or "503" in str(exc_info.value)
            assert mock_post.call_count == 2  # Initial + 1 retry

    @pytest.mark.asyncio
    async def test_api_response_error_with_message(self):
        """Test handling of API errors with error message in response"""
        provider = OpenAIProvider(api_key="test-key")

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.content = b'{"error": {"message": "Invalid request parameters"}}'
        mock_response.json.return_value = {
            "error": {"message": "Invalid request parameters"}
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderResponseException) as exc_info:
                await provider._make_request("/chat/completions", {})

            assert "Invalid request parameters" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_connection_error_with_retry(self):
        """Test handling of connection errors with retry logic"""
        provider = OpenAIProvider(api_key="test-key", max_retries=2)

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            # First two calls raise connection error, third succeeds
            mock_post.side_effect = [
                httpx.ConnectError("Connection refused"),
                httpx.ConnectError("Connection refused"),
                Mock(status_code=200, json=lambda: {"result": "success"})
            ]

            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await provider._make_request("/chat/completions", {})

            assert result == {"result": "success"}
            assert mock_post.call_count == 3

    @pytest.mark.asyncio
    async def test_connection_error_exhausted_retries(self):
        """Test that connection errors raise exception after max retries"""
        provider = OpenAIProvider(api_key="test-key", max_retries=1)

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")

            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(LLMProviderConnectionException) as exc_info:
                    await provider._make_request("/chat/completions", {})

            assert "Connection refused" in str(exc_info.value)
            assert mock_post.call_count == 2  # Initial + 1 retry

    @pytest.mark.asyncio
    async def test_timeout_error_with_retry(self):
        """Test handling of timeout errors with retry logic"""
        provider = OpenAIProvider(api_key="test-key", max_retries=1)

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            # First call times out, second succeeds
            mock_post.side_effect = [
                httpx.TimeoutException("Request timed out"),
                Mock(status_code=200, json=lambda: {"result": "success"})
            ]

            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await provider._make_request("/chat/completions", {})

            assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_timeout_error_exhausted_retries(self):
        """Test that timeout errors raise exception after max retries"""
        provider = OpenAIProvider(api_key="test-key", max_retries=1)

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timed out")

            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(LLMProviderConnectionException) as exc_info:
                    await provider._make_request("/chat/completions", {})

            assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_invalid_image_size_raises_exception(self):
        """Test that oversized images raise validation exception"""
        provider = OpenAIProvider(api_key="test-key")

        # Create image larger than 20MB
        large_image = b'\x89PNG\r\n\x1a\n' + b'\x00' * (21 * 1024 * 1024)

        with pytest.raises(LLMProviderException) as exc_info:
            await provider.analyze_image(
                image_data=large_image,
                prompt="Analyze"
            )

        assert "exceeds maximum" in str(exc_info.value)


class TestOpenAIProviderHealthCheck:
    """
    Test Suite for Health Check Functionality

    BUSINESS CONTEXT:
    Tests health check functionality for monitoring provider availability
    and enabling fallback to alternative providers.
    """

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check when API is accessible"""
        provider = OpenAIProvider(api_key="test-key")

        mock_response = Mock()
        mock_response.status_code = 200

        with patch.object(provider._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await provider.health_check()

        assert result is True
        mock_get.assert_called_once_with("/models")

    @pytest.mark.asyncio
    async def test_health_check_failure_non_200_status(self):
        """Test health check returns False for non-200 status codes"""
        provider = OpenAIProvider(api_key="test-key")

        mock_response = Mock()
        mock_response.status_code = 500

        with patch.object(provider._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await provider.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_failure_connection_error(self):
        """Test health check returns False on connection errors"""
        provider = OpenAIProvider(api_key="test-key")

        with patch.object(provider._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")

            result = await provider.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_failure_timeout(self):
        """Test health check returns False on timeout"""
        provider = OpenAIProvider(api_key="test-key")

        with patch.object(provider._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timed out")

            result = await provider.health_check()

        assert result is False


class TestOpenAIProviderCleanup:
    """
    Test Suite for Resource Cleanup

    BUSINESS CONTEXT:
    Tests proper cleanup of HTTP connections and resources to prevent
    memory leaks and connection pool exhaustion.
    """

    @pytest.mark.asyncio
    async def test_close_client(self):
        """Test that close() properly closes the HTTP client"""
        provider = OpenAIProvider(api_key="test-key")

        assert provider._client is not None

        with patch.object(provider._client, 'aclose', new_callable=AsyncMock) as mock_close:
            await provider.close()

            mock_close.assert_called_once()

        assert provider._client is None

    @pytest.mark.asyncio
    async def test_close_idempotent(self):
        """Test that calling close() multiple times is safe"""
        provider = OpenAIProvider(api_key="test-key")

        with patch.object(provider._client, 'aclose', new_callable=AsyncMock):
            await provider.close()
            await provider.close()  # Should not raise

        assert provider._client is None


class TestOpenAIProviderIntegration:
    """
    Test Suite for Integration Scenarios

    BUSINESS CONTEXT:
    Tests end-to-end scenarios combining multiple provider features
    to validate real-world usage patterns.
    """

    @pytest.mark.asyncio
    async def test_complete_screenshot_analysis_workflow(self):
        """Test complete workflow: image analysis -> text generation"""
        provider = OpenAIProvider(api_key="test-key")

        # Mock image analysis
        analysis_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "extracted_text": "Python Programming Course",
                        "title": "Python Basics",
                        "topics": ["Variables", "Functions", "Classes"]
                    })
                }
            }],
            "usage": {"total_tokens": 1000}
        }

        # Mock text generation
        text_response = {
            "choices": [{
                "message": {"content": "Generated course outline..."}
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 500}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [analysis_response, text_response]

            # Step 1: Analyze screenshot
            image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
            vision_result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Extract course content"
            )

            assert vision_result.suggested_title == "Python Basics"

            # Step 2: Generate detailed content based on analysis
            text_result = await provider.generate_text(
                prompt=f"Create a detailed outline for: {vision_result.suggested_title}",
                system_prompt="You are a course creation expert"
            )

            assert text_result.content == "Generated course outline..."
            assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_provider_fallback_on_error(self):
        """Test that provider errors enable fallback to alternative providers"""
        provider = OpenAIProvider(api_key="test-key")

        # Simulate provider failure
        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = LLMProviderRateLimitException(
                message="Rate limit exceeded. Retry after 60 seconds",
                provider_name="openai",
                retry_after=60
            )

            with pytest.raises(LLMProviderRateLimitException):
                await provider.generate_text(prompt="Test")

        # In a real scenario, the application would catch this and try another provider


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--asyncio-mode=auto'])
