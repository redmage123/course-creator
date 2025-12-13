"""
Google Gemini LLM Provider Implementation

BUSINESS PURPOSE:
Implements the LLM provider interface for Google's Gemini models including
Gemini Pro Vision for screenshot-to-course generation.

TECHNICAL IMPLEMENTATION:
- Uses httpx for async HTTP requests
- Google AI Studio API format (generativelanguage.googleapis.com)
- Supports vision analysis with Gemini Pro Vision and Gemini 2.0
- Alternatively supports Vertex AI endpoint for enterprise

WHY:
Google Gemini offers strong multimodal capabilities with competitive pricing.
Gemini 2.0 Flash and Pro models provide excellent vision analysis for
extracting course content from screenshots. Organizations using Google Cloud
may prefer this for ecosystem integration.
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


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini LLM Provider

    BUSINESS PURPOSE:
    Provides access to Google's Gemini models for:
    - Screenshot/image analysis (Gemini Pro Vision, Gemini 2.0)
    - Course content generation
    - Multimodal AI operations

    TECHNICAL DETAILS:
    - API Base: https://generativelanguage.googleapis.com/v1beta
    - Authentication: API key as query parameter
    - Vision: Supported in all Gemini models
    - Streaming: Supported
    - JSON mode: Supported via response_mime_type

    MODELS:
    - gemini-2.0-flash-exp: Latest experimental with best vision
    - gemini-1.5-pro: Best quality, 2M context
    - gemini-1.5-flash: Fast, 1M context
    - gemini-1.5-flash-8b: Most cost-effective
    - gemini-pro-vision: Legacy vision model
    """

    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    DEFAULT_MODEL = "gemini-1.5-pro"
    DEFAULT_VISION_MODEL = "gemini-2.0-flash-exp"

    # Pricing per 1M tokens
    PRICING = {
        "gemini-2.0-flash-exp": {"input": 0.075, "output": 0.30},
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-1.5-flash-8b": {"input": 0.0375, "output": 0.15},
        "gemini-pro-vision": {"input": 0.25, "output": 0.50},
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
        Initialize Gemini Provider

        Args:
            api_key: Google AI Studio API key
            base_url: Custom base URL (for Vertex AI)
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
            headers={"Content-Type": "application/json"},
            timeout=httpx.Timeout(self.timeout)
        )

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def default_vision_model(self) -> str:
        return self.DEFAULT_VISION_MODEL

    def get_capabilities(self) -> LLMProviderCapabilities:
        """Get Gemini provider capabilities"""
        return LLMProviderCapabilities(
            supports_vision=True,
            supports_streaming=True,
            supports_function_calling=True,
            supports_json_mode=True,
            max_tokens=8192,
            max_image_size_mb=20.0,
            supported_image_formats=["image/png", "image/jpeg", "image/webp", "image/gif"],
            rate_limit_requests_per_minute=60,
            context_window=2000000  # 2M for Gemini 1.5 Pro
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
        Analyze an image using Gemini's vision capabilities

        BUSINESS USE CASE:
        Extract course content from screenshots with Google's
        multimodal AI models.

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

        # Gemini API format
        request_body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": analysis_prompt
                        },
                        {
                            "inline_data": {
                                "mime_type": media_type,
                                "data": image_base64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
                "responseMimeType": "application/json"
            }
        }

        response_data = await self._make_request(
            f"/models/{use_model}:generateContent",
            request_body
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract content from Gemini response
        candidates = response_data.get("candidates", [])
        if not candidates:
            raise LLMProviderResponseException(
                provider=self.provider_name,
                detail="No response candidates returned"
            )

        content_parts = candidates[0].get("content", {}).get("parts", [])
        content = ""
        for part in content_parts:
            if "text" in part:
                content += part["text"]

        usage = response_data.get("usageMetadata", {})

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
            tokens_used=usage.get("totalTokenCount", 0)
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
        Generate text using Gemini models

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

        # Build request body
        contents = []

        # Add system instruction if provided
        system_instruction = None
        if system_prompt:
            system_instruction = {"parts": [{"text": system_prompt}]}

        # Add user content
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        request_body = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature
            }
        }

        if system_instruction:
            request_body["systemInstruction"] = system_instruction

        if json_mode:
            request_body["generationConfig"]["responseMimeType"] = "application/json"

        response_data = await self._make_request(
            f"/models/{use_model}:generateContent",
            request_body
        )

        # Extract content
        candidates = response_data.get("candidates", [])
        if not candidates:
            raise LLMProviderResponseException(
                provider=self.provider_name,
                detail="No response candidates returned"
            )

        content_parts = candidates[0].get("content", {}).get("parts", [])
        content = ""
        for part in content_parts:
            if "text" in part:
                content += part["text"]

        usage = response_data.get("usageMetadata", {})
        finish_reason = candidates[0].get("finishReason", "STOP")

        # Map Gemini finish reason to standard format
        finish_reason_map = {
            "STOP": "stop",
            "MAX_TOKENS": "length",
            "SAFETY": "content_filter",
            "RECITATION": "stop"
        }
        mapped_finish_reason = finish_reason_map.get(finish_reason, finish_reason.lower())

        pricing = self.PRICING.get(use_model, {"input": 0.075, "output": 0.30})

        return LLMResponse(
            content=content,
            model=use_model,
            provider=self.provider_name,
            input_tokens=usage.get("promptTokenCount", 0),
            output_tokens=usage.get("candidatesTokenCount", 0),
            total_tokens=usage.get("totalTokenCount", 0),
            finish_reason=mapped_finish_reason,
            metadata={
                "input_cost_per_million": pricing["input"],
                "output_cost_per_million": pricing["output"]
            }
        )

    async def health_check(self) -> bool:
        """Check if Gemini API is accessible"""
        try:
            response = await self._client.get(
                f"/models?key={self.api_key}"
            )
            return response.status_code == 200
        except httpx.RequestError as e:
            logger.warning(f"Gemini health check failed: {e}")
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

        # Gemini uses API key as query parameter
        url = f"{endpoint}?key={self.api_key}"

        for attempt in range(retries + 1):
            try:
                response = await self._client.post(url, json=body)

                if response.status_code == 200:
                    return response.json()

                elif response.status_code == 401 or response.status_code == 403:
                    raise LLMProviderAuthenticationException(
                        provider=self.provider_name,
                        detail="Invalid API key or insufficient permissions"
                    )

                elif response.status_code == 429:
                    if attempt < retries:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"Gemini rate limit hit, waiting {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    raise LLMProviderRateLimitException(provider=self.provider_name)

                elif response.status_code >= 500:
                    if attempt < retries:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"Gemini server error, retrying in {wait_time}s"
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
                    error = error_body.get("error", {})
                    error_message = error.get("message", "Unknown error")
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
            logger.info("Closed Gemini provider client")
