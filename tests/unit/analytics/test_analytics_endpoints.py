"""
Unit Tests for Analytics API Endpoints

BUSINESS REQUIREMENT:
Validates RESTful API endpoints for analytics tracking including authentication,
authorization, request validation, and response formatting for educational
analytics and institutional reporting.

TECHNICAL IMPLEMENTATION:
- Uses FastAPI TestClient for endpoint testing
- Tests authentication/authorization
- Tests request validation
- Tests error handling
- Tests response formatting
"""


import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import json

from main import app


@pytest.fixture
def test_client():
    """Create test client with mocked dependencies."""
    client = TestClient(app)
    return client


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    return {
        "Authorization": "Bearer mock-jwt-token-student-123"
    }


@pytest.fixture
def sample_activity_data():
    """Sample activity tracking data."""
    return {
        "student_id": "student-123",
        "course_id": "course-456",
        "activity_type": "lab_access",
        "activity_data": {
            "lab_id": "python-basics-lab",
            "session_duration": 45
        },
        "session_id": "session-abc123"
    }


class TestActivityTrackingEndpoints:
    """Test activity tracking API endpoints."""

    @patch('analytics_endpoints.db_pool')
    @patch('analytics_endpoints.get_current_user')
    def test_track_single_activity_success(self, mock_auth, mock_db_pool, test_client, auth_headers, sample_activity_data):
        """Test successfully tracking a single student activity."""
        # Mock authentication
        mock_auth.return_value = {"id": "student-123", "role": "student"}

        # Mock database connection
        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = None

        response = test_client.post(
            "/activities/track",
            json=sample_activity_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Activity tracked successfully"
        assert "activity_id" in data
        assert "timestamp" in data

    @patch('analytics_endpoints.db_pool')
    @patch('analytics_endpoints.get_current_user')
    def test_track_batch_activities_success(self, mock_auth, mock_db_pool, test_client, auth_headers):
        """Test successfully tracking multiple activities in batch."""
        mock_auth.return_value = {"id": "student-123", "role": "student"}

        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = None

        batch_activities = [
            {
                "student_id": "student-123",
                "course_id": "course-456",
                "activity_type": "login",
                "activity_data": {"device": "desktop"}
            },
            {
                "student_id": "student-123",
                "course_id": "course-456",
                "activity_type": "content_view",
                "activity_data": {"content_id": "lesson-1"}
            },
            {
                "student_id": "student-123",
                "course_id": "course-456",
                "activity_type": "logout",
                "activity_data": {"session_duration": 3600}
            }
        ]

        response = test_client.post(
            "/activities/batch",
            json=batch_activities,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == f"Tracked {len(batch_activities)} activities successfully"
        assert data["activities_tracked"] == 3

    def test_track_activity_unauthorized(self, test_client, sample_activity_data):
        """Test activity tracking requires authentication."""
        response = test_client.post(
            "/activities/track",
            json=sample_activity_data
        )

        assert response.status_code == 403  # Forbidden


class TestLabUsageEndpoints:
    """Test lab usage tracking API endpoints."""

    @patch('analytics_endpoints.db_pool')
    @patch('analytics_endpoints.get_current_user')
    def test_track_lab_usage_success(self, mock_auth, mock_db_pool, test_client, auth_headers):
        """Test successfully tracking lab usage metrics."""
        mock_auth.return_value = {"id": "student-123", "role": "student"}

        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = None

        lab_usage_data = {
            "student_id": "student-123",
            "course_id": "course-456",
            "lab_id": "python-basics-lab",
            "session_start": datetime.utcnow().isoformat(),
            "session_end": (datetime.utcnow() + timedelta(minutes=45)).isoformat(),
            "actions_performed": 25,
            "code_executions": 12,
            "errors_encountered": 3,
            "completion_status": "completed"
        }

        response = test_client.post(
            "/lab-usage/track",
            json=lab_usage_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Lab usage tracked successfully"
        assert "metric_id" in data


class TestQuizPerformanceEndpoints:
    """Test quiz performance tracking API endpoints."""

    @patch('analytics_endpoints.db_pool')
    @patch('analytics_endpoints.get_current_user')
    def test_track_quiz_performance_success(self, mock_auth, mock_db_pool, test_client, auth_headers):
        """Test successfully tracking quiz performance."""
        mock_auth.return_value = {"id": "student-123", "role": "student"}

        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = None

        quiz_data = {
            "student_id": "student-123",
            "course_id": "course-456",
            "quiz_id": "python-basics-quiz",
            "start_time": datetime.utcnow().isoformat(),
            "end_time": (datetime.utcnow() + timedelta(minutes=15)).isoformat(),
            "questions_total": 10,
            "questions_answered": 10,
            "questions_correct": 8,
            "answers": {"q1": "option_a", "q2": "option_c"},
            "status": "completed"
        }

        response = test_client.post(
            "/quiz-performance/track",
            json=quiz_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Quiz performance tracked successfully"
        assert "performance_id" in data
        assert data["score_percentage"] == 80.0

    @patch('analytics_endpoints.db_pool')
    @patch('analytics_endpoints.get_current_user')
    def test_track_quiz_performance_calculates_duration(self, mock_auth, mock_db_pool, test_client, auth_headers):
        """Test quiz duration calculation."""
        mock_auth.return_value = {"id": "student-123", "role": "student"}

        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = None

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=20)

        quiz_data = {
            "student_id": "student-123",
            "course_id": "course-456",
            "quiz_id": "quiz-789",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "questions_total": 5,
            "questions_answered": 5,
            "questions_correct": 4,
            "status": "completed"
        }

        response = test_client.post(
            "/quiz-performance/track",
            json=quiz_data,
            headers=auth_headers
        )

        assert response.status_code == 200


class TestStudentProgressEndpoints:
    """Test student progress tracking API endpoints."""

    @patch('analytics_endpoints.db_pool')
    @patch('analytics_endpoints.get_current_user')
    def test_update_student_progress_success(self, mock_auth, mock_db_pool, test_client, auth_headers):
        """Test successfully updating student progress."""
        mock_auth.return_value = {"id": "instructor-123", "role": "instructor"}

        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = None

        progress_data = {
            "student_id": "student-123",
            "course_id": "course-456",
            "content_item_id": "lesson-789",
            "content_type": "lesson",
            "status": "completed",
            "progress_percentage": 100.0,
            "time_spent_minutes": 30,
            "last_accessed": datetime.utcnow().isoformat(),
            "completion_date": datetime.utcnow().isoformat(),
            "mastery_score": 85.5
        }

        response = test_client.post(
            "/progress/update",
            json=progress_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Progress updated successfully"
        assert "progress_id" in data
        assert data["progress_percentage"] == 100.0


class TestAnalyticsRetrievalEndpoints:
    """Test analytics data retrieval API endpoints."""

    @patch('analytics_endpoints.db_pool')
    @patch('analytics_endpoints.get_current_user')
    def test_get_student_analytics_success(self, mock_auth, mock_db_pool, test_client, auth_headers):
        """Test retrieving comprehensive student analytics."""
        mock_auth.return_value = {"id": "instructor-123", "role": "instructor"}

        # Mock database connection and query results
        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn

        # Mock activity results
        mock_conn.fetch.side_effect = [
            [  # activities
                {"activity_type": "login", "count": 5, "day": datetime.utcnow().date()},
                {"activity_type": "lab_access", "count": 3, "day": datetime.utcnow().date()}
            ],
            [  # progress data
                {"content_type": "lesson", "status": "completed", "count": 2,
                 "avg_progress": 100.0, "total_time": 60}
            ]
        ]

        # Mock single row results
        mock_conn.fetchrow.side_effect = [
            {  # lab metrics
                "avg_duration": 35.5,
                "total_actions": 150,
                "total_sessions": 8,
                "avg_executions": 12.3,
                "avg_errors": 2.1
            },
            {  # quiz metrics
                "avg_score": 82.5,
                "total_quizzes": 5,
                "avg_duration": 12.5,
                "passed_quizzes": 4
            }
        ]

        response = test_client.get(
            "/analytics/student/student-123?course_id=course-456&days_back=30",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == "student-123"
        assert data["course_id"] == "course-456"
        assert "analysis_period" in data
        assert "activity_summary" in data
        assert "lab_metrics" in data
        assert "quiz_performance" in data
        assert "engagement_score" in data
        assert "recommendations" in data

    @patch('analytics_endpoints.db_pool')
    @patch('analytics_endpoints.get_current_user')
    def test_get_course_analytics_success(self, mock_auth, mock_db_pool, test_client, auth_headers):
        """Test retrieving comprehensive course analytics."""
        mock_auth.return_value = {"id": "instructor-123", "role": "instructor"}

        # Mock database connection and query results
        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn

        # Mock query results
        mock_conn.fetchval.return_value = 25  # student count
        mock_conn.fetch.side_effect = [
            [  # activity metrics
                {"student_id": "student-1", "activity_type": "login", "count": 3},
                {"student_id": "student-2", "activity_type": "login", "count": 2}
            ],
            [  # lab completion
                {"completion_status": "completed", "count": 15, "avg_duration": 42.3},
                {"completion_status": "in_progress", "count": 8, "avg_duration": 25.1}
            ],
            [  # progress distribution
                {"status": "completed", "count": 12, "avg_progress": 100.0},
                {"status": "in_progress", "count": 13, "avg_progress": 65.5}
            ]
        ]

        # Mock quiz stats
        mock_conn.fetchrow.return_value = {
            "avg_score": 75.2,
            "score_stddev": 12.8,
            "students_attempted": 20,
            "total_attempts": 45
        }

        response = test_client.get(
            "/analytics/course/course-456?days_back=30",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["course_id"] == "course-456"
        assert "analysis_period" in data
        assert "enrollment" in data
        assert data["enrollment"]["total_students"] == 25
        assert "lab_completion" in data
        assert "quiz_performance" in data
        assert "progress_distribution" in data


class TestAnalyticsErrorHandling:
    """Test error handling for analytics endpoints."""

    def test_unauthorized_access_to_analytics(self, test_client):
        """Test unauthorized access to analytics endpoints."""
        response = test_client.post(
            "/activities/track",
            json={
                "student_id": "student-123",
                "course_id": "course-456",
                "activity_type": "login"
            }
        )

        assert response.status_code == 403  # Forbidden

    @patch('analytics_endpoints.get_current_user')
    def test_invalid_activity_data_format(self, mock_auth, test_client):
        """Test validation of invalid activity data."""
        mock_auth.return_value = {"id": "student-123", "role": "student"}

        response = test_client.post(
            "/activities/track",
            json={
                "invalid_field": "invalid_value"
                # Missing required fields
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422  # Validation error

    @patch('analytics_endpoints.db_pool')
    @patch('analytics_endpoints.get_current_user')
    def test_database_error_handling(self, mock_auth, mock_db_pool, test_client):
        """Test handling of database errors."""
        mock_auth.return_value = {"id": "student-123", "role": "student"}

        # Mock database connection failure
        mock_db_pool.acquire.side_effect = Exception("Database connection failed")

        response = test_client.post(
            "/activities/track",
            json={
                "student_id": "student-123",
                "course_id": "course-456",
                "activity_type": "login"
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 500  # Internal server error


class TestAnalyticsBusinessLogic:
    """Test analytics calculation and recommendation logic."""

    def test_engagement_score_calculation_high(self):
        """Test engagement score for high engagement student."""
        from analytics_endpoints import calculate_engagement_score

        analytics_data = {
            'activity_summary': {'total_activities': 60},
            'lab_metrics': {'total_sessions': 12},
            'quiz_performance': {'average_score': 85.0},
            'progress_summary': {
                'by_content_type': [
                    {'total_time_minutes': 180},
                    {'total_time_minutes': 120}
                ]
            }
        }

        score = calculate_engagement_score(analytics_data)
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score > 80  # Should be high engagement

    def test_engagement_score_calculation_low(self):
        """Test engagement score for low engagement student."""
        from analytics_endpoints import calculate_engagement_score

        analytics_data = {
            'activity_summary': {'total_activities': 5},
            'lab_metrics': {'total_sessions': 1},
            'quiz_performance': {'average_score': 45.0},
            'progress_summary': {
                'by_content_type': [
                    {'total_time_minutes': 30}
                ]
            }
        }

        score = calculate_engagement_score(analytics_data)
        assert isinstance(score, float)
        assert score < 50  # Should be low engagement

    def test_generate_recommendations_low_quiz_performance(self):
        """Test recommendation generation for low quiz scores."""
        from analytics_endpoints import generate_recommendations

        analytics_data = {
            'activity_summary': {'total_activities': 30},
            'lab_metrics': {'average_errors': 2, 'average_session_duration': 35},
            'quiz_performance': {'average_score': 55, 'pass_rate': 0.4},
            'engagement_score': 60
        }

        recommendations = generate_recommendations(analytics_data)
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("quiz" in rec.lower() or "review" in rec.lower() for rec in recommendations)

    def test_generate_recommendations_excellent_performance(self):
        """Test recommendations for excellent student performance."""
        from analytics_endpoints import generate_recommendations

        analytics_data = {
            'activity_summary': {'total_activities': 50},
            'lab_metrics': {'average_errors': 1, 'average_session_duration': 40},
            'quiz_performance': {'average_score': 90, 'pass_rate': 0.95},
            'engagement_score': 85
        }

        recommendations = generate_recommendations(analytics_data)
        assert isinstance(recommendations, list)
        assert any("great" in rec.lower() or "excellent" in rec.lower() for rec in recommendations)


# Run tests with: pytest tests/unit/analytics/test_analytics_endpoints.py -v
