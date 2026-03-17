"""
Screenshot Analysis Service

BUSINESS PURPOSE:
Orchestrates the analysis of uploaded screenshots using vision-capable
LLM providers. Extracts course content, structure, and metadata from
images to enable screenshot-to-course generation.

TECHNICAL IMPLEMENTATION:
- Uses provider registry to get appropriate LLM provider
- Supports fallback to alternative providers on failure
- Handles image validation and preprocessing
- Caches analysis results
- Logs usage for billing

WHY:
This service acts as the bridge between the domain layer (entities)
and infrastructure layer (LLM providers), implementing the core
business logic for screenshot analysis without coupling to any
specific provider.
"""

import asyncio
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from course_generator.domain.entities.screenshot_analysis import (
    AnalysisResult,
    CourseModule,
    CourseStructure,
    DetectedElement,
    DifficultyLevel,
    ImageMetadata,
    ScreenshotBatch,
    ScreenshotUpload,
    UploadStatus
)
from course_generator.infrastructure.llm_providers import (
    BaseLLMProvider,
    VisionAnalysisResult,
    get_provider_for_organization,
    get_registry
)
from shared.exceptions import (
    LLMProviderException,
    ScreenshotAnalysisException,
    UnsupportedImageFormatException,
    VisionAnalysisException
)


logger = logging.getLogger(__name__)


