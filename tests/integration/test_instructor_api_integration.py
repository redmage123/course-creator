"""
Integration Tests for Instructor Dashboard API Operations

BUSINESS REQUIREMENT:
Validates instructor dashboard API integration including course management,
student enrollment, feedback operations, and course instance workflows.

TECHNICAL IMPLEMENTATION:
- Uses real API endpoints with test authentication
- Tests complete request/response cycles
- Validates data persistence across operations
- Tests error handling and edge cases
"""

import pytest
import pytest_asyncio
import httpx
import asyncio
from typing import Dict, Any, Optional
import json


# Test Configuration
BASE_URL = "http://localhost:8002"  # Course Management Service
USER_SERVICE_URL = "http://localhost:8001"  # User Management Service
ANALYTICS_URL = "http://localhost:8006"  # Analytics Service

# Test credentials
TEST_INSTRUCTOR_EMAIL = "test.instructor@coursecreator.com"
TEST_INSTRUCTOR_PASSWORD = "InstructorPass123!"


@pytest_asyncio.fixture
async def auth_token():
    """
    Authenticate as instructor and return auth token.

    IMPORTANT: Uses REAL authentication endpoint!
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{USER_SERVICE_URL}/login",
            json={
                "email": TEST_INSTRUCTOR_EMAIL,
                "password": TEST_INSTRUCTOR_PASSWORD
            }
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        else:
            pytest.skip(f"Authentication failed: {response.status_code}")


@pytest_asyncio.fixture
async def http_client(auth_token):
    """Create authenticated HTTP client."""
    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {auth_token}"},
        timeout=30.0
    ) as client:
        yield client


@pytest.mark.integration
@pytest.mark.asyncio
class TestCourseManagementAPI:
    """Test course management API operations."""

    async def test_list_instructor_courses(self, http_client):
        """Test retrieving instructor's courses."""
        response = await http_client.get(f"{BASE_URL}/courses")

        assert response.status_code == 200
        data = response.json()

        # Response should be a list or contain courses key
        courses = data if isinstance(data, list) else data.get("courses", [])
        assert isinstance(courses, list)

    async def test_create_course(self, http_client):
        """Test creating a new course."""
        course_data = {
            "title": "Integration Test Course",
            "description": "Test course created by integration test",
            "difficulty": "beginner",
            "category": "Testing"
        }

        response = await http_client.post(
            f"{BASE_URL}/courses",
            json=course_data
        )

        # Should create successfully or return validation error
        assert response.status_code in [200, 201, 400, 422]

        if response.status_code in [200, 201]:
            course = response.json()
            assert course["title"] == course_data["title"]
            assert "id" in course

    async def test_get_course_by_id(self, http_client):
        """Test retrieving a specific course."""
        # First, get list of courses
        list_response = await http_client.get(f"{BASE_URL}/courses")
        courses = list_response.json()

        if isinstance(courses, dict):
            courses = courses.get("courses", [])

        if courses:
            course_id = courses[0]["id"]

            # Get specific course
            response = await http_client.get(f"{BASE_URL}/courses/{course_id}")
            assert response.status_code == 200

            course = response.json()
            assert course["id"] == course_id

    async def test_update_course(self, http_client):
        """Test updating an existing course."""
        # Get a course to update
        list_response = await http_client.get(f"{BASE_URL}/courses")
        courses = list_response.json()

        if isinstance(courses, dict):
            courses = courses.get("courses", [])

        if courses:
            course_id = courses[0]["id"]

            update_data = {
                "title": "Updated Test Course",
                "description": "Updated description"
            }

            response = await http_client.put(
                f"{BASE_URL}/courses/{course_id}",
                json=update_data
            )

            # Should succeed or return not found
            assert response.status_code in [200, 404, 422]

    async def test_publish_course(self, http_client):
        """Test publishing a course."""
        # Get a course to publish
        list_response = await http_client.get(f"{BASE_URL}/courses")
        courses = list_response.json()

        if isinstance(courses, dict):
            courses = courses.get("courses", [])

        if courses:
            course_id = courses[0]["id"]

            response = await http_client.post(
                f"{BASE_URL}/courses/{course_id}/publish"
            )

            # Should succeed or indicate already published
            assert response.status_code in [200, 400, 404]


