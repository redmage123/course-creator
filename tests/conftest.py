"""
Pytest configuration and fixtures for Course Creator Platform tests.

This file contains common fixtures and configuration for all tests
across the platform, including database setup, mock services, and
test utilities.
"""

import pytest
import pytest_asyncio
import asyncio
import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta
import uuid
import json


def pytest_addoption(parser):
    """Add custom command-line options for pytest."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require external services (DB, Redis, etc.)"
    )

# Add ALL services to path for imports
service_paths = [
    'analytics',
    'content-management',
    'content-storage',
    'course-generator',
    'course-management',
    'demo-service',
    'knowledge-graph-service',
    'lab-manager',
    'metadata-service',
    'organization-management',
    'rag-service',
    'user-management'
]

for service in service_paths:
    service_path = os.path.join(os.path.dirname(__file__), f'../services/{service}')
    service_path = os.path.abspath(service_path)  # Make absolute
    if os.path.exists(service_path):
        sys.path.insert(0, service_path)

# Add tests/e2e to path so selenium_base can be imported directly
e2e_path = os.path.join(os.path.dirname(__file__), 'e2e')
e2e_path = os.path.abspath(e2e_path)
if os.path.exists(e2e_path):
    sys.path.insert(0, e2e_path)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_pool():
    """Create a mock database connection pool (deprecated - use real db_connection)."""
    # Deprecated: Use db_connection fixture for real database testing
    # This fixture is kept for backward compatibility
    return None


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
    """Create a mock password manager (deprecated)."""
    # Deprecated: Use real password manager from services
    return None


@pytest.fixture
def mock_jwt_manager():
    """Create a mock JWT manager (deprecated)."""
    # Deprecated: Use real JWT manager from services
    return None


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager (deprecated)."""
    # Deprecated: Use real session manager from services
    return None


@pytest.fixture
def mock_user_repository():
    """Create a mock user repository (deprecated)."""
    # Deprecated: Use real repository with test database
    return None


@pytest.fixture
def mock_course_repository():
    """Create a mock course repository (deprecated)."""
    # Deprecated: Use real repository with test database
    return None


@pytest.fixture
def mock_content_repository():
    """Create a mock content repository (deprecated)."""
    # Deprecated: Use real repository with test database
    return None


@pytest.fixture
def mock_enrollment_repository():
    """Create a mock enrollment repository (deprecated)."""
    # Deprecated: Use real repository with test database
    return None


@pytest.fixture
def mock_storage_service():
    """Create a mock storage service (deprecated)."""
    # Deprecated: Use real storage service with test configuration
    return None


@pytest.fixture
def docker_client():
    """
    Create Docker client for container verification in E2E tests.

    BUSINESS CONTEXT:
    E2E tests need to verify actual Docker container state (not just UI state)
    to ensure lab environments are properly created, managed, and cleaned up.

    TECHNICAL IMPLEMENTATION:
    Uses docker-py library to interact with Docker daemon.
    Provides automatic cleanup of test containers after each test session.

    USAGE:
    - Tests can use this fixture to inspect container state
    - Tests can verify resource limits, volumes, network isolation
    - Tests can simulate container failures and recovery

    Returns:
        docker.DockerClient: Docker client instance
    """
    try:
        import docker
        client = docker.from_env()
        yield client

        # Cleanup: Remove any test containers that weren't cleaned up
        try:
            test_containers = client.containers.list(all=True, filters={"label": "test"})
            for container in test_containers:
                try:
                    container.stop(timeout=1)
                    container.remove()
                except Exception as e:
                    print(f"Error cleaning up test container {container.name}: {e}")
        except Exception as e:
            print(f"Error during docker fixture cleanup: {e}")

    except ImportError:
        pytest.skip("docker-py library not installed. Install with: pip install docker")
    except Exception as e:
        pytest.skip(f"Docker not available: {e}")


