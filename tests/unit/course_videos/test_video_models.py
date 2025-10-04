"""
Unit Tests for Course Video Pydantic Models

BUSINESS REQUIREMENT:
Validates that video data models properly enforce business rules including
file size limits, MIME type restrictions, and URL format validation.

TECHNICAL IMPLEMENTATION:
- Tests Pydantic model validation logic
- Tests VideoType enum values
- Tests file size constraints (2GB max)
- Tests MIME type validation
- Tests required vs optional fields
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'services' / 'course-management'))

import pytest
from pydantic import ValidationError
from datetime import datetime

from models.course_video import (
    VideoType,
    CourseVideoBase,
    CourseVideoCreate,
    CourseVideoUpdate,
    CourseVideo,
    CourseVideoResponse,
    CourseVideoListResponse,
    VideoUploadRequest,
    VideoUploadInitResponse
)


class TestVideoTypeEnum:
    """Test VideoType enumeration."""

    def test_video_type_values(self):
        """Test all valid video type values."""
        assert VideoType.UPLOAD.value == "upload"
        assert VideoType.LINK.value == "link"
        assert VideoType.YOUTUBE.value == "youtube"
        assert VideoType.VIMEO.value == "vimeo"

    def test_video_type_membership(self):
        """Test video type enum membership."""
        assert "upload" in [v.value for v in VideoType]
        assert "youtube" in [v.value for v in VideoType]
        assert "invalid" not in [v.value for v in VideoType]


class TestCourseVideoBase:
    """Test base video model validation."""

    def test_valid_base_model(self):
        """Test creation with valid data."""
        video = CourseVideoBase(
            title="Introduction to Python",
            description="Learn Python basics",
            video_type=VideoType.YOUTUBE,
            video_url="https://youtube.com/watch?v=abc123",
            order_index=0
        )
        assert video.title == "Introduction to Python"
        assert video.video_type == VideoType.YOUTUBE

    def test_title_required(self):
        """Test that title is required."""
        with pytest.raises(ValidationError) as exc_info:
            CourseVideoBase(
                video_type=VideoType.UPLOAD,
                video_url="https://example.com/video.mp4"
            )
        assert "title" in str(exc_info.value)

    def test_title_max_length(self):
        """Test title length constraint (255 chars)."""
        long_title = "A" * 256
        with pytest.raises(ValidationError) as exc_info:
            CourseVideoBase(
                title=long_title,
                video_type=VideoType.UPLOAD,
                video_url="https://example.com/video.mp4"
            )
        assert "title" in str(exc_info.value).lower()

    def test_description_optional(self):
        """Test that description is optional."""
        video = CourseVideoBase(
            title="Test Video",
            video_type=VideoType.UPLOAD,
            video_url="https://example.com/video.mp4"
        )
        assert video.description == ""

    def test_default_order_index(self):
        """Test default order_index value."""
        video = CourseVideoBase(
            title="Test Video",
            video_type=VideoType.UPLOAD,
            video_url="https://example.com/video.mp4"
        )
        assert video.order_index == 0

    def test_default_video_type(self):
        """Test default video_type is UPLOAD."""
        video = CourseVideoBase(
            title="Test Video",
            video_url="https://example.com/video.mp4"
        )
        assert video.video_type == VideoType.UPLOAD


class TestCourseVideoCreate:
    """Test video creation model."""

    def test_valid_create_model(self):
        """Test creation with all required fields."""
        video = CourseVideoCreate(
            course_id="550e8400-e29b-41d4-a716-446655440000",
            title="Python Tutorial",
            video_type=VideoType.YOUTUBE,
            video_url="https://youtube.com/watch?v=abc123"
        )
        assert video.course_id == "550e8400-e29b-41d4-a716-446655440000"
        assert video.title == "Python Tutorial"

    def test_course_id_required(self):
        """Test that course_id is required."""
        with pytest.raises(ValidationError) as exc_info:
            CourseVideoCreate(
                title="Test Video",
                video_type=VideoType.UPLOAD,
                video_url="https://example.com/video.mp4"
            )
        assert "course_id" in str(exc_info.value)


class TestCourseVideoUpdate:
    """Test video update model."""

    def test_all_fields_optional(self):
        """Test that all update fields are optional."""
        update = CourseVideoUpdate()
        assert update.title is None
        assert update.description is None
        assert update.video_url is None
        assert update.order_index is None

    def test_partial_update(self):
        """Test partial field updates."""
        update = CourseVideoUpdate(
            title="Updated Title",
            order_index=5
        )
        assert update.title == "Updated Title"
        assert update.order_index == 5
        assert update.description is None


class TestCourseVideo:
    """Test full video model with database fields."""

    def test_full_video_model(self):
        """Test video model with all fields."""
        now = datetime.utcnow()
        video = CourseVideo(
            id="550e8400-e29b-41d4-a716-446655440000",
            course_id="660e8400-e29b-41d4-a716-446655440001",
            title="Python Basics",
            description="Introduction to Python programming",
            video_type=VideoType.YOUTUBE,
            video_url="https://youtube.com/watch?v=abc123",
            file_path=None,
            file_size_bytes=None,
            mime_type=None,
            duration_seconds=None,
            thumbnail_url=None,
            order_index=0,
            is_active=True,
            created_at=now,
            updated_at=now
        )
        assert video.id == "550e8400-e29b-41d4-a716-446655440000"
        assert video.is_active is True

    def test_uploaded_video_with_file_metadata(self):
        """Test uploaded video with file metadata."""
        video = CourseVideo(
            id="550e8400-e29b-41d4-a716-446655440000",
            course_id="660e8400-e29b-41d4-a716-446655440001",
            title="Uploaded Tutorial",
            video_type=VideoType.UPLOAD,
            video_url="",
            file_path="/storage/videos/abc123.mp4",
            file_size_bytes=52428800,  # 50MB
            mime_type="video/mp4",
            duration_seconds=600,
            order_index=0,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        assert video.file_size_bytes == 52428800
        assert video.mime_type == "video/mp4"


class TestVideoUploadRequest:
    """Test video upload request validation."""

    def test_valid_upload_request(self):
        """Test valid upload request."""
        request = VideoUploadRequest(
            course_id="550e8400-e29b-41d4-a716-446655440000",
            filename="tutorial.mp4",
            file_size_bytes=52428800,  # 50MB
            mime_type="video/mp4",
            title="Python Tutorial",
            description="Learn Python basics"
        )
        assert request.filename == "tutorial.mp4"
        assert request.file_size_bytes == 52428800

    def test_file_size_too_large(self):
        """Test file size exceeds 2GB limit."""
        max_size = 2 * 1024 * 1024 * 1024  # 2GB
        too_large = max_size + 1

        with pytest.raises(ValidationError) as exc_info:
            VideoUploadRequest(
                course_id="550e8400-e29b-41d4-a716-446655440000",
                filename="huge_video.mp4",
                file_size_bytes=too_large,
                mime_type="video/mp4",
                title="Huge Video"
            )
        assert "too large" in str(exc_info.value).lower()

    def test_file_size_zero_invalid(self):
        """Test that zero file size is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            VideoUploadRequest(
                course_id="550e8400-e29b-41d4-a716-446655440000",
                filename="empty.mp4",
                file_size_bytes=0,
                mime_type="video/mp4",
                title="Empty Video"
            )
        assert "file_size_bytes" in str(exc_info.value)

    def test_file_size_negative_invalid(self):
        """Test that negative file size is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            VideoUploadRequest(
                course_id="550e8400-e29b-41d4-a716-446655440000",
                filename="invalid.mp4",
                file_size_bytes=-100,
                mime_type="video/mp4",
                title="Invalid Video"
            )
        assert "file_size_bytes" in str(exc_info.value)

    def test_valid_mime_types(self):
        """Test various valid video MIME types."""
        valid_types = [
            "video/mp4",
            "video/mpeg",
            "video/quicktime",
            "video/x-msvideo",
            "video/webm"
        ]

        for mime_type in valid_types:
            request = VideoUploadRequest(
                course_id="550e8400-e29b-41d4-a716-446655440000",
                filename=f"video.{mime_type.split('/')[-1]}",
                file_size_bytes=1000000,
                mime_type=mime_type,
                title="Test Video"
            )
            assert request.mime_type == mime_type

    def test_filename_max_length(self):
        """Test filename length constraint (500 chars)."""
        long_filename = "video_" + "a" * 500 + ".mp4"

        with pytest.raises(ValidationError) as exc_info:
            VideoUploadRequest(
                course_id="550e8400-e29b-41d4-a716-446655440000",
                filename=long_filename,
                file_size_bytes=1000000,
                mime_type="video/mp4",
                title="Test Video"
            )
        assert "filename" in str(exc_info.value).lower()

    def test_filename_empty_invalid(self):
        """Test that empty filename is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            VideoUploadRequest(
                course_id="550e8400-e29b-41d4-a716-446655440000",
                filename="",
                file_size_bytes=1000000,
                mime_type="video/mp4",
                title="Test Video"
            )
        assert "filename" in str(exc_info.value).lower()


