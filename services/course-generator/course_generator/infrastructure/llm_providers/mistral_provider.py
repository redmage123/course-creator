"""
Mistral AI LLM Provider Implementation

BUSINESS PURPOSE:
Implements the LLM provider interface for Mistral AI's models including
Pixtral for vision capabilities and screenshot-to-course generation.

TECHNICAL IMPLEMENTATION:
- Uses httpx for async HTTP requests
- OpenAI-compatible API format
- Supports vision analysis with Pixtral models
- European AI provider (GDPR-friendly data handling)

WHY:
Mistral AI is a leading European AI company offering high-performance models.
Pixtral provides vision capabilities for screenshot analysis. Organizations
in the EU may prefer Mistral for data residency and GDPR compliance.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional, Union
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


class MistralProvider(BaseLLMProvider):
    """
    Mistral AI LLM Provider

    BUSINESS PURPOSE:
    Provides access to Mistral AI's models for:
    - Screenshot/image analysis (Pixtral)
    - Course content generation
    - European data handling (GDPR-compliant)

    TECHNICAL DETAILS:
    - API Base: https://api.mistral.ai/v1
    - Authentication: Bearer token
    - Vision: Supported with Pixtral models
    - API Format: OpenAI-compatible

    MODELS (Vision-capable):
    - pixtral-large-latest: Large vision model
    - pixtral-12b-2409: 12B parameter vision model

    MODELS (Text-only):
    - mistral-large-latest: Most capable text model
    - mistral-medium-latest: Balanced performance
    - mistral-small-latest: Fast and efficient
    - codestral-latest: Code-focused model
    - open-mixtral-8x22b: Open-source MoE
    - open-mixtral-8x7b: Efficient MoE
    """

    DEFAULT_BASE_URL = "https://api.mistral.ai/v1"
    DEFAULT_MODEL = "mistral-large-latest"
    DEFAULT_VISION_MODEL = "pixtral-large-latest"

    # Pricing per 1M tokens
    PRICING = {
        "pixtral-large-latest": {"input": 2.00, "output": 6.00},
        "pixtral-12b-2409": {"input": 0.15, "output": 0.15},
        "mistral-large-latest": {"input": 2.00, "output": 6.00},
        "mistral-medium-latest": {"input": 2.70, "output": 8.10},
        "mistral-small-latest": {"input": 0.20, "output": 0.60},
        "codestral-latest": {"input": 0.20, "output": 0.60},
        "open-mixtral-8x22b": {"input": 2.00, "output": 6.00},
        "open-mixtral-8x7b": {"input": 0.70, "output": 0.70},
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
        Initialize Mistral Provider

        Args:
            api_key: Mistral AI API key
            base_url: Custom base URL
            model: Default model
            organization_id: Organization ID for tracking
            timeout: Request timeout
            max_retries: Maximum retries
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
        return "mistral"

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def default_vision_model(self) -> str:
        return self.DEFAULT_VISION_MODEL

    def get_capabilities(self) -> LLMProviderCapabilities:
        """Get Mistral provider capabilities"""
        return LLMProviderCapabilities(
            supports_vision=True,  # With Pixtral
            supports_streaming=True,
            supports_function_calling=True,
            supports_json_mode=True,
            max_tokens=128000,
            max_image_size_mb=20.0,
            supported_image_formats=["image/png", "image/jpeg", "image/webp", "image/gif"],
            rate_limit_requests_per_minute=100,
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
        Analyze an image using Mistral's Pixtral vision model

        BUSINESS USE CASE:
        Extract course content from screenshots using European-based
        AI for GDPR-compliant data handling.

        Args:
            image_data: Image bytes or base64 string
            prompt: Analysis prompt
            model: Model to use
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

        # Build analysis prompt
        analysis_prompt = prompt or self.get_screenshot_analysis_prompt()

        # Mistral vision API uses OpenAI-compatible format
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": analysis_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_base64}"
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

        response_data = await self._make_request("/chat/completions", request_body)

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
            confidence_score=float(parsed.get("confidence_score", 0.85)),
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
        Generate text using Mistral models

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

        response_data = await self._make_request("/chat/completions", request_body)

        content = response_data["choices"][0]["message"]["content"]
        usage = response_data.get("usage", {})
        finish_reason = response_data["choices"][0].get("finish_reason", "stop")

        pricing = self.PRICING.get(use_model, {"input": 2.00, "output": 6.00})

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
        """Check if Mistral API is accessible"""
        try:
            response = await self._client.get("/models")
            return response.status_code == 200
        except httpx.RequestError as e:
            logger.warning(f"Mistral health check failed: {e}")
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
            retries: Retries remaining

        Returns:
            Parsed response JSON

        Raises:
            LLMProviderException variants
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
                            f"Mistral rate limit hit, waiting {retry_after}s"
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    raise LLMProviderRateLimitException(
                        message=f"Rate limit exceeded, retry after {retry_after}s",
                        provider_name=self.provider_name,
                        retry_after=retry_after
                    )

                elif response.status_code >= 500:
                    if attempt < retries:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"Mistral server error, retrying in {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    raise LLMProviderResponseException(
                        message=f"Server error (status {response.status_code})",
                        provider_name=self.provider_name
                    )

                else:
                    error_body = response.json() if response.content else {}
                    error_message = error_body.get("message", "Unknown error")
                    if "object" in error_body:
                        error_message = error_body.get("object", {}).get(
                            "message", error_message
                        )
                    raise LLMProviderResponseException(
                        message=error_message,
                        provider_name=self.provider_name
                    )

            except httpx.ConnectError as e:
                if attempt < retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise LLMProviderConnectionException(
                    message=f"Connection failed: {str(e)}",
                    provider_name=self.provider_name,
                    original_exception=e
                )

            except httpx.TimeoutException as e:
                if attempt < retries:
                    await asyncio.sleep(1)
                    continue
                raise LLMProviderConnectionException(
                    message=f"Request timed out: {e}",
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
            logger.info("Closed Mistral provider client")
