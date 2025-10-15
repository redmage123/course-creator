"""
Test Fixtures for Track Management Tests

BUSINESS PURPOSE:
Provides reusable test data and database setup/teardown for TDD tests

TEST STRATEGY:
- Clean database before each test
- Create realistic test data
- Proper foreign key relationships
"""

import pytest
import psycopg2
from uuid import uuid4
import os

# Database connection string
DB_STRING = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres_password@localhost:5433/course_creator'
)


@pytest.fixture(scope="function")
def db_connection():
    """
    Provide database connection with automatic cleanup

    USAGE:
    Tests can use this fixture to get a fresh database state
    """
    conn = psycopg2.connect(DB_STRING)
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def clean_test_data(db_connection):
    """
    Clean all test data before and after each test

    BUSINESS VALUE:
    Each test runs in isolation with no data pollution
    """
    conn = db_connection

    def _clean():
        with conn.cursor() as cur:
            # Disable trigger temporarily to allow cleanup
            cur.execute("ALTER TABLE track_instructors DISABLE TRIGGER enforce_min_instructors")

            # Delete in reverse FK order to avoid constraint violations
            cur.execute("DELETE FROM track_students")
            cur.execute("DELETE FROM track_instructors")
            cur.execute("DELETE FROM tracks")
            cur.execute("DELETE FROM projects WHERE is_sub_project = TRUE")
            cur.execute("DELETE FROM projects WHERE is_sub_project = FALSE")

            # Re-enable trigger
            cur.execute("ALTER TABLE track_instructors ENABLE TRIGGER enforce_min_instructors")
            conn.commit()

    # Clean before test
    _clean()

    yield

    # Clean after test
    _clean()


@pytest.fixture
def test_organization():
    """
    Provide a test organization ID

    Returns:
        UUID: Organization ID for testing
    """
    return uuid4()


@pytest.fixture
def test_project(db_connection, test_organization, clean_test_data):
    """
    Create a test main project in the database

    Returns:
        dict: Project data with id, organization_id, name, etc.
    """
    conn = db_connection
    org_id = test_organization
    project_id = uuid4()

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO projects (
                id, organization_id, name, slug,
                is_sub_project, auto_balance_students,
                created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id, organization_id, name, slug, is_sub_project, auto_balance_students
        """, (
            str(project_id), str(org_id), "Test Main Project", "test-main-project",
            False, True  # Enable auto_balance by default for testing
        ))

        row = cur.fetchone()
        conn.commit()

        return {
            'id': row[0],
            'organization_id': row[1],
            'name': row[2],
            'slug': row[3],
            'is_sub_project': row[4],
            'auto_balance_students': row[5]
        }


@pytest.fixture
def test_sub_project(db_connection, test_organization, test_project, clean_test_data):
    """
    Create a test sub-project in the database

    Returns:
        dict: Sub-project data
    """
    conn = db_connection
    org_id = test_organization
    parent_project_id = test_project['id']
    sub_project_id = uuid4()

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO projects (
                id, organization_id, name, slug,
                parent_project_id, is_sub_project, auto_balance_students,
                created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id, organization_id, name, slug, parent_project_id, is_sub_project
        """, (
            str(sub_project_id), str(org_id), "Test Sub-Project", "test-sub-project",
            parent_project_id, True, False
        ))

        row = cur.fetchone()
        conn.commit()

        return {
            'id': row[0],
            'organization_id': row[1],
            'name': row[2],
            'slug': row[3],
            'parent_project_id': row[4],
            'is_sub_project': row[5]
        }


@pytest.fixture
def test_track(db_connection, test_organization, test_project, clean_test_data):
    """
    Create a test track in the database

    Returns:
        dict: Track data
    """
    conn = db_connection
    org_id = test_organization
    project_id = test_project['id']
    track_id = uuid4()

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO tracks (
                id, organization_id, name, slug,
                project_id, sub_project_id,
                difficulty, status, display_order,
                created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id, organization_id, name, slug, project_id, sub_project_id
        """, (
            str(track_id), str(org_id), "Test Track", "test-track",
            project_id, None,  # Track belongs to main project
            'beginner', 'draft', 0
        ))

        row = cur.fetchone()
        conn.commit()

        return {
            'id': row[0],
            'organization_id': row[1],
            'name': row[2],
            'slug': row[3],
            'project_id': row[4],
            'sub_project_id': row[5]
        }


@pytest.fixture
def test_instructor():
    """
    Provide a test instructor UUID

    Returns:
        UUID: Instructor user ID
    """
    return uuid4()


@pytest.fixture
def test_student():
    """
    Provide a test student UUID

    Returns:
        UUID: Student user ID
    """
    return uuid4()