class TestVideoUploadInitResponse:
    """Test upload initiation response model."""

    def test_upload_init_response(self):
        """Test upload initialization response."""
        response = VideoUploadInitResponse(
            upload_id="upload-123",
            video_id="550e8400-e29b-41d4-a716-446655440000",
            upload_url="/api/videos/upload/upload-123/file"
        )
        assert response.upload_id == "upload-123"
        assert response.video_id == "550e8400-e29b-41d4-a716-446655440000"


class TestCourseVideoResponse:
    """Test video response models."""

    def test_single_video_response(self):
        """Test single video response wrapper."""
        now = datetime.utcnow()
        video = CourseVideo(
            id="550e8400-e29b-41d4-a716-446655440000",
            course_id="660e8400-e29b-41d4-a716-446655440001",
            title="Test Video",
            video_type=VideoType.YOUTUBE,
            video_url="https://youtube.com/watch?v=abc",
            order_index=0,
            is_active=True,
            created_at=now,
            updated_at=now
        )

        response = CourseVideoResponse(
            success=True,
            message="Video retrieved successfully",
            video=video
        )
        assert response.success is True
        assert response.video.title == "Test Video"

    def test_video_list_response(self):
        """Test video list response wrapper."""
        now = datetime.utcnow()
        videos = [
            CourseVideo(
                id=f"550e8400-e29b-41d4-a716-44665544000{i}",
                course_id="660e8400-e29b-41d4-a716-446655440001",
                title=f"Video {i}",
                video_type=VideoType.YOUTUBE,
                video_url=f"https://youtube.com/watch?v=abc{i}",
                order_index=i,
                is_active=True,
                created_at=now,
                updated_at=now
            )
            for i in range(3)
        ]

        response = CourseVideoListResponse(
            success=True,
            message="Videos retrieved",
            videos=videos,
            count=3
        )
        assert response.count == 3
        assert len(response.videos) == 3
        assert response.videos[0].title == "Video 0"


# Run tests with: pytest tests/unit/course_videos/test_video_models.py -v
