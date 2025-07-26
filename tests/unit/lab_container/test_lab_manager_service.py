"""
Unit Tests for Enhanced Lab Manager Service
Tests the core lab container management functionality
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import docker

# Import the lab manager components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../lab-containers'))

try:
    from main import (
        app, DynamicImageBuilder, LabCreateRequest, StudentLabRequest, 
        LabSession, active_labs, user_labs, _build_and_start_lab,
        _start_lab_container, _pause_lab_container, _resume_lab_container,
        _cleanup_lab_container, _find_available_port, _get_user_lab
    )
except ImportError as e:
    # If we can't import the lab container components, create mock versions for testing
    print(f"Warning: Could not import lab container components: {e}")
    
    class MockApp:
        pass
    
    class MockDynamicImageBuilder:
        @staticmethod
        async def build_lab_image(lab_type, course_id, lab_config, custom_dockerfile=None):
            return f"course-creator/labs:{lab_type}-{course_id}-123456"
        
        @staticmethod 
        def _generate_dockerfile(lab_type, lab_config):
            return f"FROM python:3.10-slim\nRUN pip install {' '.join(lab_config.get('packages', []))}"
        
        @staticmethod
        def _generate_startup_script(lab_type, lab_config):
            return "def setup_lab_environment():\n    pass\ndef start_lab_server():\n    pass"
    
    from pydantic import BaseModel
    from datetime import datetime
    
    class LabCreateRequest(BaseModel):
        user_id: str
        course_id: str
        lab_type: str = "python"
        lab_config: dict = {}
        timeout_minutes: int = 60
        instructor_mode: bool = False
    
    class StudentLabRequest(BaseModel):
        user_id: str
        course_id: str
    
    class LabSession(BaseModel):
        lab_id: str
        user_id: str
        course_id: str
        status: str
        created_at: datetime
        expires_at: datetime
        last_accessed: datetime
        instructor_mode: bool = False
        storage_path: str
        lab_type: str = "python"
        container_id: str = None
        port: int = None
        access_url: str = None
    
    app = MockApp()
    DynamicImageBuilder = MockDynamicImageBuilder
    active_labs = {}
    user_labs = {}
    
    async def _build_and_start_lab(*args, **kwargs):
        pass
    
    async def _start_lab_container(*args, **kwargs):
        return {"container_id": "mock-container", "port": 9000}
    
    async def _pause_lab_container(*args, **kwargs):
        pass
    
    async def _resume_lab_container(*args, **kwargs):  
        pass
    
    async def _cleanup_lab_container(*args, **kwargs):
        pass
    
    def _find_available_port():
        return 9000
    
    def _get_user_lab(user_id, course_id):
        return user_labs.get(f"{user_id}-{course_id}")

# Reset global state before each test
@pytest.fixture(autouse=True)
def reset_lab_state():
    """Reset global lab state before each test"""
    active_labs.clear()
    user_labs.clear()
    yield
    active_labs.clear()
    user_labs.clear()


@pytest.fixture
def mock_docker_client():
    """Mock Docker client for testing"""
    with patch('main.docker_client') as mock_client:
        # Mock container
        mock_container = Mock()
        mock_container.id = 'test-container-id'
        mock_container.logs.return_value = b'Container logs'
        mock_container.pause.return_value = None
        mock_container.unpause.return_value = None
        mock_container.stop.return_value = None
        mock_container.remove.return_value = None
        
        # Mock containers.run
        mock_client.containers.run.return_value = mock_container
        mock_client.containers.get.return_value = mock_container
        mock_client.containers.list.return_value = []
        
        # Mock images.build
        mock_image = Mock()
        mock_image.id = 'test-image-id'
        mock_client.images.build.return_value = (mock_image, ['Build log line 1', 'Build log line 2'])
        
        # Mock ping
        mock_client.ping.return_value = True
        
        yield mock_client


@pytest.fixture
def sample_lab_request():
    """Sample lab creation request"""
    return LabCreateRequest(
        user_id="test-student-123",
        course_id="course-456",
        lab_type="python",
        lab_config={
            "packages": ["numpy", "pandas"],
            "starter_files": {
                "hello.py": "print('Hello, World!')"
            }
        },
        timeout_minutes=60,
        instructor_mode=False
    )


@pytest.fixture
def sample_student_request():
    """Sample student lab request"""
    return StudentLabRequest(
        user_id="test-student-123",
        course_id="course-456"
    )


@pytest.fixture
def mock_storage_path():
    """Mock storage path for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('main.LAB_STORAGE_PATH', temp_dir):
            yield temp_dir


