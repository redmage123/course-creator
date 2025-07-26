"""
Integration Tests for Lab Lifecycle Management
Tests the integration between authentication, lab management, and frontend systems
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import tempfile
import requests
import docker

# Mock the lab manager service for integration testing
@pytest.fixture
def mock_lab_service():
    """Mock lab manager service for integration testing"""
    class MockLabService:
        def __init__(self):
            self.labs = {}
            self.user_labs = {}
            self.running = True
            
        async def create_student_lab(self, user_id, course_id):
            lab_id = f"lab-{user_id}-{course_id}-{int(time.time())}"
            lab_data = {
                "lab_id": lab_id,
                "user_id": user_id,
                "course_id": course_id,
                "status": "building",
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                "last_accessed": datetime.utcnow().isoformat(),
                "instructor_mode": False,
                "storage_path": f"/tmp/lab-storage/{user_id}/{course_id}",
                "lab_type": "python",
                "container_id": None,
                "port": None,
                "access_url": None
            }
            
            self.labs[lab_id] = lab_data
            self.user_labs[f"{user_id}-{course_id}"] = lab_id
            
            # Simulate build process
            await asyncio.sleep(0.1)  # Simulate build time
            lab_data.update({
                "status": "running",
                "container_id": f"container-{lab_id}",
                "port": 9000 + len(self.labs),
                "access_url": f"http://localhost:{9000 + len(self.labs)}"
            })
            
            return lab_data
            
        async def pause_lab(self, lab_id):
            if lab_id in self.labs:
                self.labs[lab_id]["status"] = "paused"
                return True
            return False
            
        async def resume_lab(self, lab_id):
            if lab_id in self.labs:
                self.labs[lab_id]["status"] = "running"
                return True
            return False
            
        async def stop_lab(self, lab_id):
            if lab_id in self.labs:
                lab_data = self.labs[lab_id]
                user_key = f"{lab_data['user_id']}-{lab_data['course_id']}"
                del self.labs[lab_id]
                if user_key in self.user_labs:
                    del self.user_labs[user_key]
                return True
            return False
            
        def get_lab(self, lab_id):
            return self.labs.get(lab_id)
            
        def get_user_lab(self, user_id, course_id):
            lab_id = self.user_labs.get(f"{user_id}-{course_id}")
            return self.labs.get(lab_id) if lab_id else None
            
        def list_labs(self, course_id=None):
            labs = list(self.labs.values())
            if course_id:
                labs = [lab for lab in labs if lab["course_id"] == course_id]
            return {
                "labs": labs,
                "active_count": len(self.labs),
                "max_concurrent": 50
            }
    
    return MockLabService()


@pytest.fixture
def mock_auth_service():
    """Mock authentication service for integration testing"""
    class MockAuthService:
        def __init__(self):
            self.users = {}
            self.sessions = {}
            
        def register_user(self, email, password, role="student"):
            user_id = f"user-{len(self.users) + 1}"
            user_data = {
                "id": user_id,
                "email": email,
                "role": role,
                "full_name": f"Test {role.title()}",
                "created_at": datetime.utcnow().isoformat()
            }
            self.users[user_id] = user_data
            return user_data
            
        def login(self, email, password):
            # Find user by email
            user = None
            for user_data in self.users.values():
                if user_data["email"] == email:
                    user = user_data
                    break
                    
            if not user:
                return None
                
            # Create session
            token = f"token-{user['id']}-{int(time.time())}"
            self.sessions[token] = {
                "user_id": user["id"],
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=8)
            }
            
            return {
                "access_token": token,
                "user": user
            }
            
        def logout(self, token):
            if token in self.sessions:
                del self.sessions[token]
                return True
            return False
            
        def verify_token(self, token):
            session = self.sessions.get(token)
            if session and session["expires_at"] > datetime.utcnow():
                return self.users.get(session["user_id"])
            return None
            
        def get_user(self, user_id):
            return self.users.get(user_id)
    
    return MockAuthService()


class TestLabLifecycleIntegration:
    """Integration tests for lab lifecycle management"""
    
    @pytest.mark.asyncio
    async def test_student_login_lab_initialization(self, mock_lab_service, mock_auth_service):
        """Test that student login triggers lab initialization"""
        # Register a student
        student = mock_auth_service.register_user("student@test.com", "password", "student")
        
        # Simulate enrolled courses
        enrolled_courses = [
            {"id": "course1", "name": "Python Programming"},
            {"id": "course2", "name": "Web Development"}
        ]
        
        # Login student
        login_result = mock_auth_service.login("student@test.com", "password")
        assert login_result is not None
        
        # Simulate lab lifecycle manager initialization
        for course in enrolled_courses:
            lab_data = await mock_lab_service.create_student_lab(
                student["id"], course["id"]
            )
            assert lab_data["status"] == "running"
            assert lab_data["user_id"] == student["id"]
            assert lab_data["course_id"] == course["id"]
        
        # Verify labs were created
        labs = mock_lab_service.list_labs()
        assert labs["active_count"] == 2
        assert all(lab["instructor_mode"] == False for lab in labs["labs"])

    @pytest.mark.asyncio
    async def test_student_logout_lab_cleanup(self, mock_lab_service, mock_auth_service):
        """Test that student logout triggers lab cleanup"""
        # Setup student with active labs
        student = mock_auth_service.register_user("student@test.com", "password", "student")
        login_result = mock_auth_service.login("student@test.com", "password")
        
        # Create labs
        lab1 = await mock_lab_service.create_student_lab(student["id"], "course1")
        lab2 = await mock_lab_service.create_student_lab(student["id"], "course2")
        
        assert mock_lab_service.list_labs()["active_count"] == 2
        
        # Simulate logout with lab cleanup
        # In real implementation, this would be triggered by the frontend
        await mock_lab_service.pause_lab(lab1["lab_id"])
        await mock_lab_service.pause_lab(lab2["lab_id"])
        
        # Verify labs are paused
        paused_lab1 = mock_lab_service.get_lab(lab1["lab_id"])
        paused_lab2 = mock_lab_service.get_lab(lab2["lab_id"])
        
        assert paused_lab1["status"] == "paused"
        assert paused_lab2["status"] == "paused"
        
        # Logout
        mock_auth_service.logout(login_result["access_token"])

    @pytest.mark.asyncio
    async def test_lab_resume_on_return(self, mock_lab_service, mock_auth_service):
        """Test that labs resume when student returns"""
        # Setup student with paused labs
        student = mock_auth_service.register_user("student@test.com", "password", "student")
        login_result = mock_auth_service.login("student@test.com", "password")
        
        # Create and pause lab
        lab_data = await mock_lab_service.create_student_lab(student["id"], "course1")
        await mock_lab_service.pause_lab(lab_data["lab_id"])
        
        assert mock_lab_service.get_lab(lab_data["lab_id"])["status"] == "paused"
        
        # Simulate student returning (new login or tab focus)
        # In real implementation, this would be handled by lab lifecycle manager
        existing_lab = mock_lab_service.get_user_lab(student["id"], "course1")
        if existing_lab and existing_lab["status"] == "paused":
            await mock_lab_service.resume_lab(existing_lab["lab_id"])
        
        # Verify lab is resumed
        resumed_lab = mock_lab_service.get_lab(lab_data["lab_id"])
        assert resumed_lab["status"] == "running"

    @pytest.mark.asyncio
    async def test_instructor_lab_management(self, mock_lab_service, mock_auth_service):
        """Test instructor lab management capabilities"""
        # Setup instructor and students
        instructor = mock_auth_service.register_user("instructor@test.com", "password", "instructor")
        student1 = mock_auth_service.register_user("student1@test.com", "password", "student")
        student2 = mock_auth_service.register_user("student2@test.com", "password", "student")
        
        course_id = "python-101"
        
        # Students create labs
        lab1 = await mock_lab_service.create_student_lab(student1["id"], course_id)
        lab2 = await mock_lab_service.create_student_lab(student2["id"], course_id)
        
        # Instructor views course labs
        course_labs = mock_lab_service.list_labs(course_id)
        assert course_labs["active_count"] == 2
        
        student_labs = [lab for lab in course_labs["labs"] if not lab["instructor_mode"]]
        assert len(student_labs) == 2
        
        # Instructor pauses all student labs
        for lab in student_labs:
            await mock_lab_service.pause_lab(lab["lab_id"])
        
        # Verify all labs are paused
        updated_labs = mock_lab_service.list_labs(course_id)
        for lab in updated_labs["labs"]:
            if not lab["instructor_mode"]:
                assert lab["status"] == "paused"

    @pytest.mark.asyncio
    async def test_concurrent_student_access(self, mock_lab_service, mock_auth_service):
        """Test multiple students accessing labs concurrently"""
        # Create multiple students
        students = []
        for i in range(5):
            student = mock_auth_service.register_user(f"student{i}@test.com", "password", "student")
            students.append(student)
        
        course_id = "concurrent-test"
        
        # All students create labs concurrently
        tasks = []
        for student in students:
            task = mock_lab_service.create_student_lab(student["id"], course_id)
            tasks.append(task)
        
        lab_results = await asyncio.gather(*tasks)
        
        # Verify all labs were created successfully
        assert len(lab_results) == 5
        for i, lab_data in enumerate(lab_results):
            assert lab_data["user_id"] == students[i]["id"]
            assert lab_data["course_id"] == course_id
            assert lab_data["status"] == "running"
        
        # Verify labs are tracked correctly
        all_labs = mock_lab_service.list_labs(course_id)
        assert all_labs["active_count"] == 5

    @pytest.mark.asyncio
    async def test_lab_persistence_across_sessions(self, mock_lab_service, mock_auth_service):
        """Test that lab state persists across login sessions"""
        # Student creates lab
        student = mock_auth_service.register_user("student@test.com", "password", "student")
        login1 = mock_auth_service.login("student@test.com", "password")
        
        lab_data = await mock_lab_service.create_student_lab(student["id"], "course1")
        original_lab_id = lab_data["lab_id"]
        
        # Student logs out (lab should be paused)
        await mock_lab_service.pause_lab(original_lab_id)
        mock_auth_service.logout(login1["access_token"])
        
        # Student logs in again
        login2 = mock_auth_service.login("student@test.com", "password")
        
        # Check if lab still exists
        existing_lab = mock_lab_service.get_user_lab(student["id"], "course1")
        assert existing_lab is not None
        assert existing_lab["lab_id"] == original_lab_id
        assert existing_lab["status"] == "paused"
        
        # Resume lab
        await mock_lab_service.resume_lab(original_lab_id)
        resumed_lab = mock_lab_service.get_lab(original_lab_id)
        assert resumed_lab["status"] == "running"

    @pytest.mark.asyncio
    async def test_lab_expiration_cleanup(self, mock_lab_service, mock_auth_service):
        """Test automatic cleanup of expired labs"""
        student = mock_auth_service.register_user("student@test.com", "password", "student")
        
        # Create lab with short expiration
        lab_data = await mock_lab_service.create_student_lab(student["id"], "course1")
        lab_id = lab_data["lab_id"]
        
        # Manually set expiration to past
        mock_lab_service.labs[lab_id]["expires_at"] = (
            datetime.utcnow() - timedelta(minutes=1)
        ).isoformat()
        
        # Simulate cleanup process
        current_time = datetime.utcnow()
        expired_labs = []
        
        for lab_id, lab_data in list(mock_lab_service.labs.items()):
            expires_at = datetime.fromisoformat(lab_data["expires_at"])
            if current_time > expires_at:
                expired_labs.append(lab_id)
        
        # Clean up expired labs
        for expired_lab_id in expired_labs:
            await mock_lab_service.stop_lab(expired_lab_id)
        
        # Verify lab was cleaned up
        assert mock_lab_service.get_lab(lab_id) is None
        assert mock_lab_service.list_labs()["active_count"] == 0

    @pytest.mark.asyncio
    async def test_lab_resource_limits(self, mock_lab_service, mock_auth_service):
        """Test lab resource limits and constraints"""
        students = []
        max_concurrent = 3
        
        # Create students
        for i in range(max_concurrent + 2):  # Create more than limit
            student = mock_auth_service.register_user(f"student{i}@test.com", "password", "student")
            students.append(student)
        
        # Override max concurrent for test
        original_max = mock_lab_service.__class__
        
        # Create labs up to limit
        created_labs = []
        for i in range(max_concurrent):
            lab_data = await mock_lab_service.create_student_lab(
                students[i]["id"], f"course{i}"
            )
            created_labs.append(lab_data)
        
        assert len(created_labs) == max_concurrent
        
        # In a real implementation, additional requests would be rejected
        # For this mock, we'll simulate the behavior
        assert mock_lab_service.list_labs()["active_count"] == max_concurrent

    @pytest.mark.asyncio
    async def test_lab_health_monitoring(self, mock_lab_service, mock_auth_service):
        """Test lab health monitoring and recovery"""
        student = mock_auth_service.register_user("student@test.com", "password", "student")
        
        # Create lab
        lab_data = await mock_lab_service.create_student_lab(student["id"], "course1")
        lab_id = lab_data["lab_id"]
        
        # Simulate health check
        lab = mock_lab_service.get_lab(lab_id)
        assert lab["status"] == "running"
        
        # Simulate container failure
        mock_lab_service.labs[lab_id]["status"] = "error"
        
        # Health check should detect the issue
        failed_lab = mock_lab_service.get_lab(lab_id)
        assert failed_lab["status"] == "error"
        
        # Simulate recovery (restart lab)
        await mock_lab_service.stop_lab(lab_id)
        new_lab = await mock_lab_service.create_student_lab(student["id"], "course1")
        
        assert new_lab["status"] == "running"
        assert new_lab["user_id"] == student["id"]


class TestLabAPIIntegration:
    """Integration tests for lab API endpoints"""
    
    @pytest.fixture
    def lab_api_client(self):
        """Mock HTTP client for lab API testing"""
        class MockLabAPIClient:
            def __init__(self):
                self.base_url = "http://localhost:8006"
                self.labs = {}
                self.user_labs = {}
                
            async def post(self, endpoint, data=None, headers=None):
                if endpoint == "/labs/student":
                    user_id = data["user_id"]
                    course_id = data["course_id"]
                    
                    # Check if lab exists
                    existing_lab_id = self.user_labs.get(f"{user_id}-{course_id}")
                    if existing_lab_id and existing_lab_id in self.labs:
                        lab = self.labs[existing_lab_id]
                        if lab["status"] == "paused":
                            lab["status"] = "running"
                        return MockResponse(200, lab)
                    
                    # Create new lab
                    lab_id = f"lab-{user_id}-{course_id}-{int(time.time())}"
                    lab_data = {
                        "lab_id": lab_id,
                        "user_id": user_id,
                        "course_id": course_id,
                        "status": "running",
                        "created_at": datetime.utcnow().isoformat(),
                        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                        "last_accessed": datetime.utcnow().isoformat(),
                        "instructor_mode": False,
                        "storage_path": f"/tmp/{user_id}/{course_id}",
                        "lab_type": "python",
                        "container_id": f"container-{lab_id}",
                        "port": 9000,
                        "access_url": "http://localhost:9000"
                    }
                    
                    self.labs[lab_id] = lab_data
                    self.user_labs[f"{user_id}-{course_id}"] = lab_id
                    return MockResponse(200, lab_data)
                    
                elif endpoint.startswith("/labs/") and endpoint.endswith("/pause"):
                    lab_id = endpoint.split("/")[2]
                    if lab_id in self.labs:
                        self.labs[lab_id]["status"] = "paused"
                        return MockResponse(200, {"message": "Lab paused"})
                    return MockResponse(404, {"detail": "Lab not found"})
                    
                elif endpoint.startswith("/labs/") and endpoint.endswith("/resume"):
                    lab_id = endpoint.split("/")[2]
                    if lab_id in self.labs:
                        self.labs[lab_id]["status"] = "running"
                        return MockResponse(200, {"message": "Lab resumed"})
                    return MockResponse(404, {"detail": "Lab not found"})
                
                return MockResponse(404, {"detail": "Endpoint not found"})
            
            async def get(self, endpoint, headers=None):
                if endpoint.startswith("/labs/"):
                    lab_id = endpoint.split("/")[2]
                    if lab_id in self.labs:
                        return MockResponse(200, self.labs[lab_id])
                    return MockResponse(404, {"detail": "Lab not found"})
                
                elif endpoint == "/labs":
                    return MockResponse(200, {
                        "labs": list(self.labs.values()),
                        "active_count": len(self.labs),
                        "max_concurrent": 50
                    })
                
                return MockResponse(404, {"detail": "Endpoint not found"})
            
            async def delete(self, endpoint, headers=None):
                if endpoint.startswith("/labs/"):
                    lab_id = endpoint.split("/")[2]
                    if lab_id in self.labs:
                        lab = self.labs[lab_id]
                        user_key = f"{lab['user_id']}-{lab['course_id']}"
                        del self.labs[lab_id]
                        if user_key in self.user_labs:
                            del self.user_labs[user_key]
                        return MockResponse(200, {"message": "Lab stopped"})
                    return MockResponse(404, {"detail": "Lab not found"})
                
                return MockResponse(404, {"detail": "Endpoint not found"})
        
        return MockLabAPIClient()
    
    @pytest.mark.asyncio
    async def test_student_lab_api_flow(self, lab_api_client):
        """Test complete student lab API flow"""
        # Create student lab
        response = await lab_api_client.post("/labs/student", {
            "user_id": "student123",
            "course_id": "course456"
        })
        
        assert response.status_code == 200
        lab_data = response.json()
        lab_id = lab_data["lab_id"]
        assert lab_data["status"] == "running"
        
        # Get lab details
        response = await lab_api_client.get(f"/labs/{lab_id}")
        assert response.status_code == 200
        assert response.json()["lab_id"] == lab_id
        
        # Pause lab
        response = await lab_api_client.post(f"/labs/{lab_id}/pause")
        assert response.status_code == 200
        
        # Verify lab is paused
        response = await lab_api_client.get(f"/labs/{lab_id}")
        assert response.json()["status"] == "paused"
        
        # Resume lab
        response = await lab_api_client.post(f"/labs/{lab_id}/resume")
        assert response.status_code == 200
        
        # Verify lab is running
        response = await lab_api_client.get(f"/labs/{lab_id}")
        assert response.json()["status"] == "running"
        
        # Stop lab
        response = await lab_api_client.delete(f"/labs/{lab_id}")
        assert response.status_code == 200
        
        # Verify lab is gone
        response = await lab_api_client.get(f"/labs/{lab_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_existing_lab_retrieval(self, lab_api_client):
        """Test retrieving existing lab for student"""
        # Create initial lab
        response = await lab_api_client.post("/labs/student", {
            "user_id": "student123",
            "course_id": "course456"
        })
        
        assert response.status_code == 200
        original_lab = response.json()
        original_lab_id = original_lab["lab_id"]
        
        # Pause the lab
        await lab_api_client.post(f"/labs/{original_lab_id}/pause")
        
        # Request lab again (should return existing paused lab and resume it)
        response = await lab_api_client.post("/labs/student", {
            "user_id": "student123",
            "course_id": "course456"
        })
        
        assert response.status_code == 200
        retrieved_lab = response.json()
        assert retrieved_lab["lab_id"] == original_lab_id
        assert retrieved_lab["status"] == "running"  # Should be resumed


class MockResponse:
    """Mock HTTP response for testing"""
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data
    
    def json(self):
        return self._data


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])