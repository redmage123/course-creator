"""
Ollama Local LLM Provider Implementation

BUSINESS PURPOSE:
Implements the LLM provider interface for Ollama, a local LLM server that
enables organizations to run AI models on their own infrastructure without
sending data to external APIs.

TECHNICAL IMPLEMENTATION:
- Uses httpx for async HTTP requests
- Ollama-specific API format
- Supports vision with LLaVA, bakllava, llava-llama3 models
- No API key required (local deployment)
- Configurable base URL for remote Ollama servers

WHY:
Ollama enables:
- Data privacy (no data leaves the organization)
- Cost savings (no per-token API charges)
- Offline operation capability
- Compliance with data residency requirements
Organizations with strict security policies often require local LLM deployment.
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


class OllamaProvider(BaseLLMProvider):
    """
    Ollama Local LLM Provider

    BUSINESS PURPOSE:
    Provides access to locally-hosted LLMs via Ollama for:
    - Screenshot/image analysis (LLaVA, bakllava)
    - Course content generation
    - Data-private AI operations

    TECHNICAL DETAILS:
    - Default API Base: http://localhost:11434
    - Authentication: None (local service)
    - Vision: Supported with LLaVA-family models
    - Streaming: Supported

    MODELS (Vision-capable):
    - llava: LLaVA 1.5/1.6 vision model
    - llava-llama3: LLaVA with Llama 3 base
    - bakllava: BakLLaVA vision model
    - llava:34b: Large LLaVA model

    MODELS (Text-only):
    - llama3.2: Latest Llama model
    - mistral: Mistral 7B
    - mixtral: Mixtral 8x7B
    - codellama: Code-focused Llama
    - phi3: Microsoft Phi-3
    """

    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "llama3.2"
    DEFAULT_VISION_MODEL = "llava"

    # No pricing for local models (cost is infrastructure)
    PRICING = {}

    def __init__(
        self,
        api_key: Optional[str] = None,  # Not used, but kept for interface consistency
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        timeout: float = 300.0,  # Longer timeout for local models
        max_retries: int = 3
    ):
        """
        Initialize Ollama Provider

        Args:
            api_key: Not used (Ollama doesn't require authentication)
            base_url: Ollama server URL (default: http://localhost:11434)
            model: Default model
            organization_id: Organization ID for tracking
            timeout: Request timeout (longer for local inference)
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
        return "ollama"

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def default_vision_model(self) -> str:
        return self.DEFAULT_VISION_MODEL

    def get_capabilities(self) -> LLMProviderCapabilities:
        """Get Ollama provider capabilities"""
        return LLMProviderCapabilities(
            supports_vision=True,  # With LLaVA models
            supports_streaming=True,
            supports_function_calling=False,  # Limited support
            supports_json_mode=True,  # Via format parameter
            max_tokens=32000,  # Depends on model
            max_image_size_mb=20.0,
            supported_image_formats=["image/png", "image/jpeg", "image/webp"],
            rate_limit_requests_per_minute=1000,  # Local, no rate limits
            context_window=32000  # Depends on model
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
        Analyze an image using Ollama's vision models (LLaVA)

        BUSINESS USE CASE:
        Extract course content from screenshots locally without
        sending data to external APIs.

        Args:
            image_data: Image bytes or base64 string
            prompt: Analysis prompt
            model: Vision model to use (default: llava)
            max_tokens: Max response tokens
            temperature: Sampling temperature

        Returns:
            VisionAnalysisResult with extracted content
        """
        start_time = time.time()
        use_model = model or self.default_vision_model

        # Prepare image data - Ollama expects base64 without data URI prefix
        if isinstance(image_data, bytes):
            self.validate_image(image_data)
            image_base64 = self.encode_image_to_base64(image_data)
        else:
            # Remove data URI prefix if present
            if image_data.startswith("data:"):
                image_base64 = image_data.split(",")[1]
            else:
                image_base64 = image_data

        # Build analysis prompt
        analysis_prompt = prompt or self.get_screenshot_analysis_prompt()

        # Add JSON instruction
        json_prompt = f"""{analysis_prompt}

IMPORTANT: Respond with valid JSON only, no additional text before or after the JSON object."""

        # Ollama uses /api/generate for vision
        request_body = {
            "model": use_model,
            "prompt": json_prompt,
            "images": [image_base64],
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature
            },
            "format": "json"
        }

        response_data = await self._make_request("/api/generate", request_body)

        processing_time_ms = int((time.time() - start_time) * 1000)

        content = response_data.get("response", "")

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

        # Ollama provides eval_count for tokens
        tokens_used = response_data.get("eval_count", 0)
        prompt_tokens = response_data.get("prompt_eval_count", 0)

        return VisionAnalysisResult(
            extracted_text=parsed.get("extracted_text", content),
            detected_language=parsed.get("detected_language", "en"),
            confidence_score=float(parsed.get("confidence_score", 0.8)),
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
            tokens_used=tokens_used + prompt_tokens
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
        Generate text using Ollama models

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

        # Build request for Ollama chat API
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        request_body = {
            "model": use_model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature
            }
        }

        if json_mode:
            request_body["format"] = "json"

        response_data = await self._make_request("/api/chat", request_body)

        message = response_data.get("message", {})
        content = message.get("content", "")

        # Extract token counts
        prompt_tokens = response_data.get("prompt_eval_count", 0)
        output_tokens = response_data.get("eval_count", 0)

        # Determine finish reason
        done_reason = response_data.get("done_reason", "stop")

        return LLMResponse(
            content=content,
            model=use_model,
            provider=self.provider_name,
            input_tokens=prompt_tokens,
            output_tokens=output_tokens,
            total_tokens=prompt_tokens + output_tokens,
            finish_reason=done_reason,
            metadata={
                "local_model": True,
                "total_duration_ns": response_data.get("total_duration", 0),
                "load_duration_ns": response_data.get("load_duration", 0)
            }
        )

    async def health_check(self) -> bool:
        """Check if Ollama server is accessible"""
        try:
            response = await self._client.get("/api/tags")
            return response.status_code == 200
        except httpx.RequestError as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    async def list_models(self) -> list:
        """
        List available models on the Ollama server

        Returns:
            List of available model names
        """
        try:
            response = await self._client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except httpx.RequestError as e:
            logger.warning(f"Failed to list Ollama models: {e}")
            return []

    async def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama registry

        Args:
            model_name: Name of model to pull

        Returns:
            True if successful
        """
        try:
            response = await self._client.post(
                "/api/pull",
                json={"name": model_name, "stream": False}
            )
            return response.status_code == 200
        except httpx.RequestError as e:
            logger.warning(f"Failed to pull Ollama model {model_name}: {e}")
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

                elif response.status_code == 404:
                    # Model not found
                    raise LLMProviderResponseException(
                        provider=self.provider_name,
                        status_code=404,
                        detail=f"Model not found. Run 'ollama pull {body.get('model')}'"
                    )

                elif response.status_code >= 500:
                    if attempt < retries:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"Ollama server error, retrying in {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    raise LLMProviderResponseException(
                        provider=self.provider_name,
                        status_code=response.status_code,
                        detail="Server error"
                    )

                else:
                    error_body = {}
                    try:
                        error_body = response.json()
                    except Exception:
                        pass
                    error_message = error_body.get("error", "Unknown error")
                    raise LLMProviderResponseException(
                        provider=self.provider_name,
                        status_code=response.status_code,
                        detail=error_message
                    )

            except httpx.ConnectError as e:
                if attempt < retries:
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Ollama connection error, retrying in {wait_time}s. "
                        f"Is Ollama running at {self.base_url}?"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                raise LLMProviderConnectionException(
                    provider=self.provider_name,
                    operation="api_request",
                    original_error=f"Cannot connect to Ollama at {self.base_url}. Is it running?"
                )

            except httpx.TimeoutException as e:
                if attempt < retries:
                    logger.warning(
                        f"Ollama timeout (local models can be slow), retrying: {e}"
                    )
                    await asyncio.sleep(2)
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
            logger.info("Closed Ollama provider client")
