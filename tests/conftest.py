"""
Pytest configuration and fixtures for Course Creator Platform tests.

This file contains common fixtures and configuration for all tests
across the platform, including database setup, mock services, and
test utilities.
"""

import pytest
import asyncio
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta
import uuid
import json

# Add services to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../services/user-management'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../services/course-management'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../services/content-storage'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../services/course-generator'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../services/content-management'))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_pool():
    """Create a mock database connection pool."""
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_pool.acquire.return_value.__aexit__.return_value = None
    return mock_pool


@pytest.fixture
def mock_user_data():
    """Create mock user data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "SecurePassword123!",
        "role": "student",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_course_data():
    """Create mock course data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "title": "Test Course",
        "description": "A test course for automated testing",
        "instructor_id": str(uuid.uuid4()),
        "difficulty": "beginner",
        "category": "programming",
        "duration_hours": 40,
        "is_published": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_content_data():
    """Create mock content data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "filename": "test_file.pdf",
        "content_type": "application/pdf",
        "size": 1024,
        "uploaded_by": str(uuid.uuid4()),
        "uploaded_at": datetime.utcnow(),
        "storage_path": "/storage/test_file.pdf",
        "status": "uploaded",
        "tags": ["test", "document"],
        "metadata": {
            "pages": 10,
            "author": "Test Author"
        }
    }


@pytest.fixture
def mock_jwt_token():
    """Create a mock JWT token for testing."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTIzNDU2NzgtMTIzNC0xMjM0LTEyMzQtMTIzNDU2Nzg5MDEyIiwiZXhwIjoxNzA5MjM0NTY3fQ.test"


@pytest.fixture
def mock_password_manager():
    """Create a mock password manager."""
    mock_manager = Mock()
    mock_manager.hash_password.return_value = "hashed_password"
    mock_manager.verify_password.return_value = True
    mock_manager.is_strong_password.return_value = True
    mock_manager.validate_password_policy.return_value = True
    return mock_manager


@pytest.fixture
def mock_jwt_manager():
    """Create a mock JWT manager."""
    mock_manager = Mock()
    mock_manager.create_token.return_value = "jwt_token"
    mock_manager.validate_token.return_value = {"user_id": str(uuid.uuid4())}
    mock_manager.refresh_token.return_value = "new_jwt_token"
    return mock_manager


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager."""
    mock_manager = AsyncMock()
    mock_session = Mock()
    mock_session.id = str(uuid.uuid4())
    mock_session.user_id = str(uuid.uuid4())
    mock_session.token = "session_token"
    mock_session.expires_at = datetime.utcnow() + timedelta(hours=1)
    mock_session.created_at = datetime.utcnow()
    mock_session.last_activity = datetime.utcnow()
    mock_session.is_expired.return_value = False
    
    mock_manager.create_session.return_value = mock_session
    mock_manager.validate_session.return_value = mock_session
    mock_manager.invalidate_session.return_value = True
    mock_manager.cleanup_expired_sessions.return_value = 0
    return mock_manager


@pytest.fixture
def mock_user_repository():
    """Create a mock user repository."""
    mock_repo = AsyncMock()
    mock_repo.create_user.return_value = None
    mock_repo.get_user_by_id.return_value = None
    mock_repo.get_user_by_email.return_value = None
    mock_repo.get_user_by_username.return_value = None
    mock_repo.update_user.return_value = None
    mock_repo.delete_user.return_value = True
    mock_repo.list_users.return_value = []
    mock_repo.get_user_password_hash.return_value = "hashed_password"
    mock_repo.update_user_password.return_value = True
    return mock_repo


@pytest.fixture
def mock_course_repository():
    """Create a mock course repository."""
    mock_repo = AsyncMock()
    mock_repo.create_course.return_value = None
    mock_repo.get_course_by_id.return_value = None
    mock_repo.update_course.return_value = None
    mock_repo.delete_course.return_value = True
    mock_repo.list_courses.return_value = []
    mock_repo.get_instructor_courses.return_value = []
    mock_repo.search_courses.return_value = []
    return mock_repo


@pytest.fixture
def mock_content_repository():
    """Create a mock content repository."""
    mock_repo = AsyncMock()
    mock_repo.create_content.return_value = None
    mock_repo.get_content_by_id.return_value = None
    mock_repo.update_content.return_value = None
    mock_repo.delete_content.return_value = True
    mock_repo.list_user_content.return_value = []
    mock_repo.search_content.return_value = []
    return mock_repo


@pytest.fixture
def mock_enrollment_repository():
    """Create a mock enrollment repository."""
    mock_repo = AsyncMock()
    mock_repo.create_enrollment.return_value = None
    mock_repo.get_enrollment.return_value = None
    mock_repo.update_enrollment.return_value = None
    mock_repo.delete_enrollment.return_value = True
    mock_repo.get_user_enrollments.return_value = []
    mock_repo.get_course_enrollments.return_value = []
    return mock_repo


@pytest.fixture
def mock_storage_service():
    """Create a mock storage service."""
    mock_service = AsyncMock()
    mock_service.store_file.return_value = "/storage/test_file.pdf"
    mock_service.get_file.return_value = b"test file content"
    mock_service.delete_file.return_value = True
    mock_service.get_file_info.return_value = {
        "size": 1024,
        "modified_at": datetime.utcnow(),
        "content_type": "application/pdf"
    }
    mock_service.get_user_storage_stats.return_value = Mock(
        total_files=10,
        total_size=1024000,
        used_quota=512000,
        available_quota=512000,
        quota_percentage=50.0
    )
    return mock_service


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service."""
    mock_service = AsyncMock()
    mock_service.generate_course_content.return_value = {
        "title": "Generated Course",
        "description": "AI-generated course content",
        "modules": [
            {
                "title": "Module 1",
                "content": "Module 1 content",
                "duration": 60
            }
        ]
    }
    mock_service.generate_slides.return_value = [
        {
            "title": "Slide 1",
            "content": "Slide 1 content",
            "slide_number": 1
        }
    ]
    mock_service.generate_quiz.return_value = {
        "title": "Generated Quiz",
        "questions": [
            {
                "question": "What is Python?",
                "type": "multiple_choice",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A"
            }
        ]
    }
    return mock_service


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(b"test content")
    temp_file.close()
    yield temp_file.name
    os.unlink(temp_file.name)


