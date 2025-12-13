"""
Meta Llama LLM Provider Implementation

BUSINESS PURPOSE:
Implements the LLM provider interface for Meta's Llama models, accessed through
hosted APIs like Together.ai, Replicate, or Fireworks. Supports Llama 3.2 Vision
for screenshot-to-course generation.

TECHNICAL IMPLEMENTATION:
- Uses httpx for async HTTP requests
- OpenAI-compatible API format (Together.ai, Fireworks)
- Supports vision with Llama 3.2 Vision models
- Configurable base URL for different hosting providers

WHY:
Meta's Llama models are open-source and offer competitive performance
with proprietary models. They can be accessed through various hosting
providers, giving organizations flexibility in where their data is processed.
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


class LlamaProvider(BaseLLMProvider):
    """
    Meta Llama LLM Provider (via hosting services)

    BUSINESS PURPOSE:
    Provides access to Meta's Llama models via hosted APIs for:
    - Screenshot/image analysis (Llama 3.2 Vision)
    - Course content generation
    - Open-source model flexibility

    SUPPORTED HOSTING PROVIDERS:
    - Together.ai (default): https://api.together.xyz/v1
    - Fireworks.ai: https://api.fireworks.ai/inference/v1
    - Replicate: https://api.replicate.com/v1

    TECHNICAL DETAILS:
    - API Format: OpenAI-compatible (Together, Fireworks)
    - Authentication: Bearer token
    - Vision: Supported with Llama 3.2 Vision models
    - Streaming: Supported

    MODELS (Vision-capable):
    - meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo
    - meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo

    MODELS (Text-only):
    - meta-llama/Llama-3.3-70B-Instruct-Turbo
    - meta-llama/Llama-3.1-405B-Instruct-Turbo
    - meta-llama/Llama-3.1-70B-Instruct-Turbo
    - meta-llama/Llama-3.1-8B-Instruct-Turbo
    """

    # Default to Together.ai
    DEFAULT_BASE_URL = "https://api.together.xyz/v1"
    DEFAULT_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    DEFAULT_VISION_MODEL = "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo"

    # Alternative hosting providers
    HOSTING_PROVIDERS = {
        "together": "https://api.together.xyz/v1",
        "fireworks": "https://api.fireworks.ai/inference/v1",
        "replicate": "https://api.replicate.com/v1"
    }

    # Pricing per 1M tokens (Together.ai pricing)
    PRICING = {
        "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo": {"input": 1.20, "output": 1.20},
        "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo": {"input": 0.18, "output": 0.18},
        "meta-llama/Llama-3.3-70B-Instruct-Turbo": {"input": 0.88, "output": 0.88},
        "meta-llama/Llama-3.1-405B-Instruct-Turbo": {"input": 3.50, "output": 3.50},
        "meta-llama/Llama-3.1-70B-Instruct-Turbo": {"input": 0.88, "output": 0.88},
        "meta-llama/Llama-3.1-8B-Instruct-Turbo": {"input": 0.18, "output": 0.18},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        timeout: float = 120.0,
        max_retries: int = 3,
        hosting_provider: str = "together"
    ):
        """
        Initialize Llama Provider

        Args:
            api_key: API key for hosting provider
            base_url: Custom base URL (overrides hosting_provider)
            model: Default model
            organization_id: Organization ID for tracking
            timeout: Request timeout
            max_retries: Maximum retries
            hosting_provider: 'together', 'fireworks', or 'replicate'
        """
        # Determine base URL
        if base_url:
            final_base_url = base_url
        else:
            final_base_url = self.HOSTING_PROVIDERS.get(
                hosting_provider,
                self.DEFAULT_BASE_URL
            )

        super().__init__(
            api_key=api_key,
            base_url=final_base_url,
            model=model or self.DEFAULT_MODEL,
            organization_id=organization_id,
            timeout=timeout,
            max_retries=max_retries
        )

        self.hosting_provider = hosting_provider

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
        return "llama"

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def default_vision_model(self) -> str:
        return self.DEFAULT_VISION_MODEL

    def get_capabilities(self) -> LLMProviderCapabilities:
        """Get Llama provider capabilities"""
        return LLMProviderCapabilities(
            supports_vision=True,  # With Llama 3.2 Vision
            supports_streaming=True,
            supports_function_calling=True,
            supports_json_mode=True,
            max_tokens=128000,
            max_image_size_mb=20.0,
            supported_image_formats=["image/png", "image/jpeg", "image/webp"],
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
        Analyze an image using Llama 3.2 Vision

        BUSINESS USE CASE:
        Extract course content from screenshots using open-source
        Llama vision models.

        Args:
            image_data: Image bytes or base64 string
            prompt: Analysis prompt
            model: Vision model to use
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

        # OpenAI-compatible format for vision
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
        Generate text using Llama models

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

        pricing = self.PRICING.get(use_model, {"input": 0.88, "output": 0.88})

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
                "output_cost_per_million": pricing["output"],
                "hosting_provider": self.hosting_provider
            }
        )

    async def health_check(self) -> bool:
        """Check if Llama API is accessible"""
        try:
            response = await self._client.get("/models")
            return response.status_code == 200
        except httpx.RequestError as e:
            logger.warning(f"Llama health check failed: {e}")
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
                        provider=self.provider_name,
                        detail="Invalid API key"
                    )

                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < retries:
                        logger.warning(
                            f"Llama rate limit hit, waiting {retry_after}s"
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    raise LLMProviderRateLimitException(
                        provider=self.provider_name,
                        retry_after=retry_after
                    )

                elif response.status_code >= 500:
                    if attempt < retries:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"Llama server error, retrying in {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    raise LLMProviderResponseException(
                        provider=self.provider_name,
                        status_code=response.status_code,
                        detail="Server error"
                    )

                else:
                    error_body = response.json() if response.content else {}
                    error_message = error_body.get("error", {}).get(
                        "message", "Unknown error"
                    )
                    raise LLMProviderResponseException(
                        provider=self.provider_name,
                        status_code=response.status_code,
                        detail=error_message
                    )

            except httpx.ConnectError as e:
                if attempt < retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise LLMProviderConnectionException(
                    provider=self.provider_name,
                    operation="api_request",
                    original_error=str(e)
                )

            except httpx.TimeoutException as e:
                if attempt < retries:
                    await asyncio.sleep(1)
                    continue
                raise LLMProviderConnectionException(
                    provider=self.provider_name,
                    operation="api_request",
                    original_error=f"Request timed out: {e}"
                )

        raise LLMProviderResponseException(
            provider=self.provider_name,
            detail="Max retries exceeded"
        )

    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("Closed Llama provider client")
