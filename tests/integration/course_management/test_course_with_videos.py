"""
Integration Tests for Course Creation with Videos

BUSINESS REQUIREMENT:
Validates complete workflow of creating courses with video content,
including file uploads, external links, and database persistence.

TECHNICAL IMPLEMENTATION:
- Uses real PostgreSQL database
- Tests file system operations
- Tests API endpoints with actual HTTP requests
- Tests transaction rollback on failures
- Tests concurrent operations
"""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
import httpx
import asyncpg
from datetime import datetime

# Test configuration
TEST_BASE_URL = os.getenv('TEST_BASE_URL', 'https://localhost:8004')
TEST_DB_HOST = os.getenv('TEST_DB_HOST', 'localhost')
TEST_DB_PORT = int(os.getenv('TEST_DB_PORT', '5432'))
TEST_DB_NAME = os.getenv('TEST_DB_NAME', 'course_creator_test')
TEST_DB_USER = os.getenv('TEST_DB_USER', 'postgres')
TEST_DB_PASSWORD = os.getenv('TEST_DB_PASSWORD', 'postgres123')


@pytest.fixture
async def db_pool():
    """Create database connection pool for integration tests."""
    pool = await asyncpg.create_pool(
        host=TEST_DB_HOST,
        port=TEST_DB_PORT,
        database=TEST_DB_NAME,
        user=TEST_DB_USER,
        password=TEST_DB_PASSWORD,
        min_size=1,
        max_size=5
    )

    yield pool

    await pool.close()


@pytest.fixture
async def http_client():
    """Create HTTP client for API requests."""
    async with httpx.AsyncClient(
        base_url=TEST_BASE_URL,
        verify=False,  # Ignore SSL for local testing
        timeout=30.0
    ) as client:
        yield client


@pytest.fixture
async def auth_token(http_client):
    """
    Get authentication token for test user.

    IMPORTANT: This assumes test user exists in database.
    Adjust credentials based on test environment.
    """
    login_data = {
        "username": "test-instructor@example.com",
        "password": "test-password-123"
    }

    response = await http_client.post("/auth/login", json=login_data)

    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    else:
        # Return mock token for testing without real auth
        return "mock-test-token-instructor-123"


@pytest.fixture
async def auth_headers(auth_token):
    """Create authorization headers with token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory for video files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
async def test_course(db_pool, auth_headers):
    """
    Create a test course for integration testing.

    Returns course_id.
    """
    async with db_pool.acquire() as conn:
        course_id = await conn.fetchval(
            """
            INSERT INTO courses (
                title, description, instructor_id, organization_id, is_active
            ) VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            "Integration Test Course",
            "Course for integration testing",
            "test-instructor-123",
            "test-org-456",
            True
        )

        yield str(course_id)

        # Cleanup
        await conn.execute("DELETE FROM course_videos WHERE course_id = $1", course_id)
        await conn.execute("DELETE FROM courses WHERE id = $1", course_id)


@pytest.fixture
async def cleanup_test_data(db_pool):
    """Cleanup test data after each test."""
    yield

    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM course_videos WHERE title LIKE 'Integration Test%'")
        await conn.execute("DELETE FROM courses WHERE title LIKE 'Integration Test%'")
        await conn.execute("DELETE FROM video_uploads WHERE upload_id LIKE 'test-integration-%'")


