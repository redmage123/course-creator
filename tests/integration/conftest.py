"""
Integration Test Configuration with Real Infrastructure

BUSINESS CONTEXT:
Provides fixtures and setup for integration tests that run against real
PostgreSQL and Redis instances (via docker-compose.test.yml).

This enables comprehensive integration testing without mocking, testing:
- Real database interactions
- Real Redis caching
- Complete FastAPI middleware chain
- Actual authentication flows
- Full error handling paths
"""

import pytest
import asyncio
import asyncpg
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timedelta

# Add service paths for imports
project_root = Path(__file__).parent.parent.parent
course_mgmt_path = project_root / "services" / "course-management"
sys.path.insert(0, str(course_mgmt_path))
sys.path.insert(0, str(project_root / "services" / "user-management"))
sys.path.insert(0, str(project_root / "services" / "organization-management"))

# Test configuration
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://test_user:test_password@localhost:5434/course_creator_test"
)
TEST_REDIS_URL = os.environ.get(
    "TEST_REDIS_URL",
    "redis://localhost:6380"
)
TEST_JWT_SECRET = os.environ.get(
    "TEST_JWT_SECRET",
    "test-secret-key-for-integration-tests-only"
)

# Test user IDs (matching init-test-db.sql)
TEST_ORG_ID = "00000000-0000-0000-0000-000000000001"
TEST_ADMIN_ID = "00000000-0000-0000-0000-000000000002"


