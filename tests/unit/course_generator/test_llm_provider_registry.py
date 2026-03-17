"""
Unit Tests for LLM Provider Registry

BUSINESS CONTEXT:
Tests the provider registry's ability to manage, detect, and instantiate
LLM providers dynamically based on configuration.

TECHNICAL IMPLEMENTATION:
- Tests provider registration and discovery
- Tests auto-detection of API format
- Tests fallback chain behavior
- Tests configuration validation
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

# Import the registry and providers
from course_generator.infrastructure.llm_providers.provider_registry import (
    LLMProviderRegistry,
    ProviderRegistrationError,
    ProviderNotFoundError,
)
from course_generator.infrastructure.llm_providers.base_provider import (
    BaseLLMProvider,
    ProviderCapabilities,
)


class TestLLMProviderRegistry:
    """Test suite for LLM Provider Registry"""

    def test_registry_initialization(self):
        """Test that registry initializes with default providers"""
        registry = LLMProviderRegistry()

        # Should have all supported providers registered
        assert registry.has_provider('openai')
        assert registry.has_provider('anthropic')
        assert registry.has_provider('deepseek')
        assert registry.has_provider('qwen')
        assert registry.has_provider('ollama')
        assert registry.has_provider('llama')
        assert registry.has_provider('gemini')
        assert registry.has_provider('mistral')

    def test_get_provider_names(self):
        """Test getting list of registered provider names"""
        registry = LLMProviderRegistry()
        names = registry.get_provider_names()

        assert isinstance(names, list)
        assert len(names) >= 8  # At least 8 providers
        assert 'openai' in names
        assert 'anthropic' in names

    def test_get_provider_capabilities(self):
        """Test getting provider capabilities"""
        registry = LLMProviderRegistry()

        # OpenAI should support vision
        openai_caps = registry.get_provider_capabilities('openai')
        assert openai_caps is not None
        assert openai_caps.supports_vision is True
        assert openai_caps.supports_streaming is True

    def test_get_unknown_provider_raises_error(self):
        """Test that getting unknown provider raises error"""
        registry = LLMProviderRegistry()

        with pytest.raises(ProviderNotFoundError):
            registry.get_provider('unknown_provider')

    def test_has_provider_returns_false_for_unknown(self):
        """Test has_provider returns False for unknown provider"""
        registry = LLMProviderRegistry()

        assert registry.has_provider('nonexistent') is False

    def test_provider_registration(self):
        """Test registering a new provider"""
        registry = LLMProviderRegistry()

        # Create a mock provider class
        mock_provider_class = Mock()
        mock_provider_class.get_capabilities.return_value = ProviderCapabilities(
            supports_vision=True,
            supports_streaming=True,
            max_tokens=4096,
            supported_models=['test-model']
        )

        # Register the provider
        registry.register_provider('test_provider', mock_provider_class)

        assert registry.has_provider('test_provider')

    def test_duplicate_registration_raises_error(self):
        """Test that duplicate registration raises error"""
        registry = LLMProviderRegistry()
        mock_provider_class = Mock()

        registry.register_provider('duplicate_test', mock_provider_class)

        with pytest.raises(ProviderRegistrationError):
            registry.register_provider('duplicate_test', mock_provider_class)

    def test_get_provider_instance_with_config(self):
        """Test getting a provider instance with configuration"""
        registry = LLMProviderRegistry()

        config = {
            'api_key': 'test-key',
            'model_name': 'gpt-4-vision-preview'
        }

        # This should not raise an error
        provider = registry.get_provider('openai', config)
        assert provider is not None

    def test_get_providers_by_capability(self):
        """Test filtering providers by capability"""
        registry = LLMProviderRegistry()

        # Get all providers that support vision
        vision_providers = registry.get_providers_with_capability('supports_vision')

        assert len(vision_providers) > 0
        for provider_name in vision_providers:
            caps = registry.get_provider_capabilities(provider_name)
            assert caps.supports_vision is True

    def test_auto_detect_provider_from_api_key(self):
        """Test auto-detecting provider from API key format"""
        registry = LLMProviderRegistry()

        # OpenAI keys start with 'sk-'
        detected = registry.auto_detect_provider_from_key('sk-test123abc')
        assert detected == 'openai'

        # Anthropic keys start with 'sk-ant-'
        detected = registry.auto_detect_provider_from_key('sk-ant-test123')
        assert detected == 'anthropic'

    def test_auto_detect_unknown_key_format(self):
        """Test auto-detection returns None for unknown key format"""
        registry = LLMProviderRegistry()

        detected = registry.auto_detect_provider_from_key('random-key-format')
        assert detected is None


class TestProviderRegistryConfigValidation:
    """Test suite for provider configuration validation"""

    def test_validate_openai_config(self):
        """Test OpenAI configuration validation"""
        registry = LLMProviderRegistry()

        valid_config = {
            'api_key': 'sk-test123',
            'model_name': 'gpt-4-vision-preview'
        }

        # Should not raise
        registry.validate_config('openai', valid_config)

    def test_validate_missing_api_key(self):
        """Test validation fails without API key"""
        registry = LLMProviderRegistry()

        invalid_config = {
            'model_name': 'gpt-4-vision-preview'
        }

        with pytest.raises(ValueError, match='api_key'):
            registry.validate_config('openai', invalid_config)

    def test_validate_ollama_without_api_key(self):
        """Test Ollama doesn't require API key"""
        registry = LLMProviderRegistry()

        # Ollama is local, no API key needed
        valid_config = {
            'model_name': 'llava'
        }

        # Should not raise
        registry.validate_config('ollama', valid_config)


