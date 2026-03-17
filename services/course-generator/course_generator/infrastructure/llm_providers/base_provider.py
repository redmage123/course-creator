"""
Base LLM Provider Interface

BUSINESS PURPOSE:
Defines the abstract interface that all LLM providers must implement.
Enables organization-level LLM configuration and seamless provider switching
for screenshot-to-course generation and other AI features.

TECHNICAL IMPLEMENTATION:
- Abstract base class with required methods
- Dataclasses for structured responses
- Capability enumeration for feature detection
- Async support for non-blocking operations

WHY:
Multiple organizations use different LLM providers based on their needs,
cost constraints, and data residency requirements. This interface enables:
- Plug-and-play provider switching
- Consistent API across providers
- Feature detection for graceful degradation
"""

import base64
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from shared.exceptions import (
    LLMProviderException,
    LLMProviderConnectionException,
    LLMProviderAuthenticationException,
    LLMProviderRateLimitException,
    LLMProviderResponseException
)


logger = logging.getLogger(__name__)


class LLMProviderName(str, Enum):
    """
    Supported LLM Provider Names

    BUSINESS CONTEXT:
    Enumerates all supported LLM providers for screenshot-to-course generation.
    Each provider has different capabilities, pricing, and API requirements.
    """
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    OLLAMA = "ollama"
    LLAMA = "llama"


@dataclass
class LLMProviderCapabilities:
    """
    Capabilities of an LLM Provider

    BUSINESS CONTEXT:
    Different providers support different features. This dataclass
    enables feature detection for graceful degradation and provider selection.

    TECHNICAL FIELDS:
    - supports_vision: Can analyze images (required for screenshot analysis)
    - supports_streaming: Can stream responses
    - supports_function_calling: Can use tool/function calling
    - max_tokens: Maximum tokens per request
    - max_image_size_mb: Maximum image size for vision
    - supported_image_formats: List of supported MIME types
    """
    supports_vision: bool = False
    supports_streaming: bool = False
    supports_function_calling: bool = False
    supports_json_mode: bool = False
    max_tokens: int = 4096
    max_image_size_mb: float = 20.0
    supported_image_formats: List[str] = field(
        default_factory=lambda: ["image/png", "image/jpeg", "image/webp"]
    )
    rate_limit_requests_per_minute: int = 60
    context_window: int = 128000


@dataclass
class LLMResponse:
    """
    Standardized LLM Response

    BUSINESS CONTEXT:
    Provides a consistent response format across all LLM providers,
    enabling uniform handling in the screenshot analysis pipeline.
    """
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = "stop"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def estimated_cost(self) -> float:
        """
        Estimate API cost based on token usage

        Note: Costs vary by provider and model. This is a rough estimate.
        """
        # Default pricing (per 1M tokens)
        input_cost_per_million = self.metadata.get("input_cost_per_million", 2.50)
        output_cost_per_million = self.metadata.get("output_cost_per_million", 10.00)

        input_cost = (self.input_tokens / 1_000_000) * input_cost_per_million
        output_cost = (self.output_tokens / 1_000_000) * output_cost_per_million

        return input_cost + output_cost


@dataclass
class VisionAnalysisResult:
    """
    Result from Vision/Image Analysis

    BUSINESS CONTEXT:
    Structured output from screenshot analysis containing extracted
    course content, detected elements, and confidence scores.
    """
    extracted_text: str
    detected_language: str = "en"
    confidence_score: float = 0.0
    course_structure: Dict[str, Any] = field(default_factory=dict)
    detected_elements: List[Dict[str, Any]] = field(default_factory=list)
    suggested_title: str = ""
    suggested_description: str = ""
    suggested_topics: List[str] = field(default_factory=list)
    suggested_difficulty: str = "intermediate"
    suggested_duration_hours: int = 0
    raw_response: str = ""
    model_used: str = ""
    provider_used: str = ""
    processing_time_ms: int = 0
    tokens_used: int = 0


