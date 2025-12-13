"""
Unit Tests for Qwen (Alibaba Cloud) LLM Provider

BUSINESS CONTEXT:
Tests the Qwen provider's ability to analyze screenshots and generate
course content using Alibaba Cloud's DashScope API. Validates vision
capabilities, text generation, multilingual support, and error handling.

TECHNICAL IMPLEMENTATION:
- Tests provider initialization with DashScope API format
- Tests image analysis with Qwen-VL models
- Tests text generation with Qwen models
- Tests error handling for various failure scenarios
- Tests health check functionality
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
import httpx
from uuid import uuid4

from course_generator.infrastructure.llm_providers.qwen_provider import (
    QwenProvider
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


class TestQwenProviderInitialization:
    """Test suite for Qwen provider initialization"""

    def test_provider_initialization_with_defaults(self):
        """Test that provider initializes with default configuration"""
        provider = QwenProvider(api_key="test-key")

        assert provider.provider_name == "qwen"
        assert provider.api_key == "test-key"
        assert provider.model == "qwen-max"
        assert provider.base_url == "https://dashscope.aliyuncs.com/api/v1"
        assert provider.timeout == 120.0
        assert provider.max_retries == 3

    def test_provider_initialization_with_custom_config(self):
        """Test provider initialization with custom configuration"""
        org_id = uuid4()
        provider = QwenProvider(
            api_key="custom-key",
            base_url="https://custom.dashscope.com/v1",
            model="qwen-turbo",
            organization_id=org_id,
            timeout=180.0,
            max_retries=5
        )

        assert provider.api_key == "custom-key"
        assert provider.base_url == "https://custom.dashscope.com/v1"
        assert provider.model == "qwen-turbo"
        assert provider.organization_id == org_id
        assert provider.timeout == 180.0
        assert provider.max_retries == 5

    def test_default_model_property(self):
        """Test default_model property returns correct value"""
        provider = QwenProvider(api_key="test-key")
        assert provider.default_model == "qwen-max"

    def test_default_vision_model_property(self):
        """Test default_vision_model property returns correct value"""
        provider = QwenProvider(api_key="test-key")
        assert provider.default_vision_model == "qwen-vl-max"

    def test_get_capabilities(self):
        """Test that provider capabilities are correctly defined"""
        provider = QwenProvider(api_key="test-key")
        capabilities = provider.get_capabilities()

        assert isinstance(capabilities, LLMProviderCapabilities)
        assert capabilities.supports_vision is True
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is True
        assert capabilities.supports_json_mode is False  # Qwen uses different approach
        assert capabilities.max_tokens == 32000
        assert capabilities.max_image_size_mb == 10.0
        assert "image/png" in capabilities.supported_image_formats
        assert "image/jpeg" in capabilities.supported_image_formats
        assert capabilities.rate_limit_requests_per_minute == 100
        assert capabilities.context_window == 32000


class TestQwenImageAnalysis:
    """Test suite for Qwen image analysis functionality"""

    @pytest.mark.asyncio
    async def test_analyze_image_with_bytes(self):
        """Test image analysis with raw bytes input"""
        provider = QwenProvider(api_key="test-key")

        # Create sample PNG image bytes
        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "output": {
                "choices": [{
                    "message": {
                        "content": [{
                            "text": json.dumps({
                                "title": "Chinese Language Course",
                                "description": "Learn Mandarin Chinese",
                                "topics": ["Pronunciation", "Characters"],
                                "difficulty": "beginner",
                                "duration_hours": 15,
                                "confidence_score": 0.92
                            })
                        }]
                    }
                }]
            },
            "usage": {
                "input_tokens": 600,
                "output_tokens": 250,
                "total_tokens": 850
            }
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Analyze this course screenshot"
            )

            assert isinstance(result, VisionAnalysisResult)
            assert result.suggested_title == "Chinese Language Course"
            assert result.suggested_description == "Learn Mandarin Chinese"
            assert result.suggested_topics == ["Pronunciation", "Characters"]
            assert result.suggested_difficulty == "beginner"
            assert result.suggested_duration_hours == 15
            assert result.confidence_score == 0.92
            assert result.model_used == "qwen-vl-max"
            assert result.provider_used == "qwen"
            assert result.tokens_used == 850

    @pytest.mark.asyncio
    async def test_analyze_image_with_base64(self):
        """Test image analysis with base64 string input"""
        provider = QwenProvider(api_key="test-key")

        base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        mock_response = {
            "output": {
                "choices": [{
                    "message": {
                        "content": [{"text": '{"title": "Course", "confidence_score": 0.88}'}]
                    }
                }]
            },
            "usage": {"total_tokens": 400}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=base64_image,
                prompt="Analyze"
            )

            assert isinstance(result, VisionAnalysisResult)
            assert result.confidence_score == 0.88

    @pytest.mark.asyncio
    async def test_analyze_image_handles_markdown_json(self):
        """Test handling of markdown-wrapped JSON response"""
        provider = QwenProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "output": {
                "choices": [{
                    "message": {
                        "content": [{
                            "text": '```json\n{"title": "Test", "confidence_score": 0.9}\n```'
                        }]
                    }
                }]
            },
            "usage": {"total_tokens": 200}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Test"
            )

            assert result.suggested_title == "Test"
            assert result.confidence_score == 0.9

    @pytest.mark.asyncio
    async def test_analyze_image_handles_string_content(self):
        """Test handling of string content in response"""
        provider = QwenProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "output": {
                "choices": [{
                    "message": {
                        "content": ["Plain string content"]
                    }
                }]
            },
            "usage": {"total_tokens": 100}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Test"
            )

            assert result.extracted_text == "Plain string content"

    @pytest.mark.asyncio
    async def test_analyze_image_uses_custom_model(self):
        """Test that custom model parameter is used"""
        provider = QwenProvider(api_key="test-key")

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "output": {
                "choices": [{
                    "message": {"content": [{"text": '{"confidence_score": 0.9}'}]}
                }]
            },
            "usage": {"total_tokens": 100}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await provider.analyze_image(
                image_data=image_bytes,
                prompt="Test",
                model="qwen-vl-plus"
            )

            # Verify the request was made with custom model
            call_args = mock_request.call_args
            assert call_args[0][1]["model"] == "qwen-vl-plus"


class TestQwenTextGeneration:
    """Test suite for Qwen text generation"""

    @pytest.mark.asyncio
    async def test_generate_text_basic(self):
        """Test basic text generation"""
        provider = QwenProvider(api_key="test-key")

        mock_response = {
            "output": {
                "choices": [{
                    "message": {
                        "content": "Generated course outline content"
                    },
                    "finish_reason": "stop"
                }]
            },
            "usage": {
                "input_tokens": 15,
                "output_tokens": 30,
                "total_tokens": 45
            }
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(
                prompt="Generate a course outline for Python"
            )

            assert isinstance(result, LLMResponse)
            assert result.content == "Generated course outline content"
            assert result.model == "qwen-max"
            assert result.provider == "qwen"
            assert result.input_tokens == 15
            assert result.output_tokens == 30
            assert result.total_tokens == 45
            assert result.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_generate_text_with_system_prompt(self):
        """Test text generation with system prompt"""
        provider = QwenProvider(api_key="test-key")

        mock_response = {
            "output": {
                "choices": [{
                    "message": {"content": "Response"},
                    "finish_reason": "stop"
                }]
            },
            "usage": {"input_tokens": 50, "output_tokens": 25, "total_tokens": 75}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await provider.generate_text(
                prompt="User prompt",
                system_prompt="You are a course creator"
            )

            # Verify system prompt was included
            call_args = mock_request.call_args
            messages = call_args[0][1]["input"]["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_generate_text_with_json_mode(self):
        """Test text generation with JSON mode enabled"""
        provider = QwenProvider(api_key="test-key")

        mock_response = {
            "output": {
                "choices": [{
                    "message": {"content": '{"key": "value"}'},
                    "finish_reason": "stop"
                }]
            },
            "usage": {"total_tokens": 50}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(
                prompt="Generate JSON",
                json_mode=True
            )

            assert result.content == '{"key": "value"}'

            # Verify JSON instruction was added to system prompt
            call_args = mock_request.call_args
            messages = call_args[0][1]["input"]["messages"]
            assert any("JSON" in msg.get("content", "") for msg in messages)

    @pytest.mark.asyncio
    async def test_generate_text_cost_calculation(self):
        """Test that cost metadata is included"""
        provider = QwenProvider(api_key="test-key")

        mock_response = {
            "output": {
                "choices": [{
                    "message": {"content": "Text"},
                    "finish_reason": "stop"
                }]
            },
            "usage": {"input_tokens": 1000, "output_tokens": 500, "total_tokens": 1500}
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(prompt="Test")

            assert "input_cost_per_million" in result.metadata
            assert "output_cost_per_million" in result.metadata
            assert result.metadata["input_cost_per_million"] == 2.00
            assert result.metadata["output_cost_per_million"] == 6.00


class TestQwenErrorHandling:
    """Test suite for Qwen error handling"""

    @pytest.mark.asyncio
    async def test_authentication_error(self):
        """Test handling of authentication errors"""
        provider = QwenProvider(api_key="invalid-key")

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid API key"}

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderAuthenticationException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "qwen"

    @pytest.mark.asyncio
    async def test_qwen_api_error_in_response(self):
        """Test handling of Qwen-specific error in response body"""
        provider = QwenProvider(api_key="test-key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "InvalidParameter",
            "message": "Invalid parameter value"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderResponseException) as exc_info:
                await provider._make_request("/test", {})

            assert "Invalid parameter value" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_error(self):
        """Test handling of rate limit errors"""
        provider = QwenProvider(api_key="test-key", max_retries=1)

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"message": "Rate limit exceeded"}

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderRateLimitException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "qwen"

    @pytest.mark.asyncio
    async def test_server_error_with_retry(self):
        """Test server error with retry logic"""
        provider = QwenProvider(api_key="test-key", max_retries=2)

        # First two calls fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.json.return_value = {}

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"code": "Success", "result": "success"}

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = [
                mock_response_fail,
                mock_response_fail,
                mock_response_success
            ]

            result = await provider._make_request("/test", {})

            assert result["result"] == "success"
            assert mock_post.call_count == 3

    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Test handling of connection errors"""
        provider = QwenProvider(api_key="test-key", max_retries=1)

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")

            with pytest.raises(LLMProviderConnectionException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "qwen"

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test handling of timeout errors"""
        provider = QwenProvider(api_key="test-key", max_retries=1)

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timeout")

            with pytest.raises(LLMProviderConnectionException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "qwen"


class TestQwenHealthCheck:
    """Test suite for Qwen health check"""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check"""
        provider = QwenProvider(api_key="test-key")

        mock_response = Mock()
        mock_response.status_code = 200

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            is_healthy = await provider.health_check()

            assert is_healthy is True
            # Verify it uses minimal test generation
            call_args = mock_post.call_args
            assert call_args[0][0] == "/services/aigc/text-generation/generation"

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test failed health check"""
        provider = QwenProvider(api_key="test-key")

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.RequestError("Network error")

            is_healthy = await provider.health_check()

            assert is_healthy is False

    @pytest.mark.asyncio
    async def test_provider_close(self):
        """Test that provider client closes properly"""
        provider = QwenProvider(api_key="test-key")

        with patch.object(provider._client, 'aclose', new_callable=AsyncMock) as mock_close:
            await provider.close()

            mock_close.assert_called_once()
            assert provider._client is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