@pytest.fixture
def mock_file_upload():
    """Create a mock file upload object."""
    mock_upload = Mock()
    mock_upload.filename = "test.pdf"
    mock_upload.content_type = "application/pdf"
    mock_upload.size = 1024
    mock_upload.read.return_value = b"test file content"
    return mock_upload


@pytest.fixture
def test_config():
    """Create test configuration."""
    return {
        "database": {
            "host": "localhost",
            "port": 5432,
            "database": "course_creator_test",
            "user": "test_user",
            "password": "test_password"
        },
        "redis": {
            "host": "localhost",
            "port": 6379,
            "database": 1
        },
        "jwt": {
            "secret_key": "test_secret_key",
            "algorithm": "HS256",
            "expiration_hours": 24
        },
        "storage": {
            "type": "local",
            "path": "/tmp/test_storage"
        },
        "ai": {
            "provider": "mock",
            "api_key": "test_api_key"
        }
    }


@pytest.fixture
def mock_fastapi_client():
    """Create a mock FastAPI test client."""
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    
    app = FastAPI()
    
    @app.get("/health")
    def health_check():
        return {"status": "healthy"}
    
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["DATABASE_URL"] = "postgresql://test_user:test_password@localhost:5432/course_creator_test"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    os.environ["JWT_SECRET_KEY"] = "test_secret_key"
    os.environ["STORAGE_PATH"] = "/tmp/test_storage"
    
    yield
    
    # Clean up environment variables
    test_vars = ["TESTING", "LOG_LEVEL", "DATABASE_URL", "REDIS_URL", "JWT_SECRET_KEY", "STORAGE_PATH"]
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def sample_course_generation_request():
    """Create a sample course generation request."""
    return {
        "title": "Python Programming Fundamentals",
        "description": "Learn Python programming from basics to advanced concepts",
        "difficulty": "beginner",
        "duration_hours": 40,
        "topics": [
            "Variables and Data Types",
            "Control Structures",
            "Functions",
            "Object-Oriented Programming",
            "Error Handling",
            "File I/O",
            "Libraries and Modules"
        ],
        "learning_objectives": [
            "Understand Python syntax and semantics",
            "Write effective Python programs",
            "Apply object-oriented programming concepts",
            "Handle errors and exceptions",
            "Work with files and data",
            "Use Python libraries effectively"
        ],
        "target_audience": "beginners with no programming experience",
        "prerequisites": [],
        "assessment_methods": ["quizzes", "projects", "final_exam"]
    }


