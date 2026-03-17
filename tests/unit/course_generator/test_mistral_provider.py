"""
Unit Tests for Mistral AI LLM Provider

BUSINESS CONTEXT:
Tests the Mistral AI provider's ability to analyze screenshots and generate
course content using Mistral's models including Pixtral for vision capabilities.
Validates European AI provider integration for GDPR-compliant data handling.

TECHNICAL IMPLEMENTATION:
- Tests provider initialization with Mistral AI API
- Tests image analysis with Pixtral vision models
- Tests text generation with Mistral models
- Tests error handling for various failure scenarios
- Tests health check functionality
- Tests Mistral-specific pricing and cost calculations
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
import httpx
from uuid import uuid4

from course_generator.infrastructure.llm_providers.mistral_provider import (
    MistralProvider
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


class TestMistralProviderInitialization:
    """Test suite for Mistral provider initialization"""

    def test_provider_initialization_with_defaults(self):
        """Test that provider initializes with default configuration"""
        provider = MistralProvider(api_key="test-key")

        assert provider.provider_name == "mistral"
        assert provider.api_key == "test-key"
        assert provider.model == "mistral-large-latest"
        assert provider.base_url == "https://api.mistral.ai/v1"
        assert provider.timeout == 120.0
        assert provider.max_retries == 3

    def test_provider_initialization_with_custom_config(self):
        """Test provider initialization with custom configuration"""
        org_id = uuid4()
        provider = MistralProvider(
            api_key="custom-key",
            base_url="https://custom.mistral.ai/v1",
            model="mistral-small-latest",
            organization_id=org_id,
            timeout=180.0,
            max_retries=5
        )

        assert provider.api_key == "custom-key"
        assert provider.base_url == "https://custom.mistral.ai/v1"
        assert provider.model == "mistral-small-latest"
        assert provider.organization_id == org_id
        assert provider.timeout == 180.0
        assert provider.max_retries == 5

    def test_default_model_property(self):
        """Test default_model property returns correct value"""
        provider = MistralProvider(api_key="test-key")
        assert provider.default_model == "mistral-large-latest"

    def test_default_vision_model_property(self):
        """Test default_vision_model property returns correct value"""
        provider = MistralProvider(api_key="test-key")
        assert provider.default_vision_model == "pixtral-large-latest"

    def test_get_capabilities(self):
        """Test that provider capabilities are correctly defined"""
        provider = MistralProvider(api_key="test-key")
        capabilities = provider.get_capabilities()

        assert isinstance(capabilities, LLMProviderCapabilities)
        assert capabilities.supports_vision is True  # With Pixtral
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is True
        assert capabilities.supports_json_mode is True
        assert capabilities.max_tokens == 128000
        assert capabilities.max_image_size_mb == 20.0
        assert "image/png" in capabilities.supported_image_formats
        assert "image/jpeg" in capabilities.supported_image_formats
        assert "image/webp" in capabilities.supported_image_formats
        assert "image/gif" in capabilities.supported_image_formats
        assert capabilities.rate_limit_requests_per_minute == 100
        assert capabilities.context_window == 128000

    def test_pricing_is_defined(self):
        """Test that pricing is defined for Mistral models"""
        provider = MistralProvider(api_key="test-key")

        # Verify pricing exists for key models
        assert "pixtral-large-latest" in provider.PRICING
        assert "pixtral-12b-2409" in provider.PRICING
        assert "mistral-large-latest" in provider.PRICING
        assert "mistral-small-latest" in provider.PRICING
        assert "codestral-latest" in provider.PRICING
        assert "open-mixtral-8x22b" in provider.PRICING

        # Verify pricing structure
        for model, pricing in provider.PRICING.items():
            assert "input" in pricing
            assert "output" in pricing
            assert pricing["input"] > 0
            assert pricing["output"] > 0


class TestMistralImageAnalysis:
    """Test suite for Mistral image analysis functionality"""

    @pytest.mark.asyncio
    async def test_analyze_image_with_bytes(self):
        """Test image analysis with raw bytes input using Pixtral"""
        provider = MistralProvider(api_key="test-key")

        # Create sample PNG image bytes
        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "title": "GDPR Compliance Training",
                        "description": "European data protection guidelines",
                        "topics": ["Data Privacy", "User Rights", "Compliance"],
                        "difficulty": "intermediate",
                        "duration_hours": 12,
                        "confidence_score": 0.91
                    })
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 650,
                "completion_tokens": 280,
                "total_tokens": 930
            }
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Analyze this data protection course screenshot"
            )

            assert isinstance(result, VisionAnalysisResult)
            assert result.suggested_title == "GDPR Compliance Training"
            assert result.suggested_description == "European data protection guidelines"
            assert result.suggested_topics == ["Data Privacy", "User Rights", "Compliance"]
            assert result.suggested_difficulty == "intermediate"
            assert result.suggested_duration_hours == 12
            assert result.confidence_score == 0.91
            assert result.model_used == "pixtral-large-latest"
            assert result.provider_used == "mistral"
            assert result.tokens_used == 930

    @pytest.mark.asyncio
    async def test_analyze_image_with_base64(self):
        """Test image analysis with base64 string input"""
        provider = MistralProvider(api_key="test-key")

        base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "title": "EU AI Act Overview",
                        "confidence_score": 0.89
                    })
                }
            }],
            "usage": {"total_tokens": 480}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=base64_image,
                prompt="Analyze"
            )

            assert isinstance(result, VisionAnalysisResult)
            assert result.suggested_title == "EU AI Act Overview"
            assert result.confidence_score == 0.89

    @pytest.mark.asyncio
    async def test_analyze_image_uses_custom_model(self):
        """Test that custom model parameter is used"""
        provider = MistralProvider(api_key="test-key")

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
                model="pixtral-12b-2409"
            )

            # Verify the request was made with custom model
            call_args = mock_request.call_args
            assert call_args[0][1]["model"] == "pixtral-12b-2409"

    @pytest.mark.asyncio
    async def test_analyze_image_handles_non_json_response(self):
        """Test handling of non-JSON response content"""
        provider = MistralProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "choices": [{
                "message": {
                    "content": "This screenshot shows an introduction to European regulations"
                }
            }],
            "usage": {"total_tokens": 55}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Test"
            )

            assert result.extracted_text == "This screenshot shows an introduction to European regulations"

    @pytest.mark.asyncio
    async def test_analyze_image_requests_json_format(self):
        """Test that JSON format is requested in analysis"""
        provider = MistralProvider(api_key="test-key")

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

    @pytest.mark.asyncio
    async def test_analyze_image_includes_processing_time(self):
        """Test that processing time is calculated and included"""
        provider = MistralProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "choices": [{
                "message": {"content": '{"title": "Test", "confidence_score": 0.9}'}
            }],
            "usage": {"total_tokens": 100}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Test"
            )

            assert result.processing_time_ms is not None
            assert result.processing_time_ms >= 0


class TestMistralTextGeneration:
    """Test suite for Mistral text generation"""

    @pytest.mark.asyncio
    async def test_generate_text_basic(self):
        """Test basic text generation"""
        provider = MistralProvider(api_key="test-key")

        mock_response = {
            "choices": [{
                "message": {
                    "content": "Generated course content for French language learning"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 15,
                "completion_tokens": 40,
                "total_tokens": 55
            }
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(
                prompt="Generate a French language course outline"
            )

            assert isinstance(result, LLMResponse)
            assert result.content == "Generated course content for French language learning"
            assert result.model == "mistral-large-latest"
            assert result.provider == "mistral"
            assert result.input_tokens == 15
            assert result.output_tokens == 40
            assert result.total_tokens == 55
            assert result.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_generate_text_with_system_prompt(self):
        """Test text generation with system prompt"""
        provider = MistralProvider(api_key="test-key")

        mock_response = {
            "choices": [{
                "message": {"content": "Response"},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 60, "completion_tokens": 32, "total_tokens": 92}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await provider.generate_text(
                prompt="User prompt",
                system_prompt="You are a European educational expert"
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
        provider = MistralProvider(api_key="test-key")

        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"sections": ["Introduction", "Main Content", "Summary"]}'
                },
                "finish_reason": "stop"
            }],
            "usage": {"total_tokens": 58}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(
                prompt="Generate JSON",
                json_mode=True
            )

            assert result.content == '{"sections": ["Introduction", "Main Content", "Summary"]}'

            # Verify response_format was set
            call_args = mock_request.call_args
            assert call_args[0][1]["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_generate_text_cost_calculation(self):
        """Test that cost metadata is included"""
        provider = MistralProvider(api_key="test-key")

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
            # Verify pricing matches the model
            assert result.metadata["input_cost_per_million"] == 2.00  # mistral-large-latest
            assert result.metadata["output_cost_per_million"] == 6.00

    @pytest.mark.asyncio
    async def test_generate_text_with_custom_model(self):
        """Test text generation with different Mistral models"""
        provider = MistralProvider(api_key="test-key")

        mock_response = {
            "choices": [{
                "message": {"content": "Code generation result"},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(
                prompt="Generate Python code",
                model="codestral-latest"
            )

            assert result.model == "codestral-latest"

            # Verify correct pricing is used
            assert result.metadata["input_cost_per_million"] == 0.20  # codestral-latest
            assert result.metadata["output_cost_per_million"] == 0.60

    @pytest.mark.asyncio
    async def test_generate_text_with_temperature_control(self):
        """Test text generation with temperature parameter"""
        provider = MistralProvider(api_key="test-key")

        mock_response = {
            "choices": [{
                "message": {"content": "Creative response"},
                "finish_reason": "stop"
            }],
            "usage": {"total_tokens": 50}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await provider.generate_text(
                prompt="Generate creative content",
                temperature=0.9
            )

            # Verify temperature was set
            call_args = mock_request.call_args
            assert call_args[0][1]["temperature"] == 0.9


class TestMistralErrorHandling:
    """Test suite for Mistral error handling"""

    @pytest.mark.asyncio
    async def test_authentication_error(self):
        """Test handling of authentication errors (401)"""
        provider = MistralProvider(api_key="invalid-key")

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "message": "Invalid API key"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderAuthenticationException) as exc_info:
                await provider._make_request("/test", {})

            # Check provider_name in details dict
            assert exc_info.value.details.get("provider_name") == "mistral"

    @pytest.mark.asyncio
    async def test_rate_limit_error_with_retry_after(self):
        """Test handling of rate limit errors with Retry-After header"""
        provider = MistralProvider(api_key="test-key", max_retries=1)

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "45"}
        mock_response.json.return_value = {"message": "Rate limit exceeded"}

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderRateLimitException) as exc_info:
                await provider._make_request("/test", {})

            # Check provider_name in details dict
            assert exc_info.value.details.get("provider_name") == "mistral"
            # retry_after is in details dict
            assert exc_info.value.details.get("retry_after") == 45

    @pytest.mark.asyncio
    async def test_server_error_with_retry(self):
        """Test server error with retry logic"""
        provider = MistralProvider(api_key="test-key", max_retries=2)

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
    async def test_server_error_max_retries_exceeded(self):
        """Test server error when max retries are exhausted"""
        provider = MistralProvider(api_key="test-key", max_retries=2)

        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.content = b""

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response_fail

            with pytest.raises(LLMProviderResponseException) as exc_info:
                await provider._make_request("/test", {})

            # Check provider_name in details dict
            assert exc_info.value.details.get("provider_name") == "mistral"

    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Test handling of connection errors"""
        provider = MistralProvider(api_key="test-key", max_retries=1)

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")

            with pytest.raises(LLMProviderConnectionException) as exc_info:
                await provider._make_request("/test", {})

            # Check provider_name in details dict
            assert exc_info.value.details.get("provider_name") == "mistral"
            assert "Connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test handling of timeout errors"""
        provider = MistralProvider(api_key="test-key", max_retries=1)

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timeout")

            with pytest.raises(LLMProviderConnectionException) as exc_info:
                await provider._make_request("/test", {})

            # Check provider_name in details dict
            assert exc_info.value.details.get("provider_name") == "mistral"
            assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_response_error_with_message(self):
        """Test handling of error response with message"""
        provider = MistralProvider(api_key="test-key", max_retries=1)

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.content = b'{"message": "Invalid model specified"}'
        mock_response.json.return_value = {"message": "Invalid model specified"}

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderResponseException) as exc_info:
                await provider._make_request("/test", {})

            assert "Invalid model specified" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_response_error_with_object_format(self):
        """Test handling of error response with nested object format"""
        provider = MistralProvider(api_key="test-key", max_retries=1)

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.content = b'{"object": {"message": "Nested error"}}'
        mock_response.json.return_value = {"object": {"message": "Nested error"}}

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderResponseException) as exc_info:
                await provider._make_request("/test", {})

            assert "Nested error" in str(exc_info.value)


