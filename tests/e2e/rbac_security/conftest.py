"""
Pytest fixtures and configuration for RBAC security E2E tests.

BUSINESS CONTEXT:
Provides test fixtures for user authentication, test data setup,
and database verification for RBAC permission testing.

TECHNICAL IMPLEMENTATION:
- PostgreSQL test database connection
- Test user credentials
- Organization test data
- Course and enrollment test data
"""

import pytest
import asyncio
import asyncpg
import os
from typing import Dict, List, Optional


@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for async tests.

    TECHNICAL REQUIREMENT:
    Pytest-asyncio requires an event loop fixture for async test support.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_pool():
    """
    Create PostgreSQL connection pool for database verification.

    BUSINESS CONTEXT:
    E2E tests verify UI behavior against actual database state
    to ensure data integrity and permission enforcement.

    Returns:
        asyncpg.Pool: Database connection pool
    """
    database_url = os.getenv(
        'TEST_DATABASE_URL',
        'postgresql://postgres:postgres_password@localhost:5433/course_creator_test'
    )

    pool = await asyncpg.create_pool(database_url)
    yield pool
    await pool.close()


@pytest.fixture
def test_users() -> Dict[str, Dict[str, str]]:
    """
    Test user credentials for different roles.

    BUSINESS CONTEXT:
    Provides authenticated users for each role type to test
    role-specific permissions and access controls.

    Returns:
        Dict mapping role names to user credentials
    """
    return {
        'site_admin': {
            'email': 'siteadmin@test.org',
            'password': 'SecureP@ss123',
            'role': 'SITE_ADMIN',
            'user_id': 'user-site-admin-001',
            'name': 'Site Admin User'
        },
        'org_admin': {
            'email': 'orgadmin@testorg.com',
            'password': 'SecureP@ss123',
            'role': 'ORGANIZATION_ADMIN',
            'user_id': 'user-org-admin-001',
            'organization_id': 'org-001',
            'name': 'Organization Admin User'
        },
        'instructor': {
            'email': 'instructor@testorg.com',
            'password': 'SecureP@ss123',
            'role': 'INSTRUCTOR',
            'user_id': 'user-instructor-001',
            'organization_id': 'org-001',
            'name': 'Instructor User'
        },
        'student': {
            'email': 'student@testorg.com',
            'password': 'SecureP@ss123',
            'role': 'STUDENT',
            'user_id': 'user-student-001',
            'organization_id': 'org-001',
            'name': 'Student User'
        },
        'instructor_other_org': {
            'email': 'instructor@otherorg.com',
            'password': 'SecureP@ss123',
            'role': 'INSTRUCTOR',
            'user_id': 'user-instructor-002',
            'organization_id': 'org-002',
            'name': 'Instructor Other Org'
        }
    }


@pytest.fixture
def test_organizations() -> List[Dict[str, str]]:
    """
    Test organization data.

    BUSINESS CONTEXT:
    Multi-tenant platform requires multiple organizations to test
    cross-organization access control and data isolation.

    Returns:
        List of organization data dictionaries
    """
    return [
        {
            'organization_id': 'org-001',
            'name': 'Test Organization',
            'slug': 'test-org',
            'status': 'active'
        },
        {
            'organization_id': 'org-002',
            'name': 'Other Organization',
            'slug': 'other-org',
            'status': 'active'
        },
        {
            'organization_id': 'org-003',
            'name': 'Third Organization',
            'slug': 'third-org',
            'status': 'active'
        }
    ]


@pytest.fixture
def test_courses() -> List[Dict[str, str]]:
    """
    Test course data.

    BUSINESS CONTEXT:
    Courses are assigned to instructors and enrolled by students.
    Tests verify proper course access control based on assignments.

    Returns:
        List of course data dictionaries
    """
    return [
        {
            'course_id': 'course-001',
            'title': 'Introduction to Python',
            'organization_id': 'org-001',
            'instructor_id': 'user-instructor-001',
            'status': 'published'
        },
        {
            'course_id': 'course-002',
            'title': 'Advanced JavaScript',
            'organization_id': 'org-001',
            'instructor_id': 'user-instructor-001',
            'status': 'published'
        },
        {
            'course_id': 'course-888',
            'title': 'Data Science Fundamentals',
            'organization_id': 'org-001',
            'instructor_id': 'user-instructor-002',
            'status': 'published'
        },
        {
            'course_id': 'course-999',
            'title': 'Machine Learning',
            'organization_id': 'org-002',
            'instructor_id': 'user-instructor-002',
            'status': 'published'
        }
    ]


