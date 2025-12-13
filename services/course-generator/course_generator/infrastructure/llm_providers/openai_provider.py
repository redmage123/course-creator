"""
OpenAI LLM Provider Implementation

BUSINESS PURPOSE:
Implements the LLM provider interface for OpenAI's GPT models including
GPT-5.2 with vision capabilities for screenshot-to-course generation.

TECHNICAL IMPLEMENTATION:
- Uses httpx for async HTTP requests
- Supports vision analysis with GPT-5.2 and GPT-4o models
- Handles rate limiting, retries, and error translation
- Token counting and cost estimation

WHY:
OpenAI provides state-of-the-art vision and language models. GPT-5.2 offers
advanced multimodal capabilities essential for accurate screenshot analysis
and course content generation.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

import httpx

from course_generator.infrastructure.llm_providers.base_provider import (
    BaseLLMProvider,
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


logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI LLM Provider

    BUSINESS PURPOSE:
    Provides access to OpenAI's GPT models (including GPT-5.2) for:
    - Screenshot/image analysis (vision)
    - Course content generation
    - Quiz and exercise creation

    TECHNICAL DETAILS:
    - API Base: https://api.openai.com/v1
    - Authentication: Bearer token
    - Vision: Supported in GPT-4o, GPT-4-turbo, GPT-5.2
    - Streaming: Supported
    - JSON mode: Supported

    MODELS:
    - gpt-5.2: Latest model with advanced vision and reasoning
    - gpt-5.2-vision: Vision-specific variant
    - gpt-4o: Multimodal model with vision
    - gpt-4o-mini: Cost-effective multimodal model
    - gpt-4-turbo: Previous generation with vision
    """

    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-5.2"
    DEFAULT_VISION_MODEL = "gpt-5.2"

    # Pricing per 1M tokens (as of late 2025)
    PRICING = {
        "gpt-5.2": {"input": 5.00, "output": 15.00},
        "gpt-5.2-vision": {"input": 5.00, "output": 15.00},
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        timeout: float = 120.0,
        max_retries: int = 3
    ):
        """
        Initialize OpenAI Provider

        Args:
            api_key: OpenAI API key
            base_url: Custom base URL (for Azure OpenAI or proxies)
            model: Default model (defaults to gpt-5.2)
            organization_id: Organization ID for usage tracking
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
            model=model or self.DEFAULT_MODEL,
            organization_id=organization_id,
            timeout=timeout,
            max_retries=max_retries
        )

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=httpx.Timeout(self.timeout)
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def default_vision_model(self) -> str:
        return self.DEFAULT_VISION_MODEL

    def get_capabilities(self) -> LLMProviderCapabilities:
        """Get OpenAI provider capabilities"""
        return LLMProviderCapabilities(
            supports_vision=True,
            supports_streaming=True,
            supports_function_calling=True,
            supports_json_mode=True,
            max_tokens=128000,
            max_image_size_mb=20.0,
            supported_image_formats=["image/png", "image/jpeg", "image/webp", "image/gif"],
            rate_limit_requests_per_minute=500,
            context_window=128000
        )

    async def analyze_image(
        self,
        image_data: Union[bytes, str],
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3
    ) -> VisionAnalysisResult:
        """
        Analyze an image using OpenAI's vision models

        BUSINESS USE CASE:
        Extract course content from screenshots for course generation.

        Args:
            image_data: Image bytes or base64 string
            prompt: Analysis prompt
            model: Model to use (defaults to gpt-5.2)
            max_tokens: Max response tokens
            temperature: Sampling temperature

        Returns:
            VisionAnalysisResult with extracted content
        """
        start_time = time.time()
        use_model = model or self.default_vision_model

        # Prepare image data
        if isinstance(image_data, bytes):
            self.validate_image(image_data)
            image_base64 = self.encode_image_to_base64(image_data)
            media_type = self.get_image_media_type(image_data)
        else:
            image_base64 = image_data
            media_type = "image/png"

        # Build the request
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt or self.get_screenshot_analysis_prompt()
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_base64}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ]

        request_body = {
            "model": use_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }

        # Make the API call with retries
        response_data = await self._make_request(
            "/chat/completions",
            request_body
        )

        # Parse the response
        processing_time_ms = int((time.time() - start_time) * 1000)
        content = response_data["choices"][0]["message"]["content"]
        usage = response_data.get("usage", {})

        # Parse JSON response
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {"extracted_text": content}

        return VisionAnalysisResult(
            extracted_text=parsed.get("extracted_text", content),
            detected_language=parsed.get("detected_language", "en"),
            confidence_score=float(parsed.get("confidence_score", 0.9)),
            course_structure=parsed.get("course_structure", {}),
            detected_elements=parsed.get("detected_elements", []),
            suggested_title=parsed.get("title", ""),
            suggested_description=parsed.get("description", ""),
            suggested_topics=parsed.get("topics", []),
            suggested_difficulty=parsed.get("difficulty", "intermediate"),
            suggested_duration_hours=int(parsed.get("duration_hours", 0)),
            raw_response=content,
            model_used=use_model,
            provider_used=self.provider_name,
            processing_time_ms=processing_time_ms,
            tokens_used=usage.get("total_tokens", 0)
        )

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
        Generate text using OpenAI's models

        Args:
            prompt: User prompt
            system_prompt: System context
            model: Model to use
            max_tokens: Max response tokens
            temperature: Sampling temperature
            json_mode: Request JSON output

        Returns:
            LLMResponse with generated text
        """
        use_model = model or self.model

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        request_body = {
            "model": use_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if json_mode:
            request_body["response_format"] = {"type": "json_object"}

        response_data = await self._make_request(
            "/chat/completions",
            request_body
        )

        content = response_data["choices"][0]["message"]["content"]
        usage = response_data.get("usage", {})
        finish_reason = response_data["choices"][0].get("finish_reason", "stop")

        # Get pricing for cost estimation
        pricing = self.PRICING.get(use_model, {"input": 2.50, "output": 10.00})

        return LLMResponse(
            content=content,
            model=use_model,
            provider=self.provider_name,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            finish_reason=finish_reason,
            metadata={
                "input_cost_per_million": pricing["input"],
                "output_cost_per_million": pricing["output"]
            }
        )

    async def health_check(self) -> bool:
        """
        Check if OpenAI API is accessible

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self._client.get("/models")
            return response.status_code == 200
        except httpx.RequestError as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False

    async def _make_request(
        self,
        endpoint: str,
        body: Dict[str, Any],
        retries: int = None
    ) -> Dict[str, Any]:
        """
        Make an API request with retry logic

        Args:
            endpoint: API endpoint
            body: Request body
            retries: Number of retries remaining

        Returns:
            Parsed response JSON

        Raises:
            LLMProviderException: On API errors
        """
        retries = retries if retries is not None else self.max_retries

        for attempt in range(retries + 1):
            try:
                response = await self._client.post(endpoint, json=body)

                if response.status_code == 200:
                    return response.json()

                elif response.status_code == 401:
                    raise LLMProviderAuthenticationException(
                        message="Invalid API key",
                        provider_name=self.provider_name
                    )

                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < retries:
                        logger.warning(
                            f"OpenAI rate limit hit, waiting {retry_after}s "
                            f"(attempt {attempt + 1}/{retries + 1})"
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    raise LLMProviderRateLimitException(
                        message=f"Rate limit exceeded. Retry after {retry_after} seconds",
                        provider_name=self.provider_name,
                        retry_after=retry_after
                    )

                elif response.status_code >= 500:
                    if attempt < retries:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"OpenAI server error {response.status_code}, "
                            f"retrying in {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    raise LLMProviderResponseException(
                        message=f"Server error (HTTP {response.status_code})",
                        provider_name=self.provider_name
                    )

                else:
                    error_body = response.json() if response.content else {}
                    error_message = error_body.get("error", {}).get(
                        "message", "Unknown error"
                    )
                    raise LLMProviderResponseException(
                        message=f"API error (HTTP {response.status_code}): {error_message}",
                        provider_name=self.provider_name
                    )

            except httpx.ConnectError as e:
                if attempt < retries:
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"OpenAI connection error, retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                raise LLMProviderConnectionException(
                    message=f"Failed to connect to OpenAI API: {str(e)}",
                    provider_name=self.provider_name,
                    original_exception=e
                )

            except httpx.TimeoutException as e:
                if attempt < retries:
                    logger.warning(f"OpenAI timeout, retrying: {e}")
                    await asyncio.sleep(1)
                    continue
                raise LLMProviderConnectionException(
                    message=f"Request to OpenAI API timed out: {str(e)}",
                    provider_name=self.provider_name,
                    original_exception=e
                )

        raise LLMProviderResponseException(
            message="Max retries exceeded",
            provider_name=self.provider_name
        )

    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("Closed OpenAI provider client")
