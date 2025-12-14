"""
Test Data Seeder for True E2E Testing

BUSINESS CONTEXT:
True E2E tests need predictable test data to validate complete workflows.
This seeder creates test data directly in the database before tests run,
ensuring a known starting state.

TECHNICAL IMPLEMENTATION:
- Direct PostgreSQL connection for fast data creation
- UUID-prefixed entity names for test isolation
- Transaction-based operations for cleanup
- Password hashing matching the application's bcrypt implementation

USAGE:
    seeder = DataSeeder()
    org = seeder.create_organization("Test Org")
    admin = seeder.create_org_admin(org.id, "admin@test.com", "password123")
    # ... run tests ...
    seeder.cleanup()  # Removes all test data
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4
from dataclasses import dataclass

import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


@dataclass
class SeededOrganization:
    """Represents a seeded organization."""
    id: str
    name: str
    slug: str


@dataclass
class SeededUser:
    """Represents a seeded user."""
    id: str
    email: str
    username: str
    role: str
    organization_id: Optional[str]
    password: str  # Plaintext for test login


@dataclass
class SeededCourse:
    """Represents a seeded course."""
    id: str
    title: str
    instructor_id: str
    organization_id: Optional[str]
    is_published: bool


@dataclass
class SeededEnrollment:
    """Represents a seeded enrollment."""
    id: str
    course_id: str
    student_id: str


class DataSeeder:
    """
    Seeds test data directly into the database.

    All seeded entities use a test prefix for easy identification
    and cleanup after tests complete.
    """

    def __init__(self, test_prefix: str = None):
        """
        Initialize data seeder.

        Args:
            test_prefix: Prefix for all seeded entity names
                         (auto-generated if not provided)
        """
        self.test_prefix = test_prefix or f"test_{uuid4().hex[:8]}"
        self._seeded_entities: Dict[str, List[str]] = {
            'organizations': [],
            'users': [],
            'courses': [],
            'enrollments': [],
            'projects': [],
            'tracks': [],
        }
        self._connection = None

    @property
    def connection(self):
        """Get or create database connection."""
        if self._connection is None or self._connection.closed:
            self._connection = self._create_connection()
        return self._connection

    def _create_connection(self):
        """Create PostgreSQL connection from environment variables."""
        # Use test database if specified, otherwise fall back to main DB
        db_url = os.getenv('TEST_DATABASE_URL') or os.getenv('DATABASE_URL')

        if db_url:
            # Parse connection URL
            # Format: postgresql://user:password@host:port/database
            import urllib.parse
            parsed = urllib.parse.urlparse(db_url)
            return psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:],  # Remove leading /
                cursor_factory=RealDictCursor
            )
        else:
            # Use default test connection parameters
            return psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '5433')),
                user=os.getenv('DB_USER', 'course_user'),
                password=os.getenv('DB_PASSWORD', 'course_pass'),
                database=os.getenv('DB_NAME', 'course_creator'),
                cursor_factory=RealDictCursor
            )

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt (matching application implementation)."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def _execute(self, query: str, params: tuple = None) -> Any:
        """Execute a query and return results."""
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            try:
                return cursor.fetchall()
            except psycopg2.ProgrammingError:
                return None

    def _execute_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Execute a query and return single result."""
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            try:
                return cursor.fetchone()
            except psycopg2.ProgrammingError:
                return None

    def _insert(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Execute insert and return inserted row."""
        result = self._execute_one(query, params)
        self.connection.commit()
        return result

    # ========================================================================
    # ORGANIZATION SEEDING
    # ========================================================================

    def create_organization(
        self,
        name: str = None,
        slug: str = None
    ) -> SeededOrganization:
        """
        Create a test organization.

        Args:
            name: Organization name (auto-generated if not provided)
            slug: Organization slug (derived from name if not provided)

        Returns:
            SeededOrganization with created data
        """
        org_id = str(uuid4())
        name = name or f"{self.test_prefix}_org"
        slug = slug or name.lower().replace(' ', '-').replace('_', '-')

        query = """
            INSERT INTO organizations (id, name, slug, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, name, slug
        """
        now = datetime.utcnow()
        result = self._insert(query, (org_id, name, slug, now, now))

        self._seeded_entities['organizations'].append(org_id)
        logger.info(f"Seeded organization: {name} ({org_id})")

        return SeededOrganization(
            id=result['id'],
            name=result['name'],
            slug=result['slug']
        )

    # ========================================================================
    # USER SEEDING
    # ========================================================================

    def create_user(
        self,
        email: str,
        password: str,
        role: str,
        organization_id: str = None,
        username: str = None,
        first_name: str = None,
        last_name: str = None
    ) -> SeededUser:
        """
        Create a test user.

        Args:
            email: User email
            password: Plaintext password
            role: User role (site_admin, organization_admin, instructor, student)
            organization_id: Associated organization ID
            username: Username (derived from email if not provided)
            first_name: User first name
            last_name: User last name

        Returns:
            SeededUser with created data
        """
        user_id = str(uuid4())
        username = username or email.split('@')[0]
        password_hash = self._hash_password(password)
        first_name = first_name or self.test_prefix
        last_name = last_name or "User"

        query = """
            INSERT INTO users (
                id, email, username, password_hash, role_name,
                organization_id, first_name, last_name,
                is_active, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, email, username, role_name, organization_id
        """
        now = datetime.utcnow()
        result = self._insert(query, (
            user_id, email, username, password_hash, role,
            organization_id, first_name, last_name,
            True, now, now
        ))

        self._seeded_entities['users'].append(user_id)
        logger.info(f"Seeded user: {email} ({role})")

        return SeededUser(
            id=result['id'],
            email=result['email'],
            username=result['username'],
            role=result['role_name'],
            organization_id=result['organization_id'],
            password=password  # Return plaintext for test login
        )

    def create_site_admin(
        self,
        email: str = None,
        password: str = "TestPass123!"
    ) -> SeededUser:
        """Create a site admin user."""
        email = email or f"{self.test_prefix}_siteadmin@test.com"
        return self.create_user(email, password, "site_admin")

    def create_org_admin(
        self,
        organization_id: str,
        email: str = None,
        password: str = "TestPass123!"
    ) -> SeededUser:
        """Create an organization admin user."""
        email = email or f"{self.test_prefix}_orgadmin@test.com"
        return self.create_user(
            email, password, "organization_admin",
            organization_id=organization_id
        )

    def create_instructor(
        self,
        organization_id: str,
        email: str = None,
        password: str = "TestPass123!"
    ) -> SeededUser:
        """Create an instructor user."""
        email = email or f"{self.test_prefix}_instructor@test.com"
        return self.create_user(
            email, password, "instructor",
            organization_id=organization_id
        )

    def create_student(
        self,
        organization_id: str,
        email: str = None,
        password: str = "TestPass123!"
    ) -> SeededUser:
        """Create a student user."""
        email = email or f"{self.test_prefix}_student@test.com"
        return self.create_user(
            email, password, "student",
            organization_id=organization_id
        )

    # ========================================================================
    # COURSE SEEDING
    # ========================================================================

    def create_course(
        self,
        instructor_id: str,
        title: str = None,
        description: str = None,
        organization_id: str = None,
        is_published: bool = False,
        difficulty_level: str = "beginner"
    ) -> SeededCourse:
        """
        Create a test course.

        Args:
            instructor_id: Course instructor's user ID
            title: Course title
            description: Course description
            organization_id: Associated organization ID
            is_published: Whether course is published
            difficulty_level: beginner, intermediate, or advanced

        Returns:
            SeededCourse with created data
        """
        course_id = str(uuid4())
        title = title or f"{self.test_prefix}_course"
        description = description or f"Test course created by {self.test_prefix}"

        query = """
            INSERT INTO courses (
                id, title, description, instructor_id, organization_id,
                is_published, difficulty_level, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, title, instructor_id, organization_id, is_published
        """
        now = datetime.utcnow()
        result = self._insert(query, (
            course_id, title, description, instructor_id, organization_id,
            is_published, difficulty_level, now, now
        ))

        self._seeded_entities['courses'].append(course_id)
        logger.info(f"Seeded course: {title} (published={is_published})")

        return SeededCourse(
            id=result['id'],
            title=result['title'],
            instructor_id=result['instructor_id'],
            organization_id=result['organization_id'],
            is_published=result['is_published']
        )

    # ========================================================================
    # ENROLLMENT SEEDING
    # ========================================================================

    def create_enrollment(
        self,
        course_id: str,
        student_id: str
    ) -> SeededEnrollment:
        """
        Create a course enrollment.

        Args:
            course_id: Course ID
            student_id: Student user ID

        Returns:
            SeededEnrollment with created data
        """
        enrollment_id = str(uuid4())

        query = """
            INSERT INTO enrollments (
                id, course_id, student_id, status, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, course_id, student_id
        """
        now = datetime.utcnow()
        result = self._insert(query, (
            enrollment_id, course_id, student_id, 'active', now, now
        ))

        self._seeded_entities['enrollments'].append(enrollment_id)
        logger.info(f"Seeded enrollment: student {student_id} in course {course_id}")

        return SeededEnrollment(
            id=result['id'],
            course_id=result['course_id'],
            student_id=result['student_id']
        )

    # ========================================================================
    # COMPLETE SCENARIO SEEDING
    # ========================================================================

    def seed_complete_org_scenario(
        self,
        org_name: str = None
    ) -> Dict[str, Any]:
        """
        Seed a complete organization scenario with all user types.

        Creates:
        - 1 Organization
        - 1 Org Admin
        - 2 Instructors
        - 3 Students
        - 2 Courses (1 published, 1 unpublished)
        - Enrollments for all students

        Returns:
            Dictionary with all created entities
        """
        org = self.create_organization(org_name)

        org_admin = self.create_org_admin(org.id)
        instructor1 = self.create_instructor(
            org.id,
            email=f"{self.test_prefix}_instructor1@test.com"
        )
        instructor2 = self.create_instructor(
            org.id,
            email=f"{self.test_prefix}_instructor2@test.com"
        )

        students = []
        for i in range(3):
            students.append(self.create_student(
                org.id,
                email=f"{self.test_prefix}_student{i+1}@test.com"
            ))

        # Create courses - one published, one unpublished
        published_course = self.create_course(
            instructor_id=instructor1.id,
            title=f"{self.test_prefix}_Published Course",
            organization_id=org.id,
            is_published=True
        )
        unpublished_course = self.create_course(
            instructor_id=instructor2.id,
            title=f"{self.test_prefix}_Draft Course",
            organization_id=org.id,
            is_published=False
        )

        # Enroll students in published course
        enrollments = []
        for student in students:
            enrollments.append(self.create_enrollment(
                published_course.id,
                student.id
            ))

        return {
            'organization': org,
            'org_admin': org_admin,
            'instructors': [instructor1, instructor2],
            'students': students,
            'courses': [published_course, unpublished_course],
            'enrollments': enrollments,
        }

    # ========================================================================
    # CLEANUP
    # ========================================================================

    def cleanup(self) -> None:
        """
        Remove all seeded test data.

        Called automatically in teardown fixtures, but can also
        be called manually for immediate cleanup.
        """
        try:
            # Delete in reverse order of dependencies
            for enrollment_id in self._seeded_entities['enrollments']:
                self._execute(
                    "DELETE FROM enrollments WHERE id = %s",
                    (enrollment_id,)
                )

            for course_id in self._seeded_entities['courses']:
                self._execute(
                    "DELETE FROM courses WHERE id = %s",
                    (course_id,)
                )

            for user_id in self._seeded_entities['users']:
                self._execute(
                    "DELETE FROM users WHERE id = %s",
                    (user_id,)
                )

            for org_id in self._seeded_entities['organizations']:
                self._execute(
                    "DELETE FROM organizations WHERE id = %s",
                    (org_id,)
                )

            self.connection.commit()
            logger.info(f"Cleaned up test data with prefix: {self.test_prefix}")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            self.connection.rollback()
            raise
        finally:
            self._seeded_entities = {
                'organizations': [],
                'users': [],
                'courses': [],
                'enrollments': [],
                'projects': [],
                'tracks': [],
            }

    def cleanup_by_prefix(self, prefix: str = None) -> None:
        """
        Clean up all entities matching a prefix.

        Useful for cleaning up orphaned test data.

        Args:
            prefix: Prefix to match (uses test_prefix if not provided)
        """
        prefix = prefix or self.test_prefix
        pattern = f"{prefix}%"

        try:
            # Delete enrollments for matching courses
            self._execute("""
                DELETE FROM enrollments
                WHERE course_id IN (
                    SELECT id FROM courses WHERE title LIKE %s
                )
            """, (pattern,))

            # Delete courses
            self._execute("DELETE FROM courses WHERE title LIKE %s", (pattern,))

            # Delete users
            self._execute("DELETE FROM users WHERE email LIKE %s", (pattern,))

            # Delete organizations
            self._execute("DELETE FROM organizations WHERE name LIKE %s", (pattern,))

            self.connection.commit()
            logger.info(f"Cleaned up all data matching prefix: {prefix}")

        except Exception as e:
            logger.error(f"Prefix cleanup failed: {e}")
            self.connection.rollback()
            raise

    def close(self) -> None:
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.debug("Database connection closed")
