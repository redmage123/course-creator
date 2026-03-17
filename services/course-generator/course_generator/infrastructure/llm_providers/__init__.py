"""
LLM Providers Package

BUSINESS PURPOSE:
Provides a unified interface for multiple LLM providers to support
screenshot-to-course generation and other AI features. Enables organizations
to configure their preferred LLM provider (OpenAI, Anthropic, Deepseek,
Qwen, Ollama, Llama, Gemini, Mistral) with their own API keys.

TECHNICAL IMPLEMENTATION:
- Abstract base class for provider interface
- Provider-specific implementations for 8 providers
- Provider registry for auto-detection and management
- Fallback chain support for high availability

SUPPORTED PROVIDERS:
- OpenAI (GPT-5.2, GPT-4o) - Premium vision and text
- Anthropic (Claude 3.5) - Strong reasoning and vision
- Deepseek (Deepseek-VL) - Cost-effective alternative
- Qwen (Qwen-VL) - Alibaba Cloud, strong multilingual
- Ollama (LLaVA) - Local/self-hosted models
- Llama (Llama 3.2 Vision) - Meta models via Together/Fireworks
- Gemini (Gemini 2.0) - Google's multimodal models
- Mistral (Pixtral) - European GDPR-friendly option
"""

from course_generator.infrastructure.llm_providers.base_provider import (
    BaseLLMProvider,
    LLMProviderCapabilities,
    LLMProviderName,
    LLMResponse,
    VisionAnalysisResult
)
from course_generator.infrastructure.llm_providers.provider_registry import (
    LLMProviderRegistry,
    ProviderConfig,
    ProviderPriority,
    OrganizationLLMConfig,
    get_registry,
    get_provider_for_organization
)

# Provider implementations
from course_generator.infrastructure.llm_providers.openai_provider import OpenAIProvider
from course_generator.infrastructure.llm_providers.anthropic_provider import AnthropicProvider
from course_generator.infrastructure.llm_providers.deepseek_provider import DeepseekProvider
from course_generator.infrastructure.llm_providers.qwen_provider import QwenProvider
from course_generator.infrastructure.llm_providers.ollama_provider import OllamaProvider
from course_generator.infrastructure.llm_providers.llama_provider import LlamaProvider
from course_generator.infrastructure.llm_providers.gemini_provider import GeminiProvider
from course_generator.infrastructure.llm_providers.mistral_provider import MistralProvider

__all__ = [
    # Base classes and types
    'BaseLLMProvider',
    'LLMProviderCapabilities',
    'LLMProviderName',
    'LLMResponse',
    'VisionAnalysisResult',

    # Registry and configuration
    'LLMProviderRegistry',
    'ProviderConfig',
    'ProviderPriority',
    'OrganizationLLMConfig',
    'get_registry',
    'get_provider_for_organization',

    # Provider implementations
    'OpenAIProvider',
    'AnthropicProvider',
    'DeepseekProvider',
    'QwenProvider',
    'OllamaProvider',
    'LlamaProvider',
    'GeminiProvider',
    'MistralProvider',
]
