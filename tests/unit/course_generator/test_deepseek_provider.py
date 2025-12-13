"""
Unit Tests for Deepseek LLM Provider

BUSINESS CONTEXT:
Tests the Deepseek provider's ability to analyze screenshots and generate
course content. Validates vision capabilities, text generation, error handling,
and health checks.

TECHNICAL IMPLEMENTATION:
- Tests provider initialization
- Tests image analysis with Deepseek-VL
- Tests text generation
- Tests error handling for various failure scenarios
- Tests health check functionality
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
import httpx
from uuid import uuid4

from course_generator.infrastructure.llm_providers.deepseek_provider import (
    DeepseekProvider
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


class TestDeepseekProviderInitialization:
    """Test suite for Deepseek provider initialization"""

    def test_provider_initialization_with_defaults(self):
        """Test that provider initializes with default configuration"""
        provider = DeepseekProvider(api_key="test-key")

        assert provider.provider_name == "deepseek"
        assert provider.api_key == "test-key"
        assert provider.model == "deepseek-chat"
        assert provider.base_url == "https://api.deepseek.com/v1"
        assert provider.timeout == 120.0
        assert provider.max_retries == 3

    def test_provider_initialization_with_custom_config(self):
        """Test provider initialization with custom configuration"""
        org_id = uuid4()
        provider = DeepseekProvider(
            api_key="custom-key",
            base_url="https://custom.deepseek.com/v1",
            model="deepseek-coder",
            organization_id=org_id,
            timeout=180.0,
            max_retries=5
        )

        assert provider.api_key == "custom-key"
        assert provider.base_url == "https://custom.deepseek.com/v1"
        assert provider.model == "deepseek-coder"
        assert provider.organization_id == org_id
        assert provider.timeout == 180.0
        assert provider.max_retries == 5

    def test_default_model_property(self):
        """Test default_model property returns correct value"""
        provider = DeepseekProvider(api_key="test-key")
        assert provider.default_model == "deepseek-chat"

    def test_default_vision_model_property(self):
        """Test default_vision_model property returns correct value"""
        provider = DeepseekProvider(api_key="test-key")
        assert provider.default_vision_model == "deepseek-vl"

    def test_get_capabilities(self):
        """Test that provider capabilities are correctly defined"""
        provider = DeepseekProvider(api_key="test-key")
        capabilities = provider.get_capabilities()

        assert isinstance(capabilities, LLMProviderCapabilities)
        assert capabilities.supports_vision is True
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is True
        assert capabilities.supports_json_mode is True
        assert capabilities.max_tokens == 32000
        assert capabilities.max_image_size_mb == 10.0
        assert "image/png" in capabilities.supported_image_formats
        assert "image/jpeg" in capabilities.supported_image_formats
        assert capabilities.rate_limit_requests_per_minute == 60
        assert capabilities.context_window == 32000


class TestDeepseekImageAnalysis:
    """Test suite for Deepseek image analysis functionality"""

    @pytest.mark.asyncio
    async def test_analyze_image_with_bytes(self):
        """Test image analysis with raw bytes input"""
        provider = DeepseekProvider(api_key="test-key")

        # Create sample PNG image bytes
        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "title": "Python Programming",
                        "description": "Learn Python basics",
                        "topics": ["Variables", "Functions"],
                        "difficulty": "beginner",
                        "duration_hours": 10,
                        "confidence_score": 0.95
                    })
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 500,
                "completion_tokens": 200,
                "total_tokens": 700
            }
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Analyze this screenshot"
            )

            assert isinstance(result, VisionAnalysisResult)
            assert result.suggested_title == "Python Programming"
            assert result.suggested_description == "Learn Python basics"
            assert result.suggested_topics == ["Variables", "Functions"]
            assert result.suggested_difficulty == "beginner"
            assert result.suggested_duration_hours == 10
            assert result.confidence_score == 0.95
            assert result.model_used == "deepseek-vl"
            assert result.provider_used == "deepseek"
            assert result.tokens_used == 700

    @pytest.mark.asyncio
    async def test_analyze_image_with_base64(self):
        """Test image analysis with base64 string input"""
        provider = DeepseekProvider(api_key="test-key")

        base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "title": "Course Title",
                        "confidence_score": 0.85
                    })
                }
            }],
            "usage": {"total_tokens": 500}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=base64_image,
                prompt="Analyze"
            )

            assert isinstance(result, VisionAnalysisResult)
            assert result.confidence_score == 0.85

    @pytest.mark.asyncio
    async def test_analyze_image_uses_custom_model(self):
        """Test that custom model parameter is used"""
        provider = DeepseekProvider(api_key="test-key")

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
                model="deepseek-vl-custom"
            )

            # Verify the request was made with custom model
            call_args = mock_request.call_args
            assert call_args[0][1]["model"] == "deepseek-vl-custom"

    @pytest.mark.asyncio
    async def test_analyze_image_handles_non_json_response(self):
        """Test handling of non-JSON response content"""
        provider = DeepseekProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "choices": [{
                "message": {
                    "content": "This is not JSON content"
                }
            }],
            "usage": {"total_tokens": 50}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Test"
            )

            assert result.extracted_text == "This is not JSON content"


class TestDeepseekTextGeneration:
    """Test suite for Deepseek text generation"""

    @pytest.mark.asyncio
    async def test_generate_text_basic(self):
        """Test basic text generation"""
        provider = DeepseekProvider(api_key="test-key")

        mock_response = {
            "choices": [{
                "message": {
                    "content": "Generated text response"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(
                prompt="Generate a course outline"
            )

            assert isinstance(result, LLMResponse)
            assert result.content == "Generated text response"
            assert result.model == "deepseek-chat"
            assert result.provider == "deepseek"
            assert result.input_tokens == 10
            assert result.output_tokens == 20
            assert result.total_tokens == 30
            assert result.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_generate_text_with_system_prompt(self):
        """Test text generation with system prompt"""
        provider = DeepseekProvider(api_key="test-key")

        mock_response = {
            "choices": [{"message": {"content": "Response"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await provider.generate_text(
                prompt="User prompt",
                system_prompt="You are a helpful assistant"
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
        provider = DeepseekProvider(api_key="test-key")

        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"key": "value"}'
                },
                "finish_reason": "stop"
            }],
            "usage": {"total_tokens": 50}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(
                prompt="Generate JSON",
                json_mode=True
            )

            assert result.content == '{"key": "value"}'

            # Verify response_format was set
            call_args = mock_request.call_args
            assert call_args[0][1]["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_generate_text_cost_calculation(self):
        """Test that cost metadata is included"""
        provider = DeepseekProvider(api_key="test-key")

        mock_response = {
            "choices": [{"message": {"content": "Text"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(prompt="Test")

            assert "input_cost_per_million" in result.metadata
            assert "output_cost_per_million" in result.metadata
            assert result.metadata["input_cost_per_million"] == 0.14
            assert result.metadata["output_cost_per_million"] == 0.28


class TestDeepseekErrorHandling:
    """Test suite for Deepseek error handling"""

    @pytest.mark.asyncio
    async def test_authentication_error(self):
        """Test handling of authentication errors"""
        provider = DeepseekProvider(api_key="invalid-key")

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": {"message": "Invalid API key"}}

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderAuthenticationException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "deepseek"

    @pytest.mark.asyncio
    async def test_rate_limit_error(self):
        """Test handling of rate limit errors"""
        provider = DeepseekProvider(api_key="test-key")

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderRateLimitException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "deepseek"

    @pytest.mark.asyncio
    async def test_server_error_with_retry(self):
        """Test server error with retry logic"""
        provider = DeepseekProvider(api_key="test-key", max_retries=2)

        # First two calls fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.json.return_value = {}

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
        provider = DeepseekProvider(api_key="test-key", max_retries=1)

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")

            with pytest.raises(LLMProviderConnectionException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "deepseek"
            assert "Connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test handling of timeout errors"""
        provider = DeepseekProvider(api_key="test-key", max_retries=1)

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timeout")

            with pytest.raises(LLMProviderConnectionException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "deepseek"


class TestDeepseekHealthCheck:
    """Test suite for Deepseek health check"""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check"""
        provider = DeepseekProvider(api_key="test-key")

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
        provider = DeepseekProvider(api_key="test-key")

        with patch.object(provider._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.RequestError("Network error")

            is_healthy = await provider.health_check()

            assert is_healthy is False

    @pytest.mark.asyncio
    async def test_provider_close(self):
        """Test that provider client closes properly"""
        provider = DeepseekProvider(api_key="test-key")

        with patch.object(provider._client, 'aclose', new_callable=AsyncMock) as mock_close:
            await provider.close()

            mock_close.assert_called_once()
            assert provider._client is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
