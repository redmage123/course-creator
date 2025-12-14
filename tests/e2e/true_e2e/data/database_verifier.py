"""
Database Verifier for True E2E Testing

BUSINESS CONTEXT:
True E2E tests must verify that UI actions result in correct database state.
This verifier provides methods to query the database and compare with UI state.

TECHNICAL IMPLEMENTATION:
- Read-only database queries
- Type-safe result objects
- Comparison helpers for UI vs DB validation

USAGE:
    verifier = DatabaseVerifier()

    # After user creates course via UI
    courses = verifier.get_courses_for_organization(org_id)
    assert len(courses) == expected_count
    assert courses[0].title == "My New Course"
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


@dataclass
class CourseRecord:
    """Represents a course database record."""
    id: str
    title: str
    description: Optional[str]
    instructor_id: str
    organization_id: Optional[str]
    is_published: bool
    difficulty_level: str
    created_at: datetime
    updated_at: datetime


@dataclass
class UserRecord:
    """Represents a user database record."""
    id: str
    email: str
    username: str
    role_name: str
    organization_id: Optional[str]
    is_active: bool
    created_at: datetime


@dataclass
class EnrollmentRecord:
    """Represents an enrollment database record."""
    id: str
    course_id: str
    student_id: str
    status: str
    created_at: datetime


@dataclass
class OrganizationRecord:
    """Represents an organization database record."""
    id: str
    name: str
    slug: str
    created_at: datetime


class DatabaseVerifier:
    """
    Verifies database state for E2E test assertions.

    This class provides read-only access to the database for
    validating that UI actions result in correct data changes.
    """

    def __init__(self):
        """Initialize database verifier."""
        self._connection = None

    @property
    def connection(self):
        """Get or create database connection."""
        if self._connection is None or self._connection.closed:
            self._connection = self._create_connection()
        return self._connection

    def _create_connection(self):
        """Create PostgreSQL connection from environment variables."""
        db_url = os.getenv('TEST_DATABASE_URL') or os.getenv('DATABASE_URL')

        if db_url:
            import urllib.parse
            parsed = urllib.parse.urlparse(db_url)
            return psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:],
                cursor_factory=RealDictCursor
            )
        else:
            return psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '5433')),
                user=os.getenv('DB_USER', 'course_user'),
                password=os.getenv('DB_PASSWORD', 'course_pass'),
                database=os.getenv('DB_NAME', 'course_creator'),
                cursor_factory=RealDictCursor
            )

    def _execute(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a query and return all results."""
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def _execute_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Execute a query and return single result."""
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    # ========================================================================
    # COURSE QUERIES
    # ========================================================================

    def get_course_by_id(self, course_id: str) -> Optional[CourseRecord]:
        """
        Get course by ID.

        Args:
            course_id: Course UUID

        Returns:
            CourseRecord or None if not found
        """
        query = """
            SELECT id, title, description, instructor_id, organization_id,
                   is_published, difficulty_level, created_at, updated_at
            FROM courses
            WHERE id = %s
        """
        result = self._execute_one(query, (course_id,))
        if result:
            return CourseRecord(**result)
        return None

    def get_courses_for_organization(
        self,
        organization_id: str,
        include_unpublished: bool = True
    ) -> List[CourseRecord]:
        """
        Get all courses for an organization.

        Args:
            organization_id: Organization UUID
            include_unpublished: Whether to include unpublished courses

        Returns:
            List of CourseRecord objects
        """
        if include_unpublished:
            query = """
                SELECT id, title, description, instructor_id, organization_id,
                       is_published, difficulty_level, created_at, updated_at
                FROM courses
                WHERE organization_id = %s
                ORDER BY created_at DESC
            """
            params = (organization_id,)
        else:
            query = """
                SELECT id, title, description, instructor_id, organization_id,
                       is_published, difficulty_level, created_at, updated_at
                FROM courses
                WHERE organization_id = %s AND is_published = true
                ORDER BY created_at DESC
            """
            params = (organization_id,)

        results = self._execute(query, params)
        return [CourseRecord(**r) for r in results]

    def get_courses_for_instructor(
        self,
        instructor_id: str,
        include_unpublished: bool = True
    ) -> List[CourseRecord]:
        """
        Get all courses for an instructor.

        Args:
            instructor_id: Instructor's user UUID
            include_unpublished: Whether to include unpublished courses

        Returns:
            List of CourseRecord objects
        """
        if include_unpublished:
            query = """
                SELECT id, title, description, instructor_id, organization_id,
                       is_published, difficulty_level, created_at, updated_at
                FROM courses
                WHERE instructor_id = %s
                ORDER BY created_at DESC
            """
        else:
            query = """
                SELECT id, title, description, instructor_id, organization_id,
                       is_published, difficulty_level, created_at, updated_at
                FROM courses
                WHERE instructor_id = %s AND is_published = true
                ORDER BY created_at DESC
            """

        results = self._execute(query, (instructor_id,))
        return [CourseRecord(**r) for r in results]

    def get_course_count(
        self,
        organization_id: str = None,
        instructor_id: str = None,
        published_only: bool = False
    ) -> int:
        """
        Get count of courses matching criteria.

        Args:
            organization_id: Filter by organization
            instructor_id: Filter by instructor
            published_only: Only count published courses

        Returns:
            Course count
        """
        conditions = []
        params = []

        if organization_id:
            conditions.append("organization_id = %s")
            params.append(organization_id)

        if instructor_id:
            conditions.append("instructor_id = %s")
            params.append(instructor_id)

        if published_only:
            conditions.append("is_published = true")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT COUNT(*) as count FROM courses WHERE {where_clause}"

        result = self._execute_one(query, tuple(params))
        return result['count'] if result else 0

    def verify_course_exists(self, course_id: str) -> bool:
        """Check if course exists."""
        return self.get_course_by_id(course_id) is not None

    # ========================================================================
    # USER QUERIES
    # ========================================================================

    def get_user_by_id(self, user_id: str) -> Optional[UserRecord]:
        """
        Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            UserRecord or None if not found
        """
        query = """
            SELECT id, email, username, role_name, organization_id,
                   is_active, created_at
            FROM users
            WHERE id = %s
        """
        result = self._execute_one(query, (user_id,))
        if result:
            return UserRecord(**result)
        return None

    def get_user_by_email(self, email: str) -> Optional[UserRecord]:
        """
        Get user by email.

        Args:
            email: User email address

        Returns:
            UserRecord or None if not found
        """
        query = """
            SELECT id, email, username, role_name, organization_id,
                   is_active, created_at
            FROM users
            WHERE email = %s
        """
        result = self._execute_one(query, (email,))
        if result:
            return UserRecord(**result)
        return None

    def get_users_for_organization(
        self,
        organization_id: str,
        role: str = None
    ) -> List[UserRecord]:
        """
        Get all users for an organization.

        Args:
            organization_id: Organization UUID
            role: Optional role filter

        Returns:
            List of UserRecord objects
        """
        if role:
            query = """
                SELECT id, email, username, role_name, organization_id,
                       is_active, created_at
                FROM users
                WHERE organization_id = %s AND role_name = %s
                ORDER BY created_at DESC
            """
            params = (organization_id, role)
        else:
            query = """
                SELECT id, email, username, role_name, organization_id,
                       is_active, created_at
                FROM users
                WHERE organization_id = %s
                ORDER BY created_at DESC
            """
            params = (organization_id,)

        results = self._execute(query, params)
        return [UserRecord(**r) for r in results]

    def verify_user_exists(self, email: str) -> bool:
        """Check if user with email exists."""
        return self.get_user_by_email(email) is not None

    # ========================================================================
    # ENROLLMENT QUERIES
    # ========================================================================

    def get_enrollments_for_course(
        self,
        course_id: str
    ) -> List[EnrollmentRecord]:
        """
        Get all enrollments for a course.

        Args:
            course_id: Course UUID

        Returns:
            List of EnrollmentRecord objects
        """
        query = """
            SELECT id, course_id, student_id, status, created_at
            FROM enrollments
            WHERE course_id = %s
            ORDER BY created_at DESC
        """
        results = self._execute(query, (course_id,))
        return [EnrollmentRecord(**r) for r in results]

    def get_enrollments_for_student(
        self,
        student_id: str
    ) -> List[EnrollmentRecord]:
        """
        Get all enrollments for a student.

        Args:
            student_id: Student's user UUID

        Returns:
            List of EnrollmentRecord objects
        """
        query = """
            SELECT id, course_id, student_id, status, created_at
            FROM enrollments
            WHERE student_id = %s
            ORDER BY created_at DESC
        """
        results = self._execute(query, (student_id,))
        return [EnrollmentRecord(**r) for r in results]

    def get_enrollment_count(
        self,
        course_id: str = None,
        student_id: str = None
    ) -> int:
        """
        Get count of enrollments matching criteria.

        Args:
            course_id: Filter by course
            student_id: Filter by student

        Returns:
            Enrollment count
        """
        conditions = []
        params = []

        if course_id:
            conditions.append("course_id = %s")
            params.append(course_id)

        if student_id:
            conditions.append("student_id = %s")
            params.append(student_id)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT COUNT(*) as count FROM enrollments WHERE {where_clause}"

        result = self._execute_one(query, tuple(params))
        return result['count'] if result else 0

    def verify_enrollment_exists(
        self,
        course_id: str,
        student_id: str
    ) -> bool:
        """Check if enrollment exists."""
        query = """
            SELECT id FROM enrollments
            WHERE course_id = %s AND student_id = %s
        """
        result = self._execute_one(query, (course_id, student_id))
        return result is not None

    # ========================================================================
    # ORGANIZATION QUERIES
    # ========================================================================

    def get_organization_by_id(
        self,
        organization_id: str
    ) -> Optional[OrganizationRecord]:
        """
        Get organization by ID.

        Args:
            organization_id: Organization UUID

        Returns:
            OrganizationRecord or None if not found
        """
        query = """
            SELECT id, name, slug, created_at
            FROM organizations
            WHERE id = %s
        """
        result = self._execute_one(query, (organization_id,))
        if result:
            return OrganizationRecord(**result)
        return None

    def get_organization_by_slug(self, slug: str) -> Optional[OrganizationRecord]:
        """
        Get organization by slug.

        Args:
            slug: Organization slug

        Returns:
            OrganizationRecord or None if not found
        """
        query = """
            SELECT id, name, slug, created_at
            FROM organizations
            WHERE slug = %s
        """
        result = self._execute_one(query, (slug,))
        if result:
            return OrganizationRecord(**result)
        return None

    # ========================================================================
    # COMPARISON HELPERS
    # ========================================================================

    def compare_course_counts(
        self,
        ui_count: int,
        organization_id: str,
        include_unpublished: bool = True
    ) -> Dict[str, Any]:
        """
        Compare UI course count with database count.

        Args:
            ui_count: Number of courses shown in UI
            organization_id: Organization to check
            include_unpublished: Whether unpublished courses should be included

        Returns:
            Comparison result with match status and details
        """
        db_count = self.get_course_count(
            organization_id=organization_id,
            published_only=not include_unpublished
        )

        return {
            'match': ui_count == db_count,
            'ui_count': ui_count,
            'db_count': db_count,
            'include_unpublished': include_unpublished,
            'message': (
                f"UI shows {ui_count} courses, DB has {db_count} "
                f"({'including' if include_unpublished else 'excluding'} unpublished)"
            )
        }

    def compare_enrollment_counts(
        self,
        ui_count: int,
        course_id: str
    ) -> Dict[str, Any]:
        """
        Compare UI enrollment count with database count.

        Args:
            ui_count: Number of enrollments shown in UI
            course_id: Course to check

        Returns:
            Comparison result with match status and details
        """
        db_count = self.get_enrollment_count(course_id=course_id)

        return {
            'match': ui_count == db_count,
            'ui_count': ui_count,
            'db_count': db_count,
            'message': f"UI shows {ui_count} enrollments, DB has {db_count}"
        }

    def verify_course_in_list(
        self,
        course_title: str,
        ui_course_titles: List[str],
        organization_id: str = None,
        instructor_id: str = None
    ) -> Dict[str, Any]:
        """
        Verify a course exists in both UI list and database.

        Args:
            course_title: Title to search for
            ui_course_titles: List of titles shown in UI
            organization_id: Organization filter for DB query
            instructor_id: Instructor filter for DB query

        Returns:
            Verification result with match status
        """
        # Check UI
        in_ui = any(course_title in title for title in ui_course_titles)

        # Check DB
        if organization_id:
            db_courses = self.get_courses_for_organization(
                organization_id, include_unpublished=True
            )
        elif instructor_id:
            db_courses = self.get_courses_for_instructor(
                instructor_id, include_unpublished=True
            )
        else:
            db_courses = []

        in_db = any(course_title in c.title for c in db_courses)

        return {
            'match': in_ui and in_db,
            'in_ui': in_ui,
            'in_db': in_db,
            'message': (
                f"Course '{course_title}': "
                f"UI={'found' if in_ui else 'NOT FOUND'}, "
                f"DB={'found' if in_db else 'NOT FOUND'}"
            )
        }

    def close(self) -> None:
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.debug("Database connection closed")
