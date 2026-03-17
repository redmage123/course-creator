"""
Qwen (Alibaba Cloud) LLM Provider Implementation

BUSINESS PURPOSE:
Implements the LLM provider interface for Alibaba Cloud's Qwen models including
Qwen-VL for vision capabilities and screenshot-to-course generation.

TECHNICAL IMPLEMENTATION:
- Uses httpx for async HTTP requests
- DashScope API format (different from OpenAI)
- Supports vision analysis with Qwen-VL models
- Popular choice for organizations with Alibaba Cloud infrastructure

WHY:
Qwen offers strong multilingual support (especially Chinese/English) and
competitive pricing, making it attractive for global organizations and
those already using Alibaba Cloud services.
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


class QwenProvider(BaseLLMProvider):
    """
    Qwen (Alibaba Cloud DashScope) LLM Provider

    BUSINESS PURPOSE:
    Provides access to Alibaba Cloud's Qwen models for:
    - Screenshot/image analysis (Qwen-VL)
    - Course content generation
    - Multilingual content (especially Chinese/English)

    TECHNICAL DETAILS:
    - API Base: https://dashscope.aliyuncs.com/api/v1
    - Authentication: Authorization header with API key
    - Vision: Supported in Qwen-VL models
    - API Format: DashScope-specific (not OpenAI-compatible)

    MODELS:
    - qwen-vl-max: Best vision-language model
    - qwen-vl-plus: Balanced vision-language model
    - qwen-max: Best text generation
    - qwen-plus: Balanced text generation
    - qwen-turbo: Fast, cost-effective
    """

    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
    DEFAULT_MODEL = "qwen-max"
    DEFAULT_VISION_MODEL = "qwen-vl-max"

    # Pricing per 1M tokens (approximate, varies by region)
    PRICING = {
        "qwen-vl-max": {"input": 2.00, "output": 6.00},
        "qwen-vl-plus": {"input": 0.80, "output": 2.40},
        "qwen-max": {"input": 2.00, "output": 6.00},
        "qwen-plus": {"input": 0.40, "output": 1.20},
        "qwen-turbo": {"input": 0.08, "output": 0.24},
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
        Initialize Qwen Provider

        Args:
            api_key: Alibaba Cloud DashScope API key
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
        return "qwen"

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def default_vision_model(self) -> str:
        return self.DEFAULT_VISION_MODEL

    def get_capabilities(self) -> LLMProviderCapabilities:
        """Get Qwen provider capabilities"""
        return LLMProviderCapabilities(
            supports_vision=True,
            supports_streaming=True,
            supports_function_calling=True,
            supports_json_mode=False,  # Qwen uses different approach
            max_tokens=32000,
            max_image_size_mb=10.0,
            supported_image_formats=["image/png", "image/jpeg", "image/webp"],
            rate_limit_requests_per_minute=100,
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
        """
        Analyze an image using Qwen-VL's vision capabilities

        BUSINESS USE CASE:
        Extract course content from screenshots with strong
        multilingual support (Chinese/English).

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

        # Build Qwen-VL specific request format
        analysis_prompt = prompt or self.get_screenshot_analysis_prompt()

        # Add JSON instruction
        json_prompt = f"""{analysis_prompt}

IMPORTANT: Respond with valid JSON only, no additional text."""

        # Qwen-VL uses a different message format
        request_body = {
            "model": use_model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "image": f"data:{media_type};base64,{image_base64}"
                            },
                            {
                                "text": json_prompt
                            }
                        ]
                    }
                ]
            },
            "parameters": {
                "max_tokens": max_tokens,
                "temperature": temperature,
                "result_format": "message"
            }
        }

        response_data = await self._make_request(
            "/services/aigc/multimodal-generation/generation",
            request_body
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract content from Qwen's response format
        output = response_data.get("output", {})
        choices = output.get("choices", [{}])
        message = choices[0].get("message", {}) if choices else {}
        content_list = message.get("content", [])

        content = ""
        for item in content_list:
            if isinstance(item, dict) and "text" in item:
                content += item["text"]
            elif isinstance(item, str):
                content += item

        usage = response_data.get("usage", {})

        # Parse JSON response
        try:
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            parsed = json.loads(content.strip())
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
        Generate text using Qwen models

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
            final_system = system_prompt
            if json_mode:
                final_system += "\n\nRespond with valid JSON only."
            messages.append({"role": "system", "content": final_system})
        elif json_mode:
            messages.append({"role": "system", "content": "Respond with valid JSON only."})

        messages.append({"role": "user", "content": prompt})

        # Qwen text generation uses different endpoint
        request_body = {
            "model": use_model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "max_tokens": max_tokens,
                "temperature": temperature,
                "result_format": "message"
            }
        }

        response_data = await self._make_request(
            "/services/aigc/text-generation/generation",
            request_body
        )

        # Extract content from Qwen response
        output = response_data.get("output", {})
        choices = output.get("choices", [{}])
        message = choices[0].get("message", {}) if choices else {}
        content = message.get("content", "")
        finish_reason = choices[0].get("finish_reason", "stop") if choices else "stop"

        usage = response_data.get("usage", {})
        pricing = self.PRICING.get(use_model, {"input": 0.40, "output": 1.20})

        return LLMResponse(
            content=content,
            model=use_model,
            provider=self.provider_name,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            finish_reason=finish_reason,
            metadata={
                "input_cost_per_million": pricing["input"],
                "output_cost_per_million": pricing["output"]
            }
        )

    async def health_check(self) -> bool:
        """Check if Qwen API is accessible"""
        try:
            # Use a minimal text generation request
            response = await self._client.post(
                "/services/aigc/text-generation/generation",
                json={
                    "model": "qwen-turbo",
                    "input": {
                        "messages": [{"role": "user", "content": "Hi"}]
                    },
                    "parameters": {
                        "max_tokens": 5,
                        "result_format": "message"
                    }
                }
            )
            return response.status_code == 200
        except httpx.RequestError as e:
            logger.warning(f"Qwen health check failed: {e}")
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
                    data = response.json()
                    # Check for Qwen-specific error in response
                    if data.get("code") and data.get("code") != "Success":
                        raise LLMProviderResponseException(
                            provider=self.provider_name,
                            detail=data.get("message", "Unknown error")
                        )
                    return data

                elif response.status_code == 401:
                    raise LLMProviderAuthenticationException(
                        provider=self.provider_name,
                        detail="Invalid API key"
                    )

                elif response.status_code == 429:
                    if attempt < retries:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"Qwen rate limit hit, waiting {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    raise LLMProviderRateLimitException(provider=self.provider_name)

                elif response.status_code >= 500:
                    if attempt < retries:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"Qwen server error, retrying in {wait_time}s"
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
                    error_message = error_body.get("message", "Unknown error")
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
            logger.info("Closed Qwen provider client")