class TestProviderRegistryFallback:
    """Test suite for provider fallback chain"""

    @pytest.mark.asyncio
    async def test_fallback_chain_on_failure(self):
        """Test fallback to next provider on failure"""
        registry = LLMProviderRegistry()

        # Configure fallback chain
        fallback_chain = ['openai', 'anthropic', 'ollama']

        # Mock the providers to simulate failure
        with patch.object(registry, 'get_provider') as mock_get:
            # First provider fails
            failing_provider = Mock()
            failing_provider.analyze_image = AsyncMock(side_effect=Exception('API Error'))

            # Second provider succeeds
            successful_provider = Mock()
            successful_provider.analyze_image = AsyncMock(return_value='Success')

            mock_get.side_effect = [failing_provider, successful_provider]

            result = await registry.execute_with_fallback(
                'analyze_image',
                fallback_chain,
                {'api_key': 'test'},
                image_data=b'test',
                prompt='test prompt'
            )

            assert result == 'Success'

    @pytest.mark.asyncio
    async def test_fallback_exhausted_raises_error(self):
        """Test error raised when all providers in chain fail"""
        registry = LLMProviderRegistry()

        fallback_chain = ['openai', 'anthropic']

        with patch.object(registry, 'get_provider') as mock_get:
            failing_provider = Mock()
            failing_provider.analyze_image = AsyncMock(side_effect=Exception('API Error'))
            mock_get.return_value = failing_provider

            with pytest.raises(Exception, match='All providers failed'):
                await registry.execute_with_fallback(
                    'analyze_image',
                    fallback_chain,
                    {'api_key': 'test'},
                    image_data=b'test',
                    prompt='test prompt'
                )


class TestProviderMetadata:
    """Test suite for provider metadata"""

    def test_get_provider_metadata(self):
        """Test getting provider metadata"""
        registry = LLMProviderRegistry()

        metadata = registry.get_provider_metadata('openai')

        assert metadata is not None
        assert 'display_name' in metadata
        assert 'api_base_url' in metadata
        assert 'supported_models' in metadata

    def test_get_all_providers_metadata(self):
        """Test getting all providers metadata"""
        registry = LLMProviderRegistry()

        all_metadata = registry.get_all_providers_metadata()

        assert isinstance(all_metadata, dict)
        assert len(all_metadata) >= 8
        assert 'openai' in all_metadata
        assert 'anthropic' in all_metadata


class TestProviderHealthCheck:
    """Test suite for provider health checking"""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check"""
        registry = LLMProviderRegistry()

        with patch.object(registry, 'get_provider') as mock_get:
            healthy_provider = Mock()
            healthy_provider.health_check = AsyncMock(return_value=True)
            mock_get.return_value = healthy_provider

            is_healthy = await registry.check_provider_health(
                'openai',
                {'api_key': 'test-key'}
            )

            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test failed health check"""
        registry = LLMProviderRegistry()

        with patch.object(registry, 'get_provider') as mock_get:
            unhealthy_provider = Mock()
            unhealthy_provider.health_check = AsyncMock(return_value=False)
            mock_get.return_value = unhealthy_provider

            is_healthy = await registry.check_provider_health(
                'openai',
                {'api_key': 'invalid-key'}
            )

            assert is_healthy is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