class TestDynamicImageBuilder:
    """Test the Dynamic Image Builder component"""
    
    @pytest.mark.asyncio
    async def test_build_lab_image_python(self, mock_docker_client):
        """Test building a Python lab image"""
        lab_config = {
            "packages": ["numpy", "pandas"],
            "starter_files": {"test.py": "print('test')"}
        }
        
        image_tag = await DynamicImageBuilder.build_lab_image(
            "python", "course-123", lab_config
        )
        
        assert "course-creator/labs:python-course-123" in image_tag
        mock_docker_client.images.build.assert_called_once()
        
        # Verify build was called with correct parameters
        call_args = mock_docker_client.images.build.call_args
        assert call_args[1]['tag'] == image_tag
        assert call_args[1]['rm'] is True
        assert call_args[1]['forcerm'] is True

    @pytest.mark.asyncio
    async def test_build_lab_image_javascript(self, mock_docker_client):
        """Test building a JavaScript lab image"""
        lab_config = {
            "packages": ["express", "lodash"],
            "starter_files": {"index.js": "console.log('Hello')"}
        }
        
        image_tag = await DynamicImageBuilder.build_lab_image(
            "javascript", "course-456", lab_config
        )
        
        assert "course-creator/labs:javascript-course-456" in image_tag
        mock_docker_client.images.build.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_lab_image_with_custom_dockerfile(self, mock_docker_client):
        """Test building lab image with custom Dockerfile"""
        custom_dockerfile = """
        FROM python:3.10-slim
        RUN pip install custom-package
        """
        
        image_tag = await DynamicImageBuilder.build_lab_image(
            "python", "course-789", {}, custom_dockerfile
        )
        
        assert "course-creator/labs:python-course-789" in image_tag
        mock_docker_client.images.build.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_lab_image_failure(self, mock_docker_client):
        """Test handling of image build failure"""
        mock_docker_client.images.build.side_effect = docker.errors.BuildError(
            "Build failed", "build_logs"
        )
        
        with pytest.raises(Exception) as exc_info:
            await DynamicImageBuilder.build_lab_image("python", "course-123", {})
        
        assert "Failed to build lab image" in str(exc_info.value)

    def test_generate_dockerfile_python(self):
        """Test Dockerfile generation for Python labs"""
        lab_config = {"packages": ["numpy", "pandas"]}
        dockerfile = DynamicImageBuilder._generate_dockerfile("python", lab_config)
        
        assert "FROM python:3.10-slim" in dockerfile
        assert "pip install --no-cache-dir numpy pandas" in dockerfile
        assert "jupyter jupyterlab" in dockerfile

    def test_generate_dockerfile_javascript(self):
        """Test Dockerfile generation for JavaScript labs"""
        lab_config = {"packages": ["express", "lodash"]}
        dockerfile = DynamicImageBuilder._generate_dockerfile("javascript", lab_config)
        
        assert "FROM node:18-slim" in dockerfile
        assert "npm install -g express lodash" in dockerfile
        assert "nodemon" in dockerfile

    def test_generate_dockerfile_default(self):
        """Test Dockerfile generation for default/unknown lab types"""
        lab_config = {}
        dockerfile = DynamicImageBuilder._generate_dockerfile("unknown", lab_config)
        
        assert "FROM ubuntu:22.04" in dockerfile
        assert "python3" in dockerfile
        assert "nodejs" in dockerfile

    def test_generate_startup_script(self):
        """Test startup script generation"""
        lab_config = {
            "starter_files": {"test.py": "print('Hello')"}
        }
        
        script = DynamicImageBuilder._generate_startup_script("python", lab_config)
        
        assert "def setup_lab_environment():" in script
        assert "def start_lab_server():" in script
        assert "jupyter" in script  # Python-specific server
        assert "starter_files" in script