class TestMistralHealthCheck:
    """Test suite for Mistral health check"""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check"""
        provider = MistralProvider(api_key="test-key")

        mock_response = Mock()
        mock_response.status_code = 200

        with patch.object(provider._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            is_healthy = await provider.health_check()

            assert is_healthy is True
            mock_get.assert_called_once_with("/models")

    @pytest.mark.asyncio
    async def test_health_check_failure_status_code(self):
        """Test health check failure due to status code"""
        provider = MistralProvider(api_key="test-key")

        mock_response = Mock()
        mock_response.status_code = 500

        with patch.object(provider._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            is_healthy = await provider.health_check()

            assert is_healthy is False

    @pytest.mark.asyncio
    async def test_health_check_failure_network_error(self):
        """Test health check failure due to network error"""
        provider = MistralProvider(api_key="test-key")

        with patch.object(provider._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.RequestError("Network error")

            is_healthy = await provider.health_check()

            assert is_healthy is False

    @pytest.mark.asyncio
    async def test_provider_close(self):
        """Test that provider client closes properly"""
        provider = MistralProvider(api_key="test-key")

        with patch.object(provider._client, 'aclose', new_callable=AsyncMock) as mock_close:
            await provider.close()

            mock_close.assert_called_once()
            assert provider._client is None


class TestMistralModelSelection:
    """Test suite for Mistral model selection and availability"""

    def test_vision_models_available(self):
        """Test that vision models are defined in pricing"""
        provider = MistralProvider(api_key="test-key")

        # Pixtral models should be available
        assert "pixtral-large-latest" in provider.PRICING
        assert "pixtral-12b-2409" in provider.PRICING

    def test_text_models_available(self):
        """Test that text-only models are defined in pricing"""
        provider = MistralProvider(api_key="test-key")

        # Text models should be available
        assert "mistral-large-latest" in provider.PRICING
        assert "mistral-medium-latest" in provider.PRICING
        assert "mistral-small-latest" in provider.PRICING
        assert "codestral-latest" in provider.PRICING

    def test_open_source_models_available(self):
        """Test that open-source MoE models are defined"""
        provider = MistralProvider(api_key="test-key")

        # Open-source MoE models
        assert "open-mixtral-8x22b" in provider.PRICING
        assert "open-mixtral-8x7b" in provider.PRICING

    def test_default_model_is_valid(self):
        """Test that default model is a valid model"""
        provider = MistralProvider(api_key="test-key")

        assert provider.default_model in provider.PRICING
        assert provider.default_vision_model in provider.PRICING


class TestMistralGDPRCompliance:
    """
    Test suite for GDPR-related considerations

    BUSINESS CONTEXT:
    Mistral AI is a European company, making it a preferred choice for
    organizations with strict data residency requirements.
    """

    def test_provider_uses_european_endpoint(self):
        """Test that default endpoint is European (Mistral HQ in Paris)"""
        provider = MistralProvider(api_key="test-key")

        # Verify default base URL points to Mistral's API
        assert "mistral.ai" in provider.base_url

    def test_custom_endpoint_configurable(self):
        """Test that custom endpoint can be configured for self-hosted deployments"""
        custom_url = "https://internal-mistral.company.eu/v1"
        provider = MistralProvider(
            api_key="test-key",
            base_url=custom_url
        )

        assert provider.base_url == custom_url


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
