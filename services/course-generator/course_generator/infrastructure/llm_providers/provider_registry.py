"""
LLM Provider Registry and Factory

BUSINESS PURPOSE:
Central registry for all LLM providers enabling:
- Organization-level provider configuration
- Auto-detection of provider from API URL/key
- Fallback chain support for high availability
- Dynamic provider instantiation

TECHNICAL IMPLEMENTATION:
- Factory pattern for provider creation
- Registry pattern for provider management
- Configuration-driven instantiation
- Database integration for org settings

WHY:
Organizations need flexibility in choosing their LLM provider based on:
- Cost constraints
- Data residency requirements (GDPR)
- Performance needs
- Existing cloud infrastructure
This registry enables seamless provider switching without code changes.
"""

import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Type
from uuid import UUID

from course_generator.infrastructure.llm_providers.base_provider import (
    BaseLLMProvider,
    LLMProviderCapabilities,
    LLMProviderName
)
from shared.exceptions import (
    LLMProviderException,
    LLMProviderAuthenticationException
)


logger = logging.getLogger(__name__)


class ProviderPriority(int, Enum):
    """Provider priority for fallback ordering"""
    PRIMARY = 1
    SECONDARY = 2
    TERTIARY = 3
    FALLBACK = 4


@dataclass
class ProviderConfig:
    """
    Configuration for an LLM provider instance

    BUSINESS CONTEXT:
    Stores all settings needed to instantiate a provider,
    typically loaded from organization configuration.
    """
    provider_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    vision_model: Optional[str] = None
    timeout: float = 120.0
    max_retries: int = 3
    priority: ProviderPriority = ProviderPriority.PRIMARY
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrganizationLLMConfig:
    """
    Organization-level LLM configuration

    BUSINESS CONTEXT:
    Organizations can configure multiple providers with priorities.
    The system will use the primary provider and fall back to
    secondary/tertiary if the primary fails.
    """
    organization_id: UUID
    providers: List[ProviderConfig] = field(default_factory=list)
    default_provider: Optional[str] = None
    vision_provider: Optional[str] = None
    fallback_enabled: bool = True