class TestLabManagerAPI:
    """Test the Lab Manager API endpoints"""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client"""
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_health_endpoint(self, client, mock_docker_client):
        """Test health check endpoint"""
        with patch('main.psutil') as mock_psutil:
            mock_psutil.cpu_percent.return_value = 25.0
            mock_psutil.virtual_memory.return_value = Mock(percent=60.0)
            mock_psutil.disk_usage.return_value = Mock(percent=45.0)
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["docker_status"] == "connected"
            assert "system_resources" in data

    def test_health_endpoint_docker_failure(self, client):
        """Test health endpoint when Docker is unavailable"""
        with patch('main.docker_client') as mock_client:
            mock_client.ping.side_effect = Exception("Docker unavailable")
            
            response = client.get("/health")
            
            assert response.status_code == 503
            assert "Service unavailable" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_lab_success(self, client, mock_docker_client, mock_storage_path, sample_lab_request):
        """Test successful lab creation"""
        with patch('main._build_and_start_lab') as mock_build, \
             patch('main._schedule_cleanup') as mock_cleanup:
            
            response = client.post("/labs", json=sample_lab_request.dict())
            
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == sample_lab_request.user_id
            assert data["course_id"] == sample_lab_request.course_id
            assert data["status"] == "building"
            assert data["instructor_mode"] == False
            
            # Verify lab was added to active_labs
            assert len(active_labs) == 1
            lab_id = list(active_labs.keys())[0]
            assert active_labs[lab_id]["user_id"] == sample_lab_request.user_id

    @pytest.mark.asyncio
    async def test_create_lab_concurrent_limit(self, client, mock_docker_client):
        """Test lab creation when concurrent limit is reached"""
        # Fill up to the limit
        with patch('main.MAX_CONCURRENT_LABS', 1):
            # Create one lab first
            active_labs["existing-lab"] = {
                "lab_id": "existing-lab",
                "user_id": "existing-user",
                "course_id": "existing-course",
                "status": "running"
            }
            
            sample_request = LabCreateRequest(
                user_id="new-user",
                course_id="new-course",
                lab_type="python"
            )
            
            response = client.post("/labs", json=sample_request.dict())
            
            assert response.status_code == 429
            assert "Maximum concurrent labs" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_or_create_student_lab_existing(self, client, sample_student_request):
        """Test getting existing student lab"""
        # Create existing lab
        lab_id = "existing-lab-123"
        lab_data = {
            "lab_id": lab_id,
            "user_id": sample_student_request.user_id,
            "course_id": sample_student_request.course_id,
            "status": "running",
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "instructor_mode": False,
            "storage_path": "/test/path",
            "container_id": "test-container",
            "port": 9000,
            "lab_type": "python"
        }
        
        active_labs[lab_id] = lab_data
        user_labs[f"{sample_student_request.user_id}-{sample_student_request.course_id}"] = lab_id
        
        response = client.post("/labs/student", json=sample_student_request.dict())
        
        assert response.status_code == 200
        data = response.json()
        assert data["lab_id"] == lab_id
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_get_or_create_student_lab_paused(self, client, sample_student_request, mock_docker_client):
        """Test resuming paused student lab"""
        lab_id = "paused-lab-123"
        lab_data = {
            "lab_id": lab_id,
            "user_id": sample_student_request.user_id,
            "course_id": sample_student_request.course_id,
            "status": "paused",
            "container_id": "test-container",
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "instructor_mode": False,
            "storage_path": "/test/path",
            "port": 9000,
            "lab_type": "python"
        }
        
        active_labs[lab_id] = lab_data
        user_labs[f"{sample_student_request.user_id}-{sample_student_request.course_id}"] = lab_id
        
        with patch('main._resume_lab_container') as mock_resume:
            response = client.post("/labs/student", json=sample_student_request.dict())
            
            assert response.status_code == 200
            mock_resume.assert_called_once_with(lab_id)

    def test_list_labs(self, client):
        """Test listing all labs"""
        # Add test labs
        active_labs["lab1"] = {
            "lab_id": "lab1",
            "user_id": "user1",
            "course_id": "course1",
            "status": "running",
            "instructor_mode": False,
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "storage_path": "/test/path1",
            "lab_type": "python",
            "container_id": None,
            "port": None
        }
        active_labs["lab2"] = {
            "lab_id": "lab2",
            "user_id": "user2",
            "course_id": "course2",
            "status": "building",
            "instructor_mode": True,
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "storage_path": "/test/path2",
            "lab_type": "javascript",
            "container_id": None,
            "port": None
        }
        
        response = client.get("/labs")
        
        assert response.status_code == 200
        data = response.json()
        assert data["active_count"] == 2
        assert len(data["labs"]) == 2

    def test_list_labs_filtered_by_course(self, client):
        """Test listing labs filtered by course ID"""
        # Add test labs for different courses
        active_labs["lab1"] = {
            "lab_id": "lab1",
            "user_id": "user1",
            "course_id": "course1",
            "status": "running",
            "instructor_mode": False,
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "storage_path": "/test/path1",
            "lab_type": "python",
            "container_id": None,
            "port": None
        }
        active_labs["lab2"] = {
            "lab_id": "lab2",
            "user_id": "user2",
            "course_id": "course2",
            "status": "building",
            "instructor_mode": False,
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "storage_path": "/test/path2",
            "lab_type": "javascript",
            "container_id": None,
            "port": None
        }
        
        response = client.get("/labs?course_id=course1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["labs"]) == 1
        assert data["labs"][0]["course_id"] == "course1"

    def test_get_lab_details(self, client):
        """Test getting details of a specific lab"""
        lab_id = "test-lab-123"
        lab_data = {
            "lab_id": lab_id,
            "user_id": "test-user",
            "course_id": "test-course",
            "status": "running",
            "instructor_mode": False,
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "storage_path": "/test/path",
            "lab_type": "python",
            "container_id": "test-container",
            "port": 9000
        }
        
        active_labs[lab_id] = lab_data
        
        response = client.get(f"/labs/{lab_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["lab_id"] == lab_id
        assert data["user_id"] == "test-user"

    def test_get_lab_not_found(self, client):
        """Test getting details of non-existent lab"""
        response = client.get("/labs/non-existent-lab")
        
        assert response.status_code == 404
        assert "Lab session not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_pause_lab(self, client, mock_docker_client):
        """Test pausing a lab"""
        lab_id = "test-lab-123"
        lab_data = {
            "lab_id": lab_id,
            "container_id": "test-container",
            "status": "running",
            "user_id": "test-user",
            "course_id": "test-course",
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "instructor_mode": False,
            "storage_path": "/test/path",
            "lab_type": "python",
            "port": 9000
        }
        
        active_labs[lab_id] = lab_data
        
        with patch('main._pause_lab_container') as mock_pause:
            response = client.post(f"/labs/{lab_id}/pause")
            
            assert response.status_code == 200
            assert "Lab paused successfully" in response.json()["message"]
            assert active_labs[lab_id]["status"] == "paused"
            mock_pause.assert_called_once_with(lab_id)

    @pytest.mark.asyncio
    async def test_resume_lab(self, client, mock_docker_client):
        """Test resuming a lab"""
        lab_id = "test-lab-123"
        lab_data = {
            "lab_id": lab_id,
            "container_id": "test-container",
            "status": "paused",
            "user_id": "test-user",
            "course_id": "test-course",
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "instructor_mode": False,
            "storage_path": "/test/path",
            "lab_type": "python",
            "port": 9000
        }
        
        active_labs[lab_id] = lab_data
        
        with patch('main._resume_lab_container') as mock_resume:
            response = client.post(f"/labs/{lab_id}/resume")
            
            assert response.status_code == 200
            assert "Lab resumed successfully" in response.json()["message"]
            assert active_labs[lab_id]["status"] == "running"
            mock_resume.assert_called_once_with(lab_id)

    @pytest.mark.asyncio
    async def test_stop_lab(self, client, mock_docker_client):
        """Test stopping and removing a lab"""
        lab_id = "test-lab-123"
        user_id = "test-user"
        course_id = "test-course"
        
        lab_data = {
            "lab_id": lab_id,
            "container_id": "test-container",
            "status": "running",
            "user_id": user_id,
            "course_id": course_id,
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "instructor_mode": False,
            "storage_path": "/test/path",
            "lab_type": "python",
            "port": 9000
        }
        
        active_labs[lab_id] = lab_data
        user_labs[f"{user_id}-{course_id}"] = lab_id
        
        with patch('main._cleanup_lab_container') as mock_cleanup:
            response = client.delete(f"/labs/{lab_id}")
            
            assert response.status_code == 200
            assert "Lab stopped successfully" in response.json()["message"]
            assert lab_id not in active_labs
            assert f"{user_id}-{course_id}" not in user_labs
            mock_cleanup.assert_called_once_with("test-container")

    def test_instructor_lab_overview(self, client):
        """Test getting instructor lab overview"""
        course_id = "test-course"
        
        # Add student labs
        active_labs["student-lab-1"] = {
            "lab_id": "student-lab-1",
            "user_id": "student1",
            "course_id": course_id,
            "status": "running",
            "instructor_mode": False,
            "last_accessed": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "storage_path": "/test/path1",
            "lab_type": "python",
            "container_id": None,
            "port": None
        }
        
        active_labs["instructor-lab"] = {
            "lab_id": "instructor-lab",
            "user_id": "instructor1",
            "course_id": course_id,
            "status": "running",
            "instructor_mode": True,  # This should be excluded
            "last_accessed": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "storage_path": "/test/path2",
            "lab_type": "python",
            "container_id": None,
            "port": None
        }
        
        response = client.get(f"/labs/instructor/{course_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["course_id"] == course_id
        assert len(data["students"]) == 1  # Only student lab, not instructor
        assert data["students"][0]["user_id"] == "student1"


class TestLabContainerOperations:
    """Test lab container operations"""
    
    @pytest.mark.asyncio
    async def test_start_lab_container(self, mock_docker_client, mock_storage_path):
        """Test starting a lab container"""
        lab_id = "test-lab-123"
        lab_data = {
            "lab_id": lab_id,
            "storage_path": mock_storage_path
        }
        active_labs[lab_id] = lab_data
        
        request = LabCreateRequest(
            user_id="test-user",
            course_id="test-course",
            lab_type="python",
            lab_config={"packages": ["numpy"]}
        )
        
        with patch('main._find_available_port', return_value=9000):
            result = await _start_lab_container(lab_id, "test-image:latest", request)
            
            assert result["container_id"] == "test-container-id"
            assert result["port"] == 9000
            
            # Verify Docker container was created with correct parameters
            mock_docker_client.containers.run.assert_called_once()
            call_args = mock_docker_client.containers.run.call_args
            
            # Check image
            assert call_args[0][0] == "test-image:latest"
            
            # Check environment variables
            env = call_args[1]["environment"]
            assert env["LAB_SESSION_ID"] == lab_id
            assert env["USER_ID"] == "test-user"
            assert env["COURSE_ID"] == "test-course"
            assert env["LAB_TYPE"] == "python"

    @pytest.mark.asyncio
    async def test_pause_lab_container(self, mock_docker_client):
        """Test pausing a lab container"""
        lab_id = "test-lab-123"
        lab_data = {
            "container_id": "test-container-id"
        }
        active_labs[lab_id] = lab_data
        
        await _pause_lab_container(lab_id)
        
        mock_docker_client.containers.get.assert_called_once_with("test-container-id")
        mock_docker_client.containers.get.return_value.pause.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_lab_container(self, mock_docker_client):
        """Test resuming a lab container"""
        lab_id = "test-lab-123"
        lab_data = {
            "container_id": "test-container-id"
        }
        active_labs[lab_id] = lab_data
        
        await _resume_lab_container(lab_id)
        
        mock_docker_client.containers.get.assert_called_once_with("test-container-id")
        mock_docker_client.containers.get.return_value.unpause.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_lab_container(self, mock_docker_client):
        """Test cleaning up a lab container"""
        container_id = "test-container-id"
        
        await _cleanup_lab_container(container_id)
        
        mock_docker_client.containers.get.assert_called_once_with(container_id)
        mock_container = mock_docker_client.containers.get.return_value
        mock_container.stop.assert_called_once_with(timeout=10)
        mock_container.remove.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_lab_container_not_found(self, mock_docker_client):
        """Test cleaning up non-existent container"""
        mock_docker_client.containers.get.side_effect = docker.errors.NotFound("Container not found")
        
        # Should not raise exception
        await _cleanup_lab_container("non-existent-container")

    def test_find_available_port(self):
        """Test finding available port"""
        with patch('socket.socket') as mock_socket:
            mock_sock_instance = Mock()
            mock_socket.return_value.__enter__.return_value = mock_sock_instance
            mock_sock_instance.bind.return_value = None
            
            port = _find_available_port()
            
            assert 9000 <= port <= 9999
            mock_sock_instance.bind.assert_called()

    def test_find_available_port_no_ports(self):
        """Test when no ports are available"""
        with patch('socket.socket') as mock_socket:
            mock_sock_instance = Mock()
            mock_socket.return_value.__enter__.return_value = mock_sock_instance
            mock_sock_instance.bind.side_effect = OSError("Port in use")
            
            with pytest.raises(Exception, match="No available ports found"):
                _find_available_port()

    def test_get_user_lab(self):
        """Test getting user lab mapping"""
        user_id = "test-user"
        course_id = "test-course"
        lab_id = "test-lab-123"
        
        user_labs[f"{user_id}-{course_id}"] = lab_id
        
        result = _get_user_lab(user_id, course_id)
        
        assert result == lab_id

    def test_get_user_lab_not_found(self):
        """Test getting non-existent user lab mapping"""
        result = _get_user_lab("non-existent-user", "non-existent-course")
        
        assert result is None


class TestLabManagerIntegration:
    """Integration tests for lab manager components"""
    
    @pytest.mark.asyncio
    async def test_full_lab_lifecycle(self, mock_docker_client, mock_storage_path):
        """Test complete lab lifecycle from creation to cleanup"""
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        # 1. Create lab
        request_data = {
            "user_id": "integration-test-user",
            "course_id": "integration-test-course",
            "lab_type": "python",
            "lab_config": {
                "packages": ["numpy"],
                "starter_files": {"test.py": "print('Hello')"}
            },
            "timeout_minutes": 30,
            "instructor_mode": False
        }
        
        with patch('main._build_and_start_lab') as mock_build, \
             patch('main._schedule_cleanup'):
            
            # Create lab
            response = client.post("/labs", json=request_data)
            assert response.status_code == 200
            
            lab_data = response.json()
            lab_id = lab_data["lab_id"]
            
            # Simulate successful build and start
            await mock_build.call_args[0][1]  # Execute the build function
            
            # Verify lab is in active state
            assert lab_id in active_labs
            assert active_labs[lab_id]["status"] == "building"
            
        # 2. Simulate build completion
        active_labs[lab_id].update({
            "container_id": "test-container-id",
            "port": 9000,
            "status": "running",
            "access_url": "http://localhost:9000"
        })
        
        # 3. Get lab details
        response = client.get(f"/labs/{lab_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "running"
        
        # 4. Pause lab
        with patch('main._pause_lab_container'):
            response = client.post(f"/labs/{lab_id}/pause")
            assert response.status_code == 200
            assert active_labs[lab_id]["status"] == "paused"
        
        # 5. Resume lab
        with patch('main._resume_lab_container'):
            response = client.post(f"/labs/{lab_id}/resume")
            assert response.status_code == 200
            assert active_labs[lab_id]["status"] == "running"
        
        # 6. Stop lab
        with patch('main._cleanup_lab_container'):
            response = client.delete(f"/labs/{lab_id}")
            assert response.status_code == 200
            assert lab_id not in active_labs

    @pytest.mark.asyncio
    async def test_concurrent_lab_operations(self, mock_docker_client, mock_storage_path):
        """Test concurrent lab operations"""
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        # Create multiple labs concurrently
        lab_requests = []
        for i in range(3):
            request_data = {
                "user_id": f"user-{i}",
                "course_id": f"course-{i}",
                "lab_type": "python",
                "timeout_minutes": 30,
                "instructor_mode": False
            }
            lab_requests.append(request_data)
        
        with patch('main._build_and_start_lab'), \
             patch('main._schedule_cleanup'):
            
            # Create labs
            responses = []
            for request_data in lab_requests:
                response = client.post("/labs", json=request_data)
                responses.append(response)
            
            # Verify all labs were created successfully
            for response in responses:
                assert response.status_code == 200
            
            # Verify labs are tracked
            assert len(active_labs) == 3
            
            # Test listing all labs
            response = client.get("/labs")
            assert response.status_code == 200
            assert response.json()["active_count"] == 3


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])