@pytest.fixture
def sample_quiz_data():
    """Create sample quiz data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "course_id": str(uuid.uuid4()),
        "title": "Python Basics Quiz",
        "description": "Test your knowledge of Python basics",
        "difficulty": "beginner",
        "time_limit": 30,
        "questions": [
            {
                "id": str(uuid.uuid4()),
                "question": "What is the correct way to define a variable in Python?",
                "type": "multiple_choice",
                "options": [
                    "var x = 5",
                    "x = 5",
                    "int x = 5",
                    "define x = 5"
                ],
                "correct_answer": "x = 5",
                "points": 1
            },
            {
                "id": str(uuid.uuid4()),
                "question": "Python is a compiled language.",
                "type": "true_false",
                "correct_answer": "False",
                "points": 1
            }
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_lab_environment():
    """Create sample lab environment data."""
    return {
        "id": str(uuid.uuid4()),
        "course_id": str(uuid.uuid4()),
        "name": "Python Programming Lab",
        "description": "Interactive Python programming environment",
        "language": "python",
        "template": "python_basic",
        "resources": {
            "cpu": "1000m",
            "memory": "512Mi",
            "storage": "1Gi"
        },
        "environment_variables": {
            "PYTHON_VERSION": "3.9",
            "PYTHONPATH": "/workspace"
        },
        "files": [
            {
                "name": "main.py",
                "content": "print('Hello, World!')",
                "type": "python"
            }
        ],
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


# Custom pytest markers for test categorization
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as testing authentication"
    )
    config.addinivalue_line(
        "markers", "frontend: mark test as testing frontend"
    )


# Pytest collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test items during collection."""
    for item in items:
        # Add unit marker to unit tests
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add e2e marker to e2e tests
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Add frontend marker to frontend tests
        if "frontend" in str(item.fspath):
            item.add_marker(pytest.mark.frontend)
        
        # Add slow marker to tests that might be slow
        if any(keyword in item.name.lower() for keyword in ["performance", "load", "stress"]):
            item.add_marker(pytest.mark.slow)


# Custom assertions for testing
def assert_valid_uuid(value):
    """Assert that a value is a valid UUID."""
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


def assert_valid_email(email):
    """Assert that an email is valid."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def assert_valid_datetime(dt):
    """Assert that a value is a valid datetime."""
    return isinstance(dt, datetime)


# Test utilities
class TestUtils:
    """Utility class for testing."""
    
    @staticmethod
    def create_mock_user(**kwargs):
        """Create a mock user with default values."""
        defaults = {
            "id": str(uuid.uuid4()),
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "student",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        defaults.update(kwargs)
        return Mock(**defaults)
    
    @staticmethod
    def create_mock_course(**kwargs):
        """Create a mock course with default values."""
        defaults = {
            "id": str(uuid.uuid4()),
            "title": "Test Course",
            "description": "A test course",
            "instructor_id": str(uuid.uuid4()),
            "difficulty": "beginner",
            "category": "programming",
            "duration_hours": 40,
            "is_published": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        defaults.update(kwargs)
        return Mock(**defaults)
    
    @staticmethod
    def create_mock_content(**kwargs):
        """Create a mock content with default values."""
        defaults = {
            "id": str(uuid.uuid4()),
            "filename": "test.pdf",
            "content_type": "application/pdf",
            "size": 1024,
            "uploaded_by": str(uuid.uuid4()),
            "uploaded_at": datetime.utcnow(),
            "storage_path": "/storage/test.pdf",
            "status": "uploaded",
            "tags": [],
            "metadata": {}
        }
        defaults.update(kwargs)
        return Mock(**defaults)


# Make utility functions available to all tests
pytest.assert_valid_uuid = assert_valid_uuid
pytest.assert_valid_email = assert_valid_email
pytest.assert_valid_datetime = assert_valid_datetime
pytest.TestUtils = TestUtils