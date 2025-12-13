"""
Unit Tests for Anthropic Claude LLM Provider

BUSINESS CONTEXT:
Tests the Anthropic provider's ability to:
- Initialize with proper configuration
- Analyze images using Claude's vision models
- Generate text completions
- Handle various error scenarios (auth, rate limits, API errors)
- Estimate token usage and costs
- Perform health checks
- Support different Claude model versions

TECHNICAL IMPLEMENTATION:
- Uses pytest with async support
- Mocks httpx for API calls
- Tests error handling and retry logic
- Validates response parsing and data transformation
"""

import base64
import json
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from uuid import uuid4, UUID
import httpx

from course_generator.infrastructure.llm_providers.anthropic_provider import AnthropicProvider
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


@pytest.fixture
def api_key():
    """Fixture providing a test API key"""
    return "sk-ant-test-api-key-12345"


@pytest.fixture
def organization_id():
    """Fixture providing a test organization ID"""
    return uuid4()


@pytest.fixture
def provider(api_key, organization_id):
    """Fixture providing an initialized Anthropic provider"""
    return AnthropicProvider(
        api_key=api_key,
        organization_id=organization_id,
        timeout=30.0,
        max_retries=2
    )


@pytest.fixture
def sample_image_bytes():
    """Fixture providing sample PNG image bytes"""
    # PNG magic bytes + minimal valid PNG data
    return b'\x89PNG\r\n\x1a\n' + b'\x00' * 100


@pytest.fixture
def sample_jpeg_bytes():
    """Fixture providing sample JPEG image bytes"""
    # JPEG magic bytes
    return b'\xff\xd8\xff\xe0' + b'\x00' * 100


class TestAnthropicProviderInitialization:
    """Test suite for Anthropic provider initialization"""

    def test_initialization_with_defaults(self, api_key):
        """Test provider initializes with default values"""
        provider = AnthropicProvider(api_key=api_key)

        assert provider.api_key == api_key
        assert provider.base_url == AnthropicProvider.DEFAULT_BASE_URL
        assert provider.model == AnthropicProvider.DEFAULT_MODEL
        assert provider.timeout == 120.0  # Default timeout
        assert provider.max_retries == 3  # Default max_retries
        assert provider.organization_id is None

    def test_initialization_with_custom_config(self, api_key, organization_id):
        """Test provider initializes with custom configuration"""
        custom_base_url = "https://custom-api.example.com/v1"
        custom_model = "claude-3-opus-20240229"
        custom_timeout = 60.0
        custom_retries = 5

        provider = AnthropicProvider(
            api_key=api_key,
            base_url=custom_base_url,
            model=custom_model,
            organization_id=organization_id,
            timeout=custom_timeout,
            max_retries=custom_retries
        )

        assert provider.api_key == api_key
        assert provider.base_url == custom_base_url
        assert provider.model == custom_model
        assert provider.organization_id == organization_id
        assert provider.timeout == custom_timeout
        assert provider.max_retries == custom_retries

    def test_client_headers_configuration(self, api_key):
        """Test that httpx client is configured with correct headers"""
        provider = AnthropicProvider(api_key=api_key)

        assert provider._client is not None
        assert provider._client.headers.get("x-api-key") == api_key
        assert provider._client.headers.get("anthropic-version") == AnthropicProvider.API_VERSION
        assert provider._client.headers.get("Content-Type") == "application/json"

    def test_provider_name_property(self, provider):
        """Test provider name property returns 'anthropic'"""
        assert provider.provider_name == "anthropic"

    def test_default_model_property(self, provider):
        """Test default model property"""
        assert provider.default_model == "claude-3-5-sonnet-20241022"

    def test_default_vision_model_property(self, provider):
        """Test default vision model property"""
        assert provider.default_vision_model == "claude-3-5-sonnet-20241022"