class LLMProviderRegistry:
    """
    Registry and Factory for LLM Providers

    BUSINESS PURPOSE:
    Manages all available LLM providers and creates instances
    based on organization configuration or explicit parameters.

    FEATURES:
    - Provider registration
    - Auto-detection from URL/key patterns
    - Factory methods for instantiation
    - Fallback chain support
    - Organization configuration loading

    USAGE:
    ```python
    registry = LLMProviderRegistry()

    # Get provider by name
    provider = await registry.get_provider("openai", api_key="sk-...")

    # Get provider for organization
    provider = await registry.get_provider_for_organization(org_id)

    # Auto-detect provider
    provider = await registry.auto_detect_provider(api_key="sk-...")
    ```
    """

    # Provider class mapping
    _provider_classes: Dict[str, Type[BaseLLMProvider]] = {}

    # URL patterns for auto-detection
    _url_patterns = {
        r"api\.openai\.com": "openai",
        r"api\.anthropic\.com": "anthropic",
        r"api\.deepseek\.com": "deepseek",
        r"dashscope\.aliyuncs\.com": "qwen",
        r"localhost:11434": "ollama",
        r"127\.0\.0\.1:11434": "ollama",
        r"api\.together\.xyz": "llama",
        r"api\.fireworks\.ai": "llama",
        r"api\.replicate\.com": "llama",
        r"generativelanguage\.googleapis\.com": "gemini",
        r"api\.mistral\.ai": "mistral",
    }

    # API key patterns for auto-detection
    _key_patterns = {
        r"^sk-[a-zA-Z0-9]{20,}$": "openai",
        r"^sk-ant-[a-zA-Z0-9-]+$": "anthropic",
        r"^sk-[a-f0-9]{32}$": "deepseek",
        r"^AIza[a-zA-Z0-9_-]{35}$": "gemini",
    }

    def __init__(self):
        """Initialize the registry and register all providers"""
        self._register_providers()
        self._org_configs: Dict[UUID, OrganizationLLMConfig] = {}

    def _register_providers(self):
        """Register all available providers"""
        # Import providers here to avoid circular imports
        from course_generator.infrastructure.llm_providers.openai_provider import OpenAIProvider
        from course_generator.infrastructure.llm_providers.anthropic_provider import AnthropicProvider
        from course_generator.infrastructure.llm_providers.deepseek_provider import DeepseekProvider
        from course_generator.infrastructure.llm_providers.qwen_provider import QwenProvider
        from course_generator.infrastructure.llm_providers.ollama_provider import OllamaProvider
        from course_generator.infrastructure.llm_providers.llama_provider import LlamaProvider
        from course_generator.infrastructure.llm_providers.gemini_provider import GeminiProvider
        from course_generator.infrastructure.llm_providers.mistral_provider import MistralProvider

        self._provider_classes = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "deepseek": DeepseekProvider,
            "qwen": QwenProvider,
            "ollama": OllamaProvider,
            "llama": LlamaProvider,
            "gemini": GeminiProvider,
            "mistral": MistralProvider,
        }

        logger.info(f"Registered {len(self._provider_classes)} LLM providers")

    def get_available_providers(self) -> List[str]:
        """
        Get list of available provider names

        Returns:
            List of provider names
        """
        return list(self._provider_classes.keys())

    def get_provider_class(self, provider_name: str) -> Optional[Type[BaseLLMProvider]]:
        """
        Get provider class by name

        Args:
            provider_name: Provider identifier

        Returns:
            Provider class or None
        """
        return self._provider_classes.get(provider_name.lower())

    def detect_provider_from_url(self, url: str) -> Optional[str]:
        """
        Auto-detect provider from base URL

        Args:
            url: API base URL

        Returns:
            Provider name or None
        """
        for pattern, provider in self._url_patterns.items():
            if re.search(pattern, url, re.IGNORECASE):
                logger.debug(f"Detected provider '{provider}' from URL pattern")
                return provider
        return None

    def detect_provider_from_key(self, api_key: str) -> Optional[str]:
        """
        Auto-detect provider from API key format

        Args:
            api_key: API key string

        Returns:
            Provider name or None
        """
        for pattern, provider in self._key_patterns.items():
            if re.match(pattern, api_key):
                logger.debug(f"Detected provider '{provider}' from key pattern")
                return provider
        return None

    async def create_provider(
        self,
        provider_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """
        Create a provider instance

        Args:
            provider_name: Provider identifier
            api_key: API key (optional, can use env var)
            base_url: Custom base URL
            model: Default model
            organization_id: Organization ID for tracking
            **kwargs: Additional provider-specific args

        Returns:
            Configured provider instance

        Raises:
            LLMProviderException: If provider not found
        """
        provider_class = self.get_provider_class(provider_name)

        if not provider_class:
            available = ", ".join(self.get_available_providers())
            raise LLMProviderException(
                f"Unknown provider '{provider_name}'. Available: {available}"
            )

        # Get API key from env if not provided
        if not api_key:
            env_var = f"{provider_name.upper()}_API_KEY"
            api_key = os.environ.get(env_var)

        # Create provider instance
        provider = provider_class(
            api_key=api_key,
            base_url=base_url,
            model=model,
            organization_id=organization_id,
            **kwargs
        )

        logger.info(
            f"Created {provider_name} provider for org {organization_id}"
        )

        return provider

    async def auto_detect_and_create(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """
        Auto-detect provider and create instance

        Attempts to detect provider from:
        1. Base URL pattern
        2. API key pattern
        3. Environment variables

        Args:
            api_key: API key
            base_url: Base URL
            model: Default model
            organization_id: Organization ID
            **kwargs: Additional args

        Returns:
            Configured provider instance

        Raises:
            LLMProviderException: If provider cannot be detected
        """
        provider_name = None

        # Try URL detection first
        if base_url:
            provider_name = self.detect_provider_from_url(base_url)

        # Try key detection if URL didn't match
        if not provider_name and api_key:
            provider_name = self.detect_provider_from_key(api_key)

        # Check for environment variables
        if not provider_name:
            for name in self.get_available_providers():
                env_key = os.environ.get(f"{name.upper()}_API_KEY")
                if env_key:
                    provider_name = name
                    api_key = env_key
                    break

        if not provider_name:
            raise LLMProviderException(
                "Could not auto-detect LLM provider. "
                "Please specify provider_name explicitly."
            )

        return await self.create_provider(
            provider_name=provider_name,
            api_key=api_key,
            base_url=base_url,
            model=model,
            organization_id=organization_id,
            **kwargs
        )

    def set_organization_config(
        self,
        organization_id: UUID,
        config: OrganizationLLMConfig
    ):
        """
        Set organization LLM configuration

        Args:
            organization_id: Organization ID
            config: LLM configuration
        """
        self._org_configs[organization_id] = config
        logger.info(f"Set LLM config for org {organization_id}")

    def get_organization_config(
        self,
        organization_id: UUID
    ) -> Optional[OrganizationLLMConfig]:
        """
        Get organization LLM configuration

        Args:
            organization_id: Organization ID

        Returns:
            Configuration or None
        """
        return self._org_configs.get(organization_id)

    async def get_provider_for_organization(
        self,
        organization_id: UUID,
        require_vision: bool = False,
        provider_override: Optional[str] = None
    ) -> BaseLLMProvider:
        """
        Get configured provider for an organization

        BUSINESS LOGIC:
        1. Check for provider override
        2. Get org config from cache/database
        3. Select appropriate provider (vision if required)
        4. Create and return provider instance

        Args:
            organization_id: Organization ID
            require_vision: Whether vision capability is required
            provider_override: Optional provider name to use instead

        Returns:
            Configured provider instance

        Raises:
            LLMProviderException: If no suitable provider found
        """
        # Get organization config
        org_config = self.get_organization_config(organization_id)

        if not org_config:
            # Load from database (would be implemented in DAO)
            # For now, fall back to auto-detection
            logger.warning(
                f"No LLM config for org {organization_id}, "
                "falling back to auto-detection"
            )
            return await self.auto_detect_and_create(
                organization_id=organization_id
            )

        # Determine which provider to use
        if provider_override:
            provider_name = provider_override
        elif require_vision and org_config.vision_provider:
            provider_name = org_config.vision_provider
        elif org_config.default_provider:
            provider_name = org_config.default_provider
        elif org_config.providers:
            # Use highest priority active provider
            active_providers = [
                p for p in org_config.providers
                if p.is_active
            ]
            if not active_providers:
                raise LLMProviderException(
                    f"No active providers configured for org {organization_id}"
                )
            provider_config = min(active_providers, key=lambda p: p.priority)
            provider_name = provider_config.provider_name
        else:
            raise LLMProviderException(
                f"No providers configured for org {organization_id}"
            )

        # Find provider config
        provider_config = None
        for config in org_config.providers:
            if config.provider_name == provider_name:
                provider_config = config
                break

        if not provider_config:
            # Create with just provider name
            return await self.create_provider(
                provider_name=provider_name,
                organization_id=organization_id
            )

        # Check vision capability if required
        if require_vision:
            provider_class = self.get_provider_class(provider_name)
            if provider_class:
                temp_instance = provider_class.__new__(provider_class)
                temp_instance._client = None
                capabilities = temp_instance.get_capabilities()
                if not capabilities.supports_vision:
                    raise LLMProviderException(
                        f"Provider '{provider_name}' does not support vision. "
                        f"Configure a vision-capable provider for org {organization_id}"
                    )

        # Create provider with config
        return await self.create_provider(
            provider_name=provider_config.provider_name,
            api_key=provider_config.api_key,
            base_url=provider_config.base_url,
            model=provider_config.vision_model if require_vision else provider_config.model,
            organization_id=organization_id,
            timeout=provider_config.timeout,
            max_retries=provider_config.max_retries
        )

    async def get_fallback_providers(
        self,
        organization_id: UUID,
        exclude: Optional[List[str]] = None
    ) -> List[BaseLLMProvider]:
        """
        Get fallback providers for an organization

        BUSINESS LOGIC:
        When primary provider fails, return list of fallback
        providers in priority order.

        Args:
            organization_id: Organization ID
            exclude: Provider names to exclude

        Returns:
            List of fallback providers
        """
        org_config = self.get_organization_config(organization_id)

        if not org_config or not org_config.fallback_enabled:
            return []

        exclude = exclude or []
        fallback_providers = []

        # Get active providers sorted by priority
        active_providers = sorted(
            [p for p in org_config.providers if p.is_active],
            key=lambda p: p.priority
        )

        for config in active_providers:
            if config.provider_name in exclude:
                continue

            try:
                provider = await self.create_provider(
                    provider_name=config.provider_name,
                    api_key=config.api_key,
                    base_url=config.base_url,
                    model=config.model,
                    organization_id=organization_id
                )
                fallback_providers.append(provider)
            except LLMProviderException as e:
                logger.warning(
                    f"Failed to create fallback provider "
                    f"{config.provider_name}: {e}"
                )

        return fallback_providers


# Global registry instance
_registry: Optional[LLMProviderRegistry] = None


def get_registry() -> LLMProviderRegistry:
    """
    Get the global provider registry

    Returns:
        LLMProviderRegistry singleton
    """
    global _registry
    if _registry is None:
        _registry = LLMProviderRegistry()
    return _registry


async def get_provider_for_organization(
    organization_id: UUID,
    require_vision: bool = False,
    provider_override: Optional[str] = None
) -> BaseLLMProvider:
    """
    Convenience function to get provider for organization

    Args:
        organization_id: Organization ID
        require_vision: Whether vision is required
        provider_override: Optional provider override

    Returns:
        Configured provider instance
    """
    registry = get_registry()
    return await registry.get_provider_for_organization(
        organization_id=organization_id,
        require_vision=require_vision,
        provider_override=provider_override
    )
