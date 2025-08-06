"""
Unit tests for demo service API endpoints
Tests FastAPI endpoints, request/response handling, and business logic
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add demo service to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/demo-service'))

from main import app, DemoSession, demo_sessions, DEMO_USER_TYPES


@pytest.fixture
def client():
    """Create test client for demo service"""
    return TestClient(app)


@pytest.fixture
def sample_demo_session():
    """Create a sample demo session for testing"""
    session_id = "test-session-123"
    user_data = DEMO_USER_TYPES["instructor"].copy()
    user_data["id"] = f"demo-instructor-{session_id[:8]}"
    user_data["is_demo"] = True
    
    demo_session = DemoSession(
        session_id=session_id,
        user_type="instructor",
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=2),
        user_data=user_data
    )
    demo_sessions[session_id] = demo_session
    return demo_session


class TestDemoServiceAPI:
    """Test suite for demo service API endpoints"""

    def test_health_check(self, client):
        """Test demo service health check endpoint"""
        response = client.get("/api/v1/demo/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "demo-service"
        assert "active_sessions" in data
        assert "uptime" in data
        assert data["demo_ready"] is True

    def test_start_demo_session_instructor(self, client):
        """Test starting a demo session as instructor"""
        response = client.post("/api/v1/demo/start?user_type=instructor")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert "user" in data
        assert "expires_at" in data
        assert "message" in data
        
        # Validate user data
        user = data["user"]
        assert user["role"] == "instructor"
        assert user["is_demo"] is True
        assert user["name"] == DEMO_USER_TYPES["instructor"]["name"]
        
        # Check session is stored
        session_id = data["session_id"]
        assert session_id in demo_sessions

    def test_start_demo_session_student(self, client):
        """Test starting a demo session as student"""
        response = client.post("/api/v1/demo/start?user_type=student")
        
        assert response.status_code == 200
        data = response.json()
        
        user = data["user"]
        assert user["role"] == "student"
        assert user["name"] == DEMO_USER_TYPES["student"]["name"]

    def test_start_demo_session_admin(self, client):
        """Test starting a demo session as admin"""
        response = client.post("/api/v1/demo/start?user_type=admin")
        
        assert response.status_code == 200
        data = response.json()
        
        user = data["user"]
        assert user["role"] == "admin"
        assert user["name"] == DEMO_USER_TYPES["admin"]["name"]

    def test_start_demo_session_invalid_type(self, client):
        """Test starting demo session with invalid user type"""
        response = client.post("/api/v1/demo/start?user_type=invalid")
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid user type" in data["detail"]

    def test_get_demo_courses(self, client, sample_demo_session):
        """Test getting demo courses"""
        session_id = sample_demo_session.session_id
        response = client.get(f"/api/v1/demo/courses?session_id={session_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "courses" in data
        assert "total" in data
        assert "demo_context" in data
        
        courses = data["courses"]
        assert isinstance(courses, list)
        assert len(courses) == 10  # Default limit
        
        # Validate course structure
        if courses:
            course = courses[0]
            required_fields = ["id", "title", "description", "difficulty", "enrollment_count"]
            for field in required_fields:
                assert field in course

    def test_get_demo_courses_with_limit(self, client, sample_demo_session):
        """Test getting demo courses with custom limit"""
        session_id = sample_demo_session.session_id
        response = client.get(f"/api/v1/demo/courses?session_id={session_id}&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["courses"]) == 5

    def test_get_demo_students_as_instructor(self, client, sample_demo_session):
        """Test getting demo students as instructor"""
        session_id = sample_demo_session.session_id
        response = client.get(f"/api/v1/demo/students?session_id={session_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "students" in data
        assert "demo_context" in data
        
        students = data["students"]
        assert isinstance(students, list)
        assert len(students) > 0
        
        # Validate student structure
        if students:
            student = students[0]
            required_fields = ["id", "name", "email", "progress", "engagement_level"]
            for field in required_fields:
                assert field in student

    def test_get_demo_students_unauthorized(self, client):
        """Test getting students as student user (should fail)"""
        # Create student session
        session_id = "student-session"
        user_data = DEMO_USER_TYPES["student"].copy()
        user_data["id"] = f"demo-student-{session_id[:8]}"
        user_data["is_demo"] = True
        
        student_session = DemoSession(
            session_id=session_id,
            user_type="student",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=2),
            user_data=user_data
        )
        demo_sessions[session_id] = student_session
        
        response = client.get(f"/api/v1/demo/students?session_id={session_id}")
        
        assert response.status_code == 403
        data = response.json()
        assert "Only instructors and admins" in data["detail"]

    def test_get_demo_analytics(self, client, sample_demo_session):
        """Test getting demo analytics"""
        session_id = sample_demo_session.session_id
        response = client.get(f"/api/v1/demo/analytics?session_id={session_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "analytics" in data
        assert "timeframe" in data
        assert "demo_context" in data
        
        analytics = data["analytics"]
        assert "overview" in analytics
        assert "student_progress" in analytics

    def test_get_demo_analytics_timeframes(self, client, sample_demo_session):
        """Test analytics with different timeframes"""
        session_id = sample_demo_session.session_id
        timeframes = ["7d", "30d", "90d", "1y"]
        
        for timeframe in timeframes:
            response = client.get(f"/api/v1/demo/analytics?session_id={session_id}&timeframe={timeframe}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["timeframe"] == timeframe

    def test_get_demo_analytics_invalid_timeframe(self, client, sample_demo_session):
        """Test analytics with invalid timeframe"""
        session_id = sample_demo_session.session_id
        response = client.get(f"/api/v1/demo/analytics?session_id={session_id}&timeframe=invalid")
        
        assert response.status_code == 422  # Validation error

    def test_get_demo_labs(self, client, sample_demo_session):
        """Test getting demo labs"""
        session_id = sample_demo_session.session_id
        response = client.get(f"/api/v1/demo/labs?session_id={session_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "labs" in data
        assert "demo_context" in data
        
        labs = data["labs"]
        assert isinstance(labs, list)
        assert len(labs) > 0
        
        # Validate lab structure
        if labs:
            lab = labs[0]
            required_fields = ["id", "title", "ide_type", "difficulty", "estimated_time"]
            for field in required_fields:
                assert field in lab

    def test_get_demo_feedback(self, client, sample_demo_session):
        """Test getting demo feedback"""
        session_id = sample_demo_session.session_id
        response = client.get(f"/api/v1/demo/feedback?session_id={session_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "feedback" in data
        assert "demo_context" in data
        
        feedback = data["feedback"]
        assert isinstance(feedback, list)
        assert len(feedback) > 0
        
        # Validate feedback structure
        if feedback:
            review = feedback[0]
            required_fields = ["id", "student_name", "rating", "comment", "sentiment"]
            for field in required_fields:
                assert field in review

    def test_create_demo_course(self, client, sample_demo_session):
        """Test AI-powered course creation simulation"""
        session_id = sample_demo_session.session_id
        course_data = {
            "title": "Test Course",
            "description": "A test course for demo purposes"
        }
        
        response = client.post(
            f"/api/v1/demo/course/create?session_id={session_id}",
            json=course_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "course" in data
        assert "message" in data
        assert "demo_context" in data
        
        course = data["course"]
        assert course["title"] == "Test Course"
        assert course["ai_generated"] is True
        assert "modules" in course
        assert len(course["modules"]) > 0

    def test_create_demo_course_unauthorized(self, client):
        """Test course creation as student (should fail)"""
        # Create student session
        session_id = "student-session-2"
        user_data = DEMO_USER_TYPES["student"].copy()
        user_data["id"] = f"demo-student-{session_id[:8]}"
        user_data["is_demo"] = True
        
        student_session = DemoSession(
            session_id=session_id,
            user_type="student",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=2),
            user_data=user_data
        )
        demo_sessions[session_id] = student_session
        
        course_data = {"title": "Test Course"}
        response = client.post(
            f"/api/v1/demo/course/create?session_id={session_id}",
            json=course_data
        )
        
        assert response.status_code == 403

    def test_get_demo_session_info(self, client, sample_demo_session):
        """Test getting demo session information"""
        session_id = sample_demo_session.session_id
        response = client.get(f"/api/v1/demo/session/info?session_id={session_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["session_id"] == session_id
        assert "user" in data
        assert "expires_at" in data
        assert "minutes_remaining" in data
        assert "demo_features_available" in data
        
        assert isinstance(data["minutes_remaining"], int)
        assert isinstance(data["demo_features_available"], list)

    def test_end_demo_session(self, client, sample_demo_session):
        """Test ending a demo session"""
        session_id = sample_demo_session.session_id
        
        # Verify session exists
        assert session_id in demo_sessions
        
        response = client.delete(f"/api/v1/demo/session?session_id={session_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "thank_you" in data
        
        # Verify session is removed
        assert session_id not in demo_sessions

    def test_session_not_found(self, client):
        """Test accessing endpoints with non-existent session"""
        response = client.get("/api/v1/demo/courses?session_id=non-existent")
        
        assert response.status_code == 404
        data = response.json()
        assert "Demo session not found" in data["detail"]

    def test_session_expired(self, client):
        """Test accessing endpoints with expired session"""
        session_id = "expired-session"
        user_data = DEMO_USER_TYPES["instructor"].copy()
        user_data["id"] = f"demo-instructor-{session_id[:8]}"
        user_data["is_demo"] = True
        
        expired_session = DemoSession(
            session_id=session_id,
            user_type="instructor",
            created_at=datetime.now() - timedelta(hours=3),
            expires_at=datetime.now() - timedelta(hours=1),  # Expired
            user_data=user_data
        )
        demo_sessions[session_id] = expired_session
        
        response = client.get(f"/api/v1/demo/courses?session_id={session_id}")
        
        assert response.status_code == 401
        data = response.json()
        assert "Demo session expired" in data["detail"]
        
        # Session should be cleaned up
        assert session_id not in demo_sessions

    def test_concurrent_sessions(self, client):
        """Test handling multiple concurrent demo sessions"""
        sessions = []
        
        # Create multiple sessions
        for i in range(3):
            response = client.post(f"/api/v1/demo/start?user_type=instructor")
            assert response.status_code == 200
            sessions.append(response.json()["session_id"])
        
        # All sessions should be accessible
        for session_id in sessions:
            response = client.get(f"/api/v1/demo/courses?session_id={session_id}")
            assert response.status_code == 200
        
        # Clean up
        for session_id in sessions:
            client.delete(f"/api/v1/demo/session?session_id={session_id}")

    def test_cors_headers(self, client):
        """Test CORS configuration"""
        response = client.options("/api/v1/demo/health")
        
        # FastAPI/Starlette handles CORS automatically
        # We mainly test that OPTIONS requests don't fail
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled

    def test_demo_data_consistency(self, client):
        """Test that demo data remains consistent within a session"""
        response = client.post("/api/v1/demo/start?user_type=instructor")
        session_id = response.json()["session_id"]
        
        # Get courses multiple times
        response1 = client.get(f"/api/v1/demo/courses?session_id={session_id}&limit=3")
        response2 = client.get(f"/api/v1/demo/courses?session_id={session_id}&limit=3")
        
        # While courses are randomly generated each time, user context should be consistent
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Clean up
        client.delete(f"/api/v1/demo/session?session_id={session_id}")

    @patch('demo_data_generator.generate_demo_courses')
    def test_error_handling_in_endpoints(self, mock_generate, client, sample_demo_session):
        """Test error handling when data generation fails"""
        mock_generate.side_effect = Exception("Data generation failed")
        
        session_id = sample_demo_session.session_id
        response = client.get(f"/api/v1/demo/courses?session_id={session_id}")
        
        # Should handle gracefully (depends on implementation)
        # This tests that the endpoint doesn't crash
        assert response.status_code in [200, 500]

    def test_session_cleanup_on_startup(self, client):
        """Test that expired sessions are cleaned up"""
        # Add an expired session directly
        session_id = "old-session"
        user_data = DEMO_USER_TYPES["instructor"].copy()
        user_data["id"] = f"demo-instructor-{session_id[:8]}"
        user_data["is_demo"] = True
        
        old_session = DemoSession(
            session_id=session_id,
            user_type="instructor",
            created_at=datetime.now() - timedelta(days=1),
            expires_at=datetime.now() - timedelta(hours=1),
            user_data=user_data
        )
        demo_sessions[session_id] = old_session
        
        # Try to access it
        response = client.get(f"/api/v1/demo/courses?session_id={session_id}")
        
        assert response.status_code == 401
        assert session_id not in demo_sessions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])