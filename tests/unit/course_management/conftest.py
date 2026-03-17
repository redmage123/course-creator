"""
Pytest configuration and fixtures for Course Management tests.

This file provides test fixtures for unit testing course
management services.

NOTE: This file has been refactored to remove all mock usage.
Tests should use real implementations or be marked with @pytest.mark.skip
if they require external services that cannot be easily provided in unit tests.
"""
import pytest


# ============================================================================
# DATABASE FIXTURES (for future use with real database testing)
# ============================================================================

@pytest.fixture
def db_connection():
    """
    Provides a real database connection for integration testing.

    BUSINESS CONTEXT:
    Unit tests that need database access should use this fixture
    to get a real connection to a test database.

    TECHNICAL IMPLEMENTATION:
    Connects to test database using environment variables.
    Automatically rolls back changes after each test for isolation.
    """
    import psycopg2
    import os

    conn = psycopg2.connect(
        host=os.getenv('TEST_DB_HOST', 'localhost'),
        port=os.getenv('TEST_DB_PORT', '5433'),
        user=os.getenv('TEST_DB_USER', 'course_user'),
        password=os.getenv('TEST_DB_PASSWORD', 'course_pass'),
        database=os.getenv('TEST_DB_NAME', 'course_creator')
    )
    yield conn
    conn.rollback()
    conn.close()


# ============================================================================
# SERVICE FIXTURES (for future use with real service instances)
# ============================================================================

@pytest.fixture
def http_client():
    """
    Provides a real HTTP client for testing external API calls.

    BUSINESS CONTEXT:
    Tests that need to make HTTP requests should use this fixture.
    For tests that cannot make real HTTP calls, use @pytest.mark.skip

    NOTE: Currently returns None - needs implementation with real HTTP client.
    """
    # TODO: Implement real HTTP client (e.g., httpx.AsyncClient())
    return None


# ============================================================================
# ENTITY FIXTURES (real domain entities for testing)
# ============================================================================

@pytest.fixture
def sample_student_email():
    """Provides a sample student email for testing."""
    return "student@example.com"


@pytest.fixture
def sample_instructor_email():
    """Provides a sample instructor email for testing."""
    return "instructor@example.com"


@pytest.fixture
def sample_course_id():
    """Provides a sample course ID for testing."""
    from uuid import uuid4
    return str(uuid4())


@pytest.fixture
def sample_organization_id():
    """Provides a sample organization ID for testing."""
    from uuid import uuid4
    return str(uuid4())


# ============================================================================
# TEST DATA FIXTURES (for file-based testing)
# ============================================================================

@pytest.fixture
def sample_csv_roster():
    """
    Provides sample CSV roster data for bulk enrollment testing.

    BUSINESS CONTEXT:
    Used for testing spreadsheet parsing and bulk enrollment workflows.
    """
    return """first_name,last_name,email,role
John,Doe,john.doe@example.com,student
Jane,Smith,jane.smith@example.com,student
Bob,Johnson,bob.johnson@example.com,student"""


@pytest.fixture
def sample_project_spec_dict():
    """
    Provides sample project specification data for bulk project creation.

    BUSINESS CONTEXT:
    Used for testing project builder workflows.
    """
    from uuid import uuid4
    return {
        "name": "Test Training Program",
        "organization_id": str(uuid4()),
        "description": "A test training program",
        "locations": [
            {
                "name": "New York",
                "city": "New York",
                "max_students": 30
            }
        ],
        "tracks": [
            {
                "name": "Backend Development",
                "courses": [
                    {
                        "title": "Python Basics",
                        "description": "Learn Python fundamentals",
                        "duration_hours": 20
                    }
                ]
            }
        ],
        "instructors": [
            {
                "name": "John Doe",
                "email": "john@example.com",
                "track_names": ["Backend Development"]
            }
        ],
        "students": [
            {
                "name": "Alice Student",
                "email": "alice@example.com",
                "track_name": "Backend Development",
                "location_name": "New York"
            }
        ]
    }


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """
    Cleanup fixture that runs after each test.

    BUSINESS CONTEXT:
    Ensures test isolation by cleaning up any resources created during tests.
    """
    yield
    # Cleanup code here (if needed)
    pass