@pytest.fixture
def student_credentials():
    """
    Provide student credentials for E2E authentication tests.

    BUSINESS CONTEXT:
    E2E tests need realistic student credentials to test authentication,
    authorization, and lab access workflows.

    SECURITY NOTE:
    These are test credentials only, used in isolated test environments.
    Never use production credentials in tests.

    Returns:
        dict: Student credentials with username, email, and password
    """
    return {
        "username": "test_student",
        "email": "student.test@example.com",
        "password": "password123",
        "role": "student"
    }


@pytest.fixture
def instructor_credentials():
    """
    Provide instructor credentials for E2E authentication tests.

    BUSINESS CONTEXT:
    Instructors need different permissions than students (can view student labs,
    create courses, manage content). Tests verify these role-based permissions.

    Returns:
        dict: Instructor credentials with username, email, and password
    """
    return {
        "username": "test_instructor",
        "email": "instructor@example.com",
        "password": "password123",
        "role": "instructor"
    }


@pytest.fixture
def test_base_url():
    """
    Provide base URL for E2E tests.

    BUSINESS CONTEXT:
    All E2E tests must use HTTPS (as per CLAUDE.md requirements).
    Default is https://localhost:3000 but can be overridden with env var.

    IMPORTANT: Platform is HTTPS-only, HTTP is not supported.

    Returns:
        str: Base URL for E2E tests (always HTTPS)
    """
    return os.getenv('TEST_BASE_URL', 'https://localhost:3000')


@pytest.fixture
def selenium_config():
    """
    Provide Selenium configuration for E2E tests.

    BUSINESS CONTEXT:
    Provides configured SeleniumConfig object for Page Object Model classes.

    Returns:
        SeleniumConfig: Configuration object with test settings
    """
    from tests.e2e.selenium_base import SeleniumConfig
    return SeleniumConfig()


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service (deprecated)."""
    # Deprecated: Use real AI service with test configuration
    return None


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
    """Create a mock file upload object (deprecated)."""
    # Deprecated: Use real file upload with test files
    return None


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
    
    # Centralized logging test environment variables
    os.environ["DOCKER_CONTAINER"] = "true"
    os.environ["SERVICE_NAME"] = "test-service"
    os.environ["LOG_LEVEL"] = "INFO"
    
    yield
    
    # Clean up environment variables
    test_vars = [
        "TESTING", "LOG_LEVEL", "DATABASE_URL", "REDIS_URL", 
        "JWT_SECRET_KEY", "STORAGE_PATH", "DOCKER_CONTAINER", "SERVICE_NAME"
    ]
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing (deprecated)."""
    # Deprecated: Use real logger from logging module
    import logging
    return logging.getLogger('test')


@pytest.fixture
def mock_syslog_logger():
    """Create a mock syslog logger for centralized logging tests (deprecated)."""
    # Deprecated: Use real syslog logger configuration
    import logging
    return logging.getLogger('test.syslog')


@pytest.fixture
def mock_logging_setup():
    """Mock the centralized logging setup (deprecated)."""
    # Deprecated: Use real logging configuration
    import logging
    logging.basicConfig(level=logging.INFO)
    return logging


@pytest.fixture
def centralized_logging_config():
    """Configuration for centralized logging tests."""
    return {
        "service_name": "test-service",
        "log_level": "INFO",
        "log_file": "/var/log/course-creator/test-service.log",
        "syslog_format": "%(asctime)s %(hostname)s %(name)s[%(process)d]: %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        "console_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "docker_container": True
    }


