"""
Unit Tests for Video Validation Logic

BUSINESS REQUIREMENT:
Validates file validation, URL validation, and business rule enforcement
for video uploads and links.

TECHNICAL IMPLEMENTATION:
- Tests file type validation
- Tests file size validation
- Tests URL format validation
- Tests platform-specific URL validation (YouTube, Vimeo)
- Tests MIME type validation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'services' / 'course-management'))

import pytest
from pydantic import ValidationError

from models.course_video import (
    VideoType,
    VideoUploadRequest,
    CourseVideoCreate
)


class TestFileTypeValidation:
    """Test video file type validation."""

    def test_valid_mp4(self):
        """Test MP4 files are accepted."""
        request = VideoUploadRequest(
            course_id="test-course",
            filename="video.mp4",
            file_size_bytes=1000000,
            mime_type="video/mp4",
            title="Test Video"
        )
        assert request.mime_type == "video/mp4"

    def test_valid_mpeg(self):
        """Test MPEG files are accepted."""
        request = VideoUploadRequest(
            course_id="test-course",
            filename="video.mpeg",
            file_size_bytes=1000000,
            mime_type="video/mpeg",
            title="Test Video"
        )
        assert request.mime_type == "video/mpeg"

    def test_valid_quicktime(self):
        """Test QuickTime (MOV) files are accepted."""
        request = VideoUploadRequest(
            course_id="test-course",
            filename="video.mov",
            file_size_bytes=1000000,
            mime_type="video/quicktime",
            title="Test Video"
        )
        assert request.mime_type == "video/quicktime"

    def test_valid_webm(self):
        """Test WebM files are accepted."""
        request = VideoUploadRequest(
            course_id="test-course",
            filename="video.webm",
            file_size_bytes=1000000,
            mime_type="video/webm",
            title="Test Video"
        )
        assert request.mime_type == "video/webm"

    def test_valid_avi(self):
        """Test AVI files are accepted."""
        request = VideoUploadRequest(
            course_id="test-course",
            filename="video.avi",
            file_size_bytes=1000000,
            mime_type="video/x-msvideo",
            title="Test Video"
        )
        assert request.mime_type == "video/x-msvideo"


class TestFileSizeValidation:
    """Test file size validation and limits."""

    def test_small_file_accepted(self):
        """Test small files (< 1MB) are accepted."""
        request = VideoUploadRequest(
            course_id="test-course",
            filename="small.mp4",
            file_size_bytes=500000,  # 500KB
            mime_type="video/mp4",
            title="Small Video"
        )
        assert request.file_size_bytes == 500000

    def test_medium_file_accepted(self):
        """Test medium files (~ 100MB) are accepted."""
        file_size = 100 * 1024 * 1024  # 100MB
        request = VideoUploadRequest(
            course_id="test-course",
            filename="medium.mp4",
            file_size_bytes=file_size,
            mime_type="video/mp4",
            title="Medium Video"
        )
        assert request.file_size_bytes == file_size

    def test_large_file_accepted(self):
        """Test large files (~ 1GB) are accepted."""
        file_size = 1 * 1024 * 1024 * 1024  # 1GB
        request = VideoUploadRequest(
            course_id="test-course",
            filename="large.mp4",
            file_size_bytes=file_size,
            mime_type="video/mp4",
            title="Large Video"
        )
        assert request.file_size_bytes == file_size

    def test_max_file_size_accepted(self):
        """Test file at exactly 2GB limit is accepted."""
        max_size = 2 * 1024 * 1024 * 1024  # 2GB exactly
        request = VideoUploadRequest(
            course_id="test-course",
            filename="max_size.mp4",
            file_size_bytes=max_size,
            mime_type="video/mp4",
            title="Max Size Video"
        )
        assert request.file_size_bytes == max_size

    def test_file_too_large_rejected(self):
        """Test file larger than 2GB is rejected."""
        max_size = 2 * 1024 * 1024 * 1024  # 2GB
        too_large = max_size + 1

        with pytest.raises(ValidationError) as exc_info:
            VideoUploadRequest(
                course_id="test-course",
                filename="too_large.mp4",
                file_size_bytes=too_large,
                mime_type="video/mp4",
                title="Too Large Video"
            )
        assert "too large" in str(exc_info.value).lower()

    def test_zero_size_rejected(self):
        """Test zero-byte files are rejected."""
        with pytest.raises(ValidationError):
            VideoUploadRequest(
                course_id="test-course",
                filename="empty.mp4",
                file_size_bytes=0,
                mime_type="video/mp4",
                title="Empty Video"
            )

    def test_negative_size_rejected(self):
        """Test negative file sizes are rejected."""
        with pytest.raises(ValidationError):
            VideoUploadRequest(
                course_id="test-course",
                filename="invalid.mp4",
                file_size_bytes=-100,
                mime_type="video/mp4",
                title="Invalid Video"
            )


class TestURLValidation:
    """Test video URL validation."""

    def test_valid_youtube_url(self):
        """Test valid YouTube URLs."""
        valid_urls = [
            "https://www.youtube.com/watch?v=abc123",
            "https://youtube.com/watch?v=abc123",
            "https://youtu.be/abc123",
            "https://www.youtube.com/watch?v=abc123&t=10s"
        ]

        for url in valid_urls:
            video = CourseVideoCreate(
                course_id="test-course",
                title="YouTube Video",
                video_type=VideoType.YOUTUBE,
                video_url=url
            )
            assert video.video_url == url

    def test_valid_vimeo_url(self):
        """Test valid Vimeo URLs."""
        valid_urls = [
            "https://vimeo.com/123456789",
            "https://www.vimeo.com/123456789",
            "https://vimeo.com/channels/staffpicks/123456789"
        ]

        for url in valid_urls:
            video = CourseVideoCreate(
                course_id="test-course",
                title="Vimeo Video",
                video_type=VideoType.VIMEO,
                video_url=url
            )
            assert video.video_url == url

    def test_valid_custom_url(self):
        """Test valid custom video URLs."""
        valid_urls = [
            "https://example.com/videos/tutorial.mp4",
            "https://cdn.example.com/video/123/file.mp4",
            "https://storage.googleapis.com/bucket/video.mp4"
        ]

        for url in valid_urls:
            video = CourseVideoCreate(
                course_id="test-course",
                title="Custom Video",
                video_type=VideoType.LINK,
                video_url=url
            )
            assert video.video_url == url

    def test_http_urls_accepted(self):
        """Test that HTTP (non-HTTPS) URLs are accepted."""
        video = CourseVideoCreate(
            course_id="test-course",
            title="HTTP Video",
            video_type=VideoType.LINK,
            video_url="http://example.com/video.mp4"
        )
        assert video.video_url == "http://example.com/video.mp4"


class TestFilenameValidation:
    """Test filename validation rules."""

    def test_valid_filenames(self):
        """Test various valid filenames."""
        valid_names = [
            "video.mp4",
            "my_video.mp4",
            "tutorial-part-1.mp4",
            "Python Tutorial 2024.mp4",
            "видео.mp4",  # Unicode
            "video (1).mp4"
        ]

        for filename in valid_names:
            request = VideoUploadRequest(
                course_id="test-course",
                filename=filename,
                file_size_bytes=1000000,
                mime_type="video/mp4",
                title="Test Video"
            )
            assert request.filename == filename

    def test_filename_too_long_rejected(self):
        """Test filenames exceeding 500 chars are rejected."""
        long_filename = "video_" + "a" * 500 + ".mp4"

        with pytest.raises(ValidationError) as exc_info:
            VideoUploadRequest(
                course_id="test-course",
                filename=long_filename,
                file_size_bytes=1000000,
                mime_type="video/mp4",
                title="Test Video"
            )
        assert "filename" in str(exc_info.value).lower()

    def test_empty_filename_rejected(self):
        """Test empty filenames are rejected."""
        with pytest.raises(ValidationError):
            VideoUploadRequest(
                course_id="test-course",
                filename="",
                file_size_bytes=1000000,
                mime_type="video/mp4",
                title="Test Video"
            )


class TestVideoTitleValidation:
    """Test video title validation."""

    def test_valid_titles(self):
        """Test various valid titles."""
        valid_titles = [
            "Introduction to Python",
            "Module 1: Getting Started",
            "Advanced Concepts (Part 2)",
            "TypeScript & JavaScript",
            "Tutorial #1",
            "A" * 255  # Max length
        ]

        for title in valid_titles:
            video = CourseVideoCreate(
                course_id="test-course",
                title=title,
                video_url="https://youtube.com/watch?v=abc"
            )
            assert video.title == title

    def test_title_too_long_rejected(self):
        """Test titles exceeding 255 chars are rejected."""
        long_title = "A" * 256

        with pytest.raises(ValidationError):
            CourseVideoCreate(
                course_id="test-course",
                title=long_title,
                video_url="https://youtube.com/watch?v=abc"
            )

    def test_empty_title_rejected(self):
        """Test empty titles are rejected."""
        with pytest.raises(ValidationError):
            CourseVideoCreate(
                course_id="test-course",
                title="",
                video_url="https://youtube.com/watch?v=abc"
            )


class TestVideoTypeValidation:
    """Test video type validation."""

    def test_all_video_types_accepted(self):
        """Test all defined video types are valid."""
        types_and_urls = [
            (VideoType.UPLOAD, ""),
            (VideoType.YOUTUBE, "https://youtube.com/watch?v=abc"),
            (VideoType.VIMEO, "https://vimeo.com/123"),
            (VideoType.LINK, "https://example.com/video.mp4")
        ]

        for video_type, url in types_and_urls:
            video = CourseVideoCreate(
                course_id="test-course",
                title="Test Video",
                video_type=video_type,
                video_url=url
            )
            assert video.video_type == video_type

    def test_default_video_type(self):
        """Test default video type is UPLOAD."""
        video = CourseVideoCreate(
            course_id="test-course",
            title="Test Video",
            video_url="https://example.com/video.mp4"
        )
        assert video.video_type == VideoType.UPLOAD


class TestDescriptionValidation:
    """Test video description validation."""

    def test_description_optional(self):
        """Test description is optional."""
        video = CourseVideoCreate(
            course_id="test-course",
            title="Test Video",
            video_url="https://youtube.com/watch?v=abc"
        )
        assert video.description == ""

    def test_long_description_accepted(self):
        """Test long descriptions are accepted."""
        long_description = "A" * 5000  # 5000 chars

        video = CourseVideoCreate(
            course_id="test-course",
            title="Test Video",
            description=long_description,
            video_url="https://youtube.com/watch?v=abc"
        )
        assert len(video.description) == 5000

    def test_unicode_description_accepted(self):
        """Test Unicode characters in descriptions."""
        description = "Este es un vídeo en español 🎥 中文字符"

        video = CourseVideoCreate(
            course_id="test-course",
            title="Test Video",
            description=description,
            video_url="https://youtube.com/watch?v=abc"
        )
        assert video.description == description


class TestOrderIndexValidation:
    """Test order index validation."""

    def test_default_order_index(self):
        """Test default order index is 0."""
        video = CourseVideoCreate(
            course_id="test-course",
            title="Test Video",
            video_url="https://youtube.com/watch?v=abc"
        )
        assert video.order_index == 0

    def test_custom_order_indices(self):
        """Test custom order indices."""
        for i in range(10):
            video = CourseVideoCreate(
                course_id="test-course",
                title=f"Video {i}",
                video_url=f"https://youtube.com/watch?v=abc{i}",
                order_index=i
            )
            assert video.order_index == i

    def test_negative_order_index_accepted(self):
        """Test negative order indices are accepted (for reordering)."""
        video = CourseVideoCreate(
            course_id="test-course",
            title="Test Video",
            video_url="https://youtube.com/watch?v=abc",
            order_index=-1
        )
        assert video.order_index == -1


# Run tests with: pytest tests/unit/course_videos/test_video_validation.py -v