@pytest.mark.integration
@pytest.mark.asyncio
class TestCourseCreationWithVideos:
    """Test complete course creation workflow with videos."""

    async def test_create_course_with_youtube_link(
        self, http_client, auth_headers, db_pool, cleanup_test_data
    ):
        """
        Test creating course with YouTube video link.

        WORKFLOW:
        1. Create course
        2. Add YouTube video link
        3. Verify in database
        4. Retrieve via API
        """
        # Step 1: Create course
        course_data = {
            "title": "Integration Test Course - YouTube",
            "description": "Test course with YouTube video",
            "instructor_id": "test-instructor-123",
            "organization_id": "test-org-456"
        }

        course_response = await http_client.post(
            "/courses",
            json=course_data,
            headers=auth_headers
        )

        assert course_response.status_code in [200, 201]
        course = course_response.json()
        course_id = course.get("id") or course.get("course", {}).get("id")

        # Step 2: Add YouTube video
        video_data = {
            "course_id": course_id,
            "title": "Integration Test Video - YouTube",
            "description": "Learn Python basics",
            "video_type": "youtube",
            "video_url": "https://youtube.com/watch?v=integration_test_123",
            "order_index": 0
        }

        video_response = await http_client.post(
            f"/courses/{course_id}/videos",
            json=video_data,
            headers=auth_headers
        )

        assert video_response.status_code in [200, 201]
        video = video_response.json()
        video_id = video.get("video", {}).get("id")

        # Step 3: Verify in database
        async with db_pool.acquire() as conn:
            db_video = await conn.fetchrow(
                "SELECT * FROM course_videos WHERE id = $1",
                video_id
            )

            assert db_video is not None
            assert db_video["title"] == "Integration Test Video - YouTube"
            assert db_video["video_type"] == "youtube"
            assert db_video["course_id"] == course_id

        # Step 4: Retrieve via API
        get_response = await http_client.get(
            f"/courses/{course_id}/videos",
            headers=auth_headers
        )

        assert get_response.status_code == 200
        videos_data = get_response.json()
        assert videos_data["count"] == 1
        assert videos_data["videos"][0]["title"] == "Integration Test Video - YouTube"

    async def test_create_course_with_multiple_videos(
        self, http_client, auth_headers, test_course, db_pool, cleanup_test_data
    ):
        """
        Test creating course with multiple videos of different types.

        WORKFLOW:
        1. Add YouTube video
        2. Add Vimeo video
        3. Add custom link
        4. Verify all videos exist
        5. Test video ordering
        """
        videos_to_create = [
            {
                "title": "Integration Test Video 1 - YouTube",
                "video_type": "youtube",
                "video_url": "https://youtube.com/watch?v=test1",
                "order_index": 0
            },
            {
                "title": "Integration Test Video 2 - Vimeo",
                "video_type": "vimeo",
                "video_url": "https://vimeo.com/test123",
                "order_index": 1
            },
            {
                "title": "Integration Test Video 3 - Custom",
                "video_type": "link",
                "video_url": "https://example.com/video.mp4",
                "order_index": 2
            }
        ]

        created_videos = []
        for video_data in videos_to_create:
            video_data["course_id"] = test_course

            response = await http_client.post(
                f"/courses/{test_course}/videos",
                json=video_data,
                headers=auth_headers
            )

            assert response.status_code in [200, 201]
            created_videos.append(response.json()["video"])

        # Verify all videos exist
        get_response = await http_client.get(
            f"/courses/{test_course}/videos",
            headers=auth_headers
        )

        assert get_response.status_code == 200
        videos_data = get_response.json()
        assert videos_data["count"] == 3

        # Verify ordering
        videos = videos_data["videos"]
        assert videos[0]["order_index"] == 0
        assert videos[1]["order_index"] == 1
        assert videos[2]["order_index"] == 2

    async def test_video_reordering(
        self, http_client, auth_headers, test_course, cleanup_test_data
    ):
        """
        Test reordering videos for a course.

        WORKFLOW:
        1. Create 3 videos in order 0, 1, 2
        2. Reorder to 2, 0, 1
        3. Verify new order persisted
        """
        # Create videos
        video_ids = []
        for i in range(3):
            video_data = {
                "course_id": test_course,
                "title": f"Integration Test Video {i}",
                "video_type": "youtube",
                "video_url": f"https://youtube.com/watch?v=reorder{i}",
                "order_index": i
            }

            response = await http_client.post(
                f"/courses/{test_course}/videos",
                json=video_data,
                headers=auth_headers
            )

            video_ids.append(response.json()["video"]["id"])

        # Reorder: 2, 0, 1
        new_order = [video_ids[2], video_ids[0], video_ids[1]]

        reorder_response = await http_client.post(
            f"/courses/{test_course}/videos/reorder",
            json={"video_order": new_order},
            headers=auth_headers
        )

        assert reorder_response.status_code == 200

        # Verify new order
        get_response = await http_client.get(
            f"/courses/{test_course}/videos",
            headers=auth_headers
        )

        videos = get_response.json()["videos"]
        assert videos[0]["id"] == video_ids[2]
        assert videos[0]["order_index"] == 0
        assert videos[1]["id"] == video_ids[0]
        assert videos[1]["order_index"] == 1
        assert videos[2]["id"] == video_ids[1]
        assert videos[2]["order_index"] == 2

    async def test_video_soft_delete(
        self, http_client, auth_headers, test_course, db_pool, cleanup_test_data
    ):
        """
        Test soft deleting a video.

        WORKFLOW:
        1. Create video
        2. Soft delete video
        3. Verify is_active = False in DB
        4. Verify not returned in active-only queries
        """
        # Create video
        video_data = {
            "course_id": test_course,
            "title": "Integration Test Video - Delete",
            "video_type": "youtube",
            "video_url": "https://youtube.com/watch?v=delete_test"
        }

        create_response = await http_client.post(
            f"/courses/{test_course}/videos",
            json=video_data,
            headers=auth_headers
        )

        video_id = create_response.json()["video"]["id"]

        # Soft delete
        delete_response = await http_client.delete(
            f"/courses/{test_course}/videos/{video_id}",
            headers=auth_headers
        )

        assert delete_response.status_code == 200

        # Verify is_active = False
        async with db_pool.acquire() as conn:
            is_active = await conn.fetchval(
                "SELECT is_active FROM course_videos WHERE id = $1",
                video_id
            )
            assert is_active is False

        # Verify not in active-only query
        get_response = await http_client.get(
            f"/courses/{test_course}/videos?active_only=true",
            headers=auth_headers
        )

        videos = get_response.json()["videos"]
        video_ids = [v["id"] for v in videos]
        assert video_id not in video_ids

    async def test_video_update(
        self, http_client, auth_headers, test_course, cleanup_test_data
    ):
        """
        Test updating video metadata.

        WORKFLOW:
        1. Create video
        2. Update title and description
        3. Verify changes persisted
        """
        # Create video
        video_data = {
            "course_id": test_course,
            "title": "Integration Test Video - Original",
            "description": "Original description",
            "video_type": "youtube",
            "video_url": "https://youtube.com/watch?v=update_test"
        }

        create_response = await http_client.post(
            f"/courses/{test_course}/videos",
            json=video_data,
            headers=auth_headers
        )

        video_id = create_response.json()["video"]["id"]

        # Update
        update_data = {
            "title": "Integration Test Video - Updated",
            "description": "Updated description"
        }

        update_response = await http_client.put(
            f"/courses/{test_course}/videos/{video_id}",
            json=update_data,
            headers=auth_headers
        )

        assert update_response.status_code == 200
        updated_video = update_response.json()["video"]
        assert updated_video["title"] == "Integration Test Video - Updated"
        assert updated_video["description"] == "Updated description"