@pytest.fixture
def test_enrollments() -> List[Dict[str, str]]:
    """
    Test course enrollment data.

    BUSINESS CONTEXT:
    Enrollments link students to courses. Tests verify students
    can only access enrolled courses.

    Returns:
        List of enrollment data dictionaries
    """
    return [
        {
            'enrollment_id': 'enroll-001',
            'student_id': 'user-student-001',
            'course_id': 'course-001',
            'status': 'active',
            'progress': 35.5
        },
        {
            'enrollment_id': 'enroll-002',
            'student_id': 'user-student-001',
            'course_id': 'course-002',
            'status': 'active',
            'progress': 72.3
        },
        {
            'enrollment_id': 'enroll-003',
            'student_id': 'user-student-001',
            'course_id': 'course-003',
            'status': 'active',
            'progress': 10.0
        }
    ]


@pytest.fixture
async def verify_user_role(db_pool):
    """
    Verify user role in database.

    BUSINESS CONTEXT:
    Ensures test users have correct roles assigned in database
    before running permission tests.

    Args:
        db_pool: PostgreSQL connection pool

    Returns:
        Async function to verify user role
    """
    async def _verify(user_id: str, expected_role: str) -> bool:
        """
        Check if user has expected role in database.

        Args:
            user_id: User ID to check
            expected_role: Expected role type

        Returns:
            True if role matches
        """
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT ur.role_type
                FROM user_roles ur
                WHERE ur.user_id = $1
                LIMIT 1
                """,
                user_id
            )

            if not result:
                return False

            return result['role_type'] == expected_role

    return _verify


@pytest.fixture
async def verify_course_assignment(db_pool):
    """
    Verify course instructor assignment in database.

    BUSINESS CONTEXT:
    Confirms instructor is assigned to specific courses
    before testing course access permissions.

    Args:
        db_pool: PostgreSQL connection pool

    Returns:
        Async function to verify course assignment
    """
    async def _verify(instructor_id: str, course_id: str) -> bool:
        """
        Check if instructor is assigned to course.

        Args:
            instructor_id: Instructor user ID
            course_id: Course ID to check

        Returns:
            True if instructor is assigned
        """
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT ci.instructor_id
                FROM course_instructors ci
                WHERE ci.instructor_id = $1 AND ci.course_id = $2
                """,
                instructor_id,
                course_id
            )

            return result is not None

    return _verify


@pytest.fixture
async def verify_course_enrollment(db_pool):
    """
    Verify student course enrollment in database.

    BUSINESS CONTEXT:
    Confirms student is enrolled in specific courses
    before testing course content access.

    Args:
        db_pool: PostgreSQL connection pool

    Returns:
        Async function to verify enrollment
    """
    async def _verify(student_id: str, course_id: str) -> bool:
        """
        Check if student is enrolled in course.

        Args:
            student_id: Student user ID
            course_id: Course ID to check

        Returns:
            True if student is enrolled
        """
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT ce.enrollment_id
                FROM course_enrollments ce
                WHERE ce.student_id = $1
                  AND ce.course_id = $2
                  AND ce.status = 'active'
                """,
                student_id,
                course_id
            )

            return result is not None

    return _verify


@pytest.fixture
async def get_organization_member_count(db_pool):
    """
    Get member count for organization.

    BUSINESS CONTEXT:
    Verifies organization member counts displayed in UI
    match actual database records.

    Args:
        db_pool: PostgreSQL connection pool

    Returns:
        Async function to get member count
    """
    async def _get_count(organization_id: str) -> int:
        """
        Get total members in organization.

        Args:
            organization_id: Organization ID

        Returns:
            Member count
        """
        async with db_pool.acquire() as conn:
            result = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM organization_members om
                WHERE om.organization_id = $1
                  AND om.status = 'active'
                """,
                organization_id
            )

            return result or 0

    return _get_count


@pytest.fixture
def rbac_test_config() -> Dict[str, any]:
    """
    RBAC test configuration.

    BUSINESS CONTEXT:
    Centralized configuration for RBAC security tests including
    timeout values, retry settings, and security thresholds.

    Returns:
        Configuration dictionary
    """
    return {
        'base_url': os.getenv('TEST_BASE_URL', 'https://localhost:3000'),
        'api_timeout': 30,
        'page_load_timeout': 15,
        'element_wait_timeout': 10,
        'max_retries': 3,
        'security_checks': {
            'verify_https': True,
            'verify_cors': True,
            'verify_csrf': True,
            'verify_auth_headers': True
        },
        'test_data_cleanup': True
    }