class TestAnthropicProviderCapabilities:
    """Test suite for provider capabilities"""

    def test_get_capabilities_returns_correct_values(self, provider):
        """Test that get_capabilities returns correct capability flags"""
        capabilities = provider.get_capabilities()

        assert isinstance(capabilities, LLMProviderCapabilities)
        assert capabilities.supports_vision is True
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is True
        assert capabilities.supports_json_mode is False  # Anthropic doesn't have explicit JSON mode
        assert capabilities.max_tokens == 200000
        assert capabilities.max_image_size_mb == 20.0
        assert capabilities.context_window == 200000
        assert capabilities.rate_limit_requests_per_minute == 50

    def test_supported_image_formats(self, provider):
        """Test that supported image formats are correctly listed"""
        capabilities = provider.get_capabilities()

        expected_formats = ["image/png", "image/jpeg", "image/webp", "image/gif"]
        assert set(capabilities.supported_image_formats) == set(expected_formats)


class TestAnthropicImageAnalysis:
    """Test suite for image analysis functionality"""

    @pytest.mark.asyncio
    async def test_analyze_image_with_bytes(self, provider, sample_image_bytes):
        """Test analyzing image from raw bytes"""
        mock_response = {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "title": "Python Programming Basics",
                        "description": "Introduction to Python programming",
                        "topics": ["Variables", "Functions", "Loops"],
                        "difficulty": "beginner",
                        "duration_hours": 10,
                        "detected_language": "en",
                        "confidence_score": 0.95,
                        "extracted_text": "Learn Python programming from scratch"
                    })
                }
            ],
            "usage": {
                "input_tokens": 1500,
                "output_tokens": 500
            },
            "stop_reason": "end_turn"
        }

        # Mock the HTTP client
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=Mock(return_value=mock_response)
            )

            result = await provider.analyze_image(
                image_data=sample_image_bytes,
                prompt="Analyze this course screenshot"
            )

            assert isinstance(result, VisionAnalysisResult)
            assert result.suggested_title == "Python Programming Basics"
            assert result.suggested_description == "Introduction to Python programming"
            assert len(result.suggested_topics) == 3
            assert result.suggested_difficulty == "beginner"
            assert result.suggested_duration_hours == 10
            assert result.detected_language == "en"
            assert result.confidence_score == 0.95
            assert result.model_used == provider.default_vision_model
            assert result.provider_used == "anthropic"
            assert result.tokens_used == 2000  # 1500 + 500

    @pytest.mark.asyncio
    async def test_analyze_image_with_base64_string(self, provider):
        """Test analyzing image from base64 string"""
        base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        mock_response = {
            "content": [{"type": "text", "text": '{"extracted_text": "Test content"}'}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.analyze_image(
                image_data=base64_image,
                prompt="Analyze this image"
            )

            assert isinstance(result, VisionAnalysisResult)
            assert result.extracted_text == "Test content"

    @pytest.mark.asyncio
    async def test_analyze_image_with_custom_model(self, provider, sample_image_bytes):
        """Test analyzing image with custom model parameter"""
        custom_model = "claude-3-opus-20240229"
        mock_response = {
            "content": [{"type": "text", "text": '{"extracted_text": "Custom model test"}'}],
            "usage": {"input_tokens": 200, "output_tokens": 100},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.analyze_image(
                image_data=sample_image_bytes,
                prompt="Test prompt",
                model=custom_model
            )

            assert result.model_used == custom_model
            # Verify the request was made with the custom model
            call_args = mock_post.call_args
            assert call_args[1]['json']['model'] == custom_model

    @pytest.mark.asyncio
    async def test_analyze_image_with_custom_parameters(self, provider, sample_image_bytes):
        """Test analyzing image with custom max_tokens and temperature"""
        mock_response = {
            "content": [{"type": "text", "text": '{"extracted_text": "Test"}'}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            await provider.analyze_image(
                image_data=sample_image_bytes,
                prompt="Test",
                max_tokens=8000,
                temperature=0.5
            )

            call_args = mock_post.call_args
            request_body = call_args[1]['json']
            assert request_body['max_tokens'] == 8000
            assert request_body['temperature'] == 0.5

    @pytest.mark.asyncio
    async def test_analyze_image_json_extraction_from_markdown(self, provider, sample_image_bytes):
        """Test that JSON is correctly extracted from markdown code blocks"""
        mock_response = {
            "content": [{"type": "text", "text": '```json\n{"extracted_text": "From markdown"}\n```'}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.analyze_image(
                image_data=sample_image_bytes,
                prompt="Test"
            )

            assert result.extracted_text == "From markdown"

    @pytest.mark.asyncio
    async def test_analyze_image_invalid_json_fallback(self, provider, sample_image_bytes):
        """Test that invalid JSON falls back to raw text extraction"""
        invalid_json_text = "This is not JSON but plain text response"
        mock_response = {
            "content": [{"type": "text", "text": invalid_json_text}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.analyze_image(
                image_data=sample_image_bytes,
                prompt="Test"
            )

            assert result.extracted_text == invalid_json_text

    @pytest.mark.asyncio
    async def test_analyze_image_validates_image_format(self, provider):
        """Test that image validation catches unsupported formats"""
        # Create fake image bytes with unsupported format
        unsupported_image = b'BM' + b'\x00' * 100  # BMP format

        with pytest.raises(LLMProviderException) as exc_info:
            await provider.analyze_image(
                image_data=unsupported_image,
                prompt="Test"
            )

        # The error should mention unsupported format or size issues
        assert "anthropic" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_analyze_image_validates_image_size(self, provider):
        """Test that image validation catches oversized images"""
        # Create image larger than 20MB limit
        oversized_image = b'\x89PNG\r\n\x1a\n' + b'\x00' * (21 * 1024 * 1024)

        with pytest.raises(LLMProviderException) as exc_info:
            await provider.analyze_image(
                image_data=oversized_image,
                prompt="Test"
            )

        assert "size" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_analyze_image_message_format(self, provider, sample_image_bytes):
        """Test that Claude message format is correctly constructed"""
        mock_response = {
            "content": [{"type": "text", "text": '{"extracted_text": "Test"}'}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            await provider.analyze_image(
                image_data=sample_image_bytes,
                prompt="Test prompt"
            )

            call_args = mock_post.call_args
            request_body = call_args[1]['json']

            # Verify message structure
            assert 'messages' in request_body
            assert len(request_body['messages']) == 1
            assert request_body['messages'][0]['role'] == 'user'
            assert 'content' in request_body['messages'][0]

            # Verify content blocks
            content_blocks = request_body['messages'][0]['content']
            assert len(content_blocks) == 2  # Image + text

            # Verify image block
            image_block = content_blocks[0]
            assert image_block['type'] == 'image'
            assert 'source' in image_block
            assert image_block['source']['type'] == 'base64'
            assert image_block['source']['media_type'] == 'image/png'

            # Verify text block
            text_block = content_blocks[1]
            assert text_block['type'] == 'text'
            assert 'Test prompt' in text_block['text']


class TestAnthropicTextGeneration:
    """Test suite for text generation functionality"""

    @pytest.mark.asyncio
    async def test_generate_text_basic(self, provider):
        """Test basic text generation"""
        mock_response = {
            "id": "msg_456",
            "content": [{"type": "text", "text": "Generated response text"}],
            "usage": {"input_tokens": 50, "output_tokens": 30},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.generate_text(prompt="Test prompt")

            assert isinstance(result, LLMResponse)
            assert result.content == "Generated response text"
            assert result.model == provider.model
            assert result.provider == "anthropic"
            assert result.input_tokens == 50
            assert result.output_tokens == 30
            assert result.total_tokens == 80
            assert result.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_generate_text_with_system_prompt(self, provider):
        """Test text generation with system prompt"""
        system_prompt = "You are a helpful AI assistant"
        user_prompt = "What is Python?"

        mock_response = {
            "content": [{"type": "text", "text": "Python is a programming language"}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt
            )

            # Verify system prompt was included
            call_args = mock_post.call_args
            request_body = call_args[1]['json']
            assert 'system' in request_body
            assert request_body['system'] == system_prompt

    @pytest.mark.asyncio
    async def test_generate_text_json_mode(self, provider):
        """Test text generation with JSON mode (emulated via prompt)"""
        mock_response = {
            "content": [{"type": "text", "text": '{"key": "value"}'}],
            "usage": {"input_tokens": 50, "output_tokens": 20},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.generate_text(
                prompt="Generate JSON",
                json_mode=True
            )

            # Verify JSON instruction was added to system prompt
            call_args = mock_post.call_args
            request_body = call_args[1]['json']
            assert 'system' in request_body
            assert "json" in request_body['system'].lower()

    @pytest.mark.asyncio
    async def test_generate_text_json_mode_with_existing_system_prompt(self, provider):
        """Test JSON mode appends to existing system prompt"""
        mock_response = {
            "content": [{"type": "text", "text": '{"result": "test"}'}],
            "usage": {"input_tokens": 50, "output_tokens": 20},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            await provider.generate_text(
                prompt="Test",
                system_prompt="You are helpful",
                json_mode=True
            )

            call_args = mock_post.call_args
            request_body = call_args[1]['json']
            system = request_body['system']
            assert "You are helpful" in system
            assert "json" in system.lower()

    @pytest.mark.asyncio
    async def test_generate_text_custom_model(self, provider):
        """Test text generation with custom model"""
        custom_model = "claude-3-haiku-20240307"
        mock_response = {
            "content": [{"type": "text", "text": "Response"}],
            "usage": {"input_tokens": 20, "output_tokens": 10},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.generate_text(
                prompt="Test",
                model=custom_model
            )

            assert result.model == custom_model
            call_args = mock_post.call_args
            assert call_args[1]['json']['model'] == custom_model

    @pytest.mark.asyncio
    async def test_generate_text_custom_parameters(self, provider):
        """Test text generation with custom max_tokens and temperature"""
        mock_response = {
            "content": [{"type": "text", "text": "Response"}],
            "usage": {"input_tokens": 30, "output_tokens": 15},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            await provider.generate_text(
                prompt="Test",
                max_tokens=2000,
                temperature=0.9
            )

            call_args = mock_post.call_args
            request_body = call_args[1]['json']
            assert request_body['max_tokens'] == 2000
            assert request_body['temperature'] == 0.9

    @pytest.mark.asyncio
    async def test_generate_text_finish_reason_mapping(self, provider):
        """Test that Claude's stop_reason is correctly mapped to standard finish_reason"""
        test_cases = [
            ("end_turn", "stop"),
            ("max_tokens", "length"),
            ("stop_sequence", "stop"),
        ]

        for claude_reason, expected_reason in test_cases:
            mock_response = {
                "content": [{"type": "text", "text": "Response"}],
                "usage": {"input_tokens": 10, "output_tokens": 5},
                "stop_reason": claude_reason
            }

            with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

                result = await provider.generate_text(prompt="Test")
                assert result.finish_reason == expected_reason

    @pytest.mark.asyncio
    async def test_generate_text_multiple_content_blocks(self, provider):
        """Test handling response with multiple text content blocks"""
        mock_response = {
            "content": [
                {"type": "text", "text": "First block. "},
                {"type": "text", "text": "Second block."}
            ],
            "usage": {"input_tokens": 20, "output_tokens": 10},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.generate_text(prompt="Test")
            assert result.content == "First block. Second block."

    @pytest.mark.asyncio
    async def test_generate_text_cost_metadata(self, provider):
        """Test that cost metadata is included in response"""
        mock_response = {
            "content": [{"type": "text", "text": "Response"}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.generate_text(prompt="Test")

            assert 'input_cost_per_million' in result.metadata
            assert 'output_cost_per_million' in result.metadata
            assert result.estimated_cost > 0


class TestAnthropicErrorHandling:
    """Test suite for error handling"""

    @pytest.mark.asyncio
    async def test_authentication_error(self, provider):
        """Test handling of authentication errors (401)"""
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(
                status_code=401,
                json=Mock(return_value={"error": {"message": "Invalid API key"}})
            )

            with pytest.raises(LLMProviderAuthenticationException) as exc_info:
                await provider.generate_text(prompt="Test")

            assert exc_info.value.details.get("provider_name") == "anthropic"
            assert "Invalid API key" in str(exc_info.value) or "authentication" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rate_limit_error_with_retry(self, provider):
        """Test handling of rate limit errors (429) with retry"""
        provider.max_retries = 1  # Limit retries for faster test

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(
                status_code=429,
                headers={"retry-after": "1"}
            )

            with pytest.raises(LLMProviderRateLimitException) as exc_info:
                await provider.generate_text(prompt="Test")

            assert exc_info.value.details.get("provider_name") == "anthropic"
            assert exc_info.value.details.get("retry_after") == 1
            # Should have retried once
            assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_rate_limit_success_after_retry(self, provider):
        """Test successful retry after rate limit"""
        success_response = {
            "content": [{"type": "text", "text": "Success after retry"}],
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "stop_reason": "end_turn"
        }

        call_count = 0

        async def mock_post_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return Mock(status_code=429, headers={"retry-after": "0"})
            return Mock(status_code=200, json=Mock(return_value=success_response))

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = mock_post_side_effect

            result = await provider.generate_text(prompt="Test")
            assert result.content == "Success after retry"
            assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_server_error_with_retry(self, provider):
        """Test handling of server errors (500+) with exponential backoff"""
        provider.max_retries = 2

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(
                status_code=503,
                json=Mock(return_value={"error": {"message": "Service unavailable"}}),
                content=b'{"error": {"message": "Service unavailable"}}'
            )

            with pytest.raises(LLMProviderResponseException) as exc_info:
                await provider.generate_text(prompt="Test")

            assert exc_info.value.details.get("provider_name") == "anthropic"
            # Should have retried
            assert mock_post.call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_connection_error_with_retry(self, provider):
        """Test handling of connection errors with retry"""
        provider.max_retries = 1

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")

            with pytest.raises(LLMProviderConnectionException) as exc_info:
                await provider.generate_text(prompt="Test")

            assert exc_info.value.details.get("provider_name") == "anthropic"
            assert "Connection failed" in str(exc_info.value) or "connection" in str(exc_info.value).lower()
            assert mock_post.call_count == 2  # Initial + 1 retry

    @pytest.mark.asyncio
    async def test_timeout_error_with_retry(self, provider):
        """Test handling of timeout errors with retry"""
        provider.max_retries = 1

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timed out")

            with pytest.raises(LLMProviderConnectionException) as exc_info:
                await provider.generate_text(prompt="Test")

            assert exc_info.value.details.get("provider_name") == "anthropic"
            assert "timed out" in str(exc_info.value).lower() or "timeout" in str(exc_info.value).lower()
            assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_generic_api_error(self, provider):
        """Test handling of generic API errors"""
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(
                status_code=400,
                json=Mock(return_value={"error": {"message": "Invalid request"}}),
                content=b'{"error": {"message": "Invalid request"}}'
            )

            with pytest.raises(LLMProviderResponseException) as exc_info:
                await provider.generate_text(prompt="Test")

            assert exc_info.value.details.get("provider_name") == "anthropic"
            assert "Invalid request" in str(exc_info.value) or "response" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_error_with_empty_response_body(self, provider):
        """Test handling errors when response body is empty"""
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(
                status_code=400,
                content=b'',
                json=Mock(side_effect=Exception("No content"))
            )

            with pytest.raises(LLMProviderResponseException) as exc_info:
                await provider.generate_text(prompt="Test")

            assert exc_info.value.details.get("provider_name") == "anthropic"


class TestAnthropicHealthCheck:
    """Test suite for health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_success(self, provider):
        """Test successful health check"""
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200)

            result = await provider.health_check()
            assert result is True

            # Verify it used the minimal haiku model
            call_args = mock_post.call_args
            assert call_args[1]['json']['model'] == "claude-3-haiku-20240307"
            assert call_args[1]['json']['max_tokens'] == 5

    @pytest.mark.asyncio
    async def test_health_check_failure(self, provider):
        """Test failed health check"""
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=503)

            result = await provider.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_connection_error(self, provider):
        """Test health check with connection error"""
        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Cannot connect")

            result = await provider.health_check()
            assert result is False


class TestAnthropicModelVersions:
    """Test suite for different Claude model versions"""

    @pytest.mark.asyncio
    async def test_sonnet_model(self, api_key):
        """Test using Claude 3.5 Sonnet model"""
        provider = AnthropicProvider(
            api_key=api_key,
            model="claude-3-5-sonnet-20241022"
        )

        mock_response = {
            "content": [{"type": "text", "text": "Sonnet response"}],
            "usage": {"input_tokens": 50, "output_tokens": 25},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.generate_text(prompt="Test")
            assert result.model == "claude-3-5-sonnet-20241022"
            # Verify pricing metadata
            assert result.metadata['input_cost_per_million'] == 3.00
            assert result.metadata['output_cost_per_million'] == 15.00

    @pytest.mark.asyncio
    async def test_opus_model(self, api_key):
        """Test using Claude 3 Opus model"""
        provider = AnthropicProvider(
            api_key=api_key,
            model="claude-3-opus-20240229"
        )

        mock_response = {
            "content": [{"type": "text", "text": "Opus response"}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.generate_text(prompt="Test")
            assert result.model == "claude-3-opus-20240229"
            # Verify pricing metadata
            assert result.metadata['input_cost_per_million'] == 15.00
            assert result.metadata['output_cost_per_million'] == 75.00

    @pytest.mark.asyncio
    async def test_haiku_model(self, api_key):
        """Test using Claude 3 Haiku model"""
        provider = AnthropicProvider(
            api_key=api_key,
            model="claude-3-haiku-20240307"
        )

        mock_response = {
            "content": [{"type": "text", "text": "Haiku response"}],
            "usage": {"input_tokens": 30, "output_tokens": 15},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.generate_text(prompt="Test")
            assert result.model == "claude-3-haiku-20240307"
            # Verify pricing metadata
            assert result.metadata['input_cost_per_million'] == 0.25
            assert result.metadata['output_cost_per_million'] == 1.25

    @pytest.mark.asyncio
    async def test_unknown_model_default_pricing(self, api_key):
        """Test that unknown models get default pricing"""
        provider = AnthropicProvider(
            api_key=api_key,
            model="claude-future-model-v1"
        )

        mock_response = {
            "content": [{"type": "text", "text": "Future model response"}],
            "usage": {"input_tokens": 50, "output_tokens": 25},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.generate_text(prompt="Test")
            # Should use default pricing
            assert result.metadata['input_cost_per_million'] == 3.00
            assert result.metadata['output_cost_per_million'] == 15.00


class TestAnthropicTokenCounting:
    """Test suite for token counting and cost estimation"""

    @pytest.mark.asyncio
    async def test_token_counting_in_response(self, provider):
        """Test that tokens are correctly counted in response"""
        mock_response = {
            "content": [{"type": "text", "text": "Response"}],
            "usage": {"input_tokens": 123, "output_tokens": 456},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.generate_text(prompt="Test")

            assert result.input_tokens == 123
            assert result.output_tokens == 456
            assert result.total_tokens == 579

    @pytest.mark.asyncio
    async def test_cost_estimation(self, provider):
        """Test cost estimation based on token usage"""
        mock_response = {
            "content": [{"type": "text", "text": "Response"}],
            "usage": {"input_tokens": 1000000, "output_tokens": 1000000},  # 1M each
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.generate_text(prompt="Test")

            # For default sonnet model: $3.00 input + $15.00 output = $18.00
            assert result.estimated_cost == 18.00

    @pytest.mark.asyncio
    async def test_vision_token_counting(self, provider, sample_image_bytes):
        """Test token counting in vision analysis"""
        mock_response = {
            "content": [{"type": "text", "text": '{"extracted_text": "Test"}'}],
            "usage": {"input_tokens": 2000, "output_tokens": 500},
            "stop_reason": "end_turn"
        }

        with patch.object(provider._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = Mock(status_code=200, json=Mock(return_value=mock_response))

            result = await provider.analyze_image(
                image_data=sample_image_bytes,
                prompt="Test"
            )

            assert result.tokens_used == 2500


class TestAnthropicClientLifecycle:
    """Test suite for client lifecycle management"""

    @pytest.mark.asyncio
    async def test_close_client(self, provider):
        """Test closing the HTTP client"""
        assert provider._client is not None

        await provider.close()

        assert provider._client is None

    @pytest.mark.asyncio
    async def test_close_idempotent(self, provider):
        """Test that close can be called multiple times safely"""
        await provider.close()
        await provider.close()  # Should not raise error

        assert provider._client is None


class TestAnthropicUtilityMethods:
    """Test suite for utility methods inherited from base provider"""

    def test_encode_image_to_base64(self, provider, sample_image_bytes):
        """Test encoding image to base64"""
        result = provider.encode_image_to_base64(sample_image_bytes)

        assert isinstance(result, str)
        # Verify it's valid base64
        decoded = base64.b64decode(result)
        assert decoded == sample_image_bytes

    def test_get_image_media_type_png(self, provider, sample_image_bytes):
        """Test detecting PNG image type"""
        media_type = provider.get_image_media_type(sample_image_bytes)
        assert media_type == "image/png"

    def test_get_image_media_type_jpeg(self, provider, sample_jpeg_bytes):
        """Test detecting JPEG image type"""
        media_type = provider.get_image_media_type(sample_jpeg_bytes)
        assert media_type == "image/jpeg"

    def test_get_image_media_type_webp(self, provider):
        """Test detecting WebP image type"""
        webp_bytes = b'RIFF' + b'\x00' * 4 + b'WEBP' + b'\x00' * 100
        media_type = provider.get_image_media_type(webp_bytes)
        assert media_type == "image/webp"

    def test_get_image_media_type_gif(self, provider):
        """Test detecting GIF image type"""
        gif_bytes = b'GIF89a' + b'\x00' * 100
        media_type = provider.get_image_media_type(gif_bytes)
        assert media_type == "image/gif"

    def test_get_image_media_type_unknown_defaults_to_png(self, provider):
        """Test that unknown image types default to PNG"""
        unknown_bytes = b'UNKNOWN' + b'\x00' * 100
        media_type = provider.get_image_media_type(unknown_bytes)
        assert media_type == "image/png"

    def test_validate_image_success(self, provider, sample_image_bytes):
        """Test successful image validation"""
        # Should not raise exception
        provider.validate_image(sample_image_bytes)

    def test_get_screenshot_analysis_prompt(self, provider):
        """Test getting default screenshot analysis prompt"""
        prompt = provider.get_screenshot_analysis_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "course" in prompt.lower()
        assert "json" in prompt.lower()


class TestAnthropicProviderRepresentation:
    """Test suite for provider string representation"""

    def test_repr(self, provider):
        """Test string representation of provider"""
        repr_str = repr(provider)

        assert "AnthropicProvider" in repr_str
        assert provider.model in repr_str
        assert "anthropic" in repr_str
