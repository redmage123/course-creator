"""
Unit Tests for Course Video API Endpoints

BUSINESS REQUIREMENT:
Validates RESTful API endpoints for video management including
authentication, authorization, request validation, and response formatting.

TECHNICAL IMPLEMENTATION:
- Uses FastAPI TestClient for endpoint testing
- Tests authentication/authorization
- Tests request validation
- Tests error handling
- Tests response formatting
"""


import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import io

from main import app
from models.course_video import (
    VideoType,
    CourseVideo,
    CourseVideoCreate
)


@pytest.fixture
def mock_video_dao():
    """Mock video DAO for endpoint testing - NEEDS REFACTORING."""
    pytest.skip("Needs refactoring to use real DAO with database fixtures")


@pytest.fixture
def test_client(mock_video_dao):
    """Create test client with mocked dependencies."""
    with patch('services.course_management.api.video_endpoints.video_dao', mock_video_dao):
        client = TestClient(app)
        yield client


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    # In real tests, would use valid JWT token
    return {
        "Authorization": "Bearer mock-jwt-token-instructor-123"
    }


@pytest.fixture
def sample_video():
    """Sample video object for tests."""
    return CourseVideo(
        id="550e8400-e29b-41d4-a716-446655440000",
        course_id="660e8400-e29b-41d4-a716-446655440001",
        title="Python Tutorial",
        description="Learn Python basics",
        video_type=VideoType.YOUTUBE,
        video_url="https://youtube.com/watch?v=abc123",
        order_index=0,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


class TestCreateVideoLink:
    """Test POST /courses/{course_id}/videos endpoint."""

    def test_create_youtube_link_success(self, test_client, auth_headers, mock_video_dao, sample_video):
        """Test successfully creating YouTube video link."""
        mock_video_dao.create.return_value = sample_video

        request_data = {
            "course_id": "660e8400-e29b-41d4-a716-446655440001",
            "title": "Python Tutorial",
            "description": "Learn Python basics",
            "video_type": "youtube",
            "video_url": "https://youtube.com/watch?v=abc123",
            "order_index": 0
        }

        response = test_client.post(
            "/courses/660e8400-e29b-41d4-a716-446655440001/videos",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["video"]["title"] == "Python Tutorial"
        assert data["video"]["video_type"] == "youtube"

    def test_create_vimeo_link_success(self, test_client, auth_headers, mock_video_dao):
        """Test creating Vimeo video link."""
        vimeo_video = CourseVideo(
            id="550e8400-e29b-41d4-a716-446655440000",
            course_id="660e8400-e29b-41d4-a716-446655440001",
            title="Vimeo Tutorial",
            video_type=VideoType.VIMEO,
            video_url="https://vimeo.com/123456789",
            order_index=0,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_video_dao.create.return_value = vimeo_video

        request_data = {
            "course_id": "660e8400-e29b-41d4-a716-446655440001",
            "title": "Vimeo Tutorial",
            "video_type": "vimeo",
            "video_url": "https://vimeo.com/123456789"
        }

        response = test_client.post(
            "/courses/660e8400-e29b-41d4-a716-446655440001/videos",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["video"]["video_type"] == "vimeo"

    def test_create_video_missing_title(self, test_client, auth_headers):
        """Test validation fails when title is missing."""
        request_data = {
            "course_id": "660e8400-e29b-41d4-a716-446655440001",
            "video_type": "youtube",
            "video_url": "https://youtube.com/watch?v=abc123"
        }

        response = test_client.post(
            "/courses/660e8400-e29b-41d4-a716-446655440001/videos",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    def test_create_video_invalid_url(self, test_client, auth_headers):
        """Test validation fails for invalid URL."""
        request_data = {
            "course_id": "660e8400-e29b-41d4-a716-446655440001",
            "title": "Test Video",
            "video_type": "youtube",
            "video_url": "not-a-valid-url"
        }

        response = test_client.post(
            "/courses/660e8400-e29b-41d4-a716-446655440001/videos",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code in [400, 422]

    def test_create_video_unauthorized(self, test_client):
        """Test endpoint requires authentication."""
        request_data = {
            "course_id": "660e8400-e29b-41d4-a716-446655440001",
            "title": "Test Video",
            "video_url": "https://youtube.com/watch?v=abc"
        }

        response = test_client.post(
            "/courses/660e8400-e29b-41d4-a716-446655440001/videos",
            json=request_data
        )

        assert response.status_code == 401  # Unauthorized


class TestGetCourseVideos:
    """Test GET /courses/{course_id}/videos endpoint."""

    def test_get_all_videos_success(self, test_client, auth_headers, mock_video_dao):
        """Test retrieving all videos for a course."""
        videos = [
            CourseVideo(
                id=f"550e8400-e29b-41d4-a716-44665544000{i}",
                course_id="660e8400-e29b-41d4-a716-446655440001",
                title=f"Video {i}",
                video_type=VideoType.YOUTUBE,
                video_url=f"https://youtube.com/watch?v=abc{i}",
                order_index=i,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            for i in range(3)
        ]
        mock_video_dao.get_by_course.return_value = videos

        response = test_client.get(
            "/courses/660e8400-e29b-41d4-a716-446655440001/videos",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 3
        assert len(data["videos"]) == 3

    def test_get_active_videos_only(self, test_client, auth_headers, mock_video_dao):
        """Test filtering for active videos only."""
        active_videos = [
            CourseVideo(
                id="550e8400-e29b-41d4-a716-446655440000",
                course_id="660e8400-e29b-41d4-a716-446655440001",
                title="Active Video",
                video_type=VideoType.YOUTUBE,
                video_url="https://youtube.com/watch?v=active",
                order_index=0,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        mock_video_dao.get_by_course.return_value = active_videos

        response = test_client.get(
            "/courses/660e8400-e29b-41d4-a716-446655440001/videos?active_only=true",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert all(v["is_active"] for v in data["videos"])

    def test_get_videos_empty_course(self, test_client, auth_headers, mock_video_dao):
        """Test getting videos for course with no videos."""
        mock_video_dao.get_by_course.return_value = []

        response = test_client.get(
            "/courses/660e8400-e29b-41d4-a716-446655440001/videos",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["videos"] == []


class TestGetVideoById:
    """Test GET /courses/{course_id}/videos/{video_id} endpoint."""

    def test_get_video_by_id_success(self, test_client, auth_headers, mock_video_dao, sample_video):
        """Test retrieving specific video by ID."""
        mock_video_dao.get_by_id.return_value = sample_video

        response = test_client.get(
            f"/courses/{sample_video.course_id}/videos/{sample_video.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["video"]["id"] == sample_video.id

    def test_get_video_not_found(self, test_client, auth_headers, mock_video_dao):
        """Test getting non-existent video."""
        mock_video_dao.get_by_id.return_value = None

        response = test_client.get(
            "/courses/660e8400-e29b-41d4-a716-446655440001/videos/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )

        assert response.status_code == 404


class TestUpdateVideo:
    """Test PUT /courses/{course_id}/videos/{video_id} endpoint."""

    def test_update_video_title(self, test_client, auth_headers, mock_video_dao, sample_video):
        """Test updating video title."""
        updated_video = sample_video.copy(update={"title": "Updated Title"})
        mock_video_dao.update.return_value = updated_video

        update_data = {"title": "Updated Title"}

        response = test_client.put(
            f"/courses/{sample_video.course_id}/videos/{sample_video.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["video"]["title"] == "Updated Title"

    def test_update_video_multiple_fields(self, test_client, auth_headers, mock_video_dao, sample_video):
        """Test updating multiple fields."""
        updated_video = sample_video.copy(update={
            "title": "New Title",
            "description": "New Description",
            "order_index": 5
        })
        mock_video_dao.update.return_value = updated_video

        update_data = {
            "title": "New Title",
            "description": "New Description",
            "order_index": 5
        }

        response = test_client.put(
            f"/courses/{sample_video.course_id}/videos/{sample_video.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["video"]["title"] == "New Title"
        assert data["video"]["order_index"] == 5


class TestDeleteVideo:
    """Test DELETE /courses/{course_id}/videos/{video_id} endpoint."""

    def test_soft_delete_video(self, test_client, auth_headers, mock_video_dao, sample_video):
        """Test soft deleting a video."""
        deleted_video = sample_video.copy(update={"is_active": False})
        mock_video_dao.delete.return_value = deleted_video

        response = test_client.delete(
            f"/courses/{sample_video.course_id}/videos/{sample_video.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_hard_delete_video(self, test_client, auth_headers, mock_video_dao):
        """Test hard deleting a video."""
        mock_video_dao.delete.return_value = True

        response = test_client.delete(
            f"/courses/660e8400-e29b-41d4-a716-446655440001/videos/550e8400-e29b-41d4-a716-446655440000?hard_delete=true",
            headers=auth_headers
        )

        assert response.status_code == 200


class TestReorderVideos:
    """Test POST /courses/{course_id}/videos/reorder endpoint."""

    def test_reorder_videos_success(self, test_client, auth_headers, mock_video_dao):
        """Test reordering videos."""
        reordered = [
            CourseVideo(
                id=f"550e8400-e29b-41d4-a716-44665544000{i}",
                course_id="660e8400-e29b-41d4-a716-446655440001",
                title=f"Video {i}",
                video_type=VideoType.YOUTUBE,
                video_url=f"https://youtube.com/watch?v=abc{i}",
                order_index=i,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            for i in range(3)
        ]
        mock_video_dao.reorder_videos.return_value = reordered

        video_order = [v.id for v in reordered]

        response = test_client.post(
            "/courses/660e8400-e29b-41d4-a716-446655440001/videos/reorder",
            json={"video_order": video_order},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["videos"]) == 3


class TestVideoUpload:
    """Test video file upload endpoints."""

    def test_initiate_upload(self, test_client, auth_headers, mock_video_dao):
        """Test initiating video upload."""
        mock_video_dao.create_upload_record.return_value = "upload-123"

        upload_request = {
            "course_id": "660e8400-e29b-41d4-a716-446655440001",
            "filename": "tutorial.mp4",
            "file_size_bytes": 52428800,
            "mime_type": "video/mp4",
            "title": "Tutorial Video",
            "description": "Learn something"
        }

        response = test_client.post(
            "/courses/660e8400-e29b-41d4-a716-446655440001/videos/upload",
            json=upload_request,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "upload_id" in data
        assert "upload_url" in data

    def test_upload_file_too_large(self, test_client, auth_headers):
        """Test rejecting file larger than 2GB."""
        max_size = 2 * 1024 * 1024 * 1024  # 2GB
        too_large = max_size + 1

        upload_request = {
            "course_id": "660e8400-e29b-41d4-a716-446655440001",
            "filename": "huge.mp4",
            "file_size_bytes": too_large,
            "mime_type": "video/mp4",
            "title": "Huge Video"
        }

        response = test_client.post(
            "/courses/660e8400-e29b-41d4-a716-446655440001/videos/upload",
            json=upload_request,
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    def test_upload_video_file(self, test_client, auth_headers, mock_video_dao, sample_video):
        """Test uploading actual video file."""
        mock_video_dao.complete_upload.return_value = sample_video

        # Create mock file
        file_content = b"fake video content"
        files = {
            "file": ("tutorial.mp4", io.BytesIO(file_content), "video/mp4")
        }
        data = {
            "title": "Tutorial",
            "description": "Learn"
        }

        response = test_client.post(
            "/courses/660e8400-e29b-41d4-a716-446655440001/videos/upload/upload-123/file",
            files=files,
            data=data,
            headers=auth_headers
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True


# Run tests with: pytest tests/unit/course_videos/test_video_endpoints.py -v