class BaseLLMProvider(ABC):
    """
    Abstract Base Class for LLM Providers

    BUSINESS PURPOSE:
    Defines the contract that all LLM provider implementations must follow.
    Enables seamless switching between providers (OpenAI, Anthropic, Deepseek,
    Qwen, Ollama, Llama) based on organization configuration.

    TECHNICAL IMPLEMENTATION:
    - Abstract methods for core functionality
    - Common utility methods for all providers
    - Error handling and retry logic
    - Token counting and cost estimation

    USAGE:
    Each provider implementation extends this class and implements:
    - analyze_image(): For screenshot/vision analysis
    - generate_text(): For text completion/generation
    - get_capabilities(): For feature detection
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        timeout: float = 60.0,
        max_retries: int = 3
    ):
        """
        Initialize LLM Provider

        Args:
            api_key: API key for the provider (from org config or env)
            base_url: Custom base URL (for self-hosted or proxied APIs)
            model: Default model to use
            organization_id: Organization ID for usage tracking
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for transient failures
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.organization_id = organization_id
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None

        logger.info(
            f"Initialized {self.provider_name} provider with model {self.model}"
        )

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Get the provider name

        Returns:
            Provider name string (e.g., 'openai', 'anthropic')
        """
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """
        Get the default model for this provider

        Returns:
            Default model identifier
        """
        pass

    @property
    @abstractmethod
    def default_vision_model(self) -> str:
        """
        Get the default vision-capable model for this provider

        Returns:
            Default vision model identifier
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> LLMProviderCapabilities:
        """
        Get provider capabilities

        BUSINESS USE CASE:
        Feature detection for screenshot-to-course generation.
        Must check if provider supports vision before attempting image analysis.

        Returns:
            LLMProviderCapabilities dataclass
        """
        pass

    @abstractmethod
    async def analyze_image(
        self,
        image_data: Union[bytes, str],
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3
    ) -> VisionAnalysisResult:
        """
        Analyze an image using the vision model

        BUSINESS USE CASE:
        Core functionality for screenshot-to-course generation.
        Extracts course content, structure, and metadata from screenshots.

        Args:
            image_data: Image bytes or base64-encoded string
            prompt: Analysis prompt (what to extract from the image)
            model: Override default model
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (lower = more focused)

        Returns:
            VisionAnalysisResult with extracted content

        Raises:
            LLMProviderException: Base exception for provider errors
            LLMProviderConnectionException: Network/connection issues
            LLMProviderAuthenticationException: Invalid API key
            LLMProviderRateLimitException: Rate limit exceeded
        """
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        json_mode: bool = False
    ) -> LLMResponse:
        """
        Generate text completion

        BUSINESS USE CASE:
        Course content generation, quiz creation, and other text
        generation tasks after screenshot analysis.

        Args:
            prompt: User prompt
            system_prompt: System/context prompt
            model: Override default model
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            json_mode: Request JSON-formatted output

        Returns:
            LLMResponse with generated text

        Raises:
            LLMProviderException: Base exception for provider errors
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is healthy and accessible

        BUSINESS USE CASE:
        Verify provider connectivity before attempting operations.
        Used for fallback provider selection.

        Returns:
            True if provider is healthy, False otherwise
        """
        pass

    async def close(self):
        """
        Close the provider client and cleanup resources
        """
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info(f"Closed {self.provider_name} provider client")

    # Utility Methods

    def encode_image_to_base64(self, image_data: bytes) -> str:
        """
        Encode image bytes to base64 string

        Args:
            image_data: Raw image bytes

        Returns:
            Base64-encoded string
        """
        return base64.b64encode(image_data).decode("utf-8")

    def get_image_media_type(self, image_data: bytes) -> str:
        """
        Detect image MIME type from bytes

        Args:
            image_data: Raw image bytes

        Returns:
            MIME type string (e.g., 'image/png')
        """
        # Check magic bytes for common formats
        if image_data[:8] == b'\x89PNG\r\n\x1a\n':
            return "image/png"
        elif image_data[:2] == b'\xff\xd8':
            return "image/jpeg"
        elif image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
            return "image/webp"
        elif image_data[:6] in (b'GIF87a', b'GIF89a'):
            return "image/gif"
        else:
            return "image/png"  # Default fallback

    def validate_image(self, image_data: bytes) -> None:
        """
        Validate image data before sending to API

        Args:
            image_data: Raw image bytes

        Raises:
            LLMProviderException: If image validation fails
        """
        capabilities = self.get_capabilities()

        # Check size
        size_mb = len(image_data) / (1024 * 1024)
        if size_mb > capabilities.max_image_size_mb:
            raise LLMProviderException(
                f"Image size ({size_mb:.1f}MB) exceeds maximum "
                f"({capabilities.max_image_size_mb}MB) for {self.provider_name}"
            )

        # Check format
        media_type = self.get_image_media_type(image_data)
        if media_type not in capabilities.supported_image_formats:
            raise LLMProviderException(
                f"Image format {media_type} not supported by {self.provider_name}. "
                f"Supported: {capabilities.supported_image_formats}"
            )

    def get_screenshot_analysis_prompt(self) -> str:
        """
        Get the standard prompt for screenshot analysis

        BUSINESS USE CASE:
        Consistent prompt for extracting course content from screenshots.

        Returns:
            Analysis prompt string
        """
        return """Analyze this screenshot of educational/course content and extract the following information:

1. **Course Title**: What is the main title or topic shown?
2. **Course Description**: Write a brief description of what this content covers.
3. **Topics/Sections**: List all topics, sections, or modules visible.
4. **Learning Objectives**: What will students learn from this content?
5. **Difficulty Level**: Estimate the difficulty (beginner, intermediate, advanced).
6. **Estimated Duration**: How long would it take to cover this material (in hours)?
7. **Prerequisites**: What prior knowledge might be needed?
8. **Key Concepts**: List the main concepts or skills covered.

Provide your response in the following JSON format:
{
    "title": "Course Title",
    "description": "Brief course description",
    "topics": ["Topic 1", "Topic 2", ...],
    "learning_objectives": ["Objective 1", "Objective 2", ...],
    "difficulty": "beginner|intermediate|advanced",
    "duration_hours": 10,
    "prerequisites": ["Prerequisite 1", ...],
    "key_concepts": ["Concept 1", "Concept 2", ...],
    "detected_language": "en",
    "confidence_score": 0.95
}

Be thorough and extract as much relevant information as possible from the image."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model}, provider={self.provider_name})"