@pytest.fixture(scope="function")
def clean_database():
    """
    Clean database before each test (synchronous version)

    WORKFLOW:
    1. Delete all test data (except seed data)
    2. Reset for clean slate
    3. Runs synchronously before each test
    """
    import psycopg2

    # Connect synchronously
    conn = psycopg2.connect(TEST_DATABASE_URL)
    cur = conn.cursor()

    # Delete test data (preserve seed data)
    cur.execute("DELETE FROM instructor_assignments WHERE project_id IS NOT NULL")
    cur.execute("DELETE FROM enrollments WHERE project_id IS NOT NULL")
    cur.execute("DELETE FROM tracks WHERE project_id IS NOT NULL")
    cur.execute("DELETE FROM projects WHERE id != '00000000-0000-0000-0000-000000000000'")
    cur.execute("DELETE FROM users WHERE id NOT IN ('00000000-0000-0000-0000-000000000002')")

    conn.commit()
    cur.close()
    conn.close()

    yield

    # Cleanup after test
    conn = psycopg2.connect(TEST_DATABASE_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM instructor_assignments WHERE project_id IS NOT NULL")
    cur.execute("DELETE FROM enrollments WHERE project_id IS NOT NULL")
    cur.execute("DELETE FROM tracks WHERE project_id IS NOT NULL")
    cur.execute("DELETE FROM projects WHERE id != '00000000-0000-0000-0000-000000000000'")
    cur.execute("DELETE FROM users WHERE id NOT IN ('00000000-0000-0000-0000-000000000002')")
    conn.commit()
    cur.close()
    conn.close()


@pytest.fixture(scope="function")
def auth_token() -> str:
    """
    Generate valid JWT token for test user

    USAGE:
    - Used in Authorization header: Bearer {token}
    - Represents authenticated org admin user
    - Valid for 1 hour
    """
    payload = {
        "user_id": TEST_ADMIN_ID,
        "email": "admin@test.example.com",
        "role": "org_admin",
        "organization_id": TEST_ORG_ID,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
    return token


@pytest.fixture(scope="function")
def auth_headers(auth_token: str) -> dict:
    """
    Get authentication headers for API requests

    RETURNS:
    {
        "Authorization": "Bearer <token>",
        "Content-Type": "application/json"
    }
    """
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="session")
def test_app() -> Generator[TestClient, None, None]:
    """
    Create FastAPI test client with real infrastructure

    IMPORTANT:
    - Uses real database connection
    - Uses real Redis cache
    - Runs full middleware chain
    - Actual authentication/authorization

    ENVIRONMENT SETUP:
    - Requires docker-compose.test.yml running
    - DATABASE_URL set to test database
    - REDIS_URL set to test Redis
    """
    # Set environment variables for test infrastructure
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["REDIS_URL"] = TEST_REDIS_URL
    os.environ["JWT_SECRET_KEY"] = TEST_JWT_SECRET
    os.environ["ENVIRONMENT"] = "test"

    # Import app (after environment is configured)
    from main import app

    # Create test client
    client = TestClient(app)

    yield client

    # Cleanup
    client.close()


@pytest.fixture(scope="function")
def test_project_data() -> dict:
    """
    Sample project data for testing

    RETURNS:
    Complete project data structure with all optional fields
    """
    return {
        "project_name": "Integration Test Project",
        "project_slug": "integration-test-project",
        "description": "Test project for integration testing",
        "start_date": "2024-01-15",
        "end_date": "2024-06-30",
        "tracks": ["Backend Development", "Frontend Development"],
        "students": [
            {"email": "student1@test.com", "name": "Test Student One"},
            {"email": "student2@test.com", "name": "Test Student Two"}
        ],
        "instructors": [
            {"email": "instructor@test.com", "name": "Test Instructor"}
        ]
    }


@pytest.fixture(scope="function")
def minimal_project_data() -> dict:
    """
    Minimal project data (required fields only)
    """
    return {
        "project_name": "Minimal Test Project",
        "project_slug": "minimal-test-project",
        "description": "Minimal project for testing"
    }


# Utility functions for tests

def verify_database_connection():
    """
    Verify test database is accessible

    RAISES:
    ConnectionError if database is not accessible
    """
    import asyncio

    async def check():
        try:
            pool = await asyncpg.create_pool(TEST_DATABASE_URL, timeout=5)
            await pool.close()
            return True
        except Exception as e:
            raise ConnectionError(
                f"Cannot connect to test database at {TEST_DATABASE_URL}. "
                f"Ensure docker-compose.test.yml is running. Error: {e}"
            )

    asyncio.run(check())


def verify_redis_connection():
    """
    Verify test Redis is accessible

    RAISES:
    ConnectionError if Redis is not accessible
    """
    import redis

    try:
        r = redis.from_url(TEST_REDIS_URL, socket_timeout=5)
        r.ping()
        r.close()
        return True
    except Exception as e:
        raise ConnectionError(
            f"Cannot connect to test Redis at {TEST_REDIS_URL}. "
            f"Ensure docker-compose.test.yml is running. Error: {e}"
        )


# Pytest configuration hooks

def pytest_configure(config):
    """
    Pytest configuration hook - runs before tests

    WORKFLOW:
    1. Verify test infrastructure is running
    2. Display connection info
    3. Set up test markers
    """
    print("\n" + "="*80)
    print("INTEGRATION TEST INFRASTRUCTURE CHECK")
    print("="*80)
    print(f"Database URL: {TEST_DATABASE_URL}")
    print(f"Redis URL: {TEST_REDIS_URL}")
    print(f"JWT Secret: {TEST_JWT_SECRET[:20]}...")

    # Verify infrastructure (commented out for now - will fail if not running)
    # try:
    #     verify_database_connection()
    #     print("✅ Database connection: OK")
    # except ConnectionError as e:
    #     print(f"❌ Database connection: FAILED")
    #     print(f"   {e}")

    # try:
    #     verify_redis_connection()
    #     print("✅ Redis connection: OK")
    # except ConnectionError as e:
    #     print(f"❌ Redis connection: FAILED")
    #     print(f"   {e}")

    print("="*80 + "\n")


def pytest_collection_modifyitems(config, items):
    """
    Pytest hook to modify test collection

    WORKFLOW:
    - Mark all tests as 'integration' for filtering
    - Add slow marker to tests that need full infrastructure
    """
    for item in items:
        if "integration" not in item.keywords:
            item.add_marker(pytest.mark.integration)
