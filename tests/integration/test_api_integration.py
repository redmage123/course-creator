"""
Integration tests for API endpoints.
Tests end-to-end workflows between different services.
"""

import pytest
import requests
import json
import time
from datetime import datetime


class TestAPIIntegration:
    """Integration tests for the complete API stack."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        cls.auth_base = "http://localhost:8000"
        cls.course_base = "http://localhost:8004"
        cls.test_user = {
            "email": "integration.test@example.com",
            "username": "integrationtest",
            "full_name": "Integration Test User",
            "password": "testpass123"
        }
        cls.test_course = {
            "title": "Integration Test Course",
            "description": "A course for integration testing",
            "instructor_id": "integration-test-user-id",
            "category": "IT",
            "difficulty_level": "beginner",
            "estimated_duration": 2
        }
        cls.access_token = None
        cls.course_id = None
        
    def test_01_services_are_running(self):
        """Test that all required services are running."""
        # Test user management service
        try:
            response = requests.get(f"{self.auth_base}/health", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.RequestException:
            pytest.skip("User management service not running")
            
        # Test course management service
        try:
            response = requests.get(f"{self.course_base}/health", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.RequestException:
            pytest.skip("Course management service not running")
            
    def test_02_user_registration_flow(self):
        """Test complete user registration flow."""
        # Register new user
        response = requests.post(
            f"{self.auth_base}/auth/register",
            json=self.test_user
        )
        
        # Should succeed or user already exists
        assert response.status_code in [200, 400]
        
        if response.status_code == 400:
            # User already exists, which is fine for integration tests
            data = response.json()
            assert "already registered" in data.get("detail", "")
            
    def test_03_user_login_flow(self):
        """Test complete user login flow."""
        login_data = {
            "username": self.test_user["email"],
            "password": self.test_user["password"]
        }
        
        response = requests.post(
            f"{self.auth_base}/auth/login",
            data=login_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Store token for subsequent tests
        self.__class__.access_token = data["access_token"]
        
    def test_04_authenticated_user_profile(self):
        """Test getting user profile with authentication."""
        assert self.access_token is not None
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(f"{self.auth_base}/users/profile", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user" in data
        assert data["user"]["email"] == self.test_user["email"]
        
    def test_05_course_creation_flow(self):
        """Test complete course creation flow."""
        response = requests.post(
            f"{self.course_base}/courses",
            json=self.test_course
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == self.test_course["title"]
        assert data["description"] == self.test_course["description"]
        assert data["instructor_id"] == self.test_course["instructor_id"]
        assert "id" in data
        
        # Store course ID for subsequent tests
        self.__class__.course_id = data["id"]
        
    def test_06_course_retrieval_flow(self):
        """Test retrieving the created course."""
        assert self.course_id is not None
        
        response = requests.get(f"{self.course_base}/courses/{self.course_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == self.test_course["title"]
        assert data["id"] == self.course_id
        
    def test_07_course_list_flow(self):
        """Test retrieving all courses."""
        response = requests.get(f"{self.course_base}/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        
        # Find our test course in the list
        test_course = next((c for c in data if c["id"] == self.course_id), None)
        assert test_course is not None
        assert test_course["title"] == self.test_course["title"]
        
    def test_08_course_update_flow(self):
        """Test updating a course."""
        assert self.course_id is not None
        
        update_data = {
            "title": "Updated Integration Test Course",
            "description": "Updated description for integration testing"
        }
        
        response = requests.put(
            f"{self.course_base}/courses/{self.course_id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Course updated successfully"
        
        # Verify the update
        response = requests.get(f"{self.course_base}/courses/{self.course_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
        
    def test_09_course_publish_flow(self):
        """Test publishing a course."""
        assert self.course_id is not None
        
        response = requests.post(f"{self.course_base}/courses/{self.course_id}/publish")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Course published successfully"
        
        # Verify the course is published
        response = requests.get(f"{self.course_base}/courses/{self.course_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"
        
    def test_10_student_enrollment_flow(self):
        """Test student enrollment in a course."""
        assert self.course_id is not None
        
        enrollment_data = {
            "course_id": self.course_id,
            "student_email": "student@example.com",
            "student_name": "Test Student"
        }
        
        response = requests.post(
            f"{self.course_base}/courses/{self.course_id}/enroll",
            json=enrollment_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Student enrolled successfully"
        
        # Verify enrollment
        response = requests.get(f"{self.course_base}/courses/{self.course_id}/enrollments")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        student_enrollment = next(
            (e for e in data if e["student_email"] == enrollment_data["student_email"]),
            None
        )
        assert student_enrollment is not None
        assert student_enrollment["student_name"] == enrollment_data["student_name"]
        
    def test_11_bulk_enrollment_flow(self):
        """Test bulk student enrollment."""
        assert self.course_id is not None
        
        bulk_data = {
            "course_id": self.course_id,
            "students": [
                {"email": "bulk1@example.com", "name": "Bulk Student 1"},
                {"email": "bulk2@example.com", "name": "Bulk Student 2"},
                {"email": "bulk3@example.com", "name": "Bulk Student 3"}
            ]
        }
        
        response = requests.post(
            f"{self.course_base}/courses/{self.course_id}/bulk-enroll",
            json=bulk_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["enrolled_count"] == 3
        assert data["failed_count"] == 0
        
        # Verify bulk enrollments
        response = requests.get(f"{self.course_base}/courses/{self.course_id}/enrollments")
        assert response.status_code == 200
        data = response.json()
        
        # Should have at least 4 enrollments now (1 from previous test + 3 bulk)
        assert len(data) >= 4
        
    def test_12_course_statistics_flow(self):
        """Test getting course statistics."""
        response = requests.get(f"{self.course_base}/courses/statistics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_courses" in data
        assert "published_courses" in data
        assert "draft_courses" in data
        assert isinstance(data["total_courses"], int)
        assert data["total_courses"] >= 1  # At least our test course
        
    def test_13_instructor_courses_flow(self):
        """Test getting courses by instructor - using course list endpoint."""
        # Since there's no specific instructor endpoint, we'll test getting all courses
        # and verify our test course is in the list
        response = requests.get(f"{self.course_base}/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Should find our test course
        test_course = next((c for c in data if c.get("id") == self.course_id), None)
        assert test_course is not None
        assert test_course["instructor_id"] == self.test_course["instructor_id"]
        
    def test_14_error_handling_flows(self):
        """Test error handling for various scenarios."""
        # Test getting non-existent course
        response = requests.get(f"{self.course_base}/courses/nonexistent_id")
        assert response.status_code == 404
        
        # Test invalid authentication
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(f"{self.auth_base}/users/profile", headers=headers)
        assert response.status_code == 401
        
        # Test course creation with invalid data
        invalid_course = {"title": ""}  # Missing required fields
        response = requests.post(f"{self.course_base}/courses", json=invalid_course)
        assert response.status_code == 422
        
    def test_15_concurrent_access_flow(self):
        """Test concurrent access to the same resources."""
        import threading
        import concurrent.futures
        
        def get_course():
            response = requests.get(f"{self.course_base}/courses/{self.course_id}")
            return response.status_code == 200
        
        # Test concurrent course retrieval
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(get_course) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
        # All requests should succeed
        assert all(results)
        
    def test_16_performance_baseline(self):
        """Test basic performance characteristics."""
        # Test course list performance
        start_time = time.time()
        response = requests.get(f"{self.course_base}/courses")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Should respond within 2 seconds
        
        # Test course detail performance
        start_time = time.time()
        response = requests.get(f"{self.course_base}/courses/{self.course_id}")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second
        
    def test_17_cleanup_test_data(self):
        """Clean up test data."""
        # Delete the test course
        if self.course_id:
            response = requests.delete(f"{self.course_base}/courses/{self.course_id}")
            # Should succeed or course might already be deleted
            assert response.status_code in [200, 404]
            
        # Note: We don't delete the test user as it might be needed for other tests
        # and user deletion requires admin privileges
        
    @classmethod
    def teardown_class(cls):
        """Clean up after all tests."""
        print("\\nIntegration tests completed")
        print(f"Test user: {cls.test_user['email']}")
        if cls.course_id:
            print(f"Test course ID: {cls.course_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])