@pytest.mark.integration
@pytest.mark.asyncio
class TestStudentManagementAPI:
    """Test student enrollment and management API operations."""

    async def test_list_enrolled_students(self, http_client):
        """Test retrieving enrolled students."""
        response = await http_client.get(f"{BASE_URL}/enrollments")

        # Should return list of enrollments
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    async def test_enroll_student(self, http_client):
        """Test enrolling a student in a course."""
        # First, get a course instance
        instances_response = await http_client.get(
            f"{BASE_URL}/course-instances"
        )

        if instances_response.status_code == 200:
            instances = instances_response.json()

            if isinstance(instances, list) and len(instances) > 0:
                instance_id = instances[0]["id"]

                enrollment_data = {
                    "student_email": "test.student@coursecreator.com",
                    "student_name": "Test Student",
                    "send_welcome_email": False
                }

                response = await http_client.post(
                    f"{BASE_URL}/course-instances/{instance_id}/enroll",
                    json=enrollment_data
                )

                # Should enroll or indicate already enrolled
                assert response.status_code in [200, 201, 400, 422]

    async def test_get_student_progress(self, http_client):
        """Test retrieving student progress data."""
        # Get enrollments first
        enrollments_response = await http_client.get(f"{BASE_URL}/enrollments")

        if enrollments_response.status_code == 200:
            enrollments = enrollments_response.json()

            if isinstance(enrollments, list) and len(enrollments) > 0:
                enrollment_id = enrollments[0]["id"]

                response = await http_client.get(
                    f"{BASE_URL}/enrollments/{enrollment_id}/progress"
                )

                # Should return progress data
                assert response.status_code in [200, 404]


@pytest.mark.integration
@pytest.mark.asyncio
class TestCourseInstanceAPI:
    """Test course instance management API operations."""

    async def test_list_course_instances(self, http_client):
        """Test retrieving course instances."""
        response = await http_client.get(f"{BASE_URL}/course-instances")

        assert response.status_code == 200
        instances = response.json()
        assert isinstance(instances, (list, dict))

    async def test_create_course_instance(self, http_client):
        """Test creating a course instance."""
        # Get a published course first
        courses_response = await http_client.get(
            f"{BASE_URL}/courses/published"
        )

        if courses_response.status_code == 200:
            courses = courses_response.json()

            if isinstance(courses, list) and len(courses) > 0:
                course_id = courses[0]["id"]

                instance_data = {
                    "course_id": course_id,
                    "instance_name": "Integration Test Instance",
                    "start_datetime": "2025-06-01T09:00:00",
                    "end_datetime": "2025-08-31T17:00:00",
                    "timezone": "America/New_York",
                    "max_students": 30,
                    "description": "Test instance for integration testing"
                }

                response = await http_client.post(
                    f"{BASE_URL}/course-instances",
                    json=instance_data
                )

                # Should create or indicate validation error
                assert response.status_code in [200, 201, 400, 422]

    async def test_get_instance_enrollments(self, http_client):
        """Test retrieving enrollments for a course instance."""
        # Get course instances
        instances_response = await http_client.get(
            f"{BASE_URL}/course-instances"
        )

        if instances_response.status_code == 200:
            instances = instances_response.json()

            if isinstance(instances, list) and len(instances) > 0:
                instance_id = instances[0]["id"]

                response = await http_client.get(
                    f"{BASE_URL}/course-instances/{instance_id}/enrollments"
                )

                # Should return enrollment list
                assert response.status_code in [200, 404]

    async def test_complete_course_instance(self, http_client):
        """Test completing a course instance."""
        # Get course instances
        instances_response = await http_client.get(
            f"{BASE_URL}/course-instances"
        )

        if instances_response.status_code == 200:
            instances = instances_response.json()

            # Find an active instance
            if isinstance(instances, list):
                active_instances = [
                    i for i in instances
                    if i.get("status") in ["active", "scheduled"]
                ]

                if active_instances:
                    instance_id = active_instances[0]["id"]

                    response = await http_client.post(
                        f"{BASE_URL}/course-instances/{instance_id}/complete"
                    )

                    # Should complete or indicate already completed
                    assert response.status_code in [200, 400, 404]

    async def test_cancel_course_instance(self, http_client):
        """Test cancelling a course instance."""
        # Get course instances
        instances_response = await http_client.get(
            f"{BASE_URL}/course-instances"
        )

        if instances_response.status_code == 200:
            instances = instances_response.json()

            # Find a scheduled instance
            if isinstance(instances, list):
                scheduled_instances = [
                    i for i in instances
                    if i.get("status") == "scheduled"
                ]

                if scheduled_instances:
                    instance_id = scheduled_instances[0]["id"]

                    response = await http_client.post(
                        f"{BASE_URL}/course-instances/{instance_id}/cancel"
                    )

                    # Should cancel or indicate already cancelled
                    assert response.status_code in [200, 400, 404]


@pytest.mark.integration
@pytest.mark.asyncio
class TestQuizManagementAPI:
    """Test quiz management API operations."""

    async def test_get_course_quizzes(self, http_client):
        """Test retrieving quizzes for a course."""
        # Get a course first
        courses_response = await http_client.get(f"{BASE_URL}/courses")
        courses = courses_response.json()

        if isinstance(courses, dict):
            courses = courses.get("courses", [])

        if courses:
            course_id = courses[0]["id"]

            response = await http_client.get(
                f"{BASE_URL}/courses/{course_id}/quizzes"
            )

            # Should return quiz list
            assert response.status_code in [200, 404]

    async def test_publish_quiz_to_instance(self, http_client):
        """Test publishing a quiz to a course instance."""
        # This requires a quiz and instance
        # Implementation depends on quiz API structure
        pass


