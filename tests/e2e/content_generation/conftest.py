"""
Pytest configuration for content generation tests

BUSINESS PURPOSE:
- Provides database connection for content verification
- Sets up content generation test environment
- Manages test data cleanup
- Provides common fixtures for AI generation testing
"""

import pytest
import os
import psycopg2
from datetime import datetime


@pytest.fixture(scope="session")
def db_connection():
    """
    Provides PostgreSQL database connection for content verification
    
    BUSINESS REQUIREMENT:
    Tests must verify content_versions table state for accurate
    version tracking and rollback verification.
    """
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'course_creator'),
        user=os.getenv('DB_USER', 'course_user'),
        password=os.getenv('DB_PASSWORD', 'password')
    )
    yield conn
    conn.close()


@pytest.fixture
def cleanup_test_content(db_connection):
    """
    Cleanup test content versions after each test
    
    BUSINESS REQUIREMENT:
    Prevents test data pollution affecting production
    or other tests.
    """
    yield
    
    # Cleanup content versions created during test
    cursor = db_connection.cursor()
    cursor.execute("""
        DELETE FROM content_versions 
        WHERE feedback LIKE '%test_%' 
        OR feedback LIKE '%Iteration%'
    """)
    db_connection.commit()
    cursor.close()


@pytest.fixture
def test_instructor_credentials():
    """
    Provides test instructor credentials for content generation
    
    BUSINESS REQUIREMENT:
    Content generation is restricted to instructors.
    """
    return {
        'email': 'instructor@example.com',
        'password': 'InstructorPass123!',
        'instructor_id': 'test_instructor_001',
        'organization_id': 'test_org_001'
    }


@pytest.fixture
def ai_model_options():
    """
    Provides available AI model options for testing
    
    BUSINESS REQUIREMENT:
    Platform supports multiple AI models for content generation.
    """
    return ['gpt-4', 'claude', 'llama']


@pytest.fixture
def difficulty_levels():
    """
    Provides difficulty level options for quiz generation
    
    BUSINESS REQUIREMENT:
    Quizzes can be generated at different difficulty levels.
    """
    return ['easy', 'medium', 'hard']
