"""
Integration tests for demo service
Tests demo service integration with other platform components and external dependencies
"""

import pytest
import requests
import asyncio
from datetime import datetime, timedelta
import json
import time

from tests.framework.test_config import TestConfig
from tests.utils import wait_for_service, create_test_session


class TestDemoServiceIntegration:
    """Integration tests for demo service with other platform components"""

    @classmethod
    def setup_class(cls):
        """Setup test class with configuration"""
        cls.config = TestConfig()
        base_url = "http://localhost"  # Default for integration tests
        cls.demo_base_url = f"{base_url}:8010/api/v1/demo"
        cls.frontend_base_url = f"{base_url}:3000"
        
        # Wait for services to be ready
        wait_for_service(cls.demo_base_url + "/health", timeout=30)

    def test_demo_service_health_integration(self):
        """Test demo service health check integration"""
        response = requests.get(f"{self.demo_base_url}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "demo-service"
        assert "active_sessions" in data
        assert isinstance(data["active_sessions"], int)

    def test_demo_session_lifecycle_integration(self):
        """Test complete demo session lifecycle"""
        # 1. Start demo session
        start_response = requests.post(f"{self.demo_base_url}/start?user_type=instructor")
        assert start_response.status_code == 200
        
        session_data = start_response.json()
        session_id = session_data["session_id"]
        
        try:
            # 2. Get session info
            info_response = requests.get(f"{self.demo_base_url}/session/info?session_id={session_id}")
            assert info_response.status_code == 200
            
            info = info_response.json()
            assert info["session_id"] == session_id
            assert info["user_type"] == "instructor"
            
            # 3. Use session to get courses
            courses_response = requests.get(f"{self.demo_base_url}/courses?session_id={session_id}")
            assert courses_response.status_code == 200
            
            courses_data = courses_response.json()
            assert "courses" in courses_data
            assert len(courses_data["courses"]) > 0
            
            # 4. Create a course using the session
            course_data = {
                "title": "Integration Test Course",
                "description": "A course created during integration testing"
            }
            
            create_response = requests.post(
                f"{self.demo_base_url}/course/create?session_id={session_id}",
                json=course_data
            )
            assert create_response.status_code == 200
            
            created_course = create_response.json()["course"]
            assert created_course["title"] == "Integration Test Course"
            assert created_course["ai_generated"] is True
            
        finally:
            # 5. Clean up session
            delete_response = requests.delete(f"{self.demo_base_url}/session?session_id={session_id}")
            assert delete_response.status_code == 200

    def test_demo_user_type_workflows(self):
        """Test different user type workflows end-to-end"""
        user_types = ["instructor", "student", "admin"]
        sessions = []
        
        try:
            # Create sessions for each user type
            for user_type in user_types:
                response = requests.post(f"{self.demo_base_url}/start?user_type={user_type}")
                assert response.status_code == 200
                
                session_data = response.json()
                sessions.append((session_data["session_id"], user_type))
            
            # Test user-specific endpoints
            for session_id, user_type in sessions:
                # All users can get courses
                courses_response = requests.get(f"{self.demo_base_url}/courses?session_id={session_id}")
                assert courses_response.status_code == 200
                
                # Only instructors and admins can see students
                students_response = requests.get(f"{self.demo_base_url}/students?session_id={session_id}")
                if user_type in ["instructor", "admin"]:
                    assert students_response.status_code == 200
                else:
                    assert students_response.status_code == 403
                
                # All users can get analytics (different views)
                analytics_response = requests.get(f"{self.demo_base_url}/analytics?session_id={session_id}")
                assert analytics_response.status_code == 200
                
                analytics_data = analytics_response.json()["analytics"]
                
                # Validate user-specific analytics structure
                if user_type == "instructor":
                    assert "overview" in analytics_data
                    assert "student_progress" in analytics_data
                elif user_type == "student":
                    assert "learning_progress" in analytics_data
                    assert "weekly_activity" in analytics_data
                elif user_type == "admin":
                    assert "platform_overview" in analytics_data
                    assert "growth_metrics" in analytics_data
                
        finally:
            # Clean up all sessions
            for session_id, _ in sessions:
                requests.delete(f"{self.demo_base_url}/session?session_id={session_id}")

    def test_demo_data_richness_integration(self):
        """Test that demo data is rich and realistic across all endpoints"""
        # Start instructor session
        start_response = requests.post(f"{self.demo_base_url}/start?user_type=instructor")
        session_id = start_response.json()["session_id"]
        
        try:
            # Test courses have comprehensive data
            courses_response = requests.get(f"{self.demo_base_url}/courses?session_id={session_id}&limit=5")
            courses_data = courses_response.json()
            
            for course in courses_data["courses"]:
                # Validate rich course data
                assert "modules" in course and len(course["modules"]) > 0
                assert "skills_taught" in course and len(course["skills_taught"]) > 0
                assert "instructor" in course
                assert course["enrollment_count"] > 0
                assert 0 <= course["completion_rate"] <= 100
                assert 0 <= course["rating"] <= 5
            
            # Test students have detailed profiles
            students_response = requests.get(f"{self.demo_base_url}/students?session_id={session_id}")
            students_data = students_response.json()
            
            for student in students_data["students"]:
                assert "quiz_scores" in student and len(student["quiz_scores"]) > 0
                assert "achievements" in student
                assert student["time_spent"] > 0
                assert "last_active" in student
            
            # Test labs have complete specifications
            labs_response = requests.get(f"{self.demo_base_url}/labs?session_id={session_id}")
            labs_data = labs_response.json()
            
            for lab in labs_data["labs"]:
                assert "technologies" in lab and len(lab["technologies"]) > 0
                assert "learning_objectives" in lab
                assert "container_resources" in lab
                assert lab["estimated_time"] > 0
            
            # Test feedback has sentiment analysis
            feedback_response = requests.get(f"{self.demo_base_url}/feedback?session_id={session_id}")
            feedback_data = feedback_response.json()
            
            for review in feedback_data["feedback"]:
                assert "sentiment" in review
                assert "topics_mentioned" in review
                assert review["rating"] in range(1, 6)
                assert len(review["comment"]) > 0
                
        finally:
            requests.delete(f"{self.demo_base_url}/session?session_id={session_id}")

    def test_demo_analytics_time_series_integration(self):
        """Test analytics time series data generation"""
        start_response = requests.post(f"{self.demo_base_url}/start?user_type=instructor")
        session_id = start_response.json()["session_id"]
        
        try:
            timeframes = ["7d", "30d", "90d", "1y"]
            
            for timeframe in timeframes:
                response = requests.get(f"{self.demo_base_url}/analytics?session_id={session_id}&timeframe={timeframe}")
                assert response.status_code == 200
                
                analytics = response.json()["analytics"]
                assert analytics["timeframe"] == timeframe
                
                # Validate time series data
                progress_data = analytics["student_progress"]
                assert len(progress_data) > 0
                
                # Check data has proper date progression
                dates = [item["date"] for item in progress_data]
                parsed_dates = [datetime.fromisoformat(date) for date in dates]
                
                # Should be in chronological order
                assert parsed_dates == sorted(parsed_dates)
                
        finally:
            requests.delete(f"{self.demo_base_url}/session?session_id={session_id}")

    def test_demo_session_expiration_integration(self):
        """Test session expiration handling in integration environment"""
        start_response = requests.post(f"{self.demo_base_url}/start?user_type=instructor")
        session_id = start_response.json()["session_id"]
        
        # Verify session works initially
        response = requests.get(f"{self.demo_base_url}/courses?session_id={session_id}")
        assert response.status_code == 200
        
        # Get session info to check expiration time
        info_response = requests.get(f"{self.demo_base_url}/session/info?session_id={session_id}")
        assert info_response.status_code == 200
        
        info = info_response.json()
        assert info["minutes_remaining"] > 0
        assert info["minutes_remaining"] <= 120  # Should be <= 2 hours
        
        # Clean up
        requests.delete(f"{self.demo_base_url}/session?session_id={session_id}")

    def test_concurrent_demo_sessions_integration(self):
        """Test multiple concurrent demo sessions"""
        sessions = []
        num_sessions = 5
        
        try:
            # Create multiple concurrent sessions
            for i in range(num_sessions):
                response = requests.post(f"{self.demo_base_url}/start?user_type=instructor")
                assert response.status_code == 200
                sessions.append(response.json()["session_id"])
            
            # All sessions should work independently
            for session_id in sessions:
                courses_response = requests.get(f"{self.demo_base_url}/courses?session_id={session_id}&limit=2")
                assert courses_response.status_code == 200
                
                # Each session should have different course data (random generation)
                courses = courses_response.json()["courses"]
                assert len(courses) == 2
            
            # Check service health with multiple active sessions
            health_response = requests.get(f"{self.demo_base_url}/health")
            assert health_response.status_code == 200
            
            health_data = health_response.json()
            assert health_data["active_sessions"] >= num_sessions
            
        finally:
            # Clean up all sessions
            for session_id in sessions:
                requests.delete(f"{self.demo_base_url}/session?session_id={session_id}")

    def test_demo_course_creation_simulation_integration(self):
        """Test AI course creation simulation with realistic timing"""
        start_response = requests.post(f"{self.demo_base_url}/start?user_type=instructor")
        session_id = start_response.json()["session_id"]
        
        try:
            course_data = {
                "title": "AI-Generated Integration Test Course",
                "description": "Testing the AI course generation simulation"
            }
            
            # Measure response time (should simulate AI processing delay)
            start_time = time.time()
            
            response = requests.post(
                f"{self.demo_base_url}/course/create?session_id={session_id}",
                json=course_data
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            assert response.status_code == 200
            
            # Should have simulated processing delay (around 2 seconds)
            assert processing_time >= 1.5
            assert processing_time <= 5.0
            
            created_course = response.json()["course"]
            
            # Validate AI-generated content
            assert created_course["ai_generated"] is True
            assert created_course["title"] == course_data["title"]
            assert len(created_course["modules"]) > 0
            
            # Should have realistic course structure
            for module in created_course["modules"]:
                assert "lessons" in module
                assert "quizzes" in module
                assert module["lessons"] > 0
            
        finally:
            requests.delete(f"{self.demo_base_url}/session?session_id={session_id}")

    def test_demo_service_error_recovery_integration(self):
        """Test demo service error handling and recovery"""
        # Test with invalid session ID
        response = requests.get(f"{self.demo_base_url}/courses?session_id=invalid-session")
        assert response.status_code == 404
        
        error_data = response.json()
        assert "Demo session not found" in error_data["detail"]
        
        # Test with malformed requests
        response = requests.post(f"{self.demo_base_url}/start?user_type=")
        assert response.status_code == 400
        
        # Service should still be healthy after errors
        health_response = requests.get(f"{self.demo_base_url}/health")
        assert health_response.status_code == 200

    def test_demo_data_consistency_across_endpoints(self):
        """Test data consistency across different endpoints within a session"""
        start_response = requests.post(f"{self.demo_base_url}/start?user_type=instructor")
        session_id = start_response.json()["session_id"]
        session_user = start_response.json()["user"]
        
        try:
            # Get session info
            info_response = requests.get(f"{self.demo_base_url}/session/info?session_id={session_id}")
            info_user = info_response.json()["user"]
            
            # User data should be consistent
            assert session_user["name"] == info_user["name"]
            assert session_user["role"] == info_user["role"]
            assert session_user["organization"] == info_user["organization"]
            
            # Get analytics - should reflect user context
            analytics_response = requests.get(f"{self.demo_base_url}/analytics?session_id={session_id}")
            analytics = analytics_response.json()["analytics"]
            
            # Instructor analytics should have instructor-specific data
            assert "overview" in analytics
            assert "student_progress" in analytics
            assert "course_performance" in analytics
            
        finally:
            requests.delete(f"{self.demo_base_url}/session?session_id={session_id}")

    def test_demo_service_performance_integration(self):
        """Test demo service performance under load"""
        sessions = []
        
        try:
            # Create multiple sessions quickly
            start_time = time.time()
            
            for i in range(10):
                response = requests.post(f"{self.demo_base_url}/start?user_type=instructor")
                assert response.status_code == 200
                sessions.append(response.json()["session_id"])
            
            session_creation_time = time.time() - start_time
            
            # Should create sessions quickly (< 5 seconds for 10 sessions)
            assert session_creation_time < 5.0
            
            # Test concurrent data requests
            start_time = time.time()
            
            for session_id in sessions[:5]:  # Test first 5
                courses_response = requests.get(f"{self.demo_base_url}/courses?session_id={session_id}&limit=3")
                assert courses_response.status_code == 200
            
            data_fetch_time = time.time() - start_time
            
            # Should handle multiple concurrent requests efficiently
            assert data_fetch_time < 10.0
            
        finally:
            # Clean up
            for session_id in sessions:
                requests.delete(f"{self.demo_base_url}/session?session_id={session_id}")

    @pytest.mark.skip(reason="Frontend integration test - requires running frontend")
    def test_frontend_demo_integration(self):
        """Test integration between frontend and demo service"""
        # This would test the actual frontend demo button integration
        # Requires a running frontend service and potentially browser automation
        
        try:
            # Test frontend health
            frontend_response = requests.get(f"{self.frontend_base_url}/health")
            assert frontend_response.status_code == 200
            
            # Test demo API proxy through frontend nginx
            demo_health_response = requests.get(f"{self.frontend_base_url}/api/v1/demo/health")
            assert demo_health_response.status_code == 200
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Frontend service not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])