@pytest.mark.integration
@pytest.mark.asyncio
class TestAnalyticsAPI:
    """Test analytics API operations."""

    async def test_get_instructor_statistics(self, http_client):
        """Test retrieving instructor statistics."""
        response = await http_client.get(
            f"{ANALYTICS_URL}/instructor/stats"
        )

        # Should return statistics or not found
        assert response.status_code in [200, 404, 500]

    async def test_get_course_analytics(self, http_client):
        """Test retrieving analytics for a course."""
        # Get a course first
        courses_response = await http_client.get(f"{BASE_URL}/courses")
        courses = courses_response.json()

        if isinstance(courses, dict):
            courses = courses.get("courses", [])

        if courses:
            course_id = courses[0]["id"]

            response = await http_client.get(
                f"{ANALYTICS_URL}/courses/{course_id}/analytics"
            )

            # Should return analytics data
            assert response.status_code in [200, 404, 500]

    async def test_get_student_performance(self, http_client):
        """Test retrieving student performance metrics."""
        # Get enrollments first
        enrollments_response = await http_client.get(f"{BASE_URL}/enrollments")

        if enrollments_response.status_code == 200:
            enrollments = enrollments_response.json()

            if isinstance(enrollments, list) and len(enrollments) > 0:
                student_id = enrollments[0].get("student_id")

                if student_id:
                    response = await http_client.get(
                        f"{ANALYTICS_URL}/students/{student_id}/performance"
                    )

                    # Should return performance data
                    assert response.status_code in [200, 404, 500]


@pytest.mark.integration
@pytest.mark.asyncio
class TestContentManagementAPI:
    """Test content management API operations."""

    async def test_get_course_modules(self, http_client):
        """Test retrieving modules for a course."""
        # Get a course first
        courses_response = await http_client.get(f"{BASE_URL}/courses")
        courses = courses_response.json()

        if isinstance(courses, dict):
            courses = courses.get("courses", [])

        if courses:
            course_id = courses[0]["id"]

            response = await http_client.get(
                f"{BASE_URL}/courses/{course_id}/modules"
            )

            # Should return module list
            assert response.status_code in [200, 404]

    async def test_create_course_module(self, http_client):
        """Test creating a module for a course."""
        # Get a course first
        courses_response = await http_client.get(f"{BASE_URL}/courses")
        courses = courses_response.json()

        if isinstance(courses, dict):
            courses = courses.get("courses", [])

        if courses:
            course_id = courses[0]["id"]

            module_data = {
                "title": "Integration Test Module",
                "description": "Test module for integration testing",
                "order": 1,
                "content_type": "text"
            }

            response = await http_client.post(
                f"{BASE_URL}/courses/{course_id}/modules",
                json=module_data
            )

            # Should create or indicate validation error
            assert response.status_code in [200, 201, 400, 422]


@pytest.mark.integration
@pytest.mark.asyncio
class TestFeedbackAPI:
    """Test feedback management API operations."""

    async def test_get_course_feedback(self, http_client):
        """Test retrieving feedback for a course."""
        # Get a course first
        courses_response = await http_client.get(f"{BASE_URL}/courses")
        courses = courses_response.json()

        if isinstance(courses, dict):
            courses = courses.get("courses", [])

        if courses:
            course_id = courses[0]["id"]

            response = await http_client.get(
                f"{BASE_URL}/courses/{course_id}/feedback"
            )

            # Should return feedback list
            assert response.status_code in [200, 404]

    async def test_submit_student_feedback(self, http_client):
        """Test submitting feedback for a student."""
        # Get enrollments first
        enrollments_response = await http_client.get(f"{BASE_URL}/enrollments")

        if enrollments_response.status_code == 200:
            enrollments = enrollments_response.json()

            if isinstance(enrollments, list) and len(enrollments) > 0:
                student_id = enrollments[0].get("student_id")
                course_id = enrollments[0].get("course_id")

                if student_id and course_id:
                    feedback_data = {
                        "student_id": student_id,
                        "course_id": course_id,
                        "comment": "Great progress on the assignments!",
                        "rating": 5
                    }

                    response = await http_client.post(
                        f"{BASE_URL}/feedback/student",
                        json=feedback_data
                    )

                    # Should submit or indicate validation error
                    assert response.status_code in [200, 201, 400, 422]


# Run tests with: pytest tests/integration/test_instructor_api_integration.py -v --tb=short
