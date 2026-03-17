"""
Pytest Fixtures for Video Features E2E Tests

BUSINESS CONTEXT:
Provides reusable fixtures for database connections, test data setup,
and cleanup operations specific to video testing scenarios.

FIXTURES:
1. db_connection - PostgreSQL database connection with auto-cleanup
2. test_student_data - Create test students for video tracking
3. test_video_data - Create test videos with metadata
4. cleanup_video_sessions - Clean up watch sessions after tests
"""

import pytest
import psycopg2
import uuid
from datetime import datetime


@pytest.fixture
def db_connection():
    """
    Provide PostgreSQL database connection for E2E tests.

    BUSINESS REQUIREMENT:
    Tests need database access to verify data persistence and
    validate multi-layer verification (UI + Database + Video Player State).

    DESIGN PATTERN: Resource Management
    Automatically closes connection after test completion.

    Yields:
        psycopg2.connection: Active database connection
    """
    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        database="course_creator",
        user="postgres",
        password="postgres_password"
    )

    # Enable autocommit for DDL operations
    conn.autocommit = False

    yield conn

    # Cleanup: Close connection
    conn.close()


@pytest.fixture
def test_student_data(db_connection):
    """
    Create test student accounts for video tracking tests.

    BUSINESS REQUIREMENT:
    Video tests need authenticated student accounts to test
    progress tracking, watch time analytics, and completion detection.

    Returns:
        dict: Test student data with keys:
            - student_id (int)
            - email (str)
            - password (str)
            - course_id (int)
    """
    cursor = db_connection.cursor()

    # Generate unique student email
    student_email = f"video_test_student_{uuid.uuid4().hex[:8]}@test.com"

    # Insert test student (adjust schema as needed)
    cursor.execute("""
        INSERT INTO students (email, password_hash, first_name, last_name, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        RETURNING student_id
    """, (student_email, "hashed_password_123", "Test", "Student"))

    student_id = cursor.fetchone()[0]
    db_connection.commit()

    # Create test course and enrollment
    cursor.execute("""
        INSERT INTO courses (title, description, created_at)
        VALUES (%s, %s, NOW())
        RETURNING course_id
    """, ("Test Video Course", "Course for video playback testing"))

    course_id = cursor.fetchone()[0]
    db_connection.commit()

    # Enroll student in course
    cursor.execute("""
        INSERT INTO enrollments (student_id, course_id, enrolled_at)
        VALUES (%s, %s, NOW())
    """, (student_id, course_id))
    db_connection.commit()

    student_data = {
        'student_id': student_id,
        'email': student_email,
        'password': 'password123',  # Plain text for login tests
        'course_id': course_id
    }

    cursor.close()

    yield student_data

    # Cleanup: Delete test student and related data
    cursor = db_connection.cursor()
    cursor.execute("DELETE FROM enrollments WHERE student_id = %s", (student_id,))
    cursor.execute("DELETE FROM video_watch_sessions WHERE student_email = %s", (student_email,))
    cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
    cursor.execute("DELETE FROM courses WHERE course_id = %s", (course_id,))
    db_connection.commit()
    cursor.close()


@pytest.fixture
def test_video_data(db_connection, test_student_data):
    """
    Create test video records for playback and analytics tests.

    BUSINESS REQUIREMENT:
    Tests need realistic video data with metadata (duration, resolution, URL)
    to validate playback controls and analytics calculations.

    Args:
        db_connection: Database connection fixture
        test_student_data: Student data fixture (provides course_id)

    Returns:
        dict: Test video data with keys:
            - video_id (int)
            - title (str)
            - duration (int) - in seconds
            - url (str)
            - course_id (int)
    """
    cursor = db_connection.cursor()
    course_id = test_student_data['course_id']

    # Insert test video
    cursor.execute("""
        INSERT INTO videos (
            course_id, title, description, duration_seconds,
            video_url, resolution, codec, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        RETURNING video_id
    """, (
        course_id,
        "Test Video - Introduction to Testing",
        "Sample video for E2E playback tests",
        300,  # 5 minutes
        "https://localhost:8008/videos/test_video.mp4",
        "1080p",
        "h264"
    ))

    video_id = cursor.fetchone()[0]
    db_connection.commit()

    video_data = {
        'video_id': video_id,
        'title': "Test Video - Introduction to Testing",
        'duration': 300,
        'url': "https://localhost:8008/videos/test_video.mp4",
        'course_id': course_id
    }

    cursor.close()

    yield video_data

    # Cleanup: Delete test video
    cursor = db_connection.cursor()
    cursor.execute("DELETE FROM videos WHERE video_id = %s", (video_id,))
    db_connection.commit()
    cursor.close()


@pytest.fixture
def cleanup_video_sessions(db_connection):
    """
    Clean up video watch sessions after tests.

    BUSINESS REQUIREMENT:
    Ensures test isolation by removing all video watch sessions
    created during test execution.

    DESIGN PATTERN: Cleanup Fixture
    Runs after test completion to maintain clean test database.

    Args:
        db_connection: Database connection fixture
    """
    # Track session IDs created during test
    session_ids = []

    def register_session(session_id):
        """Register a session ID for cleanup."""
        session_ids.append(session_id)

    # Provide registration function to test
    yield register_session

    # Cleanup: Delete all registered sessions
    if session_ids:
        cursor = db_connection.cursor()
        cursor.execute(
            "DELETE FROM video_watch_sessions WHERE session_id = ANY(%s)",
            (session_ids,)
        )
        db_connection.commit()
        cursor.close()


@pytest.fixture(autouse=True)
def setup_video_test_environment(db_connection):
    """
    Auto-run setup for all video tests.

    BUSINESS REQUIREMENT:
    Ensures video_watch_sessions table exists with correct schema
    before running any video tests.

    DESIGN PATTERN: Auto-use Fixture
    Runs automatically before every video test without explicit import.

    Args:
        db_connection: Database connection fixture
    """
    cursor = db_connection.cursor()

    # Create video_watch_sessions table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_watch_sessions (
            session_id SERIAL PRIMARY KEY,
            student_email VARCHAR(255) NOT NULL,
            video_id INTEGER NOT NULL,
            watch_time_seconds INTEGER DEFAULT 0,
            last_position FLOAT DEFAULT 0,
            completion_percentage FLOAT DEFAULT 0,
            is_completed BOOLEAN DEFAULT FALSE,
            quality_preference VARCHAR(20) DEFAULT 'auto',
            playback_speed FLOAT DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(student_email, video_id)
        )
    """)
    db_connection.commit()
    cursor.close()

    yield

    # No cleanup needed - table persists for other tests


@pytest.fixture
def mock_video_file():
    """
    Provide mock video file for upload tests.

    BUSINESS REQUIREMENT:
    Upload tests need realistic video files to validate
    file handling, progress tracking, and transcoding pipeline.

    Returns:
        dict: Mock file data with keys:
            - filename (str)
            - size (int) - in bytes
            - format (str)
            - path (str) - temporary file path
    """
    import tempfile
    import os

    # Create temporary video file (1MB dummy file)
    temp_file = tempfile.NamedTemporaryFile(
        suffix='.mp4',
        delete=False
    )

    # Write 1MB of dummy data
    temp_file.write(b'\x00' * (1024 * 1024))
    temp_file.close()

    mock_file_data = {
        'filename': 'test_video.mp4',
        'size': 1024 * 1024,  # 1MB
        'format': 'mp4',
        'path': temp_file.name
    }

    yield mock_file_data

    # Cleanup: Delete temporary file
    os.unlink(temp_file.name)
