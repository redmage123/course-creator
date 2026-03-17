"""
Deepseek LLM Provider Implementation

BUSINESS PURPOSE:
Implements the LLM provider interface for Deepseek's AI models including
Deepseek-VL for vision capabilities and screenshot-to-course generation.

TECHNICAL IMPLEMENTATION:
- Uses httpx for async HTTP requests
- OpenAI-compatible API format
- Supports vision analysis with Deepseek-VL models
- Cost-effective alternative to OpenAI/Anthropic

WHY:
Deepseek offers competitive pricing and strong performance, making it
an attractive option for organizations looking for cost-effective AI
capabilities with vision support.
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


class DeepseekProvider(BaseLLMProvider):
    """
    Deepseek LLM Provider

    BUSINESS PURPOSE:
    Provides access to Deepseek's AI models for:
    - Screenshot/image analysis (Deepseek-VL)
    - Course content generation
    - Cost-effective AI operations

    TECHNICAL DETAILS:
    - API Base: https://api.deepseek.com/v1
    - Authentication: Bearer token
    - API Format: OpenAI-compatible
    - Vision: Supported in Deepseek-VL models

    MODELS:
    - deepseek-vl: Vision-language model
    - deepseek-chat: General chat model
    - deepseek-coder: Code-focused model
    """

    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
    DEFAULT_MODEL = "deepseek-chat"
    DEFAULT_VISION_MODEL = "deepseek-vl"

    PRICING = {
        "deepseek-vl": {"input": 0.14, "output": 0.28},
        "deepseek-chat": {"input": 0.14, "output": 0.28},
        "deepseek-coder": {"input": 0.14, "output": 0.28},
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
        return "deepseek"

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def default_vision_model(self) -> str:
        return self.DEFAULT_VISION_MODEL

    def get_capabilities(self) -> LLMProviderCapabilities:
        return LLMProviderCapabilities(
            supports_vision=True,
            supports_streaming=True,
            supports_function_calling=True,
            supports_json_mode=True,
            max_tokens=32000,
            max_image_size_mb=10.0,
            supported_image_formats=["image/png", "image/jpeg", "image/webp"],
            rate_limit_requests_per_minute=60,
            context_window=32000
        )

    async def analyze_image(
        self,
        image_data: Union[bytes, str],
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3
    ) -> VisionAnalysisResult:
        start_time = time.time()
        use_model = model or self.default_vision_model

        if isinstance(image_data, bytes):
            self.validate_image(image_data)
            image_base64 = self.encode_image_to_base64(image_data)
            media_type = self.get_image_media_type(image_data)
        else:
            image_base64 = image_data
            media_type = "image/png"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt or self.get_screenshot_analysis_prompt()},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{image_base64}"}
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
        pricing = self.PRICING.get(use_model, {"input": 0.14, "output": 0.28})

        return LLMResponse(
            content=content,
            model=use_model,
            provider=self.provider_name,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            finish_reason=response_data["choices"][0].get("finish_reason", "stop"),
            metadata={
                "input_cost_per_million": pricing["input"],
                "output_cost_per_million": pricing["output"]
            }
        )

    async def health_check(self) -> bool:
        try:
            response = await self._client.get("/models")
            return response.status_code == 200
        except httpx.RequestError:
            return False

    async def _make_request(
        self,
        endpoint: str,
        body: Dict[str, Any],
        retries: int = None
    ) -> Dict[str, Any]:
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
                    if attempt < retries:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise LLMProviderRateLimitException(provider=self.provider_name)
                elif response.status_code >= 500:
                    if attempt < retries:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise LLMProviderResponseException(
                        provider=self.provider_name,
                        status_code=response.status_code
                    )
                else:
                    error_body = response.json() if response.content else {}
                    raise LLMProviderResponseException(
                        provider=self.provider_name,
                        status_code=response.status_code,
                        detail=error_body.get("error", {}).get("message", "Unknown error")
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
                    original_error=str(e)
                )

        raise LLMProviderResponseException(
            provider=self.provider_name,
            detail="Max retries exceeded"
        )

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
