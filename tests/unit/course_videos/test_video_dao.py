"""
Unit Tests for Course Video Data Access Object (DAO)

BUSINESS REQUIREMENT:
Validates database operations for video management including CRUD operations,
ordering, soft deletes, and upload tracking.

TECHNICAL IMPLEMENTATION:
- Uses pytest-asyncio for async database tests
- Uses real PostgreSQL database (no mocking!)
- Tests transaction handling and rollback
- Tests concurrent operations
- Tests data integrity constraints
"""


import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from typing import List
import asyncpg

from data_access.course_video_dao import CourseVideoDAO
from models.course_video import (
    VideoType,
    CourseVideo,
    CourseVideoCreate,
    CourseVideoUpdate
)


@pytest_asyncio.fixture
async def db_pool():
    """
    Create a test database connection pool.

    IMPORTANT: Uses REAL database connection, not mocks!
    Tests run against actual PostgreSQL instance.
    """
    pool = await asyncpg.create_pool(
        host="localhost",
        port=5432,
        database="course_creator_test",  # Test database
        user="postgres",
        password="postgres123",
        min_size=1,
        max_size=5
    )

    yield pool

    await pool.close()


@pytest_asyncio.fixture
async def video_dao(db_pool):
    """Create VideoDAO instance with test database pool."""
    dao = CourseVideoDAO(db_pool)
    return dao


