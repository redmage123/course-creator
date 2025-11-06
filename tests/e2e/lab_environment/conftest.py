"""
Pytest configuration for lab environment tests

BUSINESS PURPOSE:
- Provides Docker client for container verification
- Sets up lab-specific test environment
- Manages test data cleanup
"""

import pytest
import os
import docker
import psycopg2
from datetime import datetime

@pytest.fixture(scope="session")
def docker_client():
    """
    Provides Docker client for container verification
    
    BUSINESS REQUIREMENT:
    Tests must verify actual Docker container state,
    not just UI state, to ensure real cleanup occurs.
    """
    client = docker.from_env()
    yield client
    client.close()


@pytest.fixture
def db_connection():
    """
    Provides PostgreSQL database connection for lab session queries
    
    BUSINESS REQUIREMENT:
    Tests must verify lab_sessions table state for accurate
    cleanup and timeout tracking.
    """
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5433')),
        database=os.getenv('DB_NAME', 'course_creator'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres_password')
    )
    yield conn
    conn.close()


@pytest.fixture
def cleanup_test_labs(docker_client, db_connection):
    """
    Cleanup test lab containers and sessions after each test
    
    BUSINESS REQUIREMENT:
    Prevents resource leaks from test labs affecting
    production or other tests.
    """
    yield
    
    # Cleanup any containers created during test
    containers = docker_client.containers.list(filters={"name": "lab_test_*"})
    for container in containers:
        try:
            container.stop(timeout=5)
            container.remove(force=True)
        except Exception as e:
            print(f"Failed to cleanup container {container.name}: {e}")
    
    # Cleanup lab sessions from database
    cursor = db_connection.cursor()
    cursor.execute("DELETE FROM lab_sessions WHERE container_name LIKE 'lab_test_%'")
    db_connection.commit()
    cursor.close()


@pytest.fixture
def test_student_credentials():
    """
    Provides test student credentials for lab access
    
    BUSINESS REQUIREMENT:
    Labs are accessible to students enrolled in courses.
    """
    return {
        'email': 'student.test@example.com',
        'password': 'password123',
        'student_id': 'test_student_001',
        'course_id': 'test_course_001'
    }


@pytest.fixture
def accelerated_timeout_env(monkeypatch):
    """
    Sets accelerated timeout environment variables for testing
    
    BUSINESS REQUIREMENT:
    Tests cannot wait 2 hours for real timeout.
    Use 5-second timeout for testing purposes.
    """
    monkeypatch.setenv('LAB_INACTIVITY_TIMEOUT_SECONDS', '5')
    monkeypatch.setenv('LAB_MAX_DURATION_SECONDS', '30')
    monkeypatch.setenv('LAB_TIMEOUT_WARNING_SECONDS', '3')
    yield