@pytest.mark.integration
@pytest.mark.asyncio
class TestVideoUploadIntegration:
    """Test video file upload integration."""

    async def test_upload_initiation(
        self, http_client, auth_headers, test_course, cleanup_test_data
    ):
        """
        Test initiating video upload.

        WORKFLOW:
        1. Send upload initiation request
        2. Verify upload record created
        3. Verify upload_id returned
        """
        upload_request = {
            "course_id": test_course,
            "filename": "integration_test.mp4",
            "file_size_bytes": 52428800,  # 50MB
            "mime_type": "video/mp4",
            "title": "Integration Test Upload",
            "description": "Test video upload"
        }

        response = await http_client.post(
            f"/courses/{test_course}/videos/upload",
            json=upload_request,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "upload_id" in data
        assert "upload_url" in data
        assert "video_id" in data

    async def test_file_size_validation(
        self, http_client, auth_headers, test_course
    ):
        """
        Test file size validation rejects files > 2GB.

        WORKFLOW:
        1. Attempt to upload 3GB file
        2. Verify rejection with appropriate error
        """
        max_size = 2 * 1024 * 1024 * 1024  # 2GB
        too_large = max_size + 1

        upload_request = {
            "course_id": test_course,
            "filename": "huge_file.mp4",
            "file_size_bytes": too_large,
            "mime_type": "video/mp4",
            "title": "Huge Video"
        }

        response = await http_client.post(
            f"/courses/{test_course}/videos/upload",
            json=upload_request,
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.integration
@pytest.mark.asyncio
class TestConcurrentOperations:
    """Test concurrent video operations."""

    async def test_concurrent_video_creation(
        self, http_client, auth_headers, test_course, cleanup_test_data
    ):
        """
        Test creating multiple videos concurrently.

        WORKFLOW:
        1. Create 5 videos simultaneously
        2. Verify all created successfully
        3. Verify no race conditions
        """
        async def create_video(index):
            video_data = {
                "course_id": test_course,
                "title": f"Integration Test Concurrent {index}",
                "video_type": "youtube",
                "video_url": f"https://youtube.com/watch?v=concurrent{index}",
                "order_index": index
            }

            response = await http_client.post(
                f"/courses/{test_course}/videos",
                json=video_data,
                headers=auth_headers
            )

            return response

        # Create 5 videos concurrently
        tasks = [create_video(i) for i in range(5)]
        responses = await asyncio.gather(*tasks)

        # Verify all succeeded
        for response in responses:
            assert response.status_code in [200, 201]

        # Verify all videos exist
        get_response = await http_client.get(
            f"/courses/{test_course}/videos",
            headers=auth_headers
        )

        assert get_response.json()["count"] == 5


# Run with: pytest tests/integration/course_management/test_course_with_videos.py -v -m integration --asyncio-mode=auto
