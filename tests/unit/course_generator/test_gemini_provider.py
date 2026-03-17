"""
Unit Tests for Google Gemini LLM Provider

BUSINESS CONTEXT:
Tests the Gemini provider's ability to analyze screenshots and generate
course content using Google's Gemini models. Validates vision capabilities
with Gemini Pro Vision and Gemini 2.0, text generation, and error handling.

TECHNICAL IMPLEMENTATION:
- Tests provider initialization with Google AI Studio API
- Tests image analysis with Gemini vision models
- Tests text generation with Gemini models
- Tests error handling for various failure scenarios
- Tests health check functionality
- Tests Gemini-specific API format (different from OpenAI)
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
import httpx
from uuid import uuid4

from course_generator.infrastructure.llm_providers.gemini_provider import (
    GeminiProvider
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


class TestGeminiProviderInitialization:
    """Test suite for Gemini provider initialization"""

    def test_provider_initialization_with_defaults(self):
        """Test that provider initializes with default configuration"""
        provider = GeminiProvider(api_key="test-key")

        assert provider.provider_name == "gemini"
        assert provider.api_key == "test-key"
        assert provider.model == "gemini-1.5-pro"
        assert provider.base_url == "https://generativelanguage.googleapis.com/v1beta"
        assert provider.timeout == 120.0
        assert provider.max_retries == 3

    def test_provider_initialization_with_custom_config(self):
        """Test provider initialization with custom configuration"""
        org_id = uuid4()
        provider = GeminiProvider(
            api_key="custom-key",
            base_url="https://custom.gemini-api.com/v1",
            model="gemini-2.0-flash-exp",
            organization_id=org_id,
            timeout=180.0,
            max_retries=5
        )

        assert provider.api_key == "custom-key"
        assert provider.base_url == "https://custom.gemini-api.com/v1"
        assert provider.model == "gemini-2.0-flash-exp"
        assert provider.organization_id == org_id
        assert provider.timeout == 180.0
        assert provider.max_retries == 5

    def test_default_model_property(self):
        """Test default_model property returns correct value"""
        provider = GeminiProvider(api_key="test-key")
        assert provider.default_model == "gemini-1.5-pro"

    def test_default_vision_model_property(self):
        """Test default_vision_model property returns correct value"""
        provider = GeminiProvider(api_key="test-key")
        assert provider.default_vision_model == "gemini-2.0-flash-exp"

    def test_get_capabilities(self):
        """Test that provider capabilities are correctly defined"""
        provider = GeminiProvider(api_key="test-key")
        capabilities = provider.get_capabilities()

        assert isinstance(capabilities, LLMProviderCapabilities)
        assert capabilities.supports_vision is True
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is True
        assert capabilities.supports_json_mode is True
        assert capabilities.max_tokens == 8192
        assert capabilities.max_image_size_mb == 20.0
        assert "image/png" in capabilities.supported_image_formats
        assert "image/jpeg" in capabilities.supported_image_formats
        assert "image/gif" in capabilities.supported_image_formats
        assert capabilities.rate_limit_requests_per_minute == 60
        assert capabilities.context_window == 2000000  # 2M for Gemini 1.5 Pro


class TestGeminiImageAnalysis:
    """Test suite for Gemini image analysis functionality"""

    @pytest.mark.asyncio
    async def test_analyze_image_with_bytes(self):
        """Test image analysis with raw bytes input using Gemini"""
        provider = GeminiProvider(api_key="test-key")

        # Create sample PNG image bytes
        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "title": "Cloud Computing Fundamentals",
                            "description": "Introduction to cloud services",
                            "topics": ["AWS", "Azure", "GCP"],
                            "difficulty": "intermediate",
                            "duration_hours": 20,
                            "confidence_score": 0.94
                        })
                    }]
                },
                "finishReason": "STOP"
            }],
            "usageMetadata": {
                "promptTokenCount": 800,
                "candidatesTokenCount": 350,
                "totalTokenCount": 1150
            }
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Analyze this cloud computing course screenshot"
            )

            assert isinstance(result, VisionAnalysisResult)
            assert result.suggested_title == "Cloud Computing Fundamentals"
            assert result.suggested_description == "Introduction to cloud services"
            assert result.suggested_topics == ["AWS", "Azure", "GCP"]
            assert result.suggested_difficulty == "intermediate"
            assert result.suggested_duration_hours == 20
            assert result.confidence_score == 0.94
            assert result.model_used == "gemini-2.0-flash-exp"
            assert result.provider_used == "gemini"
            assert result.tokens_used == 1150

    @pytest.mark.asyncio
    async def test_analyze_image_with_base64(self):
        """Test image analysis with base64 string input"""
        provider = GeminiProvider(api_key="test-key")

        base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        mock_response = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '{"title": "Multimodal Course", "confidence_score": 0.91}'
                    }]
                }
            }],
            "usageMetadata": {"totalTokenCount": 500}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=base64_image,
                prompt="Analyze"
            )

            assert isinstance(result, VisionAnalysisResult)
            assert result.suggested_title == "Multimodal Course"
            assert result.confidence_score == 0.91

    @pytest.mark.asyncio
    async def test_analyze_image_handles_markdown_json(self):
        """Test handling of markdown-wrapped JSON response"""
        provider = GeminiProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '```json\n{"title": "AI Course", "confidence_score": 0.95}\n```'
                    }]
                }
            }],
            "usageMetadata": {"totalTokenCount": 250}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Test"
            )

            assert result.suggested_title == "AI Course"
            assert result.confidence_score == 0.95

    @pytest.mark.asyncio
    async def test_analyze_image_handles_multiple_parts(self):
        """Test handling of multiple text parts in response"""
        provider = GeminiProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "candidates": [{
                "content": {
                    "parts": [
                        {"text": '{"title": "Part 1", '},
                        {"text": '"confidence_score": 0.9}'}
                    ]
                }
            }],
            "usageMetadata": {"totalTokenCount": 200}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Test"
            )

            assert result.suggested_title == "Part 1"
            assert result.confidence_score == 0.9

    @pytest.mark.asyncio
    async def test_analyze_image_no_candidates_raises_error(self):
        """Test that missing candidates raises error"""
        provider = GeminiProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "candidates": [],
            "usageMetadata": {"totalTokenCount": 0}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(LLMProviderResponseException) as exc_info:
                await provider.analyze_image(
                    image_data=image_bytes,
                    prompt="Test"
                )

            assert "No response candidates" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analyze_image_uses_custom_model(self):
        """Test that custom model parameter is used"""
        provider = GeminiProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "candidates": [{
                "content": {"parts": [{"text": '{"confidence_score": 0.9}'}]}
            }],
            "usageMetadata": {"totalTokenCount": 100}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await provider.analyze_image(
                image_data=image_bytes,
                prompt="Test",
                model="gemini-1.5-flash"
            )

            # Verify the request was made with custom model
            call_args = mock_request.call_args
            assert "gemini-1.5-flash" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_analyze_image_sets_json_mime_type(self):
        """Test that JSON MIME type is set in generation config"""
        provider = GeminiProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "candidates": [{
                "content": {"parts": [{"text": '{"confidence_score": 0.9}'}]}
            }],
            "usageMetadata": {"totalTokenCount": 100}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await provider.analyze_image(
                image_data=image_bytes,
                prompt="Test"
            )

            # Verify responseMimeType was set
            call_args = mock_request.call_args
            gen_config = call_args[0][1]["generationConfig"]
            assert gen_config["responseMimeType"] == "application/json"


class TestGeminiTextGeneration:
    """Test suite for Gemini text generation"""

    @pytest.mark.asyncio
    async def test_generate_text_basic(self):
        """Test basic text generation"""
        provider = GeminiProvider(api_key="test-key")

        mock_response = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "Generated course content for Kubernetes"
                    }]
                },
                "finishReason": "STOP"
            }],
            "usageMetadata": {
                "promptTokenCount": 18,
                "candidatesTokenCount": 42,
                "totalTokenCount": 60
            }
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(
                prompt="Generate a Kubernetes course outline"
            )

            assert isinstance(result, LLMResponse)
            assert result.content == "Generated course content for Kubernetes"
            assert result.model == "gemini-1.5-pro"
            assert result.provider == "gemini"
            assert result.input_tokens == 18
            assert result.output_tokens == 42
            assert result.total_tokens == 60
            assert result.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_generate_text_with_system_prompt(self):
        """Test text generation with system instruction"""
        provider = GeminiProvider(api_key="test-key")

        mock_response = {
            "candidates": [{
                "content": {"parts": [{"text": "Response"}]},
                "finishReason": "STOP"
            }],
            "usageMetadata": {
                "promptTokenCount": 60,
                "candidatesTokenCount": 30,
                "totalTokenCount": 90
            }
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await provider.generate_text(
                prompt="User prompt",
                system_prompt="You are an expert educator"
            )

            # Verify system instruction was included
            call_args = mock_request.call_args
            assert "systemInstruction" in call_args[0][1]
            assert call_args[0][1]["systemInstruction"]["parts"][0]["text"] == "You are an expert educator"

    @pytest.mark.asyncio
    async def test_generate_text_with_json_mode(self):
        """Test text generation with JSON mode enabled"""
        provider = GeminiProvider(api_key="test-key")

        mock_response = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '{"lessons": ["Intro", "Advanced"]}'
                    }]
                },
                "finishReason": "STOP"
            }],
            "usageMetadata": {"totalTokenCount": 60}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(
                prompt="Generate JSON",
                json_mode=True
            )

            assert result.content == '{"lessons": ["Intro", "Advanced"]}'

            # Verify responseMimeType was set
            call_args = mock_request.call_args
            gen_config = call_args[0][1]["generationConfig"]
            assert gen_config["responseMimeType"] == "application/json"

    @pytest.mark.asyncio
    async def test_generate_text_finish_reason_mapping(self):
        """Test that Gemini finish reasons are mapped correctly"""
        provider = GeminiProvider(api_key="test-key")

        test_cases = [
            ("STOP", "stop"),
            ("MAX_TOKENS", "length"),
            ("SAFETY", "content_filter"),
            ("RECITATION", "stop"),
            ("UNKNOWN_REASON", "unknown_reason")
        ]

        for gemini_reason, expected_reason in test_cases:
            mock_response = {
                "candidates": [{
                    "content": {"parts": [{"text": "Text"}]},
                    "finishReason": gemini_reason
                }],
                "usageMetadata": {"totalTokenCount": 50}
            }

            with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response

                result = await provider.generate_text(prompt="Test")

                assert result.finish_reason == expected_reason

    @pytest.mark.asyncio
    async def test_generate_text_no_candidates_raises_error(self):
        """Test that missing candidates raises error"""
        provider = GeminiProvider(api_key="test-key")

        mock_response = {
            "candidates": [],
            "usageMetadata": {"totalTokenCount": 0}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(LLMProviderResponseException) as exc_info:
                await provider.generate_text(prompt="Test")

            assert "No response candidates" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_text_cost_calculation(self):
        """Test that cost metadata is included"""
        provider = GeminiProvider(api_key="test-key")

        mock_response = {
            "candidates": [{
                "content": {"parts": [{"text": "Text"}]},
                "finishReason": "STOP"
            }],
            "usageMetadata": {
                "promptTokenCount": 1000,
                "candidatesTokenCount": 500,
                "totalTokenCount": 1500
            }
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(prompt="Test")

            assert "input_cost_per_million" in result.metadata
            assert "output_cost_per_million" in result.metadata


class TestGeminiErrorHandling:
    """Test suite for Gemini error handling"""

    @pytest.mark.asyncio
    async def test_authentication_error(self):
        """Test handling of authentication errors (401/403)"""
        provider = GeminiProvider(api_key="invalid-key")

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {"message": "Invalid API key"}
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderAuthenticationException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "gemini"

    @pytest.mark.asyncio
    async def test_rate_limit_error(self):
        """Test handling of rate limit errors"""
        provider = GeminiProvider(api_key="test-key", max_retries=1)

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error": {"message": "Resource exhausted"}
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderRateLimitException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "gemini"

    @pytest.mark.asyncio
    async def test_server_error_with_retry(self):
        """Test server error with retry logic"""
        provider = GeminiProvider(api_key="test-key", max_retries=2)

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
        provider = GeminiProvider(api_key="test-key", max_retries=1)

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")

            with pytest.raises(LLMProviderConnectionException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "gemini"

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test handling of timeout errors"""
        provider = GeminiProvider(api_key="test-key", max_retries=1)

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timeout")

            with pytest.raises(LLMProviderConnectionException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "gemini"


class TestGeminiHealthCheck:
    """Test suite for Gemini health check"""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check"""
        provider = GeminiProvider(api_key="test-key")

        mock_response = Mock()
        mock_response.status_code = 200

        with patch.object(provider._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            is_healthy = await provider.health_check()

            assert is_healthy is True
            # Verify API key is in query parameter
            call_args = mock_get.call_args
            assert "key=test-key" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test failed health check"""
        provider = GeminiProvider(api_key="test-key")

        with patch.object(provider._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.RequestError("Network error")

            is_healthy = await provider.health_check()

            assert is_healthy is False

    @pytest.mark.asyncio
    async def test_provider_close(self):
        """Test that provider client closes properly"""
        provider = GeminiProvider(api_key="test-key")

        with patch.object(provider._client, 'aclose', new_callable=AsyncMock) as mock_close:
            await provider.close()

            mock_close.assert_called_once()
            assert provider._client is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