@pytest.fixture
def mock_log_file(temp_directory):
    """Create a mock log file for testing."""
    import os
    log_dir = os.path.join(temp_directory, "course-creator")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "test-service.log")
    
    # Create empty log file
    with open(log_file, 'w') as f:
        f.write("")
    
    return log_file


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
        """Create a mock user with default values (deprecated - use real user creation)."""
        # Deprecated: Use real user creation with database
        from datetime import datetime
        import uuid
        defaults = {
            "id": str(uuid.uuid4()),
            "username": "testuser",
            "email": "test@example.com",
            "role": "student",
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        defaults.update(kwargs)
        return defaults

    @staticmethod
    def create_mock_course(**kwargs):
        """Create a mock course with default values (deprecated - use real course creation)."""
        # Deprecated: Use real course creation with database
        from datetime import datetime
        import uuid
        defaults = {
            "id": str(uuid.uuid4()),
            "title": "Test Course",
            "description": "A test course",
            "instructor_id": str(uuid.uuid4()),
            "created_at": datetime.utcnow()
        }
        defaults.update(kwargs)
        return defaults

    @staticmethod
    def create_mock_content(**kwargs):
        """Create a mock content with default values (deprecated - use real content creation)."""
        # Deprecated: Use real content creation with database
        from datetime import datetime
        import uuid
        defaults = {
            "id": str(uuid.uuid4()),
            "filename": "test_file.pdf",
            "content_type": "application/pdf",
            "uploaded_at": datetime.utcnow()
        }
        defaults.update(kwargs)
        return defaults


# Make utility functions available to all tests
pytest.assert_valid_uuid = assert_valid_uuid
pytest.assert_valid_email = assert_valid_email
pytest.assert_valid_datetime = assert_valid_datetime
pytest.TestUtils = TestUtils


@pytest_asyncio.fixture
async def db_connection():
    """
    Create a database connection for integration tests.

    BUSINESS CONTEXT:
    Integration tests need direct database access to create
    test data and verify database operations.
    """
    import asyncpg

    # Get database connection parameters from environment
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', '5433'))
    db_name = os.getenv('DB_NAME', 'course_creator')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres_password')

    # Create connection
    conn = await asyncpg.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )

    yield conn

    # Close connection
    await conn.close()


@pytest_asyncio.fixture
async def api_client():
    """
    Create an HTTP client for API integration tests.

    BUSINESS CONTEXT:
    Integration tests need to make real HTTP requests to
    test the complete request/response cycle.
    """
    import httpx

    # Get API base URL from environment
    base_url = os.getenv('API_BASE_URL', 'https://localhost:8008')

    # Create async HTTP client with SSL verification disabled for testing
    async with httpx.AsyncClient(
        base_url=base_url,
        verify=False,  # Disable SSL verification for self-signed certificates
        timeout=30.0
    ) as client:
        yield client


@pytest.fixture
def site_admin_token():
    """
    Create a mock site admin authentication token.

    BUSINESS CONTEXT:
    Many API endpoints require site admin permissions,
    so tests need a valid authentication token.
    """
    # Mock token format used in development
    # In production, this would be a real JWT token
    return "mock-token-site-admin-id"


@pytest.fixture
def instructor_token():
    """Create a mock instructor authentication token."""
    return "mock-token-instructor-id"


@pytest.fixture
def student_token():
    """Create a mock student authentication token."""
    return "mock-token-student-id"


@pytest.fixture(scope="function")
def driver(selenium_config):
    """
    Create Selenium WebDriver for E2E tests with proper Chrome configuration.

    BUSINESS CONTEXT:
    E2E tests need a real browser to verify user workflows work correctly.
    Chrome is used for consistency across test environments.

    TECHNICAL IMPLEMENTATION:
    - Uses selenium_base.ChromeDriverSetup for consistent configuration
    - Supports both local Chrome and Docker Selenium Grid (SELENIUM_REMOTE)
    - Configures Chrome options for headless operation when HEADLESS=true
    - Disables GPU for stability in CI/CD environments
    - Cleans up driver after test
    """
    from tests.e2e.selenium_base import ChromeDriverSetup

    # Create driver using ChromeDriverSetup which handles remote/local automatically
    driver = ChromeDriverSetup.create_driver(selenium_config)

    yield driver

    # Cleanup: Quit driver
    try:
        driver.quit()
    except Exception as e:
        print(f"Warning: Error closing driver: {e}")


@pytest.fixture(scope="function")
def browser(driver):
    """
    Alias for driver fixture to support tests expecting 'browser' parameter.

    BUSINESS CONTEXT:
    Some E2E tests use 'browser' parameter name instead of 'driver'.
    This fixture provides compatibility without changing existing tests.

    TECHNICAL IMPLEMENTATION:
    - Simply returns the driver fixture
    - Both 'browser' and 'driver' parameters work in tests
    """
    return driver