class ScreenshotAnalysisService:
    """
    Service for analyzing screenshots using vision AI

    BUSINESS PURPOSE:
    Provides high-level operations for screenshot analysis:
    - Single image analysis
    - Batch processing
    - Course structure extraction
    - Provider fallback handling

    USAGE:
    ```python
    service = ScreenshotAnalysisService()

    # Analyze single screenshot
    result = await service.analyze_screenshot(
        image_data=image_bytes,
        organization_id=org_id,
        user_id=user_id
    )

    # Analyze batch of screenshots
    results = await service.analyze_batch(
        images=[img1, img2, img3],
        organization_id=org_id
    )
    ```
    """

    # Image validation constants
    MAX_IMAGE_SIZE_MB = 20.0
    SUPPORTED_FORMATS = {"image/png", "image/jpeg", "image/webp", "image/gif"}
    MIN_IMAGE_DIMENSION = 100
    MAX_IMAGE_DIMENSION = 8192

    def __init__(
        self,
        enable_fallback: bool = True,
        max_fallback_attempts: int = 2,
        cache_results: bool = True
    ):
        """
        Initialize Screenshot Analysis Service

        Args:
            enable_fallback: Whether to try fallback providers on failure
            max_fallback_attempts: Maximum fallback attempts
            cache_results: Whether to cache analysis results
        """
        self.enable_fallback = enable_fallback
        self.max_fallback_attempts = max_fallback_attempts
        self.cache_results = cache_results
        self._result_cache: Dict[str, AnalysisResult] = {}
        self._registry = get_registry()

    async def analyze_screenshot(
        self,
        image_data: bytes,
        organization_id: UUID,
        user_id: UUID,
        filename: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        provider_override: Optional[str] = None
    ) -> ScreenshotUpload:
        """
        Analyze a screenshot and extract course content

        BUSINESS FLOW:
        1. Validate image format and size
        2. Create upload entity
        3. Get appropriate LLM provider
        4. Analyze image with vision model
        5. Parse and structure results
        6. Return completed upload with analysis

        Args:
            image_data: Raw image bytes
            organization_id: Organization ID
            user_id: User ID performing upload
            filename: Original filename
            custom_prompt: Custom analysis prompt
            provider_override: Specific provider to use

        Returns:
            ScreenshotUpload with analysis result

        Raises:
            UnsupportedImageFormatException: If image format not supported
            VisionAnalysisException: If analysis fails
        """
        logger.info(
            f"Starting screenshot analysis for org {organization_id}"
        )

        # Create upload entity
        upload = ScreenshotUpload(
            id=uuid4(),
            organization_id=organization_id,
            user_id=user_id,
            original_filename=filename or "screenshot.png",
            status=UploadStatus.VALIDATING
        )

        try:
            # Validate and extract metadata
            metadata = self._extract_image_metadata(image_data)
            upload.image_metadata = metadata

            if not upload.validate_image():
                raise UnsupportedImageFormatException(
                    f"Image validation failed: {upload.error_message}"
                )

            # Check cache
            cache_key = metadata.file_hash
            if self.cache_results and cache_key in self._result_cache:
                logger.info(f"Cache hit for image {cache_key[:16]}...")
                upload.analysis_result = self._result_cache[cache_key]
                upload.status = UploadStatus.ANALYZED
                return upload

            # Mark as analyzing
            upload.mark_analyzing()

            # Get provider and analyze
            analysis_result = await self._analyze_with_fallback(
                image_data=image_data,
                organization_id=organization_id,
                custom_prompt=custom_prompt,
                provider_override=provider_override
            )

            # Update upload with result
            upload.mark_analyzed(analysis_result)

            # Cache result
            if self.cache_results:
                self._result_cache[cache_key] = analysis_result

            logger.info(
                f"Screenshot analysis complete for org {organization_id}, "
                f"confidence: {analysis_result.confidence_score:.2f}"
            )

            return upload

        except UnsupportedImageFormatException:
            raise
        except LLMProviderException as e:
            upload.mark_failed(str(e))
            raise VisionAnalysisException(
                f"Analysis failed: {e}"
            ) from e
        except Exception as e:
            upload.mark_failed(str(e))
            logger.exception(f"Unexpected error during screenshot analysis")
            raise ScreenshotAnalysisException(
                f"Unexpected error: {e}"
            ) from e

    async def analyze_batch(
        self,
        images: List[Tuple[bytes, str]],  # (data, filename)
        organization_id: UUID,
        user_id: UUID,
        combine_results: bool = True,
        custom_prompt: Optional[str] = None
    ) -> ScreenshotBatch:
        """
        Analyze multiple screenshots

        BUSINESS USE CASE:
        Users may upload multiple screenshots from a course or presentation
        to generate a comprehensive course structure.

        Args:
            images: List of (image_data, filename) tuples
            organization_id: Organization ID
            user_id: User ID
            combine_results: Whether to combine into single course structure
            custom_prompt: Custom analysis prompt

        Returns:
            ScreenshotBatch with all results
        """
        batch = ScreenshotBatch(
            organization_id=organization_id,
            user_id=user_id
        )

        # Analyze each image
        tasks = [
            self.analyze_screenshot(
                image_data=data,
                organization_id=organization_id,
                user_id=user_id,
                filename=filename,
                custom_prompt=custom_prompt
            )
            for data, filename in images
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch item failed: {result}")
                failed = ScreenshotUpload(
                    organization_id=organization_id,
                    user_id=user_id,
                    status=UploadStatus.FAILED,
                    error_message=str(result)
                )
                batch.add_screenshot(failed)
            else:
                batch.add_screenshot(result)

        # Combine results if requested
        if combine_results and batch.completed_count > 0:
            batch.combined_analysis = self._combine_analyses(
                [s.analysis_result for s in batch.screenshots if s.analysis_result]
            )

        batch.status = (
            UploadStatus.COMPLETED if batch.failed_count == 0
            else UploadStatus.FAILED if batch.completed_count == 0
            else UploadStatus.ANALYZED
        )

        return batch

    async def _analyze_with_fallback(
        self,
        image_data: bytes,
        organization_id: UUID,
        custom_prompt: Optional[str] = None,
        provider_override: Optional[str] = None
    ) -> AnalysisResult:
        """
        Analyze image with fallback support

        BUSINESS LOGIC:
        1. Try primary provider
        2. On failure, try fallback providers in priority order
        3. Return first successful result

        Args:
            image_data: Raw image bytes
            organization_id: Organization ID
            custom_prompt: Custom prompt
            provider_override: Specific provider

        Returns:
            AnalysisResult from successful provider

        Raises:
            VisionAnalysisException: If all providers fail
        """
        providers_tried = []
        last_error = None

        # Get primary provider
        try:
            provider = await get_provider_for_organization(
                organization_id=organization_id,
                require_vision=True,
                provider_override=provider_override
            )
            providers_tried.append(provider.provider_name)

            result = await self._analyze_with_provider(
                provider=provider,
                image_data=image_data,
                custom_prompt=custom_prompt
            )
            return result

        except LLMProviderException as e:
            last_error = e
            logger.warning(
                f"Primary provider failed: {e}, trying fallback"
            )

        # Try fallback providers
        if self.enable_fallback:
            fallback_providers = await self._registry.get_fallback_providers(
                organization_id=organization_id,
                exclude=providers_tried
            )

            for i, provider in enumerate(fallback_providers):
                if i >= self.max_fallback_attempts:
                    break

                try:
                    providers_tried.append(provider.provider_name)
                    result = await self._analyze_with_provider(
                        provider=provider,
                        image_data=image_data,
                        custom_prompt=custom_prompt
                    )
                    logger.info(
                        f"Fallback provider {provider.provider_name} succeeded"
                    )
                    return result

                except LLMProviderException as e:
                    last_error = e
                    logger.warning(
                        f"Fallback provider {provider.provider_name} failed: {e}"
                    )
                finally:
                    await provider.close()

        raise VisionAnalysisException(
            f"All providers failed. Tried: {', '.join(providers_tried)}. "
            f"Last error: {last_error}"
        )

    async def _analyze_with_provider(
        self,
        provider: BaseLLMProvider,
        image_data: bytes,
        custom_prompt: Optional[str] = None
    ) -> AnalysisResult:
        """
        Analyze image with specific provider

        Args:
            provider: LLM provider instance
            image_data: Raw image bytes
            custom_prompt: Custom prompt

        Returns:
            AnalysisResult from provider
        """
        prompt = custom_prompt or self._get_analysis_prompt()

        # Call provider's vision analysis
        vision_result: VisionAnalysisResult = await provider.analyze_image(
            image_data=image_data,
            prompt=prompt
        )

        # Convert to domain entity
        course_structure = None
        if vision_result.course_structure:
            course_structure = CourseStructure.from_dict(
                vision_result.course_structure
            )
        elif vision_result.suggested_title:
            # Build structure from individual fields
            course_structure = CourseStructure(
                title=vision_result.suggested_title,
                description=vision_result.suggested_description,
                topics=vision_result.suggested_topics,
                difficulty=self._parse_difficulty(vision_result.suggested_difficulty),
                estimated_duration_hours=vision_result.suggested_duration_hours,
                language=vision_result.detected_language
            )

        # Convert detected elements
        detected_elements = [
            DetectedElement(
                element_type=elem.get("type", "text"),
                content=elem.get("content", ""),
                confidence=float(elem.get("confidence", 0.8)),
                metadata=elem
            )
            for elem in vision_result.detected_elements
        ]

        return AnalysisResult(
            id=uuid4(),
            extracted_text=vision_result.extracted_text,
            detected_language=vision_result.detected_language,
            confidence_score=vision_result.confidence_score,
            detected_elements=detected_elements,
            course_structure=course_structure,
            raw_response=vision_result.raw_response,
            provider_used=vision_result.provider_used,
            model_used=vision_result.model_used,
            tokens_used=vision_result.tokens_used,
            processing_time_ms=vision_result.processing_time_ms,
            created_at=datetime.utcnow()
        )

    def _extract_image_metadata(self, image_data: bytes) -> ImageMetadata:
        """
        Extract metadata from image bytes

        Args:
            image_data: Raw image bytes

        Returns:
            ImageMetadata with extracted info
        """
        # Detect format from magic bytes
        format_name = self._detect_format(image_data)

        # Get dimensions (simplified - would use PIL in production)
        width, height = self._get_dimensions(image_data, format_name)

        # Calculate hash for deduplication
        file_hash = hashlib.sha256(image_data).hexdigest()

        return ImageMetadata(
            width=width,
            height=height,
            format=format_name,
            size_bytes=len(image_data),
            file_hash=file_hash
        )

    def _detect_format(self, image_data: bytes) -> str:
        """Detect image format from magic bytes"""
        if image_data[:8] == b'\x89PNG\r\n\x1a\n':
            return "png"
        elif image_data[:2] == b'\xff\xd8':
            return "jpeg"
        elif image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
            return "webp"
        elif image_data[:6] in (b'GIF87a', b'GIF89a'):
            return "gif"
        else:
            return "unknown"

    def _get_dimensions(self, image_data: bytes, format_name: str) -> Tuple[int, int]:
        """
        Get image dimensions (simplified implementation)

        In production, would use PIL/Pillow for accurate extraction.
        """
        try:
            if format_name == "png":
                # PNG: width at bytes 16-20, height at 20-24
                if len(image_data) >= 24:
                    width = int.from_bytes(image_data[16:20], 'big')
                    height = int.from_bytes(image_data[20:24], 'big')
                    return width, height
            elif format_name == "jpeg":
                # JPEG: More complex, simplified here
                return 1920, 1080  # Default assumption
            elif format_name == "gif":
                # GIF: width at 6-8, height at 8-10 (little endian)
                if len(image_data) >= 10:
                    width = int.from_bytes(image_data[6:8], 'little')
                    height = int.from_bytes(image_data[8:10], 'little')
                    return width, height
        except Exception:
            pass

        return 1920, 1080  # Default fallback

    def _parse_difficulty(self, difficulty_str: str) -> DifficultyLevel:
        """Parse difficulty string to enum"""
        try:
            return DifficultyLevel(difficulty_str.lower())
        except ValueError:
            return DifficultyLevel.INTERMEDIATE

    def _combine_analyses(
        self,
        analyses: List[AnalysisResult]
    ) -> AnalysisResult:
        """
        Combine multiple analysis results into one

        BUSINESS LOGIC:
        Merges extracted content from multiple screenshots
        into a cohesive course structure.

        Args:
            analyses: List of analysis results

        Returns:
            Combined AnalysisResult
        """
        if not analyses:
            return None

        if len(analyses) == 1:
            return analyses[0]

        # Combine extracted text
        combined_text = "\n\n---\n\n".join(
            a.extracted_text for a in analyses if a.extracted_text
        )

        # Combine course structures
        all_topics = []
        all_objectives = []
        all_modules = []
        total_duration = 0

        for analysis in analyses:
            if analysis.course_structure:
                all_topics.extend(analysis.course_structure.topics)
                all_objectives.extend(analysis.course_structure.learning_objectives)
                all_modules.extend(analysis.course_structure.modules)
                total_duration += analysis.course_structure.estimated_duration_hours

        # Deduplicate
        unique_topics = list(dict.fromkeys(all_topics))
        unique_objectives = list(dict.fromkeys(all_objectives))

        # Create combined structure
        combined_structure = CourseStructure(
            title=analyses[0].course_structure.title if analyses[0].course_structure else "Combined Course",
            description=analyses[0].course_structure.description if analyses[0].course_structure else "",
            modules=all_modules,
            topics=unique_topics,
            learning_objectives=unique_objectives,
            estimated_duration_hours=total_duration,
            difficulty=analyses[0].course_structure.difficulty if analyses[0].course_structure else DifficultyLevel.INTERMEDIATE
        )

        # Average confidence
        avg_confidence = sum(a.confidence_score for a in analyses) / len(analyses)

        return AnalysisResult(
            id=uuid4(),
            extracted_text=combined_text,
            confidence_score=avg_confidence,
            course_structure=combined_structure,
            provider_used="multiple",
            model_used="multiple",
            tokens_used=sum(a.tokens_used for a in analyses),
            processing_time_ms=sum(a.processing_time_ms for a in analyses),
            created_at=datetime.utcnow(),
            metadata={"source_count": len(analyses)}
        )

    def _get_analysis_prompt(self) -> str:
        """
        Get the default screenshot analysis prompt

        Returns:
            Analysis prompt string
        """
        return """Analyze this screenshot of educational/course content and extract detailed information.

Look for:
1. Course/lesson titles and headings
2. Topic outlines and table of contents
3. Learning objectives or goals
4. Key concepts and terminology
5. Code examples or technical content
6. Diagrams, charts, or visual aids
7. Prerequisites or requirements
8. Estimated duration or time indicators

Provide your response in this JSON format:
{
    "title": "Main course/lesson title",
    "description": "Brief description of the content",
    "course_structure": {
        "title": "Course title",
        "description": "Course description",
        "modules": [
            {
                "title": "Module title",
                "description": "Module description",
                "order": 1,
                "lessons": ["Lesson 1", "Lesson 2"],
                "estimated_duration_minutes": 30,
                "learning_objectives": ["Objective 1"]
            }
        ],
        "topics": ["Topic 1", "Topic 2"],
        "learning_objectives": ["Overall objective 1"],
        "prerequisites": ["Prerequisite 1"],
        "key_concepts": ["Concept 1", "Concept 2"],
        "difficulty": "beginner|intermediate|advanced",
        "estimated_duration_hours": 10
    },
    "detected_elements": [
        {"type": "heading", "content": "text", "confidence": 0.95},
        {"type": "code", "content": "code snippet", "confidence": 0.90}
    ],
    "extracted_text": "Full text content extracted from image",
    "detected_language": "en",
    "confidence_score": 0.85
}

Be thorough and extract all visible educational content. If certain fields are not visible, omit them or provide reasonable defaults."""

    def clear_cache(self):
        """Clear the result cache"""
        self._result_cache.clear()
        logger.info("Screenshot analysis cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cached_results": len(self._result_cache),
            "cache_enabled": self.cache_results
        }


# Factory function for dependency injection
_singleton_instance: Optional[ScreenshotAnalysisService] = None


def create_screenshot_analysis_service(
    enable_fallback: bool = True,
    max_fallback_attempts: int = 2,
    cache_results: bool = True
) -> ScreenshotAnalysisService:
    """
    Factory function to create or return singleton ScreenshotAnalysisService

    This provides a clean dependency injection pattern for the API layer.
    Returns a singleton instance to avoid recreating the service on each request.

    Args:
        enable_fallback: Whether to try fallback providers on failure
        max_fallback_attempts: Maximum number of fallback providers to try
        cache_results: Whether to cache analysis results

    Returns:
        ScreenshotAnalysisService instance
    """
    global _singleton_instance
    if _singleton_instance is None:
        _singleton_instance = ScreenshotAnalysisService(
            enable_fallback=enable_fallback,
            max_fallback_attempts=max_fallback_attempts,
            cache_results=cache_results
        )
    return _singleton_instance