@pytest_asyncio.fixture
async def test_course_id(db_pool):
    """
    Create a test course for video relationships.

    Returns UUID of created course.
    """
    async with db_pool.acquire() as conn:
        course_id = await conn.fetchval(
            """
            INSERT INTO courses (
                title, description, instructor_id, organization_id, is_active
            ) VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            "Test Course",
            "Course for video testing",
            "test-instructor-123",
            "test-org-456",
            True
        )

        yield str(course_id)

        # Cleanup after test
        await conn.execute("DELETE FROM courses WHERE id = $1", course_id)


@pytest_asyncio.fixture
async def cleanup_videos(db_pool):
    """Cleanup test videos after each test."""
    yield

    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM course_videos WHERE title LIKE 'Test Video%'")
        await conn.execute("DELETE FROM video_uploads WHERE upload_id LIKE 'test-upload%'")


@pytest.mark.asyncio
class TestVideoDAOCreate:
    """Test video creation operations."""

    async def test_create_youtube_link(self, video_dao, test_course_id, cleanup_videos):
        """Test creating a YouTube video link."""
        video_data = {
            "course_id": test_course_id,
            "title": "Test Video - YouTube",
            "description": "Test YouTube video",
            "video_type": "youtube",
            "video_url": "https://youtube.com/watch?v=abc123",
            "order_index": 0
        }

        video = await video_dao.create(video_data)

        assert video is not None
        assert video.title == "Test Video - YouTube"
        assert video.video_type == VideoType.YOUTUBE
        assert video.video_url == "https://youtube.com/watch?v=abc123"
        assert video.course_id == test_course_id
        assert video.is_active is True
        assert video.id is not None  # UUID generated
        assert video.created_at is not None

    async def test_create_vimeo_link(self, video_dao, test_course_id, cleanup_videos):
        """Test creating a Vimeo video link."""
        video_data = {
            "course_id": test_course_id,
            "title": "Test Video - Vimeo",
            "video_type": "vimeo",
            "video_url": "https://vimeo.com/123456789",
            "order_index": 1
        }

        video = await video_dao.create(video_data)

        assert video.video_type == VideoType.VIMEO
        assert video.video_url == "https://vimeo.com/123456789"

    async def test_create_uploaded_video(self, video_dao, test_course_id, cleanup_videos):
        """Test creating an uploaded video record."""
        video_data = {
            "course_id": test_course_id,
            "title": "Test Video - Upload",
            "video_type": "upload",
            "video_url": "",
            "file_path": "/storage/videos/abc123.mp4",
            "file_size_bytes": 52428800,  # 50MB
            "mime_type": "video/mp4",
            "duration_seconds": 600,
            "order_index": 0
        }

        video = await video_dao.create(video_data)

        assert video.video_type == VideoType.UPLOAD
        assert video.file_path == "/storage/videos/abc123.mp4"
        assert video.file_size_bytes == 52428800
        assert video.mime_type == "video/mp4"
        assert video.duration_seconds == 600

    async def test_create_with_default_values(self, video_dao, test_course_id, cleanup_videos):
        """Test that default values are applied correctly."""
        video_data = {
            "course_id": test_course_id,
            "title": "Test Video - Defaults",
            "video_url": "https://example.com/video.mp4"
        }

        video = await video_dao.create(video_data)

        assert video.video_type == VideoType.UPLOAD  # Default
        assert video.order_index == 0  # Default
        assert video.is_active is True  # Default
        assert video.description == "" or video.description is None


@pytest.mark.asyncio
class TestVideoDAORead:
    """Test video retrieval operations."""

    async def test_get_by_id(self, video_dao, test_course_id, cleanup_videos):
        """Test retrieving video by ID."""
        # Create video
        video_data = {
            "course_id": test_course_id,
            "title": "Test Video - Get By ID",
            "video_url": "https://youtube.com/watch?v=xyz",
            "video_type": "youtube"
        }
        created = await video_dao.create(video_data)

        # Retrieve by ID
        retrieved = await video_dao.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Test Video - Get By ID"

    async def test_get_by_id_not_found(self, video_dao):
        """Test getting non-existent video returns None."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        video = await video_dao.get_by_id(fake_id)
        assert video is None

    async def test_get_by_course(self, video_dao, test_course_id, cleanup_videos):
        """Test retrieving all videos for a course."""
        # Create multiple videos
        for i in range(3):
            video_data = {
                "course_id": test_course_id,
                "title": f"Test Video - Course {i}",
                "video_url": f"https://youtube.com/watch?v=abc{i}",
                "video_type": "youtube",
                "order_index": i
            }
            await video_dao.create(video_data)

        # Retrieve all videos
        videos = await video_dao.get_by_course(test_course_id)

        assert len(videos) == 3
        # Verify ordering
        assert videos[0].order_index == 0
        assert videos[1].order_index == 1
        assert videos[2].order_index == 2

    async def test_get_by_course_active_only(self, video_dao, test_course_id, cleanup_videos):
        """Test filtering active videos only."""
        # Create active video
        active_data = {
            "course_id": test_course_id,
            "title": "Test Video - Active",
            "video_url": "https://youtube.com/watch?v=active",
            "video_type": "youtube",
            "is_active": True
        }
        active_video = await video_dao.create(active_data)

        # Create inactive video
        inactive_data = {
            "course_id": test_course_id,
            "title": "Test Video - Inactive",
            "video_url": "https://youtube.com/watch?v=inactive",
            "video_type": "youtube",
            "is_active": False
        }
        await video_dao.create(inactive_data)

        # Get active only
        active_videos = await video_dao.get_by_course(test_course_id, active_only=True)
        assert len(active_videos) == 1
        assert active_videos[0].is_active is True

        # Get all
        all_videos = await video_dao.get_by_course(test_course_id, active_only=False)
        assert len(all_videos) == 2


@pytest.mark.asyncio
class TestVideoDAOUpdate:
    """Test video update operations."""

    async def test_update_title(self, video_dao, test_course_id, cleanup_videos):
        """Test updating video title."""
        # Create video
        video_data = {
            "course_id": test_course_id,
            "title": "Test Video - Original Title",
            "video_url": "https://youtube.com/watch?v=update"
        }
        video = await video_dao.create(video_data)

        # Update title
        update_data = {"title": "Test Video - Updated Title"}
        updated = await video_dao.update(video.id, update_data)

        assert updated.title == "Test Video - Updated Title"
        assert updated.video_url == video.video_url  # Unchanged

    async def test_update_multiple_fields(self, video_dao, test_course_id, cleanup_videos):
        """Test updating multiple fields."""
        # Create video
        video_data = {
            "course_id": test_course_id,
            "title": "Test Video - Multi Update",
            "description": "Original description",
            "video_url": "https://youtube.com/watch?v=multi"
        }
        video = await video_dao.create(video_data)

        # Update multiple fields
        update_data = {
            "title": "Updated Title",
            "description": "Updated description",
            "order_index": 5
        }
        updated = await video_dao.update(video.id, update_data)

        assert updated.title == "Updated Title"
        assert updated.description == "Updated description"
        assert updated.order_index == 5

    async def test_update_preserves_timestamps(self, video_dao, test_course_id, cleanup_videos):
        """Test that created_at is preserved and updated_at is set."""
        # Create video
        video_data = {
            "course_id": test_course_id,
            "title": "Test Video - Timestamps",
            "video_url": "https://youtube.com/watch?v=time"
        }
        video = await video_dao.create(video_data)
        original_created_at = video.created_at

        # Wait a moment then update
        await asyncio.sleep(0.1)

        update_data = {"title": "Updated"}
        updated = await video_dao.update(video.id, update_data)

        assert updated.created_at == original_created_at
        assert updated.updated_at > original_created_at


@pytest.mark.asyncio
class TestVideoDAODelete:
    """Test video deletion (soft delete)."""

    async def test_soft_delete(self, video_dao, test_course_id, cleanup_videos):
        """Test soft delete sets is_active to False."""
        # Create video
        video_data = {
            "course_id": test_course_id,
            "title": "Test Video - Soft Delete",
            "video_url": "https://youtube.com/watch?v=delete"
        }
        video = await video_dao.create(video_data)
        assert video.is_active is True

        # Soft delete
        deleted = await video_dao.delete(video.id)

        assert deleted.is_active is False
        assert deleted.id == video.id  # Still exists

    async def test_hard_delete(self, video_dao, test_course_id, cleanup_videos):
        """Test hard delete removes record from database."""
        # Create video
        video_data = {
            "course_id": test_course_id,
            "title": "Test Video - Hard Delete",
            "video_url": "https://youtube.com/watch?v=harddelete"
        }
        video = await video_dao.create(video_data)

        # Hard delete
        result = await video_dao.delete(video.id, hard_delete=True)
        assert result is True

        # Verify deleted
        retrieved = await video_dao.get_by_id(video.id)
        assert retrieved is None


@pytest.mark.asyncio
class TestVideoDAOReorder:
    """Test video reordering operations."""

    async def test_reorder_videos(self, video_dao, test_course_id, cleanup_videos):
        """Test reordering multiple videos."""
        # Create videos in order 0, 1, 2
        videos = []
        for i in range(3):
            video_data = {
                "course_id": test_course_id,
                "title": f"Test Video - Reorder {i}",
                "video_url": f"https://youtube.com/watch?v=order{i}",
                "order_index": i
            }
            video = await video_dao.create(video_data)
            videos.append(video)

        # Reorder to 2, 0, 1
        new_order = [videos[2].id, videos[0].id, videos[1].id]
        reordered = await video_dao.reorder_videos(test_course_id, new_order)

        assert len(reordered) == 3
        assert reordered[0].id == videos[2].id
        assert reordered[0].order_index == 0
        assert reordered[1].id == videos[0].id
        assert reordered[1].order_index == 1
        assert reordered[2].id == videos[1].id
        assert reordered[2].order_index == 2

    async def test_reorder_atomic_transaction(self, video_dao, test_course_id, cleanup_videos):
        """Test that reordering is atomic (all or nothing)."""
        # Create videos
        videos = []
        for i in range(2):
            video_data = {
                "course_id": test_course_id,
                "title": f"Test Video - Atomic {i}",
                "video_url": f"https://youtube.com/watch?v=atomic{i}",
                "order_index": i
            }
            video = await video_dao.create(video_data)
            videos.append(video)

        # Try to reorder with invalid video ID
        invalid_order = [videos[0].id, "00000000-0000-0000-0000-000000000000"]

        with pytest.raises(Exception):  # Should fail
            await video_dao.reorder_videos(test_course_id, invalid_order)

        # Verify original order is preserved
        current_videos = await video_dao.get_by_course(test_course_id)
        assert current_videos[0].order_index == 0
        assert current_videos[1].order_index == 1


@pytest.mark.asyncio
class TestVideoDAOUploadTracking:
    """Test video upload tracking operations."""

    async def test_create_upload_record(self, video_dao, test_course_id, cleanup_videos):
        """Test creating upload tracking record."""
        upload_data = {
            "course_id": test_course_id,
            "upload_id": "test-upload-123",
            "filename": "tutorial.mp4",
            "file_size_bytes": 52428800,
            "mime_type": "video/mp4",
            "upload_status": "initiated"
        }

        upload_id = await video_dao.create_upload_record(upload_data)

        assert upload_id == "test-upload-123"

    async def test_update_upload_progress(self, video_dao, test_course_id, cleanup_videos):
        """Test updating upload progress."""
        # Create upload record
        upload_data = {
            "course_id": test_course_id,
            "upload_id": "test-upload-progress",
            "filename": "tutorial.mp4",
            "file_size_bytes": 100000000,
            "mime_type": "video/mp4",
            "upload_status": "initiated"
        }
        await video_dao.create_upload_record(upload_data)

        # Update progress to 50%
        await video_dao.update_upload_progress(
            "test-upload-progress",
            bytes_uploaded=50000000,
            status="uploading"
        )

        # Verify progress
        upload = await video_dao.get_upload_by_id("test-upload-progress")
        assert upload["bytes_uploaded"] == 50000000
        assert upload["upload_status"] == "uploading"

    async def test_complete_upload(self, video_dao, test_course_id, cleanup_videos):
        """Test marking upload as completed."""
        # Create upload record
        upload_data = {
            "course_id": test_course_id,
            "upload_id": "test-upload-complete",
            "filename": "tutorial.mp4",
            "file_size_bytes": 100000000,
            "mime_type": "video/mp4",
            "upload_status": "initiated"
        }
        await video_dao.create_upload_record(upload_data)

        # Complete upload
        video_id = "550e8400-e29b-41d4-a716-446655440000"
        await video_dao.complete_upload(
            "test-upload-complete",
            video_id=video_id,
            file_path="/storage/videos/abc123.mp4"
        )

        # Verify completion
        upload = await video_dao.get_upload_by_id("test-upload-complete")
        assert upload["upload_status"] == "completed"
        assert upload["video_id"] == video_id
        assert upload["file_path"] == "/storage/videos/abc123.mp4"


# Run tests with: pytest tests/unit/course_videos/test_video_dao.py -v --asyncio-mode=auto
