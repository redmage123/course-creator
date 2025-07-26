"""
Integration Tests for Analytics Service
Tests the full analytics workflow including API endpoints, database interactions, and service integration
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import httpx

# Import the analytics service app
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "analytics"))

from main import app

class TestAnalyticsAPIEndpoints:
    """Integration tests for analytics API endpoints"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
        self.test_student_id = "test-student-123"
        self.test_course_id = "test-course-456"
        self.test_lab_id = "test-lab-789"
        self.test_quiz_id = "test-quiz-101"
    
    @patch('main.db_pool')
    def test_health_check(self, mock_db_pool):
        """Test health check endpoint"""
        # Mock database connection
        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = None
        
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "analytics"
        assert data["version"] == "2.0.0"
        assert "timestamp" in data
    
    @patch('main.db_pool')
    @patch('main.get_current_user')
    def test_track_student_activity(self, mock_auth, mock_db_pool):
        """Test student activity tracking endpoint"""
        # Mock authentication
        mock_auth.return_value = {"id": "user-123", "role": "student"}
        
        # Mock database connection
        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = None
        
        activity_data = {
            "student_id": self.test_student_id,
            "course_id": self.test_course_id,
            "activity_type": "lab_access",
            "activity_data": {
                "lab_id": self.test_lab_id,
                "session_duration": 45
            },
            "session_id": "session-abc123"
        }
        
        response = self.client.post(
            "/activities/track",
            json=activity_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Activity tracked successfully"
        assert "activity_id" in data
        assert "timestamp" in data
    
    @patch('main.db_pool')
    @patch('main.get_current_user')
    def test_track_lab_usage(self, mock_auth, mock_db_pool):
        """Test lab usage tracking endpoint"""
        # Mock authentication
        mock_auth.return_value = {"id": "user-123", "role": "student"}
        
        # Mock database connection
        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = None
        
        lab_usage_data = {
            "student_id": self.test_student_id,
            "course_id": self.test_course_id,
            "lab_id": self.test_lab_id,
            "session_start": datetime.utcnow().isoformat(),
            "session_end": (datetime.utcnow() + timedelta(minutes=45)).isoformat(),
            "actions_performed": 25,
            "code_executions": 12,
            "errors_encountered": 3,
            "completion_status": "completed"
        }
        
        response = self.client.post(
            "/lab-usage/track",
            json=lab_usage_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Lab usage tracked successfully"
        assert "metric_id" in data
    
    @patch('main.db_pool')
    @patch('main.get_current_user')
    def test_track_quiz_performance(self, mock_auth, mock_db_pool):
        """Test quiz performance tracking endpoint"""
        # Mock authentication
        mock_auth.return_value = {"id": "user-123", "role": "student"}
        
        # Mock database connection
        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = None
        
        quiz_data = {
            "student_id": self.test_student_id,
            "course_id": self.test_course_id,
            "quiz_id": self.test_quiz_id,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": (datetime.utcnow() + timedelta(minutes=15)).isoformat(),
            "questions_total": 10,
            "questions_answered": 10,
            "questions_correct": 8,
            "answers": {"q1": "option_a", "q2": "option_c"},
            "status": "completed"
        }
        
        response = self.client.post(
            "/quiz-performance/track",
            json=quiz_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Quiz performance tracked successfully"
        assert "performance_id" in data
        assert data["score_percentage"] == 80.0
    
    @patch('main.db_pool')
    @patch('main.get_current_user')
    def test_update_student_progress(self, mock_auth, mock_db_pool):
        """Test student progress update endpoint"""
        # Mock authentication
        mock_auth.return_value = {"id": "user-123", "role": "instructor"}
        
        # Mock database connection
        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = None
        
        progress_data = {
            "student_id": self.test_student_id,
            "course_id": self.test_course_id,
            "content_item_id": "lesson-789",
            "content_type": "lesson",
            "status": "completed",
            "progress_percentage": 100.0,
            "time_spent_minutes": 30,
            "last_accessed": datetime.utcnow().isoformat(),
            "completion_date": datetime.utcnow().isoformat(),
            "mastery_score": 85.5
        }
        
        response = self.client.post(
            "/progress/update",
            json=progress_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Progress updated successfully"
        assert "progress_id" in data
        assert data["progress_percentage"] == 100.0
    
    @patch('main.db_pool')
    @patch('main.get_current_user')
    def test_get_student_analytics(self, mock_auth, mock_db_pool):
        """Test student analytics retrieval endpoint"""
        # Mock authentication
        mock_auth.return_value = {"id": "user-123", "role": "instructor"}
        
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
        
        response = self.client.get(
            f"/analytics/student/{self.test_student_id}?course_id={self.test_course_id}&days_back=30",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == self.test_student_id
        assert data["course_id"] == self.test_course_id
        assert "analysis_period" in data
        assert "activity_summary" in data
        assert "lab_metrics" in data
        assert "quiz_performance" in data
        assert "engagement_score" in data
        assert "recommendations" in data
    
    @patch('main.db_pool')
    @patch('main.get_current_user')
    def test_get_course_analytics(self, mock_auth, mock_db_pool):
        """Test course analytics retrieval endpoint"""
        # Mock authentication
        mock_auth.return_value = {"id": "user-123", "role": "instructor"}
        
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
        
        response = self.client.get(
            f"/analytics/course/{self.test_course_id}?days_back=30",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["course_id"] == self.test_course_id
        assert "analysis_period" in data
        assert "enrollment" in data
        assert data["enrollment"]["total_students"] == 25
        assert "lab_completion" in data
        assert "quiz_performance" in data
        assert "progress_distribution" in data
    
    @patch('main.db_pool')
    @patch('main.get_current_user')
    def test_batch_activity_tracking(self, mock_auth, mock_db_pool):
        """Test batch activity tracking endpoint"""
        # Mock authentication
        mock_auth.return_value = {"id": "user-123", "role": "student"}
        
        # Mock database connection
        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = None
        
        batch_activities = [
            {
                "student_id": self.test_student_id,
                "course_id": self.test_course_id,
                "activity_type": "login",
                "activity_data": {"device": "desktop"}
            },
            {
                "student_id": self.test_student_id,
                "course_id": self.test_course_id,
                "activity_type": "content_view",
                "activity_data": {"content_id": "lesson-1"}
            },
            {
                "student_id": self.test_student_id,
                "course_id": self.test_course_id,
                "activity_type": "logout",
                "activity_data": {"session_duration": 3600}
            }
        ]
        
        response = self.client.post(
            "/activities/batch",
            json=batch_activities,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Tracked 3 activities successfully"
        assert data["activities_tracked"] == 3


class TestAnalyticsServiceIntegration:
    """Test integration with other services"""
    
    @pytest.mark.asyncio
    async def test_lab_service_integration(self):
        """Test integration with lab container service"""
        # This would test the analytics client in lab service
        # For now, we'll test the client interface
        
        from lab_containers.analytics_client import AnalyticsClient
        
        client = AnalyticsClient("http://localhost:8007")
        
        # Test that client can be instantiated
        assert client.analytics_url == "http://localhost:8007"
        assert client.session is None
        
        # Test client cleanup
        await client.close()
    
    @pytest.mark.asyncio
    async def test_course_generator_integration(self):
        """Test integration with course generator service"""
        # Test the course analytics client
        
        from services.course_generator.analytics_client import CourseAnalyticsClient
        
        client = CourseAnalyticsClient("http://localhost:8007")
        
        # Test that client can be instantiated
        assert client.analytics_url == "http://localhost:8007"
        assert client.session is None
        
        # Test client cleanup
        await client.close()


class TestAnalyticsDataFlow:
    """Test end-to-end data flow scenarios"""
    
    def setup_method(self):
        """Set up test environment"""
        self.client = TestClient(app)
        self.student_id = "flow-test-student"
        self.course_id = "flow-test-course"
    
    @patch('main.db_pool')
    @patch('main.get_current_user')
    def test_complete_student_journey(self, mock_auth, mock_db_pool):
        """Test complete student learning journey analytics"""
        # Mock authentication
        mock_auth.return_value = {"id": "user-123", "role": "student"}
        
        # Mock database connection
        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = None
        
        # 1. Student logs in
        login_response = self.client.post(
            "/activities/track",
            json={
                "student_id": self.student_id,
                "course_id": self.course_id,
                "activity_type": "login",
                "activity_data": {"device": "desktop"}
            },
            headers={"Authorization": "Bearer test-token"}
        )
        assert login_response.status_code == 200
        
        # 2. Student accesses lab
        lab_response = self.client.post(
            "/lab-usage/track",
            json={
                "student_id": self.student_id,
                "course_id": self.course_id,
                "lab_id": "python-basics-lab",
                "session_start": datetime.utcnow().isoformat(),
                "actions_performed": 15,
                "code_executions": 8,
                "errors_encountered": 2,
                "completion_status": "in_progress"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        assert lab_response.status_code == 200
        
        # 3. Student takes quiz
        quiz_response = self.client.post(
            "/quiz-performance/track",
            json={
                "student_id": self.student_id,
                "course_id": self.course_id,
                "quiz_id": "python-basics-quiz",
                "start_time": datetime.utcnow().isoformat(),
                "questions_total": 5,
                "questions_answered": 5,
                "questions_correct": 4,
                "status": "completed"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        assert quiz_response.status_code == 200
        
        # 4. Progress is updated
        progress_response = self.client.post(
            "/progress/update",
            json={
                "student_id": self.student_id,
                "course_id": self.course_id,
                "content_item_id": "python-basics-module",
                "content_type": "module",
                "status": "completed",
                "progress_percentage": 100.0,
                "time_spent_minutes": 120
            },
            headers={"Authorization": "Bearer test-token"}
        )
        assert progress_response.status_code == 200
        
        # All steps should complete successfully
        assert all(resp.status_code == 200 for resp in [
            login_response, lab_response, quiz_response, progress_response
        ])


class TestAnalyticsErrorHandling:
    """Test error handling scenarios"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_unauthorized_access(self):
        """Test unauthorized access to analytics endpoints"""
        response = self.client.post(
            "/activities/track",
            json={
                "student_id": "test-student",
                "course_id": "test-course",
                "activity_type": "login"
            }
        )
        
        # Should require authentication
        assert response.status_code == 403
    
    @patch('main.get_current_user')
    def test_invalid_data_format(self, mock_auth):
        """Test handling of invalid data formats"""
        # Mock authentication
        mock_auth.return_value = {"id": "user-123", "role": "student"}
        
        # Send invalid data
        response = self.client.post(
            "/activities/track",
            json={
                "invalid_field": "invalid_value"
                # Missing required fields
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Should return validation error
        assert response.status_code == 422
    
    @patch('main.db_pool')
    @patch('main.get_current_user')
    def test_database_error_handling(self, mock_auth, mock_db_pool):
        """Test handling of database errors"""
        # Mock authentication
        mock_auth.return_value = {"id": "user-123", "role": "student"}
        
        # Mock database connection failure
        mock_db_pool.acquire.side_effect = Exception("Database connection failed")
        
        response = self.client.post(
            "/activities/track",
            json={
                "student_id": "test-student",
                "course_id": "test-course",
                "activity_type": "login"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Should handle database errors gracefully
        assert response.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])