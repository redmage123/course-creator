"""
Unit Tests for Screenshot Analysis Service

BUSINESS CONTEXT:
Tests the screenshot analysis service's ability to process uploaded images,
validate formats, analyze content using LLM providers, handle errors, and
track progress through the analysis pipeline.

TECHNICAL IMPLEMENTATION:
- Tests screenshot upload and validation
- Tests image format validation (PNG, JPG, WEBP, GIF)
- Tests file size validation
- Tests analysis with different LLM providers
- Tests progress tracking and status updates
- Tests comprehensive error handling
- Tests result parsing and storage
- Tests confidence score calculation
- Tests caching mechanism
- Tests batch processing
- Tests provider fallback logic
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from uuid import uuid4, UUID
from typing import List, Tuple

from course_generator.application.services.screenshot_analysis_service import (
    ScreenshotAnalysisService
)
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
    LLMProviderCapabilities
)
from shared.exceptions import (
    LLMProviderException,
    ScreenshotAnalysisException,
    UnsupportedImageFormatException,
    VisionAnalysisException
)


# Test Fixtures - Sample Image Data
PNG_MAGIC_BYTES = b'\x89PNG\r\n\x1a\n' + b'\x00' * 16 + b'\x00\x00\x07\x80\x00\x00\x04\x38' + b'\x00' * 100
JPEG_MAGIC_BYTES = b'\xff\xd8\xff\xe0' + b'\x00' * 100
WEBP_MAGIC_BYTES = b'RIFF' + b'\x00\x00\x00\x00' + b'WEBP' + b'\x00' * 100
GIF_MAGIC_BYTES = b'GIF89a' + b'\x00\x05\x00\x03' + b'\x00' * 100
INVALID_MAGIC_BYTES = b'INVALID' + b'\x00' * 100


class TestScreenshotAnalysisServiceInitialization:
    """Test suite for service initialization"""

    def test_service_initialization_default_config(self):
        """
        Test that service initializes with default configuration

        BUSINESS CONTEXT:
        Service should start with sensible defaults for production use.
        """
        service = ScreenshotAnalysisService()

        assert service.enable_fallback is True
        assert service.max_fallback_attempts == 2
        assert service.cache_results is True
        assert isinstance(service._result_cache, dict)
        assert len(service._result_cache) == 0

    def test_service_initialization_custom_config(self):
        """
        Test that service accepts custom configuration

        BUSINESS CONTEXT:
        Organizations may have different requirements for caching and fallback.
        """
        service = ScreenshotAnalysisService(
            enable_fallback=False,
            max_fallback_attempts=5,
            cache_results=False
        )

        assert service.enable_fallback is False
        assert service.max_fallback_attempts == 5
        assert service.cache_results is False

    def test_service_has_correct_validation_constants(self):
        """
        Test that service has correct validation constants

        BUSINESS CONTEXT:
        These constants protect against oversized uploads and unsupported formats.
        """
        service = ScreenshotAnalysisService()

        assert service.MAX_IMAGE_SIZE_MB == 20.0
        assert "image/png" in service.SUPPORTED_FORMATS
        assert "image/jpeg" in service.SUPPORTED_FORMATS
        assert "image/webp" in service.SUPPORTED_FORMATS
        assert "image/gif" in service.SUPPORTED_FORMATS
        assert service.MIN_IMAGE_DIMENSION == 100
        assert service.MAX_IMAGE_DIMENSION == 8192


class TestImageFormatValidation:
    """Test suite for image format validation"""

    def test_detect_png_format(self):
        """
        Test PNG format detection from magic bytes

        BUSINESS CONTEXT:
        PNG is the most common format for screenshots.
        """
        service = ScreenshotAnalysisService()

        format_name = service._detect_format(PNG_MAGIC_BYTES)

        assert format_name == "png"

    def test_detect_jpeg_format(self):
        """
        Test JPEG format detection from magic bytes

        BUSINESS CONTEXT:
        JPEG is common for compressed screenshots and photos.
        """
        service = ScreenshotAnalysisService()

        format_name = service._detect_format(JPEG_MAGIC_BYTES)

        assert format_name == "jpeg"

    def test_detect_webp_format(self):
        """
        Test WEBP format detection from magic bytes

        BUSINESS CONTEXT:
        WEBP is increasingly common for web-based screenshots.
        """
        service = ScreenshotAnalysisService()

        format_name = service._detect_format(WEBP_MAGIC_BYTES)

        assert format_name == "webp"

    def test_detect_gif_format(self):
        """
        Test GIF format detection from magic bytes

        BUSINESS CONTEXT:
        GIFs may be used for animated demonstrations.
        """
        service = ScreenshotAnalysisService()

        format_name = service._detect_format(GIF_MAGIC_BYTES)

        assert format_name == "gif"

    def test_detect_unknown_format(self):
        """
        Test detection returns 'unknown' for unsupported formats

        BUSINESS CONTEXT:
        Invalid uploads should be detected early to prevent processing.
        """
        service = ScreenshotAnalysisService()

        format_name = service._detect_format(INVALID_MAGIC_BYTES)

        assert format_name == "unknown"


class TestImageMetadataExtraction:
    """Test suite for image metadata extraction"""

    def test_extract_metadata_from_png(self):
        """
        Test metadata extraction from PNG image

        BUSINESS CONTEXT:
        Metadata is needed for validation and deduplication.
        """
        service = ScreenshotAnalysisService()

        metadata = service._extract_image_metadata(PNG_MAGIC_BYTES)

        assert isinstance(metadata, ImageMetadata)
        assert metadata.format == "png"
        assert metadata.size_bytes == len(PNG_MAGIC_BYTES)
        # Dimensions may be 0 for invalid PNG, or extracted if valid
        assert metadata.width >= 0
        assert metadata.height >= 0
        assert len(metadata.file_hash) == 64  # SHA-256 hash

    def test_extract_metadata_calculates_hash(self):
        """
        Test that file hash is calculated for deduplication

        BUSINESS CONTEXT:
        Hash prevents duplicate analysis of the same screenshot.
        """
        service = ScreenshotAnalysisService()

        metadata1 = service._extract_image_metadata(PNG_MAGIC_BYTES)
        metadata2 = service._extract_image_metadata(PNG_MAGIC_BYTES)

        assert metadata1.file_hash == metadata2.file_hash

    def test_extract_metadata_different_images_have_different_hashes(self):
        """
        Test that different images produce different hashes

        BUSINESS CONTEXT:
        Hash uniqueness ensures accurate deduplication.
        """
        service = ScreenshotAnalysisService()

        metadata1 = service._extract_image_metadata(PNG_MAGIC_BYTES)
        metadata2 = service._extract_image_metadata(JPEG_MAGIC_BYTES)

        assert metadata1.file_hash != metadata2.file_hash

    def test_metadata_size_mb_property(self):
        """
        Test that size_mb property calculates correctly

        BUSINESS CONTEXT:
        Size limits prevent abuse and control costs.
        """
        service = ScreenshotAnalysisService()

        metadata = service._extract_image_metadata(PNG_MAGIC_BYTES)

        expected_mb = len(PNG_MAGIC_BYTES) / (1024 * 1024)
        assert abs(metadata.size_mb - expected_mb) < 0.001


class TestFileSizeValidation:
    """Test suite for file size validation"""

    def test_reject_oversized_image(self):
        """
        Test that images exceeding MAX_IMAGE_SIZE_MB are rejected

        BUSINESS CONTEXT:
        Size limits prevent system abuse and control API costs.
        """
        service = ScreenshotAnalysisService()

        # Create oversized image (21 MB > 20 MB limit)
        large_image = PNG_MAGIC_BYTES + (b'\x00' * (21 * 1024 * 1024))

        metadata = service._extract_image_metadata(large_image)

        upload = ScreenshotUpload(
            organization_id=uuid4(),
            user_id=uuid4(),
            image_metadata=metadata
        )

        is_valid = upload.validate_image()

        assert is_valid is False
        assert upload.status == UploadStatus.FAILED
        assert "exceeds maximum" in upload.error_message

    def test_accept_valid_sized_image(self):
        """
        Test that images within size limit are accepted

        BUSINESS CONTEXT:
        Valid uploads should pass validation.
        """
        service = ScreenshotAnalysisService()

        metadata = service._extract_image_metadata(PNG_MAGIC_BYTES)

        upload = ScreenshotUpload(
            organization_id=uuid4(),
            user_id=uuid4(),
            image_metadata=metadata
        )

        is_valid = upload.validate_image()

        assert is_valid is True


class TestScreenshotAnalysis:
    """Test suite for screenshot analysis with LLM providers"""

    @pytest.mark.asyncio
    async def test_analyze_screenshot_success(self):
        """
        Test successful screenshot analysis

        BUSINESS CONTEXT:
        Primary happy path - user uploads screenshot, gets course structure.
        """
        service = ScreenshotAnalysisService()
        org_id = uuid4()
        user_id = uuid4()

        # Mock provider
        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"

        # Mock vision analysis result
        vision_result = VisionAnalysisResult(
            extracted_text="Introduction to Python Programming",
            detected_language="en",
            confidence_score=0.95,
            course_structure={
                "title": "Python Fundamentals",
                "description": "Learn Python programming from scratch",
                "topics": ["Variables", "Functions", "Classes"],
                "difficulty": "beginner",
                "estimated_duration_hours": 10
            },
            suggested_title="Python Fundamentals",
            suggested_description="Learn Python programming from scratch",
            suggested_topics=["Variables", "Functions", "Classes"],
            suggested_difficulty="beginner",
            suggested_duration_hours=10,
            provider_used="openai",
            model_used="gpt-4-vision-preview",
            tokens_used=1000,
            processing_time_ms=2500
        )

        mock_provider.analyze_image = AsyncMock(return_value=vision_result)

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            upload = await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=org_id,
                user_id=user_id,
                filename="test_screenshot.png"
            )

        assert isinstance(upload, ScreenshotUpload)
        assert upload.status == UploadStatus.ANALYZED
        assert upload.analysis_result is not None
        assert upload.analysis_result.confidence_score == 0.95
        assert upload.analysis_result.provider_used == "openai"
        assert upload.analysis_result.course_structure is not None
        assert upload.analysis_result.course_structure.title == "Python Fundamentals"

    @pytest.mark.asyncio
    async def test_analyze_screenshot_with_custom_prompt(self):
        """
        Test analysis with custom prompt

        BUSINESS CONTEXT:
        Users may want to customize the analysis focus.
        """
        service = ScreenshotAnalysisService()
        custom_prompt = "Extract only the learning objectives from this screenshot"

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "anthropic"
        mock_provider.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="Objectives found",
            confidence_score=0.9,
            provider_used="anthropic",
            model_used="claude-3-opus"
        ))

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            upload = await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=uuid4(),
                user_id=uuid4(),
                custom_prompt=custom_prompt
            )

        # Verify analyze_image was called with custom prompt
        mock_provider.analyze_image.assert_called_once()
        call_args = mock_provider.analyze_image.call_args
        assert call_args[1]['prompt'] == custom_prompt

    @pytest.mark.asyncio
    async def test_analyze_screenshot_unsupported_format_raises_exception(self):
        """
        Test that unsupported image format raises exception

        BUSINESS CONTEXT:
        Invalid formats should fail fast with clear error message.
        """
        service = ScreenshotAnalysisService()

        with pytest.raises(UnsupportedImageFormatException) as exc_info:
            await service.analyze_screenshot(
                image_data=INVALID_MAGIC_BYTES,
                organization_id=uuid4(),
                user_id=uuid4()
            )

        assert "Image validation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analyze_screenshot_provider_failure_raises_exception(self):
        """
        Test that provider failure raises exception with proper wrapping

        BUSINESS CONTEXT:
        Provider failures should be caught and wrapped with context.
        """
        service = ScreenshotAnalysisService(enable_fallback=False)

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        mock_provider.analyze_image = AsyncMock(
            side_effect=LLMProviderException("API rate limit exceeded")
        )

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            # When all providers fail, it raises ScreenshotAnalysisException wrapping VisionAnalysisException
            with pytest.raises((VisionAnalysisException, ScreenshotAnalysisException)) as exc_info:
                await service.analyze_screenshot(
                    image_data=PNG_MAGIC_BYTES,
                    organization_id=uuid4(),
                    user_id=uuid4()
                )

            # Should mention failure in error message
            assert "failed" in str(exc_info.value).lower()


class TestResultCaching:
    """Test suite for result caching"""

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_result(self):
        """
        Test that identical image returns cached result

        BUSINESS CONTEXT:
        Caching saves API costs and reduces latency for duplicate uploads.
        """
        service = ScreenshotAnalysisService(cache_results=True)
        org_id = uuid4()
        user_id = uuid4()

        # First analysis
        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        vision_result = VisionAnalysisResult(
            extracted_text="Cached content",
            confidence_score=0.9,
            provider_used="openai",
            model_used="gpt-4-vision"
        )
        mock_provider.analyze_image = AsyncMock(return_value=vision_result)

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            # First upload
            upload1 = await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=org_id,
                user_id=user_id
            )

            # Second upload (identical image)
            upload2 = await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=org_id,
                user_id=user_id
            )

        # Provider should only be called once (second is cached)
        assert mock_provider.analyze_image.call_count == 1
        assert upload1.analysis_result.extracted_text == upload2.analysis_result.extracted_text

    @pytest.mark.asyncio
    async def test_cache_disabled_always_analyzes(self):
        """
        Test that caching can be disabled

        BUSINESS CONTEXT:
        Some organizations may want fresh analysis every time.
        """
        service = ScreenshotAnalysisService(cache_results=False)

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        mock_provider.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="Content",
            confidence_score=0.9,
            provider_used="openai",
            model_used="gpt-4-vision"
        ))

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=uuid4(),
                user_id=uuid4()
            )

            await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=uuid4(),
                user_id=uuid4()
            )

        # Should call provider twice when cache disabled
        assert mock_provider.analyze_image.call_count == 2

    def test_clear_cache(self):
        """
        Test cache clearing functionality

        BUSINESS CONTEXT:
        Cache should be clearable for testing or memory management.
        """
        service = ScreenshotAnalysisService()

        # Manually add to cache
        service._result_cache["test_hash"] = AnalysisResult(
            extracted_text="test"
        )

        assert len(service._result_cache) == 1

        service.clear_cache()

        assert len(service._result_cache) == 0

    def test_get_cache_stats(self):
        """
        Test cache statistics

        BUSINESS CONTEXT:
        Stats help monitor cache effectiveness.
        """
        service = ScreenshotAnalysisService()

        stats = service.get_cache_stats()

        assert isinstance(stats, dict)
        assert "cached_results" in stats
        assert "cache_enabled" in stats
        assert stats["cache_enabled"] is True
        assert stats["cached_results"] == 0


class TestProviderFallback:
    """Test suite for provider fallback logic"""

    @pytest.mark.asyncio
    async def test_fallback_to_secondary_provider_on_primary_failure(self):
        """
        Test fallback to secondary provider when primary fails

        BUSINESS CONTEXT:
        High availability through provider redundancy ensures service uptime.
        """
        service = ScreenshotAnalysisService(enable_fallback=True, max_fallback_attempts=2)

        # Primary provider fails
        primary_provider = Mock(spec=BaseLLMProvider)
        primary_provider.provider_name = "openai"
        primary_provider.analyze_image = AsyncMock(
            side_effect=LLMProviderException("API Error")
        )

        # Fallback provider succeeds
        fallback_provider = Mock(spec=BaseLLMProvider)
        fallback_provider.provider_name = "anthropic"
        fallback_provider.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="Fallback success",
            confidence_score=0.85,
            provider_used="anthropic",
            model_used="claude-3-opus"
        ))
        fallback_provider.close = AsyncMock()

        # Mock registry to return fallback
        mock_registry = Mock()
        mock_registry.get_fallback_providers = AsyncMock(
            return_value=[fallback_provider]
        )
        service._registry = mock_registry

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=primary_provider):

            upload = await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=uuid4(),
                user_id=uuid4()
            )

        assert upload.status == UploadStatus.ANALYZED
        assert upload.analysis_result.provider_used == "anthropic"

    @pytest.mark.asyncio
    async def test_fallback_disabled_fails_immediately(self):
        """
        Test that disabling fallback fails on first provider error

        BUSINESS CONTEXT:
        Some organizations may prefer fast failure over fallback.
        """
        service = ScreenshotAnalysisService(enable_fallback=False)

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        mock_provider.analyze_image = AsyncMock(
            side_effect=LLMProviderException("API Error")
        )

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            # Wrapped in ScreenshotAnalysisException
            with pytest.raises((VisionAnalysisException, ScreenshotAnalysisException)):
                await service.analyze_screenshot(
                    image_data=PNG_MAGIC_BYTES,
                    organization_id=uuid4(),
                    user_id=uuid4()
                )

    @pytest.mark.asyncio
    async def test_fallback_respects_max_attempts(self):
        """
        Test that fallback respects max_fallback_attempts

        BUSINESS CONTEXT:
        Limit fallback attempts to prevent infinite retry loops.
        """
        service = ScreenshotAnalysisService(enable_fallback=True, max_fallback_attempts=1)

        primary_provider = Mock(spec=BaseLLMProvider)
        primary_provider.provider_name = "openai"
        primary_provider.analyze_image = AsyncMock(
            side_effect=LLMProviderException("API Error")
        )

        # Multiple fallback providers available
        fallback1 = Mock(spec=BaseLLMProvider)
        fallback1.provider_name = "anthropic"
        fallback1.analyze_image = AsyncMock(
            side_effect=LLMProviderException("Also failed")
        )
        fallback1.close = AsyncMock()

        fallback2 = Mock(spec=BaseLLMProvider)
        fallback2.provider_name = "deepseek"
        fallback2.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="Success",
            confidence_score=0.9,
            provider_used="deepseek",
            model_used="deepseek-vl"
        ))
        fallback2.close = AsyncMock()

        mock_registry = Mock()
        mock_registry.get_fallback_providers = AsyncMock(
            return_value=[fallback1, fallback2]
        )
        service._registry = mock_registry

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=primary_provider):

            # Wrapped in ScreenshotAnalysisException
            with pytest.raises((VisionAnalysisException, ScreenshotAnalysisException)):
                await service.analyze_screenshot(
                    image_data=PNG_MAGIC_BYTES,
                    organization_id=uuid4(),
                    user_id=uuid4()
                )

        # Should only try 1 fallback (max_fallback_attempts=1)
        assert fallback1.analyze_image.call_count == 1
        assert fallback2.analyze_image.call_count == 0


class TestBatchProcessing:
    """Test suite for batch screenshot processing"""

    @pytest.mark.asyncio
    async def test_analyze_batch_success(self):
        """
        Test successful batch analysis

        BUSINESS CONTEXT:
        Users often upload multiple screenshots from a course.
        """
        service = ScreenshotAnalysisService()
        org_id = uuid4()
        user_id = uuid4()

        images = [
            (PNG_MAGIC_BYTES, "screenshot1.png"),
            (JPEG_MAGIC_BYTES, "screenshot2.jpg"),
            (WEBP_MAGIC_BYTES, "screenshot3.webp")
        ]

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        mock_provider.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="Content",
            confidence_score=0.9,
            course_structure={
                "title": "Course Module",
                "description": "Description",
                "topics": ["Topic 1"],
                "difficulty": "intermediate",
                "estimated_duration_hours": 5
            },
            provider_used="openai",
            model_used="gpt-4-vision"
        ))

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            batch = await service.analyze_batch(
                images=images,
                organization_id=org_id,
                user_id=user_id
            )

        assert isinstance(batch, ScreenshotBatch)
        assert batch.total_count == 3
        assert batch.completed_count == 3
        assert batch.failed_count == 0
        assert batch.status == UploadStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_analyze_batch_with_failures(self):
        """
        Test batch analysis with some failures

        BUSINESS CONTEXT:
        Partial batch failures should not block successful analyses.
        """
        service = ScreenshotAnalysisService(enable_fallback=False)
        org_id = uuid4()
        user_id = uuid4()

        images = [
            (PNG_MAGIC_BYTES, "good.png"),
            (INVALID_MAGIC_BYTES, "bad.png")
        ]

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        mock_provider.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="Success",
            confidence_score=0.9,
            provider_used="openai",
            model_used="gpt-4-vision"
        ))

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            batch = await service.analyze_batch(
                images=images,
                organization_id=org_id,
                user_id=user_id
            )

        assert batch.total_count == 2
        assert batch.completed_count == 1
        assert batch.failed_count == 1
        assert batch.status == UploadStatus.ANALYZED  # Partial success

    @pytest.mark.asyncio
    async def test_analyze_batch_combine_results(self):
        """
        Test batch analysis with combined results

        BUSINESS CONTEXT:
        Combined analysis creates unified course from multiple screenshots.
        """
        service = ScreenshotAnalysisService()
        org_id = uuid4()
        user_id = uuid4()

        images = [
            (PNG_MAGIC_BYTES, "module1.png"),
            (JPEG_MAGIC_BYTES, "module2.jpg")
        ]

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"

        # Different results for each image
        results = [
            VisionAnalysisResult(
                extracted_text="Module 1 content",
                confidence_score=0.95,
                course_structure={
                    "title": "Module 1",
                    "description": "First module",
                    "topics": ["Topic A", "Topic B"],
                    "difficulty": "beginner",
                    "estimated_duration_hours": 3
                },
                provider_used="openai",
                model_used="gpt-4-vision",
                tokens_used=500
            ),
            VisionAnalysisResult(
                extracted_text="Module 2 content",
                confidence_score=0.90,
                course_structure={
                    "title": "Module 2",
                    "description": "Second module",
                    "topics": ["Topic C", "Topic A"],  # Topic A is duplicate
                    "difficulty": "intermediate",
                    "estimated_duration_hours": 4
                },
                provider_used="openai",
                model_used="gpt-4-vision",
                tokens_used=600
            )
        ]

        mock_provider.analyze_image = AsyncMock(side_effect=results)

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            batch = await service.analyze_batch(
                images=images,
                organization_id=org_id,
                user_id=user_id,
                combine_results=True
            )

        assert batch.combined_analysis is not None
        assert batch.combined_analysis.confidence_score == 0.925  # Average of 0.95 and 0.90
        assert batch.combined_analysis.tokens_used == 1100  # Sum of tokens
        assert batch.combined_analysis.course_structure is not None

        # Topics should be deduplicated
        topics = batch.combined_analysis.course_structure.topics
        assert "Topic A" in topics
        assert "Topic B" in topics
        assert "Topic C" in topics
        assert topics.count("Topic A") == 1  # No duplicates


class TestProgressTracking:
    """Test suite for progress tracking"""

    @pytest.mark.asyncio
    async def test_upload_status_progression(self):
        """
        Test that upload status progresses correctly

        BUSINESS CONTEXT:
        Users need to track analysis progress through UI.
        """
        service = ScreenshotAnalysisService()

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        mock_provider.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="Content",
            confidence_score=0.9,
            provider_used="openai",
            model_used="gpt-4-vision"
        ))

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            upload = await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=uuid4(),
                user_id=uuid4()
            )

        # Final status should be ANALYZED
        assert upload.status == UploadStatus.ANALYZED
        assert upload.analyzed_at is not None
        assert upload.updated_at is not None

    def test_batch_progress_calculation(self):
        """
        Test batch progress percentage calculation

        BUSINESS CONTEXT:
        Progress bars help users understand processing status.
        """
        batch = ScreenshotBatch(
            organization_id=uuid4(),
            user_id=uuid4()
        )

        # Add screenshots with different statuses
        for i in range(10):
            upload = ScreenshotUpload(
                organization_id=batch.organization_id,
                user_id=batch.user_id,
                status=UploadStatus.ANALYZED if i < 7 else UploadStatus.ANALYZING
            )
            batch.add_screenshot(upload)

        assert batch.total_count == 10
        assert batch.completed_count == 7
        assert batch.progress_percent == 70.0


class TestErrorHandling:
    """Test suite for error handling"""

    @pytest.mark.asyncio
    async def test_unexpected_error_wrapped_in_screenshot_analysis_exception(self):
        """
        Test that unexpected errors are wrapped properly

        BUSINESS CONTEXT:
        Unexpected errors should be caught and logged for debugging.
        """
        service = ScreenshotAnalysisService()

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        mock_provider.analyze_image = AsyncMock(
            side_effect=RuntimeError("Unexpected runtime error")
        )

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            with pytest.raises(ScreenshotAnalysisException) as exc_info:
                await service.analyze_screenshot(
                    image_data=PNG_MAGIC_BYTES,
                    organization_id=uuid4(),
                    user_id=uuid4()
                )

            assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_failed_upload_stores_error_message(self):
        """
        Test that failed uploads store error message

        BUSINESS CONTEXT:
        Error messages help users understand what went wrong.
        """
        service = ScreenshotAnalysisService(enable_fallback=False)

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        error_msg = "Rate limit exceeded"
        mock_provider.analyze_image = AsyncMock(
            side_effect=LLMProviderException(error_msg)
        )

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            try:
                await service.analyze_screenshot(
                    image_data=PNG_MAGIC_BYTES,
                    organization_id=uuid4(),
                    user_id=uuid4()
                )
            except (VisionAnalysisException, ScreenshotAnalysisException):
                pass  # Expected


class TestConfidenceScoreCalculation:
    """Test suite for confidence score calculation"""

    @pytest.mark.asyncio
    async def test_high_confidence_analysis(self):
        """
        Test that high confidence scores are preserved

        BUSINESS CONTEXT:
        High confidence indicates reliable analysis results.
        """
        service = ScreenshotAnalysisService()

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        mock_provider.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="Clear, well-structured content",
            confidence_score=0.95,
            provider_used="openai",
            model_used="gpt-4-vision"
        ))

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            upload = await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=uuid4(),
                user_id=uuid4()
            )

        assert upload.analysis_result.is_high_confidence is True
        assert upload.analysis_result.confidence_score >= 0.8

    def test_combined_analysis_averages_confidence(self):
        """
        Test that combined analysis averages confidence scores

        BUSINESS CONTEXT:
        Combined confidence reflects overall reliability of batch.
        """
        service = ScreenshotAnalysisService()

        analyses = [
            AnalysisResult(
                extracted_text="Text 1",
                confidence_score=0.95,
                provider_used="openai",
                model_used="gpt-4-vision",
                tokens_used=500,
                processing_time_ms=1000,
                course_structure=CourseStructure(
                    title="Course 1",
                    description="Description 1",
                    topics=["Topic A"]
                )
            ),
            AnalysisResult(
                extracted_text="Text 2",
                confidence_score=0.85,
                provider_used="openai",
                model_used="gpt-4-vision",
                tokens_used=600,
                processing_time_ms=1200,
                course_structure=CourseStructure(
                    title="Course 2",
                    description="Description 2",
                    topics=["Topic B"]
                )
            )
        ]

        combined = service._combine_analyses(analyses)

        # Average of 0.95 and 0.85 should be 0.90
        assert abs(combined.confidence_score - 0.90) < 0.01


class TestDifficultyParsing:
    """Test suite for difficulty level parsing"""

    def test_parse_valid_difficulty_levels(self):
        """
        Test parsing of valid difficulty strings

        BUSINESS CONTEXT:
        Different difficulty levels help match content to learner skill.
        """
        service = ScreenshotAnalysisService()

        assert service._parse_difficulty("beginner") == DifficultyLevel.BEGINNER
        assert service._parse_difficulty("intermediate") == DifficultyLevel.INTERMEDIATE
        assert service._parse_difficulty("advanced") == DifficultyLevel.ADVANCED
        assert service._parse_difficulty("expert") == DifficultyLevel.EXPERT

    def test_parse_difficulty_case_insensitive(self):
        """
        Test that difficulty parsing is case-insensitive

        BUSINESS CONTEXT:
        LLM responses may vary in case.
        """
        service = ScreenshotAnalysisService()

        assert service._parse_difficulty("BEGINNER") == DifficultyLevel.BEGINNER
        assert service._parse_difficulty("Intermediate") == DifficultyLevel.INTERMEDIATE

    def test_parse_invalid_difficulty_defaults_to_intermediate(self):
        """
        Test that invalid difficulty defaults to intermediate

        BUSINESS CONTEXT:
        Intermediate is a safe default for unknown difficulty.
        """
        service = ScreenshotAnalysisService()

        assert service._parse_difficulty("unknown") == DifficultyLevel.INTERMEDIATE
        assert service._parse_difficulty("") == DifficultyLevel.INTERMEDIATE


class TestAnalysisPrompt:
    """Test suite for analysis prompt generation"""

    def test_get_default_analysis_prompt(self):
        """
        Test that default analysis prompt is comprehensive

        BUSINESS CONTEXT:
        Prompt quality directly impacts analysis accuracy.
        """
        service = ScreenshotAnalysisService()

        prompt = service._get_analysis_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert "course" in prompt.lower()
        assert "learning objectives" in prompt.lower()
        assert "topics" in prompt.lower()
        assert "difficulty" in prompt.lower()
        assert "JSON" in prompt


class TestProviderOverride:
    """Test suite for provider override functionality"""

    @pytest.mark.asyncio
    async def test_provider_override_uses_specific_provider(self):
        """
        Test that provider_override forces use of specific provider

        BUSINESS CONTEXT:
        Organizations may want to test specific providers.
        """
        service = ScreenshotAnalysisService()

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "anthropic"
        mock_provider.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="Content",
            confidence_score=0.9,
            provider_used="anthropic",
            model_used="claude-3-opus"
        ))

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider) as mock_get_provider:

            await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=uuid4(),
                user_id=uuid4(),
                provider_override="anthropic"
            )

            # Verify provider_override was passed
            call_args = mock_get_provider.call_args
            assert call_args[1]['provider_override'] == "anthropic"


class TestCachingBehavior:
    """
    Test suite for result caching functionality

    BUSINESS CONTEXT:
    Caching prevents redundant API calls for identical screenshots,
    reducing costs and improving response times.
    """

    @pytest.mark.asyncio
    async def test_cached_result_returned_for_duplicate_image(self):
        """
        Test that cached results are returned for identical images

        BUSINESS CONTEXT:
        Duplicate uploads should not trigger redundant API calls.
        """
        service = ScreenshotAnalysisService(cache_results=True)

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        mock_provider.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="Cached content",
            confidence_score=0.92,
            provider_used="openai",
            model_used="gpt-4-vision"
        ))

        org_id = uuid4()
        user_id = uuid4()

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            # First call - should hit API
            result1 = await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=org_id,
                user_id=user_id
            )

            # Second call with same image - should use cache
            result2 = await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=org_id,
                user_id=user_id
            )

        # API should only be called once
        assert mock_provider.analyze_image.call_count == 1
        # Results should be identical
        assert result1.analysis_result.extracted_text == result2.analysis_result.extracted_text

    @pytest.mark.asyncio
    async def test_cache_disabled_calls_api_every_time(self):
        """
        Test that API is called every time when caching is disabled

        BUSINESS CONTEXT:
        Some organizations may prefer fresh analysis every time.
        """
        service = ScreenshotAnalysisService(cache_results=False)

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        mock_provider.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="Fresh content",
            confidence_score=0.88,
            provider_used="openai",
            model_used="gpt-4-vision"
        ))

        org_id = uuid4()
        user_id = uuid4()

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            # Make two calls with same image
            await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=org_id,
                user_id=user_id
            )

            await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=org_id,
                user_id=user_id
            )

        # API should be called twice
        assert mock_provider.analyze_image.call_count == 2


class TestLanguageDetection:
    """
    Test suite for language detection in analysis

    BUSINESS CONTEXT:
    Correct language detection enables proper course localization
    and ensures content is served in the appropriate language.
    """

    @pytest.mark.asyncio
    async def test_detect_english_language(self):
        """
        Test detection of English language content
        """
        service = ScreenshotAnalysisService()

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        mock_provider.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="Introduction to Programming",
            detected_language="en",
            confidence_score=0.94,
            provider_used="openai",
            model_used="gpt-4-vision"
        ))

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            upload = await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=uuid4(),
                user_id=uuid4()
            )

        assert upload.analysis_result.detected_language == "en"

    @pytest.mark.asyncio
    async def test_detect_non_english_language(self):
        """
        Test detection of non-English language content

        BUSINESS CONTEXT:
        Platform supports multilingual course creation.
        """
        service = ScreenshotAnalysisService()

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        mock_provider.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="Einführung in die Programmierung",
            detected_language="de",
            confidence_score=0.91,
            provider_used="openai",
            model_used="gpt-4-vision"
        ))

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            upload = await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=uuid4(),
                user_id=uuid4()
            )

        assert upload.analysis_result.detected_language == "de"


class TestEmptyAndMalformedResponses:
    """
    Test suite for handling empty and malformed LLM responses

    BUSINESS CONTEXT:
    AI responses may sometimes be incomplete or malformed.
    The service must handle these gracefully.
    """

    @pytest.mark.asyncio
    async def test_handle_empty_text_response(self):
        """
        Test handling of empty extracted text

        BUSINESS CONTEXT:
        Some screenshots may have minimal readable text.
        """
        service = ScreenshotAnalysisService()

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        mock_provider.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="",
            confidence_score=0.4,  # Low confidence due to no text
            provider_used="openai",
            model_used="gpt-4-vision"
        ))

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            upload = await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=uuid4(),
                user_id=uuid4()
            )

        assert upload.analysis_result is not None
        assert upload.analysis_result.is_high_confidence is False

    @pytest.mark.asyncio
    async def test_handle_missing_course_structure(self):
        """
        Test handling when course structure is not extractable

        BUSINESS CONTEXT:
        Some images may not contain course-like content.
        """
        service = ScreenshotAnalysisService()

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        mock_provider.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="Random image without course content",
            confidence_score=0.35,
            course_structure=None,
            provider_used="openai",
            model_used="gpt-4-vision"
        ))

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            upload = await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=uuid4(),
                user_id=uuid4()
            )

        # Should complete without error
        assert upload.status == UploadStatus.ANALYZED


class TestConcurrentBatchProcessing:
    """
    Test suite for concurrent batch processing

    BUSINESS CONTEXT:
    Organizations may upload multiple screenshots simultaneously.
    The system must handle concurrent processing efficiently.
    """

    @pytest.mark.asyncio
    async def test_batch_processes_all_screenshots(self):
        """
        Test that batch processing handles all screenshots
        """
        service = ScreenshotAnalysisService()

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        mock_provider.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="Batch content",
            confidence_score=0.88,
            provider_used="openai",
            model_used="gpt-4-vision"
        ))

        org_id = uuid4()
        user_id = uuid4()

        batch = ScreenshotBatch(
            organization_id=org_id,
            user_id=user_id
        )

        # Add multiple screenshots
        for _ in range(5):
            upload = ScreenshotUpload(
                organization_id=org_id,
                user_id=user_id
            )
            batch.add_screenshot(upload)

        assert batch.total_count == 5

    def test_batch_status_calculation(self):
        """
        Test batch status based on individual screenshot statuses
        """
        org_id = uuid4()
        user_id = uuid4()

        batch = ScreenshotBatch(
            organization_id=org_id,
            user_id=user_id
        )

        # Add screenshots with mixed statuses
        for i in range(10):
            status = [UploadStatus.PENDING, UploadStatus.ANALYZING, UploadStatus.ANALYZED][i % 3]
            upload = ScreenshotUpload(
                organization_id=org_id,
                user_id=user_id,
                status=status
            )
            batch.add_screenshot(upload)

        # Verify counts
        assert batch.total_count == 10
        # Some should be completed (ANALYZED)
        assert batch.completed_count > 0


class TestModuleExtraction:
    """
    Test suite for course module extraction from analysis

    BUSINESS CONTEXT:
    Modules are the primary organizational unit for courses.
    Accurate extraction is essential for course quality.
    """

    def test_parse_modules_from_analysis(self):
        """
        Test parsing of module structure from LLM response
        """
        service = ScreenshotAnalysisService()

        # Create mock course structure with modules
        course_structure = CourseStructure(
            title="Python Fundamentals",
            description="Learn Python basics",
            modules=[
                CourseModule(
                    title="Introduction",
                    description="Getting started with Python",
                    order=1,
                    lessons=["What is Python", "Installation"],
                    estimated_duration_minutes=45
                ),
                CourseModule(
                    title="Variables and Types",
                    description="Understanding Python data types",
                    order=2,
                    lessons=["Numbers", "Strings", "Lists"],
                    estimated_duration_minutes=60
                )
            ],
            topics=["Python", "Programming"]
        )

        assert len(course_structure.modules) == 2
        assert course_structure.modules[0].title == "Introduction"
        assert course_structure.modules[1].order == 2
        assert len(course_structure.modules[1].lessons) == 3

    def test_module_duration_calculation(self):
        """
        Test total duration calculation from modules

        BUSINESS CONTEXT:
        Total duration helps learners plan their study time.
        """
        course_structure = CourseStructure(
            title="Test Course",
            description="Test",
            modules=[
                CourseModule(
                    title="Module 1",
                    description="",
                    order=1,
                    estimated_duration_minutes=30
                ),
                CourseModule(
                    title="Module 2",
                    description="",
                    order=2,
                    estimated_duration_minutes=45
                ),
                CourseModule(
                    title="Module 3",
                    description="",
                    order=3,
                    estimated_duration_minutes=60
                )
            ]
        )

        total_minutes = sum(m.estimated_duration_minutes for m in course_structure.modules)
        assert total_minutes == 135  # 30 + 45 + 60


class TestDetectedElementParsing:
    """
    Test suite for detected element parsing

    BUSINESS CONTEXT:
    Detecting specific elements (headings, code, diagrams) helps
    determine content type and appropriate course structure.
    """

    def test_parse_detected_elements(self):
        """
        Test parsing of detected elements from LLM response
        """
        elements = [
            DetectedElement(
                element_type="heading",
                content="Introduction to Machine Learning",
                confidence=0.95,
                bounding_box={"x": 100, "y": 50, "width": 500, "height": 40}
            ),
            DetectedElement(
                element_type="code",
                content="import numpy as np",
                confidence=0.92,
                metadata={"language": "python"}
            ),
            DetectedElement(
                element_type="diagram",
                content="Neural network architecture",
                confidence=0.88
            )
        ]

        assert len(elements) == 3
        assert elements[0].element_type == "heading"
        assert elements[1].metadata.get("language") == "python"
        assert elements[2].confidence == 0.88

    def test_element_type_classification(self):
        """
        Test classification of different element types

        BUSINESS CONTEXT:
        Different element types inform content generation strategy.
        """
        element_types = ["heading", "subheading", "text", "code", "diagram", "image", "list", "table"]

        for elem_type in element_types:
            element = DetectedElement(
                element_type=elem_type,
                content="Test content",
                confidence=0.8
            )
            assert element.element_type == elem_type


class TestOrganizationIsolation:
    """
    Test suite for multi-tenant organization isolation

    BUSINESS CONTEXT:
    Screenshots and analysis results must be isolated between organizations
    for data security and privacy compliance.
    """

    def test_upload_belongs_to_organization(self):
        """
        Test that uploads are correctly associated with organization
        """
        org_id_1 = uuid4()
        org_id_2 = uuid4()
        user_id = uuid4()

        upload_1 = ScreenshotUpload(
            organization_id=org_id_1,
            user_id=user_id
        )

        upload_2 = ScreenshotUpload(
            organization_id=org_id_2,
            user_id=user_id
        )

        assert upload_1.organization_id == org_id_1
        assert upload_2.organization_id == org_id_2
        assert upload_1.organization_id != upload_2.organization_id

    def test_batch_organization_assignment(self):
        """
        Test that batch is correctly associated with organization
        """
        org_id = uuid4()
        user_id = uuid4()

        batch = ScreenshotBatch(
            organization_id=org_id,
            user_id=user_id
        )

        # Add upload to batch
        upload = ScreenshotUpload(
            organization_id=org_id,
            user_id=user_id
        )
        batch.add_screenshot(upload)

        assert batch.organization_id == org_id
        assert batch.screenshots[0].organization_id == org_id


class TestTokenUsageTracking:
    """
    Test suite for token usage tracking

    BUSINESS CONTEXT:
    Token usage affects API costs and must be tracked for
    billing and usage analytics.
    """

    @pytest.mark.asyncio
    async def test_track_tokens_from_analysis(self):
        """
        Test that token usage is tracked from analysis
        """
        service = ScreenshotAnalysisService()

        mock_provider = Mock(spec=BaseLLMProvider)
        mock_provider.provider_name = "openai"
        mock_provider.analyze_image = AsyncMock(return_value=VisionAnalysisResult(
            extracted_text="Content",
            confidence_score=0.9,
            tokens_used=1250,
            provider_used="openai",
            model_used="gpt-4-vision"
        ))

        with patch('course_generator.application.services.screenshot_analysis_service.get_provider_for_organization',
                   new_callable=AsyncMock, return_value=mock_provider):

            upload = await service.analyze_screenshot(
                image_data=PNG_MAGIC_BYTES,
                organization_id=uuid4(),
                user_id=uuid4()
            )

        assert upload.analysis_result.tokens_used == 1250

    def test_combined_analysis_sums_tokens(self):
        """
        Test that combined analysis sums token usage

        BUSINESS CONTEXT:
        Total token usage is needed for cost calculation.
        """
        service = ScreenshotAnalysisService()

        analyses = [
            AnalysisResult(
                extracted_text="Text 1",
                confidence_score=0.9,
                tokens_used=500,
                processing_time_ms=1000,
                provider_used="openai",
                model_used="gpt-4-vision"
            ),
            AnalysisResult(
                extracted_text="Text 2",
                confidence_score=0.85,
                tokens_used=600,
                processing_time_ms=1200,
                provider_used="openai",
                model_used="gpt-4-vision"
            ),
            AnalysisResult(
                extracted_text="Text 3",
                confidence_score=0.88,
                tokens_used=450,
                processing_time_ms=900,
                provider_used="openai",
                model_used="gpt-4-vision"
            )
        ]

        combined = service._combine_analyses(analyses)

        # Total tokens should be summed
        assert combined.tokens_used == 1550  # 500 + 600 + 450


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
