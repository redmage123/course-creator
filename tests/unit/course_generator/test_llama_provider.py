"""
Unit Tests for Meta Llama LLM Provider

BUSINESS CONTEXT:
Tests the Llama provider's ability to analyze screenshots and generate
course content using Meta's Llama models via hosting services (Together.ai,
Fireworks, Replicate). Validates vision capabilities with Llama 3.2 Vision,
text generation, and error handling.

TECHNICAL IMPLEMENTATION:
- Tests provider initialization with different hosting providers
- Tests image analysis with Llama 3.2 Vision models
- Tests text generation with Llama models
- Tests error handling for various failure scenarios
- Tests health check functionality
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
import httpx
from uuid import uuid4

from course_generator.infrastructure.llm_providers.llama_provider import (
    LlamaProvider
)
from course_generator.infrastructure.llm_providers.base_provider import (
    LLMProviderCapabilities,
    LLMResponse,
    VisionAnalysisResult
)
from shared.exceptions import (
    LLMProviderConnectionException,
    LLMProviderAuthenticationException,
    LLMProviderRateLimitException,
    LLMProviderResponseException
)


class TestLlamaProviderInitialization:
    """Test suite for Llama provider initialization"""

    def test_provider_initialization_with_defaults(self):
        """Test that provider initializes with default configuration (Together.ai)"""
        provider = LlamaProvider(api_key="test-key")

        assert provider.provider_name == "llama"
        assert provider.api_key == "test-key"
        assert provider.model == "meta-llama/Llama-3.3-70B-Instruct-Turbo"
        assert provider.base_url == "https://api.together.xyz/v1"
        assert provider.hosting_provider == "together"
        assert provider.timeout == 120.0
        assert provider.max_retries == 3

    def test_provider_initialization_with_fireworks(self):
        """Test provider initialization with Fireworks hosting"""
        provider = LlamaProvider(
            api_key="test-key",
            hosting_provider="fireworks"
        )

        assert provider.base_url == "https://api.fireworks.ai/inference/v1"
        assert provider.hosting_provider == "fireworks"

    def test_provider_initialization_with_replicate(self):
        """Test provider initialization with Replicate hosting"""
        provider = LlamaProvider(
            api_key="test-key",
            hosting_provider="replicate"
        )

        assert provider.base_url == "https://api.replicate.com/v1"
        assert provider.hosting_provider == "replicate"

    def test_provider_initialization_with_custom_config(self):
        """Test provider initialization with custom configuration"""
        org_id = uuid4()
        provider = LlamaProvider(
            api_key="custom-key",
            base_url="https://custom.llama-api.com/v1",
            model="meta-llama/Llama-3.1-8B-Instruct-Turbo",
            organization_id=org_id,
            timeout=180.0,
            max_retries=5
        )

        assert provider.api_key == "custom-key"
        assert provider.base_url == "https://custom.llama-api.com/v1"
        assert provider.model == "meta-llama/Llama-3.1-8B-Instruct-Turbo"
        assert provider.organization_id == org_id
        assert provider.timeout == 180.0
        assert provider.max_retries == 5

    def test_default_model_property(self):
        """Test default_model property returns correct value"""
        provider = LlamaProvider(api_key="test-key")
        assert provider.default_model == "meta-llama/Llama-3.3-70B-Instruct-Turbo"

    def test_default_vision_model_property(self):
        """Test default_vision_model property returns correct value"""
        provider = LlamaProvider(api_key="test-key")
        assert provider.default_vision_model == "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo"

    def test_get_capabilities(self):
        """Test that provider capabilities are correctly defined"""
        provider = LlamaProvider(api_key="test-key")
        capabilities = provider.get_capabilities()

        assert isinstance(capabilities, LLMProviderCapabilities)
        assert capabilities.supports_vision is True  # With Llama 3.2 Vision
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is True
        assert capabilities.supports_json_mode is True
        assert capabilities.max_tokens == 128000
        assert capabilities.max_image_size_mb == 20.0
        assert "image/png" in capabilities.supported_image_formats
        assert "image/jpeg" in capabilities.supported_image_formats
        assert capabilities.rate_limit_requests_per_minute == 100
        assert capabilities.context_window == 128000


class TestLlamaImageAnalysis:
    """Test suite for Llama image analysis functionality"""

    @pytest.mark.asyncio
    async def test_analyze_image_with_bytes(self):
        """Test image analysis with raw bytes input using Llama 3.2 Vision"""
        provider = LlamaProvider(api_key="test-key")

        # Create sample PNG image bytes
        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "title": "Advanced Machine Learning",
                        "description": "Deep dive into ML algorithms",
                        "topics": ["Neural Networks", "Deep Learning", "CNN"],
                        "difficulty": "advanced",
                        "duration_hours": 40,
                        "confidence_score": 0.93
                    })
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 700,
                "completion_tokens": 300,
                "total_tokens": 1000
            }
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Analyze this ML course screenshot"
            )

            assert isinstance(result, VisionAnalysisResult)
            assert result.suggested_title == "Advanced Machine Learning"
            assert result.suggested_description == "Deep dive into ML algorithms"
            assert result.suggested_topics == ["Neural Networks", "Deep Learning", "CNN"]
            assert result.suggested_difficulty == "advanced"
            assert result.suggested_duration_hours == 40
            assert result.confidence_score == 0.93
            assert result.model_used == "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo"
            assert result.provider_used == "llama"
            assert result.tokens_used == 1000

    @pytest.mark.asyncio
    async def test_analyze_image_with_base64(self):
        """Test image analysis with base64 string input"""
        provider = LlamaProvider(api_key="test-key")

        base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"title": "Open Source Course", "confidence_score": 0.87}'
                }
            }],
            "usage": {"total_tokens": 450}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=base64_image,
                prompt="Analyze"
            )

            assert isinstance(result, VisionAnalysisResult)
            assert result.suggested_title == "Open Source Course"
            assert result.confidence_score == 0.87

    @pytest.mark.asyncio
    async def test_analyze_image_uses_custom_model(self):
        """Test that custom model parameter is used"""
        provider = LlamaProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "choices": [{"message": {"content": '{"confidence_score": 0.9}'}}],
            "usage": {"total_tokens": 100}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await provider.analyze_image(
                image_data=image_bytes,
                prompt="Test",
                model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo"
            )

            # Verify the request was made with custom model
            call_args = mock_request.call_args
            assert call_args[0][1]["model"] == "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo"

    @pytest.mark.asyncio
    async def test_analyze_image_handles_non_json_response(self):
        """Test handling of non-JSON response content"""
        provider = LlamaProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "choices": [{
                "message": {
                    "content": "This course covers advanced topics in data science"
                }
            }],
            "usage": {"total_tokens": 60}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Test"
            )

            assert result.extracted_text == "This course covers advanced topics in data science"

    @pytest.mark.asyncio
    async def test_analyze_image_requests_json_mode(self):
        """Test that JSON mode is requested"""
        provider = LlamaProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "choices": [{"message": {"content": '{"confidence_score": 0.9}'}}],
            "usage": {"total_tokens": 100}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await provider.analyze_image(
                image_data=image_bytes,
                prompt="Test"
            )

            # Verify response_format was set
            call_args = mock_request.call_args
            assert call_args[0][1]["response_format"] == {"type": "json_object"}


class TestLlamaTextGeneration:
    """Test suite for Llama text generation"""

    @pytest.mark.asyncio
    async def test_generate_text_basic(self):
        """Test basic text generation"""
        provider = LlamaProvider(api_key="test-key")

        mock_response = {
            "choices": [{
                "message": {
                    "content": "Generated course content for JavaScript"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 35,
                "total_tokens": 47
            }
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(
                prompt="Generate a JavaScript course outline"
            )

            assert isinstance(result, LLMResponse)
            assert result.content == "Generated course content for JavaScript"
            assert result.model == "meta-llama/Llama-3.3-70B-Instruct-Turbo"
            assert result.provider == "llama"
            assert result.input_tokens == 12
            assert result.output_tokens == 35
            assert result.total_tokens == 47
            assert result.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_generate_text_with_system_prompt(self):
        """Test text generation with system prompt"""
        provider = LlamaProvider(api_key="test-key")

        mock_response = {
            "choices": [{
                "message": {"content": "Response"},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 55, "completion_tokens": 28, "total_tokens": 83}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await provider.generate_text(
                prompt="User prompt",
                system_prompt="You are an expert course designer"
            )

            # Verify system prompt was included
            call_args = mock_request.call_args
            messages = call_args[0][1]["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_generate_text_with_json_mode(self):
        """Test text generation with JSON mode enabled"""
        provider = LlamaProvider(api_key="test-key")

        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"modules": ["Intro", "Advanced"]}'
                },
                "finish_reason": "stop"
            }],
            "usage": {"total_tokens": 55}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(
                prompt="Generate JSON",
                json_mode=True
            )

            assert result.content == '{"modules": ["Intro", "Advanced"]}'

            # Verify response_format was set
            call_args = mock_request.call_args
            assert call_args[0][1]["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_generate_text_cost_calculation(self):
        """Test that cost metadata is included with hosting provider"""
        provider = LlamaProvider(api_key="test-key", hosting_provider="together")

        mock_response = {
            "choices": [{
                "message": {"content": "Text"},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(prompt="Test")

            assert "input_cost_per_million" in result.metadata
            assert "output_cost_per_million" in result.metadata
            assert result.metadata["hosting_provider"] == "together"


class TestLlamaErrorHandling:
    """Test suite for Llama error handling"""

    @pytest.mark.asyncio
    async def test_authentication_error(self):
        """Test handling of authentication errors"""
        provider = LlamaProvider(api_key="invalid-key")

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": {"message": "Invalid API key"}}

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderAuthenticationException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "llama"

    @pytest.mark.asyncio
    async def test_rate_limit_error_with_retry_after(self):
        """Test handling of rate limit errors with Retry-After header"""
        provider = LlamaProvider(api_key="test-key", max_retries=1)

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "30"}
        mock_response.json.return_value = {"error": {"message": "Rate limit"}}

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderRateLimitException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "llama"
            assert exc_info.value.retry_after == 30

    @pytest.mark.asyncio
    async def test_server_error_with_retry(self):
        """Test server error with retry logic"""
        provider = LlamaProvider(api_key="test-key", max_retries=2)

        # First two calls fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.content = b""

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"result": "success"}

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = [
                mock_response_fail,
                mock_response_fail,
                mock_response_success
            ]

            result = await provider._make_request("/test", {})

            assert result == {"result": "success"}
            assert mock_post.call_count == 3

    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Test handling of connection errors"""
        provider = LlamaProvider(api_key="test-key", max_retries=1)

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")

            with pytest.raises(LLMProviderConnectionException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "llama"

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test handling of timeout errors"""
        provider = LlamaProvider(api_key="test-key", max_retries=1)

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timeout")

            with pytest.raises(LLMProviderConnectionException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "llama"


class TestLlamaHealthCheck:
    """Test suite for Llama health check"""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check"""
        provider = LlamaProvider(api_key="test-key")

        mock_response = Mock()
        mock_response.status_code = 200

        with patch.object(provider._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            is_healthy = await provider.health_check()

            assert is_healthy is True
            mock_get.assert_called_once_with("/models")

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test failed health check"""
        provider = LlamaProvider(api_key="test-key")

        with patch.object(provider._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.RequestError("Network error")

            is_healthy = await provider.health_check()

            assert is_healthy is False

    @pytest.mark.asyncio
    async def test_provider_close(self):
        """Test that provider client closes properly"""
        provider = LlamaProvider(api_key="test-key")

        with patch.object(provider._client, 'aclose', new_callable=AsyncMock) as mock_close:
            await provider.close()

            mock_close.assert_called_once()
            assert provider._client is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
