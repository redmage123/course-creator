"""
Anthropic Claude LLM Provider Implementation

BUSINESS PURPOSE:
Implements the LLM provider interface for Anthropic's Claude models with
vision capabilities for screenshot-to-course generation.

TECHNICAL IMPLEMENTATION:
- Uses httpx for async HTTP requests
- Supports vision analysis with Claude 3+ models
- Handles rate limiting, retries, and error translation
- Different API format than OpenAI (messages API)

WHY:
Anthropic Claude offers excellent reasoning and vision capabilities,
making it a strong alternative to OpenAI for course content extraction
and generation. Organizations may prefer Claude for various reasons
including pricing, performance, or data handling policies.
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


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude LLM Provider

    BUSINESS PURPOSE:
    Provides access to Anthropic's Claude models for:
    - Screenshot/image analysis (vision)
    - Course content generation
    - Quiz and exercise creation

    TECHNICAL DETAILS:
    - API Base: https://api.anthropic.com/v1
    - Authentication: x-api-key header
    - Vision: Supported in Claude 3+ models
    - Streaming: Supported
    - Max context: 200K tokens

    MODELS:
    - claude-3-5-sonnet-20241022: Latest, balanced performance
    - claude-3-opus-20240229: Most capable
    - claude-3-haiku-20240307: Fastest, most cost-effective
    """

    DEFAULT_BASE_URL = "https://api.anthropic.com/v1"
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    DEFAULT_VISION_MODEL = "claude-3-5-sonnet-20241022"
    API_VERSION = "2023-06-01"

    # Pricing per 1M tokens
    PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
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
        Initialize Anthropic Provider

        Args:
            api_key: Anthropic API key
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
                "x-api-key": self.api_key,
                "anthropic-version": self.API_VERSION,
                "Content-Type": "application/json"
            },
            timeout=httpx.Timeout(self.timeout)
        )

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def default_vision_model(self) -> str:
        return self.DEFAULT_VISION_MODEL

    def get_capabilities(self) -> LLMProviderCapabilities:
        """Get Anthropic provider capabilities"""
        return LLMProviderCapabilities(
            supports_vision=True,
            supports_streaming=True,
            supports_function_calling=True,
            supports_json_mode=False,  # Anthropic doesn't have explicit JSON mode
            max_tokens=200000,
            max_image_size_mb=20.0,
            supported_image_formats=["image/png", "image/jpeg", "image/webp", "image/gif"],
            rate_limit_requests_per_minute=50,
            context_window=200000
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
        Analyze an image using Claude's vision capabilities

        BUSINESS USE CASE:
        Extract course content from screenshots.

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

        # Build Claude-specific message format
        analysis_prompt = prompt or self.get_screenshot_analysis_prompt()

        # Add JSON instruction since Claude doesn't have JSON mode
        json_prompt = f"""{analysis_prompt}

IMPORTANT: Your response must be valid JSON only, with no additional text before or after the JSON object."""

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": json_prompt
                    }
                ]
            }
        ]

        request_body = {
            "model": use_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        response_data = await self._make_request("/messages", request_body)

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract content from Claude's response format
        content_blocks = response_data.get("content", [])
        content = ""
        for block in content_blocks:
            if block.get("type") == "text":
                content += block.get("text", "")

        usage = response_data.get("usage", {})

        # Parse JSON response
        try:
            # Try to extract JSON from response
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
            tokens_used=usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
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
        Generate text using Claude models

        Args:
            prompt: User prompt
            system_prompt: System context
            model: Model to use
            max_tokens: Max response tokens
            temperature: Sampling temperature
            json_mode: Request JSON output (emulated via prompt)

        Returns:
            LLMResponse with generated text
        """
        use_model = model or self.model

        # Build request
        request_body = {
            "model": use_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if system_prompt:
            request_body["system"] = system_prompt

        if json_mode:
            # Append JSON instruction since Claude doesn't have explicit JSON mode
            if system_prompt:
                request_body["system"] += "\n\nRespond with valid JSON only."
            else:
                request_body["system"] = "Respond with valid JSON only."

        response_data = await self._make_request("/messages", request_body)

        # Extract content
        content_blocks = response_data.get("content", [])
        content = ""
        for block in content_blocks:
            if block.get("type") == "text":
                content += block.get("text", "")

        usage = response_data.get("usage", {})
        stop_reason = response_data.get("stop_reason", "end_turn")

        # Map Claude's stop_reason to standard format
        finish_reason_map = {
            "end_turn": "stop",
            "max_tokens": "length",
            "stop_sequence": "stop"
        }
        finish_reason = finish_reason_map.get(stop_reason, stop_reason)

        pricing = self.PRICING.get(use_model, {"input": 3.00, "output": 15.00})

        return LLMResponse(
            content=content,
            model=use_model,
            provider=self.provider_name,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            finish_reason=finish_reason,
            metadata={
                "input_cost_per_million": pricing["input"],
                "output_cost_per_million": pricing["output"]
            }
        )

    async def health_check(self) -> bool:
        """Check if Anthropic API is accessible"""
        try:
            # Anthropic doesn't have a dedicated health endpoint
            # Use a minimal messages request
            response = await self._client.post(
                "/messages",
                json={
                    "model": "claude-3-haiku-20240307",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 5
                }
            )
            return response.status_code == 200
        except httpx.RequestError as e:
            logger.warning(f"Anthropic health check failed: {e}")
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
                    retry_after = int(response.headers.get("retry-after", 60))
                    if attempt < retries:
                        logger.warning(
                            f"Anthropic rate limit, waiting {retry_after}s"
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
                            f"Anthropic server error, retrying in {wait_time}s"
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
            logger.info("Closed Anthropic provider client")
