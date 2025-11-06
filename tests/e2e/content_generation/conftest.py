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
        port=int(os.getenv('DB_PORT', '5433')),  # Docker PostgreSQL exposed port
        database=os.getenv('DB_NAME', 'course_creator'),
        user=os.getenv('DB_USER', 'postgres'),  # Use main postgres user
        password=os.getenv('DB_PASSWORD', 'postgres_password')  # Docker postgres password
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


@pytest.fixture
def test_course_data(db_connection):
    """
    Create test course data for content generation tests

    BUSINESS REQUIREMENT:
    Content generation tests need courses in the database to verify
    generated content is correctly associated with courses.

    DESIGN PATTERN:
    - Creates course with unique identifier (UUID)
    - Returns course data for test use
    - Automatically cleans up after test completion

    Yields:
        dict: Test course data with keys:
            - id (uuid) - Course UUID
            - title (str)
            - description (str)
            - instructor_id (uuid)
    """
    import uuid
    cursor = db_connection.cursor()

    # Generate UUIDs for test data
    course_id = str(uuid.uuid4())
    instructor_id = str(uuid.uuid4())

    # Insert test instructor first (required foreign key)
    cursor.execute("""
        INSERT INTO course_creator.users (id, username, email, hashed_password, role)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (email) DO NOTHING
    """, (instructor_id, 'test_instructor_content_gen', 'instructor_content_gen@example.com', 'hashed_pass', 'instructor'))
    db_connection.commit()

    # Insert test course
    cursor.execute("""
        INSERT INTO courses (id, title, description, instructor_id, created_at, updated_at)
        VALUES (%s, %s, %s, %s, NOW(), NOW())
        RETURNING id
    """, (course_id, "AI Generated Test Course", "Course for testing content generation workflows", instructor_id))

    returned_id = cursor.fetchone()[0]
    db_connection.commit()

    course_data = {
        'id': str(returned_id),
        'course_id': str(returned_id),  # Alias for backward compatibility
        'title': "AI Generated Test Course",
        'description': "Course for testing content generation workflows",
        'instructor_id': instructor_id
    }

    cursor.close()

    yield course_data

    # Cleanup: Delete test course and related data
    cursor = db_connection.cursor()
    # Delete in correct order to respect foreign key constraints
    cursor.execute("DELETE FROM slides WHERE course_id = %s", (course_id,))
    cursor.execute("DELETE FROM modules WHERE course_id = %s", (course_id,))
    cursor.execute("DELETE FROM quizzes WHERE course_id = %s", (course_id,))
    cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
    cursor.execute("DELETE FROM course_creator.users WHERE id = %s", (instructor_id,))
    db_connection.commit()
    cursor.close()


@pytest.fixture
def ai_generation_timeout():
    """
    Provides timeout configuration for AI generation operations

    BUSINESS REQUIREMENT:
    AI content generation can take 30-120 seconds depending on complexity.
    Tests must wait sufficiently long but not indefinitely.

    DESIGN RATIONALE:
    - Default timeout: 120 seconds for complex generation
    - Poll interval: 2 seconds to check completion status
    - Max retries: 60 attempts (120s / 2s polling)

    Returns:
        dict: Timeout configuration with keys:
            - timeout_seconds (int) - Maximum wait time
            - poll_interval (int) - Seconds between status checks
            - max_retries (int) - Maximum polling attempts
    """
    return {
        'timeout_seconds': 120,  # 2 minutes max for AI generation
        'poll_interval': 2,      # Check every 2 seconds
        'max_retries': 60        # 60 attempts * 2 seconds = 120 seconds
    }
