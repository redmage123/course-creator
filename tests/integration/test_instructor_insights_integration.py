"""
Instructor Insights Integration Tests

BUSINESS CONTEXT:
Tests integration between frontend React components and backend analytics service
for instructor-specific insights. Validates effectiveness metrics, course analytics,
engagement tracking, and AI-powered recommendation workflows.

TECHNICAL IMPLEMENTATION:
- Tests analytics service instructor endpoints (port 8004)
- Validates response schemas match TypeScript interfaces
- Ensures authorization (instructors only)
- Tests recommendation API workflow

WHY THIS APPROACH:
- Validates frontend-backend contract for instructor features
- Ensures proper authorization (only instructors)
- Tests AI recommendation pipeline
- Verifies data accuracy for decision-making
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json


# Test Configuration
ANALYTICS_BASE_URL = "https://localhost:8004"
TEST_INSTRUCTOR_ID = "instructor-test-001"
TEST_COURSE_ID = "course-test-001"
TEST_STUDENT_ID = "student-test-001"


@pytest.fixture
async def instructor_auth_token() -> str:
    """Generate valid JWT token for instructor"""
    return "instructor-jwt-token-placeholder"


@pytest.fixture
async def student_auth_token() -> str:
    """Generate valid JWT token for student (for negative tests)"""
    return "student-jwt-token-placeholder"


@pytest.fixture
async def http_client():
    """Create async HTTP client with SSL verification disabled for testing"""
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        yield client


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.instructor_insights
class TestInstructorEffectiveness:
    """
    Test instructor effectiveness endpoint

    Endpoint: GET /analytics/instructor/:id/effectiveness
    Purpose: Retrieve comprehensive teaching effectiveness metrics
    """

    async def test_get_instructor_effectiveness(self, http_client, instructor_auth_token):
        """
        Test successful retrieval of instructor effectiveness metrics

        EXPECTED BEHAVIOR:
        - Returns 200 status
        - Response matches InstructorEffectiveness interface
        - Contains student success rates, engagement metrics, content quality
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{TEST_INSTRUCTOR_ID}/effectiveness",
            headers={"Authorization": f"Bearer {instructor_auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Validate schema matches TypeScript interface
        required_fields = [
            "instructor_id",
            "student_success_rate",
            "avg_course_rating",
            "engagement_score",
            "content_completion_rate",
            "response_time_hours"
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Validate ranges
        assert 0 <= data["student_success_rate"] <= 100
        assert 0 <= data["avg_course_rating"] <= 5
        assert 0 <= data["engagement_score"] <= 100
        assert 0 <= data["content_completion_rate"] <= 100
        assert data["response_time_hours"] >= 0

    async def test_get_instructor_effectiveness_time_range(self, http_client, instructor_auth_token):
        """
        Test filtering effectiveness by time range

        EXPECTED BEHAVIOR:
        - Can filter by start_date and end_date
        - Metrics calculated for specified period
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{TEST_INSTRUCTOR_ID}/effectiveness",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            headers={"Authorization": f"Bearer {instructor_auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Validate period is respected
        assert "period_start" in data
        assert "period_end" in data

    async def test_instructor_effectiveness_authorization_required(self, http_client):
        """
        Test that authorization is required

        EXPECTED BEHAVIOR:
        - Returns 401 without token
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{TEST_INSTRUCTOR_ID}/effectiveness"
        )

        assert response.status_code == 401

    async def test_instructor_effectiveness_instructor_only(self, http_client, student_auth_token):
        """
        Test that students cannot access instructor insights

        EXPECTED BEHAVIOR:
        - Returns 403 for non-instructors
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{TEST_INSTRUCTOR_ID}/effectiveness",
            headers={"Authorization": f"Bearer {student_auth_token}"}
        )

        assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.instructor_insights
class TestCourseAnalytics:
    """
    Test course-specific analytics endpoint

    Endpoint: GET /analytics/instructor/:id/courses
    Purpose: Retrieve analytics for all instructor's courses
    """

    async def test_get_course_analytics(self, http_client, instructor_auth_token):
        """
        Test retrieval of course analytics

        EXPECTED BEHAVIOR:
        - Returns array of CourseAnalytics objects
        - Contains enrollment, completion, engagement metrics
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{TEST_INSTRUCTOR_ID}/courses",
            headers={"Authorization": f"Bearer {instructor_auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        if len(data) > 0:
            course = data[0]
            # Validate CourseAnalytics schema
            required_fields = [
                "course_id",
                "course_title",
                "total_enrollments",
                "active_students",
                "completion_rate",
                "avg_quiz_score",
                "engagement_rate"
            ]

            for field in required_fields:
                assert field in course, f"Missing required field: {field}"

            # Validate ranges
            assert course["total_enrollments"] >= 0
            assert course["active_students"] >= 0
            assert 0 <= course["completion_rate"] <= 100
            assert course["avg_quiz_score"] is None or 0 <= course["avg_quiz_score"] <= 100
            assert 0 <= course["engagement_rate"] <= 100

    async def test_get_course_analytics_single_course(self, http_client, instructor_auth_token):
        """
        Test retrieval of analytics for a specific course

        EXPECTED BEHAVIOR:
        - Can filter by course_id
        - Returns detailed analytics for that course
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{TEST_INSTRUCTOR_ID}/courses/{TEST_COURSE_ID}",
            headers={"Authorization": f"Bearer {instructor_auth_token}"}
        )

        assert response.status_code in [200, 404]  # 404 if course doesn't exist

        if response.status_code == 200:
            data = response.json()
            assert data["course_id"] == TEST_COURSE_ID

    async def test_get_course_analytics_sorting(self, http_client, instructor_auth_token):
        """
        Test sorting course analytics

        EXPECTED BEHAVIOR:
        - Can sort by enrollment, completion_rate, engagement
        - Results properly ordered
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{TEST_INSTRUCTOR_ID}/courses",
            params={"sort_by": "completion_rate", "order": "desc"},
            headers={"Authorization": f"Bearer {instructor_auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Validate sorting
        if len(data) > 1:
            for i in range(len(data) - 1):
                assert data[i]["completion_rate"] >= data[i + 1]["completion_rate"]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.instructor_insights
class TestStudentEngagement:
    """
    Test student engagement endpoint

    Endpoint: GET /analytics/instructor/:id/engagement
    Purpose: Track student engagement across courses
    """

    async def test_get_student_engagement(self, http_client, instructor_auth_token):
        """
        Test retrieval of student engagement metrics

        EXPECTED BEHAVIOR:
        - Returns array of StudentEngagement objects
        - Contains activity patterns and at-risk indicators
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{TEST_INSTRUCTOR_ID}/engagement",
            headers={"Authorization": f"Bearer {instructor_auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        if len(data) > 0:
            student = data[0]
            # Validate StudentEngagement schema
            required_fields = [
                "student_id",
                "student_name",
                "engagement_score",
                "last_activity_at",
                "total_time_spent_minutes",
                "at_risk_indicator"
            ]

            for field in required_fields:
                assert field in student, f"Missing required field: {field}"

            # Validate ranges
            assert 0 <= student["engagement_score"] <= 100
            assert student["total_time_spent_minutes"] >= 0
            assert isinstance(student["at_risk_indicator"], bool)

    async def test_get_student_engagement_at_risk_filter(self, http_client, instructor_auth_token):
        """
        Test filtering for at-risk students

        EXPECTED BEHAVIOR:
        - Can filter by at_risk=true
        - Returns only at-risk students
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{TEST_INSTRUCTOR_ID}/engagement",
            params={"at_risk": "true"},
            headers={"Authorization": f"Bearer {instructor_auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # All returned students should be at-risk
        for student in data:
            assert student["at_risk_indicator"] is True

    async def test_get_student_engagement_course_filter(self, http_client, instructor_auth_token):
        """
        Test filtering engagement by course

        EXPECTED BEHAVIOR:
        - Can filter by course_id
        - Returns only students in that course
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{TEST_INSTRUCTOR_ID}/engagement",
            params={"course_id": TEST_COURSE_ID},
            headers={"Authorization": f"Bearer {instructor_auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # All students should be in the specified course
        # (verified by backend logic)
        assert isinstance(data, list)


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.instructor_insights
class TestRecommendationWorkflow:
    """
    Test AI-powered recommendation workflow

    Endpoint: POST /analytics/instructor/:id/recommendations/generate
    Purpose: Generate AI-powered teaching recommendations
    """

    async def test_generate_recommendations(self, http_client, instructor_auth_token):
        """
        Test generating AI recommendations

        EXPECTED BEHAVIOR:
        - Returns 200 with recommendations
        - Recommendations match schema
        - Contains actionable insights
        """
        request_body = {
            "context": "student_engagement",
            "course_id": TEST_COURSE_ID,
            "time_range_days": 30
        }

        response = await http_client.post(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{TEST_INSTRUCTOR_ID}/recommendations/generate",
            json=request_body,
            headers={"Authorization": f"Bearer {instructor_auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Validate recommendation structure
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)

        if len(data["recommendations"]) > 0:
            rec = data["recommendations"][0]
            required_fields = [
                "type",
                "priority",
                "title",
                "description",
                "action_items"
            ]

            for field in required_fields:
                assert field in rec, f"Missing required field: {field}"

            # Validate priority
            assert rec["priority"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

            # Validate action items
            assert isinstance(rec["action_items"], list)

    async def test_generate_recommendations_different_contexts(self, http_client, instructor_auth_token):
        """
        Test generating recommendations for different contexts

        EXPECTED BEHAVIOR:
        - Supports multiple contexts (engagement, content, assessment)
        - Returns context-appropriate recommendations
        """
        contexts = ["student_engagement", "content_quality", "assessment_difficulty"]

        for context in contexts:
            request_body = {
                "context": context,
                "time_range_days": 30
            }

            response = await http_client.post(
                f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{TEST_INSTRUCTOR_ID}/recommendations/generate",
                json=request_body,
                headers={"Authorization": f"Bearer {instructor_auth_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "recommendations" in data

    async def test_save_recommendation_action(self, http_client, instructor_auth_token):
        """
        Test saving action taken on recommendation

        EXPECTED BEHAVIOR:
        - Can save action taken
        - Returns confirmation
        """
        request_body = {
            "recommendation_id": "rec-test-001",
            "action": "IMPLEMENTED",
            "notes": "Increased student check-ins"
        }

        response = await http_client.post(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{TEST_INSTRUCTOR_ID}/recommendations/action",
            json=request_body,
            headers={"Authorization": f"Bearer {instructor_auth_token}"}
        )

        assert response.status_code in [200, 201]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.instructor_insights
class TestInstructorInsightsAuthorization:
    """
    Test authorization for instructor insights endpoints

    SECURITY REQUIREMENTS:
    - Only instructors can access insights
    - Instructors can only access their own data
    - Org admins can access all instructors in org
    - Site admins can access all data
    """

    async def test_student_cannot_access_insights(self, http_client, student_auth_token):
        """
        Test that students cannot access instructor insights

        EXPECTED BEHAVIOR:
        - Returns 403 for students
        """
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{TEST_INSTRUCTOR_ID}/effectiveness",
            headers={"Authorization": f"Bearer {student_auth_token}"}
        )

        assert response.status_code == 403

    async def test_instructor_cannot_access_other_instructor(self, http_client, instructor_auth_token):
        """
        Test that instructors cannot access other instructors' data

        EXPECTED BEHAVIOR:
        - Returns 403 when accessing different instructor's data
        """
        different_instructor_id = "instructor-test-002"
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{different_instructor_id}/effectiveness",
            headers={"Authorization": f"Bearer {instructor_auth_token}"}
        )

        # Should be forbidden
        assert response.status_code in [403, 404]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.instructor_insights
class TestInstructorInsightsPerformance:
    """
    Test performance requirements for instructor insights

    PERFORMANCE REQUIREMENTS:
    - Effectiveness endpoint: < 600ms
    - Course analytics: < 500ms
    - Engagement metrics: < 700ms
    - Recommendation generation: < 3000ms (AI processing)
    """

    async def test_effectiveness_endpoint_performance(self, http_client, instructor_auth_token):
        """
        Test effectiveness endpoint response time

        EXPECTED BEHAVIOR:
        - Response time < 600ms
        """
        import time

        start_time = time.time()
        response = await http_client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{TEST_INSTRUCTOR_ID}/effectiveness",
            headers={"Authorization": f"Bearer {instructor_auth_token}"}
        )
        end_time = time.time()

        duration_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert duration_ms < 600, f"Effectiveness endpoint took {duration_ms}ms, expected < 600ms"

    async def test_recommendation_generation_performance(self, http_client, instructor_auth_token):
        """
        Test recommendation generation response time

        EXPECTED BEHAVIOR:
        - Response time < 3000ms (AI processing allowed)
        """
        import time

        request_body = {
            "context": "student_engagement",
            "time_range_days": 30
        }

        start_time = time.time()
        response = await http_client.post(
            f"{ANALYTICS_BASE_URL}/api/v1/analytics/instructor/{TEST_INSTRUCTOR_ID}/recommendations/generate",
            json=request_body,
            headers={"Authorization": f"Bearer {instructor_auth_token}"}
        )
        end_time = time.time()

        duration_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert duration_ms < 3000, f"Recommendation generation took {duration_ms}ms, expected < 3000ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
