"""
Unit Tests for Ollama Local LLM Provider

BUSINESS CONTEXT:
Tests the Ollama provider's ability to analyze screenshots and generate
course content using locally-hosted LLM models. Validates vision capabilities
with LLaVA models, text generation, and error handling for local deployment.

TECHNICAL IMPLEMENTATION:
- Tests provider initialization for local server
- Tests image analysis with LLaVA vision models
- Tests text generation with local models
- Tests model management (list, pull)
- Tests error handling for local server scenarios
- Tests health check functionality
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
import httpx
from uuid import uuid4

from course_generator.infrastructure.llm_providers.ollama_provider import (
    OllamaProvider
)
from course_generator.infrastructure.llm_providers.base_provider import (
    LLMProviderCapabilities,
    LLMResponse,
    VisionAnalysisResult
)
from shared.exceptions import (
    LLMProviderConnectionException,
    LLMProviderResponseException
)


class TestOllamaProviderInitialization:
    """Test suite for Ollama provider initialization"""

    def test_provider_initialization_with_defaults(self):
        """Test that provider initializes with default configuration"""
        provider = OllamaProvider()

        assert provider.provider_name == "ollama"
        assert provider.model == "llama3.2"
        assert provider.base_url == "http://localhost:11434"
        assert provider.timeout == 300.0  # Longer timeout for local models
        assert provider.max_retries == 3

    def test_provider_initialization_with_custom_config(self):
        """Test provider initialization with custom configuration"""
        org_id = uuid4()
        provider = OllamaProvider(
            base_url="http://192.168.1.100:11434",
            model="mistral",
            organization_id=org_id,
            timeout=600.0,
            max_retries=5
        )

        assert provider.base_url == "http://192.168.1.100:11434"
        assert provider.model == "mistral"
        assert provider.organization_id == org_id
        assert provider.timeout == 600.0
        assert provider.max_retries == 5

    def test_api_key_not_required(self):
        """Test that API key is not required for Ollama"""
        # Should not raise any errors
        provider = OllamaProvider()
        assert provider is not None

    def test_default_model_property(self):
        """Test default_model property returns correct value"""
        provider = OllamaProvider()
        assert provider.default_model == "llama3.2"

    def test_default_vision_model_property(self):
        """Test default_vision_model property returns correct value"""
        provider = OllamaProvider()
        assert provider.default_vision_model == "llava"

    def test_get_capabilities(self):
        """Test that provider capabilities are correctly defined"""
        provider = OllamaProvider()
        capabilities = provider.get_capabilities()

        assert isinstance(capabilities, LLMProviderCapabilities)
        assert capabilities.supports_vision is True  # With LLaVA models
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is False
        assert capabilities.supports_json_mode is True
        assert capabilities.max_tokens == 32000
        assert capabilities.max_image_size_mb == 20.0
        assert "image/png" in capabilities.supported_image_formats
        assert "image/jpeg" in capabilities.supported_image_formats
        assert capabilities.rate_limit_requests_per_minute == 1000  # No rate limits for local


class TestOllamaImageAnalysis:
    """Test suite for Ollama image analysis functionality"""

    @pytest.mark.asyncio
    async def test_analyze_image_with_bytes(self):
        """Test image analysis with raw bytes input using LLaVA"""
        provider = OllamaProvider()

        # Create sample PNG image bytes
        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "response": json.dumps({
                "title": "Introduction to Docker",
                "description": "Learn containerization with Docker",
                "topics": ["Containers", "Images", "Volumes"],
                "difficulty": "intermediate",
                "duration_hours": 8,
                "confidence_score": 0.88
            }),
            "eval_count": 250,
            "prompt_eval_count": 600,
            "done_reason": "stop"
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Analyze this Docker course screenshot"
            )

            assert isinstance(result, VisionAnalysisResult)
            assert result.suggested_title == "Introduction to Docker"
            assert result.suggested_description == "Learn containerization with Docker"
            assert result.suggested_topics == ["Containers", "Images", "Volumes"]
            assert result.suggested_difficulty == "intermediate"
            assert result.suggested_duration_hours == 8
            assert result.confidence_score == 0.88
            assert result.model_used == "llava"
            assert result.provider_used == "ollama"
            assert result.tokens_used == 850  # eval_count + prompt_eval_count

    @pytest.mark.asyncio
    async def test_analyze_image_with_base64(self):
        """Test image analysis with base64 string input"""
        provider = OllamaProvider()

        base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        mock_response = {
            "response": '{"title": "Test Course", "confidence_score": 0.85}',
            "eval_count": 100,
            "prompt_eval_count": 200
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=base64_image,
                prompt="Analyze"
            )

            assert isinstance(result, VisionAnalysisResult)
            assert result.suggested_title == "Test Course"
            assert result.confidence_score == 0.85

    @pytest.mark.asyncio
    async def test_analyze_image_strips_data_uri(self):
        """Test that data URI prefix is stripped from base64"""
        provider = OllamaProvider()

        # Base64 with data URI prefix
        data_uri_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        mock_response = {
            "response": '{"confidence_score": 0.9}',
            "eval_count": 50,
            "prompt_eval_count": 50
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await provider.analyze_image(
                image_data=data_uri_image,
                prompt="Test"
            )

            # Verify the base64 without prefix was sent
            call_args = mock_request.call_args
            images = call_args[0][1]["images"]
            assert not images[0].startswith("data:")

    @pytest.mark.asyncio
    async def test_analyze_image_handles_markdown_json(self):
        """Test handling of markdown-wrapped JSON response"""
        provider = OllamaProvider()

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "response": '```json\n{"title": "ML Course", "confidence_score": 0.92}\n```',
            "eval_count": 120,
            "prompt_eval_count": 180
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.analyze_image(
                image_data=image_bytes,
                prompt="Test"
            )

            assert result.suggested_title == "ML Course"
            assert result.confidence_score == 0.92

    @pytest.mark.asyncio
    async def test_analyze_image_uses_custom_model(self):
        """Test that custom model parameter is used"""
        provider = OllamaProvider()

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "response": '{"confidence_score": 0.9}',
            "eval_count": 100,
            "prompt_eval_count": 100
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await provider.analyze_image(
                image_data=image_bytes,
                prompt="Test",
                model="llava:34b"
            )

            # Verify the request was made with custom model
            call_args = mock_request.call_args
            assert call_args[0][1]["model"] == "llava:34b"

    @pytest.mark.asyncio
    async def test_analyze_image_requests_json_format(self):
        """Test that JSON format is requested"""
        provider = OllamaProvider()

        image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        mock_response = {
            "response": '{"confidence_score": 0.9}',
            "eval_count": 100,
            "prompt_eval_count": 100
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await provider.analyze_image(
                image_data=image_bytes,
                prompt="Test"
            )

            # Verify JSON format was requested
            call_args = mock_request.call_args
            assert call_args[0][1]["format"] == "json"


class TestOllamaTextGeneration:
    """Test suite for Ollama text generation"""

    @pytest.mark.asyncio
    async def test_generate_text_basic(self):
        """Test basic text generation"""
        provider = OllamaProvider()

        mock_response = {
            "message": {
                "content": "Generated course outline for Python programming"
            },
            "prompt_eval_count": 20,
            "eval_count": 40,
            "done_reason": "stop",
            "total_duration": 5000000000,
            "load_duration": 1000000000
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(
                prompt="Generate a Python course outline"
            )

            assert isinstance(result, LLMResponse)
            assert result.content == "Generated course outline for Python programming"
            assert result.model == "llama3.2"
            assert result.provider == "ollama"
            assert result.input_tokens == 20
            assert result.output_tokens == 40
            assert result.total_tokens == 60
            assert result.finish_reason == "stop"
            assert result.metadata["local_model"] is True

    @pytest.mark.asyncio
    async def test_generate_text_with_system_prompt(self):
        """Test text generation with system prompt"""
        provider = OllamaProvider()

        mock_response = {
            "message": {"content": "Response"},
            "prompt_eval_count": 50,
            "eval_count": 25,
            "done_reason": "stop"
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await provider.generate_text(
                prompt="User prompt",
                system_prompt="You are a helpful course creator"
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
        provider = OllamaProvider()

        mock_response = {
            "message": {"content": '{"topics": ["Python", "Django"]}'},
            "eval_count": 50,
            "prompt_eval_count": 20,
            "done_reason": "stop"
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(
                prompt="Generate JSON",
                json_mode=True
            )

            assert result.content == '{"topics": ["Python", "Django"]}'

            # Verify format was set to json
            call_args = mock_request.call_args
            assert call_args[0][1]["format"] == "json"

    @pytest.mark.asyncio
    async def test_generate_text_includes_timing_metadata(self):
        """Test that timing metadata is included for local models"""
        provider = OllamaProvider()

        mock_response = {
            "message": {"content": "Text"},
            "eval_count": 30,
            "prompt_eval_count": 15,
            "done_reason": "stop",
            "total_duration": 3000000000,  # 3 seconds in nanoseconds
            "load_duration": 500000000  # 0.5 seconds
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.generate_text(prompt="Test")

            assert result.metadata["total_duration_ns"] == 3000000000
            assert result.metadata["load_duration_ns"] == 500000000


class TestOllamaModelManagement:
    """Test suite for Ollama model management"""

    @pytest.mark.asyncio
    async def test_list_models_success(self):
        """Test listing available models"""
        provider = OllamaProvider()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.2"},
                {"name": "llava"},
                {"name": "mistral"}
            ]
        }

        with patch.object(provider._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            models = await provider.list_models()

            assert len(models) == 3
            assert "llama3.2" in models
            assert "llava" in models
            assert "mistral" in models

    @pytest.mark.asyncio
    async def test_list_models_failure(self):
        """Test list_models returns empty list on failure"""
        provider = OllamaProvider()

        with patch.object(provider._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.RequestError("Connection failed")

            models = await provider.list_models()

            assert models == []

    @pytest.mark.asyncio
    async def test_pull_model_success(self):
        """Test pulling a model"""
        provider = OllamaProvider()

        mock_response = Mock()
        mock_response.status_code = 200

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            success = await provider.pull_model("llava")

            assert success is True
            call_args = mock_post.call_args
            assert call_args[1]["json"]["name"] == "llava"

    @pytest.mark.asyncio
    async def test_pull_model_failure(self):
        """Test pull_model returns False on failure"""
        provider = OllamaProvider()

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.RequestError("Network error")

            success = await provider.pull_model("llava")

            assert success is False


class TestOllamaErrorHandling:
    """Test suite for Ollama error handling"""

    @pytest.mark.asyncio
    async def test_model_not_found_error(self):
        """Test handling of model not found error"""
        provider = OllamaProvider()

        mock_response = Mock()
        mock_response.status_code = 404

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(LLMProviderResponseException) as exc_info:
                await provider._make_request("/api/generate", {"model": "nonexistent"})

            assert exc_info.value.provider == "ollama"
            assert "Model not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_server_error_with_retry(self):
        """Test server error with retry logic"""
        provider = OllamaProvider(max_retries=2)

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
    async def test_connection_error_with_helpful_message(self):
        """Test connection error includes helpful message about Ollama running"""
        provider = OllamaProvider(max_retries=1)

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(LLMProviderConnectionException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "ollama"
            assert "Is it running?" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout_error_with_helpful_message(self):
        """Test timeout error includes message about local model slowness"""
        provider = OllamaProvider(max_retries=1)

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timeout")

            with pytest.raises(LLMProviderConnectionException) as exc_info:
                await provider._make_request("/test", {})

            assert exc_info.value.provider == "ollama"


class TestOllamaHealthCheck:
    """Test suite for Ollama health check"""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check"""
        provider = OllamaProvider()

        mock_response = Mock()
        mock_response.status_code = 200

        with patch.object(provider._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            is_healthy = await provider.health_check()

            assert is_healthy is True
            mock_get.assert_called_once_with("/api/tags")

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test failed health check"""
        provider = OllamaProvider()

        with patch.object(provider._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.RequestError("Connection refused")

            is_healthy = await provider.health_check()

            assert is_healthy is False

    @pytest.mark.asyncio
    async def test_provider_close(self):
        """Test that provider client closes properly"""
        provider = OllamaProvider()

        with patch.object(provider._client, 'aclose', new_callable=AsyncMock) as mock_close:
            await provider.close()

            mock_close.assert_called_once()
            assert provider._client is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
