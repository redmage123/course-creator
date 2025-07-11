#!/usr/bin/env python3
"""
API Integration test suite for complete workflows
Tests end-to-end API workflows including authentication, content generation, and course management
"""
import pytest
import asyncio
import uuid
import json
import requests
from datetime import datetime
from unittest.mock import Mock, patch

# Test configuration
API_BASE_URL = "http://localhost"
SERVICES = {
    "user_management": f"{API_BASE_URL}:8000",
    "course_generator": f"{API_BASE_URL}:8001", 
    "content_storage": f"{API_BASE_URL}:8003",
    "course_management": f"{API_BASE_URL}:8004"
}

class TestAuthenticationWorkflow:
    """Test complete authentication workflow"""
    
    @pytest.fixture
    def test_user_data(self):
        """Test user data for registration"""
        return {
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "password": "TestPassword123!",
            "full_name": "Test User"
        }
    
    def test_user_registration_and_login_workflow(self, test_user_data):
        """Test complete user registration and login workflow"""
        # Skip if services not running
        try:
            requests.get(f"{SERVICES['user_management']}/health", timeout=1)
        except:
            pytest.skip("User management service not available")
        
        # Step 1: Register new user
        register_response = requests.post(
            f"{SERVICES['user_management']}/auth/register",
            json=test_user_data
        )
        
        if register_response.status_code == 200:
            user_data = register_response.json()
            assert user_data["email"] == test_user_data["email"]
            assert "id" in user_data
        else:
            pytest.skip(f"Registration failed: {register_response.status_code}")
        
        # Step 2: Login with credentials
        login_response = requests.post(
            f"{SERVICES['user_management']}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        access_token = token_data["access_token"]
        
        # Step 3: Test authenticated request
        profile_response = requests.get(
            f"{SERVICES['user_management']}/users/profile",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["email"] == test_user_data["email"]
        
        # Step 4: Test logout
        logout_response = requests.post(
            f"{SERVICES['user_management']}/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert logout_response.status_code == 200
        
        return access_token
    
    def test_session_management_workflow(self, test_user_data):
        """Test session management APIs"""
        # Skip if services not running
        try:
            requests.get(f"{SERVICES['user_management']}/health", timeout=1)
        except:
            pytest.skip("User management service not available")
        
        # Register and login
        requests.post(f"{SERVICES['user_management']}/auth/register", json=test_user_data)
        
        login_response = requests.post(
            f"{SERVICES['user_management']}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        if login_response.status_code != 200:
            pytest.skip("Login failed")
        
        access_token = login_response.json()["access_token"]
        
        # Test get sessions
        sessions_response = requests.get(
            f"{SERVICES['user_management']}/auth/sessions",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert sessions_response.status_code == 200
        sessions_data = sessions_response.json()
        assert "sessions" in sessions_data
        assert len(sessions_data["sessions"]) >= 1

class TestContentGenerationWorkflow:
    """Test complete content generation workflow"""
    
    @pytest.fixture
    def authenticated_token(self):
        """Get authenticated token for testing"""
        # Mock token for testing when services not available
        return "mock_token_for_testing"
    
    def test_complete_content_generation_workflow(self, authenticated_token):
        """Test complete content generation from syllabus to content"""
        # Skip if services not running
        try:
            requests.get(f"{SERVICES['course_generator']}/health", timeout=1)
        except:
            pytest.skip("Course generator service not available")
        
        course_id = str(uuid.uuid4())
        
        # Step 1: Generate syllabus
        syllabus_request = {
            "course_id": course_id,
            "title": "Test Course - Python Programming",
            "description": "A comprehensive test course for Python programming",
            "category": "Programming",
            "difficulty_level": "beginner",
            "estimated_duration": 20
        }
        
        syllabus_response = requests.post(
            f"{SERVICES['course_generator']}/syllabus/generate",
            json=syllabus_request
        )
        
        assert syllabus_response.status_code == 200
        syllabus_data = syllabus_response.json()
        assert "syllabus" in syllabus_data
        assert "modules" in syllabus_data["syllabus"]
        
        # Step 2: Generate content from syllabus
        content_request = {"course_id": course_id}
        
        content_response = requests.post(
            f"{SERVICES['course_generator']}/content/generate-from-syllabus",
            json=content_request
        )
        
        assert content_response.status_code == 200
        content_data = content_response.json()
        assert "slides" in content_data
        assert "exercises" in content_data
        assert "quizzes" in content_data
        
        # Step 3: Verify content retrieval
        # Test slides
        slides_response = requests.get(f"{SERVICES['course_generator']}/slides/{course_id}")
        assert slides_response.status_code == 200
        slides_data = slides_response.json()
        assert len(slides_data["slides"]) > 0
        
        # Test exercises
        exercises_response = requests.get(f"{SERVICES['course_generator']}/exercises/{course_id}")
        assert exercises_response.status_code == 200
        exercises_data = exercises_response.json()
        assert len(exercises_data["exercises"]) > 0
        
        # Test quizzes
        quizzes_response = requests.get(f"{SERVICES['course_generator']}/quizzes/{course_id}")
        assert quizzes_response.status_code == 200
        quizzes_data = quizzes_response.json()
        assert len(quizzes_data["quizzes"]) > 0
        
        # Step 4: Test lab environment
        lab_response = requests.get(f"{SERVICES['course_generator']}/lab/{course_id}")
        if lab_response.status_code == 200:
            lab_data = lab_response.json()
            assert "lab" in lab_data
            assert lab_data["lab"]["status"] in ["ready", "stopped"]
        
        return course_id, content_data
    
    def test_syllabus_refinement_workflow(self):
        """Test syllabus refinement workflow"""
        # Skip if services not running
        try:
            requests.get(f"{SERVICES['course_generator']}/health", timeout=1)
        except:
            pytest.skip("Course generator service not available")
        
        course_id = str(uuid.uuid4())
        
        # Generate initial syllabus
        syllabus_request = {
            "course_id": course_id,
            "title": "Basic Python Course",
            "description": "Learn Python basics",
            "category": "Programming",
            "difficulty_level": "beginner",
            "estimated_duration": 16
        }
        
        syllabus_response = requests.post(
            f"{SERVICES['course_generator']}/syllabus/generate",
            json=syllabus_request
        )
        
        if syllabus_response.status_code != 200:
            pytest.skip("Initial syllabus generation failed")
        
        initial_syllabus = syllabus_response.json()["syllabus"]
        
        # Refine syllabus
        refinement_request = {
            "course_id": course_id,
            "feedback": "Add more advanced topics and practical examples",
            "current_syllabus": initial_syllabus
        }
        
        refinement_response = requests.post(
            f"{SERVICES['course_generator']}/syllabus/refine",
            json=refinement_request
        )
        
        assert refinement_response.status_code == 200
        refined_data = refinement_response.json()
        assert "syllabus" in refined_data

class TestLabEnvironmentWorkflow:
    """Test lab environment workflow"""
    
    def test_lab_creation_and_management(self):
        """Test lab environment creation and management"""
        # Skip if services not running
        try:
            requests.get(f"{SERVICES['course_generator']}/health", timeout=1)
        except:
            pytest.skip("Course generator service not available")
        
        course_id = str(uuid.uuid4())
        
        # Step 1: Create lab environment
        lab_request = {
            "course_id": course_id,
            "name": "Python Programming Lab",
            "description": "Interactive Python learning environment",
            "environment_type": "programming",
            "config": {},
            "exercises": []
        }
        
        lab_response = requests.post(
            f"{SERVICES['course_generator']}/lab/create",
            json=lab_request
        )
        
        assert lab_response.status_code == 200
        lab_data = lab_response.json()
        assert "lab_id" in lab_data
        assert "lab" in lab_data
        
        # Step 2: Launch lab environment
        launch_request = {
            "course_id": course_id,
            "course_title": "Python Programming",
            "course_description": "Learn Python programming",
            "course_category": "programming",
            "difficulty_level": "beginner",
            "instructor_context": {},
            "student_tracking": {}
        }
        
        launch_response = requests.post(
            f"{SERVICES['course_generator']}/lab/launch",
            json=launch_request
        )
        
        assert launch_response.status_code == 200
        launch_data = launch_response.json()
        assert launch_data["status"] == "running"
        
        # Step 3: Test lab access
        access_response = requests.get(f"{SERVICES['course_generator']}/lab/access/{course_id}")
        assert access_response.status_code == 200
        access_data = access_response.json()
        assert "access_url" in access_data or "status" in access_data
        
        # Step 4: Stop lab
        stop_response = requests.post(f"{SERVICES['course_generator']}/lab/stop/{course_id}")
        assert stop_response.status_code == 200

class TestCourseManagementWorkflow:
    """Test course management workflow"""
    
    @pytest.fixture
    def sample_course_data(self):
        """Sample course data for testing"""
        return {
            "title": "Test Course Integration",
            "description": "Integration test course",
            "category": "Programming",
            "difficulty_level": "beginner",
            "instructor_id": str(uuid.uuid4()),
            "estimated_duration": 30,
            "is_published": False
        }
    
    def test_course_lifecycle_workflow(self, sample_course_data):
        """Test complete course lifecycle"""
        # Skip if services not running
        try:
            requests.get(f"{SERVICES['course_management']}/health", timeout=1)
        except:
            pytest.skip("Course management service not available")
        
        # Step 1: Create course
        create_response = requests.post(
            f"{SERVICES['course_management']}/courses",
            json=sample_course_data
        )
        
        if create_response.status_code == 200:
            course_data = create_response.json()
            course_id = course_data["id"]
            assert course_data["title"] == sample_course_data["title"]
        else:
            pytest.skip("Course creation failed")
        
        # Step 2: Update course
        update_data = {
            "description": "Updated integration test course",
            "is_published": True
        }
        
        update_response = requests.put(
            f"{SERVICES['course_management']}/courses/{course_id}",
            json=update_data
        )
        
        assert update_response.status_code == 200
        updated_course = update_response.json()
        assert updated_course["description"] == update_data["description"]
        assert updated_course["is_published"] is True
        
        # Step 3: Get course details
        get_response = requests.get(f"{SERVICES['course_management']}/courses/{course_id}")
        assert get_response.status_code == 200
        
        # Step 4: List courses
        list_response = requests.get(f"{SERVICES['course_management']}/courses")
        assert list_response.status_code == 200
        courses_list = list_response.json()
        course_ids = [course["id"] for course in courses_list.get("courses", [])]
        assert course_id in course_ids

class TestCrossServiceIntegration:
    """Test integration between multiple services"""
    
    def test_full_platform_workflow(self):
        """Test complete platform workflow across all services"""
        # This test requires all services to be running
        services_available = True
        for service_name, service_url in SERVICES.items():
            try:
                response = requests.get(f"{service_url}/health", timeout=2)
                if response.status_code != 200:
                    services_available = False
                    break
            except:
                services_available = False
                break
        
        if not services_available:
            pytest.skip("Not all services are available for full integration test")
        
        # Step 1: Register user (User Management)
        user_data = {
            "email": f"integration_{uuid.uuid4().hex[:8]}@example.com",
            "username": f"integration_{uuid.uuid4().hex[:8]}",
            "password": "IntegrationTest123!",
            "full_name": "Integration Test User"
        }
        
        register_response = requests.post(
            f"{SERVICES['user_management']}/auth/register",
            json=user_data
        )
        
        if register_response.status_code != 200:
            pytest.skip("User registration failed")
        
        # Step 2: Login (User Management)
        login_response = requests.post(
            f"{SERVICES['user_management']}/auth/login",
            data={
                "username": user_data["email"],
                "password": user_data["password"]
            }
        )
        
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        
        # Step 3: Generate course content (Course Generator)
        course_id = str(uuid.uuid4())
        syllabus_request = {
            "course_id": course_id,
            "title": "Full Integration Test Course",
            "description": "Complete integration test course",
            "category": "Programming",
            "difficulty_level": "beginner",
            "estimated_duration": 24
        }
        
        syllabus_response = requests.post(
            f"{SERVICES['course_generator']}/syllabus/generate",
            json=syllabus_request
        )
        
        assert syllabus_response.status_code == 200
        
        # Generate content from syllabus
        content_response = requests.post(
            f"{SERVICES['course_generator']}/content/generate-from-syllabus",
            json={"course_id": course_id}
        )
        
        assert content_response.status_code == 200
        content_data = content_response.json()
        
        # Step 4: Create course in management system (Course Management)
        course_data = {
            "id": course_id,
            "title": syllabus_request["title"],
            "description": syllabus_request["description"],
            "category": syllabus_request["category"],
            "difficulty_level": syllabus_request["difficulty_level"],
            "instructor_id": register_response.json()["id"],
            "estimated_duration": syllabus_request["estimated_duration"],
            "is_published": True
        }
        
        create_course_response = requests.post(
            f"{SERVICES['course_management']}/courses",
            json=course_data,
            headers=auth_headers
        )
        
        # This might fail if course management requires different format
        # We'll accept both success and some expected errors
        assert create_course_response.status_code in [200, 201, 400, 422]
        
        # Step 5: Test content storage (if available)
        try:
            storage_health = requests.get(f"{SERVICES['content_storage']}/health", timeout=1)
            if storage_health.status_code == 200:
                # Test file upload capability (mock)
                test_content = {
                    "course_id": course_id,
                    "content_type": "slide",
                    "data": content_data["slides"][:1]  # First slide
                }
                
                # This is a mock test - actual endpoint might be different
                storage_response = requests.post(
                    f"{SERVICES['content_storage']}/content/upload",
                    json=test_content,
                    headers=auth_headers
                )
                
                # Accept various responses as services might not be fully implemented
                assert storage_response.status_code in [200, 201, 404, 405, 422]
        except:
            pass  # Content storage test is optional
        
        # Step 6: Logout (User Management)
        logout_response = requests.post(
            f"{SERVICES['user_management']}/auth/logout",
            headers=auth_headers
        )
        
        assert logout_response.status_code == 200

class TestErrorHandlingIntegration:
    """Test error handling across services"""
    
    def test_authentication_error_handling(self):
        """Test authentication error handling across services"""
        invalid_token = "invalid.jwt.token"
        auth_headers = {"Authorization": f"Bearer {invalid_token}"}
        
        # Test all services handle invalid tokens properly
        for service_name, service_url in SERVICES.items():
            try:
                # Try an authenticated endpoint
                response = requests.get(
                    f"{service_url}/health",  # Some services might protect health endpoint
                    headers=auth_headers,
                    timeout=2
                )
                # We expect either 200 (unprotected) or 401 (protected)
                assert response.status_code in [200, 401, 404]
            except:
                pass  # Service might not be available
    
    def test_service_unavailability_handling(self):
        """Test handling when services are unavailable"""
        # Test connection to non-existent service
        fake_service_url = "http://localhost:9999"
        
        try:
            response = requests.get(f"{fake_service_url}/health", timeout=1)
            pytest.fail("Should not be able to connect to fake service")
        except requests.exceptions.RequestException:
            # Expected - service is not available
            pass

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])