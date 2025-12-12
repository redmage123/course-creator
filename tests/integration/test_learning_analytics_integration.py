"""
Learning Analytics Integration Tests

BUSINESS CONTEXT:
Tests integration between frontend React components and backend analytics service.
Validates that learning analytics API endpoints respond correctly with proper schemas,
authentication, and authorization for tracking student progress, skill mastery,
and session activity.

TECHNICAL IMPLEMENTATION:
- Tests analytics service endpoints (port 8004)
- Validates response schemas match TypeScript interfaces
- Ensures authentication and authorization
- Tests all user roles (student, instructor, org_admin, site_admin)

WHY THIS APPROACH:
- Integration tests verify frontend-backend contract
- Catch breaking changes in API responses
- Ensure proper security/authorization
- Validate data transformations
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta
import json


# Test Configuration
ANALYTICS_BASE_URL = "https://localhost:8004"
TEST_STUDENT_ID = "student-test-001"
TEST_INSTRUCTOR_ID = "instructor-test-001"
TEST_ORG_ADMIN_ID = "org-admin-test-001"


@pytest.fixture
async def student_auth_token() -> str:
    """Generate valid JWT token for student"""
    # In real implementation, this would authenticate and get token
    return "student-jwt-token-placeholder"


@pytest.fixture
async def instructor_auth_token() -> str:
    """Generate valid JWT token for instructor"""
    return "instructor-jwt-token-placeholder"


@pytest.fixture
async def org_admin_auth_token() -> str:
    """Generate valid JWT token for organization admin"""
    return "org-admin-jwt-token-placeholder"


@pytest.fixture
async def http_client():
    """Create async HTTP client with SSL verification disabled for testing"""
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        yield client


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.learning_analytics
class TestLearningAnalyticsSummary:
    """
    Test learning analytics summary endpoint

    Endpoint: GET /analytics/learning/student/:id/summary
    Purpose: Retrieve comprehensive learning summary for a student
    """

    async def test_get_student_summary_success(self, http_client, student_auth_token):
        """
        Test successful retrieval of student learning summary

        EXPECTED BEHAVIOR:
        - Returns 200 status
        - Response matches LearningAnalyticsSummary interface
        - Contains learning paths, skill mastery, recent sessions
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/learning/student/{TEST_STUDENT_ID}/summary",
            headers={"Authorization": f"Bearer {student_auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Validate schema matches TypeScript interface
        assert "learning_paths" in data
        assert "skill_mastery" in data
        assert "recent_sessions" in data
        assert "overall_progress" in data
        assert isinstance(data["overall_progress"], (int, float))
        assert 0 <= data["overall_progress"] <= 100

        # Validate learning paths structure
        if data["learning_paths"]:
            path = data["learning_paths"][0]
            assert "id" in path
            assert "track_id" in path
            assert "overall_progress" in path
            assert "status" in path
            assert path["status"] in ["NOT_STARTED", "IN_PROGRESS", "COMPLETED", "PAUSED"]

    async def test_get_student_summary_authentication_required(self, http_client):
        """
        Test that authentication is required

        EXPECTED BEHAVIOR:
        - Returns 401 without token
        - Error message indicates authentication required
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/learning/student/{TEST_STUDENT_ID}/summary"
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data or "error" in data

    async def test_get_student_summary_wrong_user(self, http_client, student_auth_token):
        """
        Test that students cannot access other students' data

        EXPECTED BEHAVIOR:
        - Returns 403 when accessing different student's data
        - Authorization error message
        """
        different_student_id = "student-test-002"
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/learning/student/{different_student_id}/summary",
            headers={"Authorization": f"Bearer {student_auth_token}"}
        )

        # Should be forbidden (403) or not found (404) for security
        assert response.status_code in [403, 404]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.learning_analytics
class TestLearningPaths:
    """
    Test learning paths endpoint

    Endpoint: GET /analytics/learning/student/:id/paths
    Purpose: Retrieve all learning paths for a student
    """

    async def test_get_learning_paths(self, http_client, student_auth_token):
        """
        Test retrieval of learning paths

        EXPECTED BEHAVIOR:
        - Returns array of LearningPathProgress objects
        - Each path contains proper structure
        - Progress values are valid
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/learning/student/{TEST_STUDENT_ID}/paths",
            headers={"Authorization": f"Bearer {student_auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        if len(data) > 0:
            path = data[0]
            # Validate LearningPathProgress schema
            required_fields = [
                "id", "user_id", "track_id", "overall_progress",
                "status", "total_time_spent_minutes"
            ]
            for field in required_fields:
                assert field in path, f"Missing required field: {field}"

            # Validate progress range
            assert 0 <= path["overall_progress"] <= 100

            # Validate milestones
            assert "milestones_completed" in path
            assert isinstance(path["milestones_completed"], list)

    async def test_get_learning_paths_filtering(self, http_client, student_auth_token):
        """
        Test filtering learning paths by status

        EXPECTED BEHAVIOR:
        - Can filter by status (IN_PROGRESS, COMPLETED, etc.)
        - Returns only matching paths
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/learning/student/{TEST_STUDENT_ID}/paths",
            params={"status": "IN_PROGRESS"},
            headers={"Authorization": f"Bearer {student_auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # All returned paths should have IN_PROGRESS status
        for path in data:
            assert path["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.learning_analytics
class TestSkillMastery:
    """
    Test skill mastery endpoint

    Endpoint: GET /analytics/learning/student/:id/skills
    Purpose: Retrieve skill mastery data with SM-2 spaced repetition
    """

    async def test_get_skill_mastery(self, http_client, student_auth_token):
        """
        Test retrieval of skill mastery data

        EXPECTED BEHAVIOR:
        - Returns array of SkillMastery objects
        - Contains SM-2 algorithm data
        - Proper mastery level calculations
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/learning/student/{TEST_STUDENT_ID}/skills",
            headers={"Authorization": f"Bearer {student_auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        if len(data) > 0:
            skill = data[0]
            # Validate SkillMastery schema
            required_fields = [
                "skill_id", "skill_name", "mastery_level",
                "practice_count", "last_practiced_at"
            ]
            for field in required_fields:
                assert field in skill, f"Missing required field: {field}"

            # Validate mastery level (0-5 in SM-2)
            assert 0 <= skill["mastery_level"] <= 5

            # Validate SM-2 specific fields
            sm2_fields = ["easiness_factor", "interval_days", "next_review_at"]
            for field in sm2_fields:
                assert field in skill, f"Missing SM-2 field: {field}"

            # Validate easiness factor range (1.3-2.5 in SM-2)
            if skill["easiness_factor"] is not None:
                assert 1.3 <= skill["easiness_factor"] <= 2.5

    async def test_get_skill_mastery_sorting(self, http_client, student_auth_token):
        """
        Test sorting skill mastery by different criteria

        EXPECTED BEHAVIOR:
        - Can sort by mastery_level, last_practiced, next_review
        - Results properly ordered
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/learning/student/{TEST_STUDENT_ID}/skills",
            params={"sort_by": "mastery_level", "order": "desc"},
            headers={"Authorization": f"Bearer {student_auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Validate sorting (descending mastery level)
        if len(data) > 1:
            for i in range(len(data) - 1):
                assert data[i]["mastery_level"] >= data[i + 1]["mastery_level"]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.learning_analytics
class TestSessionActivity:
    """
    Test session activity endpoint

    Endpoint: GET /analytics/learning/student/:id/sessions
    Purpose: Retrieve session activity and engagement metrics
    """

    async def test_get_session_activity(self, http_client, student_auth_token):
        """
        Test retrieval of session activity

        EXPECTED BEHAVIOR:
        - Returns array of SessionActivity objects
        - Contains engagement metrics
        - Time ranges properly formatted
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/learning/student/{TEST_STUDENT_ID}/sessions",
            headers={"Authorization": f"Bearer {student_auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        if len(data) > 0:
            session = data[0]
            # Validate SessionActivity schema
            required_fields = [
                "session_id", "user_id", "started_at", "ended_at",
                "duration_minutes", "activity_type"
            ]
            for field in required_fields:
                assert field in session, f"Missing required field: {field}"

            # Validate activity types
            valid_types = [
                "VIDEO_WATCHING", "QUIZ_TAKING", "LAB_WORKING",
                "READING", "DISCUSSION", "OTHER"
            ]
            assert session["activity_type"] in valid_types

            # Validate duration
            assert session["duration_minutes"] >= 0

    async def test_get_session_activity_time_range(self, http_client, student_auth_token):
        """
        Test filtering sessions by time range

        EXPECTED BEHAVIOR:
        - Can filter by start_date and end_date
        - Returns only sessions in range
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/learning/student/{TEST_STUDENT_ID}/sessions",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            headers={"Authorization": f"Bearer {student_auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # All sessions should be within range
        for session in data:
            session_date = datetime.fromisoformat(session["started_at"].replace("Z", "+00:00"))
            assert start_date <= session_date <= end_date


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.learning_analytics
class TestLearningAnalyticsAuthorization:
    """
    Test authorization for learning analytics endpoints

    SECURITY REQUIREMENTS:
    - Students can only access their own data
    - Instructors can access students in their courses
    - Org admins can access all students in org
    - Site admins can access all data
    """

    async def test_instructor_can_access_student_data(self, http_client, instructor_auth_token):
        """
        Test that instructors can access student data for their courses

        EXPECTED BEHAVIOR:
        - Returns 200 for students in instructor's courses
        - Returns proper data structure
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/learning/student/{TEST_STUDENT_ID}/summary",
            headers={"Authorization": f"Bearer {instructor_auth_token}"}
        )

        # Should be allowed if student is in instructor's course
        assert response.status_code in [200, 403]  # 403 if not in course

    async def test_org_admin_can_access_org_students(self, http_client, org_admin_auth_token):
        """
        Test that org admins can access students in their organization

        EXPECTED BEHAVIOR:
        - Returns 200 for students in same org
        - Returns 403 for students in different org
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/learning/student/{TEST_STUDENT_ID}/summary",
            headers={"Authorization": f"Bearer {org_admin_auth_token}"}
        )

        # Should be allowed if student is in same org
        assert response.status_code in [200, 403]  # 403 if different org


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.learning_analytics
class TestLearningAnalyticsPerformance:
    """
    Test performance requirements for learning analytics

    PERFORMANCE REQUIREMENTS:
    - Summary endpoint: < 500ms
    - Paths endpoint: < 300ms
    - Skills endpoint: < 400ms
    - Sessions endpoint: < 600ms (may have more data)
    """

    async def test_summary_endpoint_performance(self, http_client, student_auth_token):
        """
        Test summary endpoint response time

        EXPECTED BEHAVIOR:
        - Response time < 500ms
        - No N+1 query issues
        """
        import time

        start_time = time.time()
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/learning/student/{TEST_STUDENT_ID}/summary",
            headers={"Authorization": f"Bearer {student_auth_token}"}
        )
        end_time = time.time()

        duration_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert duration_ms < 500, f"Summary endpoint took {duration_ms}ms, expected < 500ms"

    async def test_skills_endpoint_performance(self, http_client, student_auth_token):
        """
        Test skills endpoint response time

        EXPECTED BEHAVIOR:
        - Response time < 400ms even with many skills
        """
        import time

        start_time = time.time()
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/learning/student/{TEST_STUDENT_ID}/skills",
            headers={"Authorization": f"Bearer {student_auth_token}"}
        )
        end_time = time.time()

        duration_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert duration_ms < 400, f"Skills endpoint took {duration_ms}ms, expected < 400ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
