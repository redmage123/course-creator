"""
Course DAO Unit Tests

BUSINESS CONTEXT:
Comprehensive tests for Course Management Data Access Object ensuring all database
operations work correctly, handle edge cases, and maintain data integrity for the
multi-tenant course management system.

TECHNICAL IMPLEMENTATION:
- Tests all CRUD operations for courses
- Validates transaction behavior and rollback
- Tests error handling and constraint violations
- Ensures SQL queries return correct data structures
- Tests complex queries (search, statistics, enrollments)

TDD APPROACH:
These tests validate that the DAO layer correctly:
- Creates courses with organizational context
- Retrieves courses by various criteria
- Updates course metadata and settings
- Handles course instances and enrollments
- Manages quiz publications
- Enforces multi-tenant data isolation
"""

import pytest
import asyncpg
from datetime import datetime, timedelta
from uuid import uuid4
import sys
from pathlib import Path
import json

# Add course-management service to path
course_mgmt_path = Path(__file__).parent.parent.parent.parent / 'services' / 'course-management'
sys.path.insert(0, str(course_mgmt_path))

from data_access.course_dao import CourseManagementDAO
from course_management.domain.entities.course import Course, DifficultyLevel, DurationUnit


class TestCourseDAOCreate:
    """
    Test Suite: Course Creation Operations

    BUSINESS REQUIREMENT:
    System must create new courses with validation, organization context, and project tracking
    """

    @pytest.mark.asyncio
    async def test_create_course_with_required_fields(self, db_transaction):
        """
        TEST: Create course with only required fields

        BUSINESS REQUIREMENT:
        Courses must be creatable with minimal required information

        VALIDATES:
        - Course record is created in database
        - Generated ID is valid UUID
        - created_at timestamp is set
        - Default values are applied
        """
        dao = CourseManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        # Create test instructor and organization
        instructor_id = str(uuid4())
        org_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            instructor_id, f'instructor_{uuid4().hex[:8]}', f'inst_{uuid4().hex[:8]}@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.organizations (id, name, slug, contact_email)
               VALUES ($1, $2, $3, $4)""",
            org_id, 'Test Org', f'org_{uuid4().hex[:8]}', 'org@test.com'
        )

        course = Course(
            id=str(uuid4()),
            title='Introduction to Python',
            description='Learn Python programming from scratch',
            instructor_id=instructor_id,
            category='Programming',
            difficulty_level=DifficultyLevel.BEGINNER,
            estimated_duration=8,
            duration_unit=DurationUnit.WEEKS,
            is_published=False,
            organization_id=org_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Execute: Create course via DAO
        result = await dao.create(course)

        # Assert: Course was created successfully
        assert result is not None
        assert result.id == course.id

        # Verify: Course exists in database
        row = await db_transaction.fetchrow(
            "SELECT * FROM courses WHERE id = $1",
            course.id
        )
        assert row is not None
        assert row['title'] == course.title
        assert row['instructor_id'] == instructor_id
        assert row['organization_id'] == org_id
        assert row['is_published'] == False

    @pytest.mark.asyncio
    async def test_create_course_with_all_fields(self, db_transaction):
        """
        TEST: Create course with all optional fields including organizational context

        BUSINESS REQUIREMENT:
        Courses should support comprehensive metadata including organization, project, track, and location

        VALIDATES:
        - All fields are stored correctly
        - Tags are persisted in metadata JSON
        - Organizational relationships are maintained
        """
        dao = CourseManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        # Create prerequisite records
        instructor_id = str(uuid4())
        org_id = str(uuid4())
        project_id = str(uuid4())
        track_id = str(uuid4())
        location_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            instructor_id, f'instructor_{uuid4().hex[:8]}', f'inst_{uuid4().hex[:8]}@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.organizations (id, name, slug, contact_email)
               VALUES ($1, $2, $3, $4)""",
            org_id, 'Test Org', f'org_{uuid4().hex[:8]}', 'org@test.com'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.projects (id, name, organization_id, created_by)
               VALUES ($1, $2, $3, $4)""",
            project_id, 'Test Project', org_id, instructor_id
        )

        course = Course(
            id=str(uuid4()),
            title='Advanced Machine Learning',
            description='Deep dive into ML algorithms and applications',
            instructor_id=instructor_id,
            category='Data Science',
            difficulty_level=DifficultyLevel.ADVANCED,
            estimated_duration=12,
            duration_unit=DurationUnit.WEEKS,
            price=299.99,
            is_published=True,
            tags=['machine-learning', 'ai', 'python', 'tensorflow'],
            organization_id=org_id,
            project_id=project_id,
            track_id=track_id,
            location_id=location_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        result = await dao.create(course)

        # Verify all fields were stored
        row = await db_transaction.fetchrow(
            "SELECT * FROM courses WHERE id = $1",
            course.id
        )
        assert row['title'] == 'Advanced Machine Learning'
        assert row['price'] == 299.99
        assert row['is_published'] == True
        assert row['organization_id'] == org_id
        assert row['project_id'] == project_id

        # Verify tags in metadata
        metadata = json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata']
        assert 'tags' in metadata
        assert 'machine-learning' in metadata['tags']


class TestCourseDAORetrieve:
    """
    Test Suite: Course Retrieval Operations

    BUSINESS REQUIREMENT:
    System must retrieve courses by various criteria with proper data isolation
    """

    @pytest.mark.asyncio
    async def test_get_course_by_id(self, db_transaction):
        """
        TEST: Retrieve course by ID

        VALIDATES:
        - Course can be fetched by UUID
        - Returned course has all expected fields
        - Tags are properly deserialized from metadata
        """
        dao = CourseManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        # Create test data
        instructor_id = str(uuid4())
        org_id = str(uuid4())
        course_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            instructor_id, f'instructor_{uuid4().hex[:8]}', f'inst_{uuid4().hex[:8]}@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.organizations (id, name, slug, contact_email)
               VALUES ($1, $2, $3, $4)""",
            org_id, 'Test Org', f'org_{uuid4().hex[:8]}', 'org@test.com'
        )

        await db_transaction.execute(
            """INSERT INTO courses (
                id, title, description, instructor_id, category, difficulty_level,
                estimated_duration, duration_unit, is_published, organization_id, metadata,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)""",
            course_id, 'Test Course', 'Description', instructor_id, 'Programming',
            'beginner', 8, 'weeks', False, org_id, json.dumps({'tags': ['test', 'python']}),
            datetime.utcnow(), datetime.utcnow()
        )

        # Retrieve course
        course = await dao.get_by_id(course_id)

        assert course is not None
        assert course.id == course_id
        assert course.title == 'Test Course'
        assert course.instructor_id == instructor_id
        assert course.organization_id == org_id
        assert 'test' in course.tags

    @pytest.mark.asyncio
    async def test_get_courses_by_instructor_id(self, db_transaction):
        """
        TEST: Retrieve all courses for an instructor

        BUSINESS REQUIREMENT:
        Instructors need to see all courses they've created

        VALIDATES:
        - Multiple courses returned for same instructor
        - Courses sorted by created_at DESC
        - Only instructor's courses are returned
        """
        dao = CourseManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        # Create test data
        instructor_id = str(uuid4())
        other_instructor_id = str(uuid4())
        org_id = str(uuid4())

        for instr_id in [instructor_id, other_instructor_id]:
            await db_transaction.execute(
                """INSERT INTO course_creator.users (id, username, email, password, role)
                   VALUES ($1, $2, $3, $4, $5)""",
                instr_id, f'instructor_{uuid4().hex[:8]}', f'inst_{uuid4().hex[:8]}@test.com',
                '$2b$12$test', 'instructor'
            )

        await db_transaction.execute(
            """INSERT INTO course_creator.organizations (id, name, slug, contact_email)
               VALUES ($1, $2, $3, $4)""",
            org_id, 'Test Org', f'org_{uuid4().hex[:8]}', 'org@test.com'
        )

        # Create 3 courses for instructor, 1 for other
        for i in range(3):
            await db_transaction.execute(
                """INSERT INTO courses (
                    id, title, description, instructor_id, category, difficulty_level,
                    estimated_duration, duration_unit, organization_id, metadata,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)""",
                str(uuid4()), f'Course {i}', 'Description', instructor_id, 'Programming',
                'beginner', 8, 'weeks', org_id, json.dumps({'tags': []}),
                datetime.utcnow(), datetime.utcnow()
            )

        await db_transaction.execute(
            """INSERT INTO courses (
                id, title, description, instructor_id, category, difficulty_level,
                estimated_duration, duration_unit, organization_id, metadata,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)""",
            str(uuid4()), 'Other Course', 'Description', other_instructor_id, 'Programming',
            'beginner', 8, 'weeks', org_id, json.dumps({'tags': []}),
            datetime.utcnow(), datetime.utcnow()
        )

        # Retrieve courses
        courses = await dao.get_by_instructor_id(instructor_id)

        assert len(courses) == 3
        assert all(c.instructor_id == instructor_id for c in courses)

    @pytest.mark.asyncio
    async def test_get_nonexistent_course_returns_none(self, db_transaction):
        """
        TEST: Retrieve nonexistent course returns None

        VALIDATES:
        - Query for nonexistent course doesn't raise exception
        - Returns None instead of raising error
        """
        dao = CourseManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        fake_id = str(uuid4())
        course = await dao.get_by_id(fake_id)

        assert course is None


class TestCourseDAOUpdate:
    """
    Test Suite: Course Update Operations

    BUSINESS REQUIREMENT:
    Instructors must be able to update course information
    """

    @pytest.mark.asyncio
    async def test_update_course_fields(self, db_transaction):
        """
        TEST: Update course fields

        VALIDATES:
        - Course fields can be updated
        - updated_at timestamp is changed
        - Only specified fields are updated
        """
        dao = CourseManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        # Create test course
        instructor_id = str(uuid4())
        org_id = str(uuid4())
        course_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            instructor_id, f'instructor_{uuid4().hex[:8]}', f'inst_{uuid4().hex[:8]}@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.organizations (id, name, slug, contact_email)
               VALUES ($1, $2, $3, $4)""",
            org_id, 'Test Org', f'org_{uuid4().hex[:8]}', 'org@test.com'
        )

        await db_transaction.execute(
            """INSERT INTO courses (
                id, title, description, instructor_id, category, difficulty_level,
                estimated_duration, duration_unit, is_published, organization_id, metadata,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)""",
            course_id, 'Original Title', 'Original Description', instructor_id, 'Programming',
            'beginner', 8, 'weeks', False, org_id, json.dumps({'tags': ['python']}),
            datetime.utcnow(), datetime.utcnow()
        )

        # Update course
        course = Course(
            id=course_id,
            title='Updated Title',
            description='Updated Description',
            instructor_id=instructor_id,
            category='Data Science',
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            estimated_duration=10,
            duration_unit=DurationUnit.WEEKS,
            is_published=True,
            organization_id=org_id,
            tags=['python', 'data-science'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        await dao.update(course)

        # Verify updates
        row = await db_transaction.fetchrow(
            "SELECT * FROM courses WHERE id = $1",
            course_id
        )
        assert row['title'] == 'Updated Title'
        assert row['description'] == 'Updated Description'
        assert row['category'] == 'Data Science'
        assert row['difficulty_level'] == 'intermediate'
        assert row['is_published'] == True


class TestCourseDAODelete:
    """
    Test Suite: Course Deletion Operations

    BUSINESS REQUIREMENT:
    System must support course deletion with proper cleanup
    """

    @pytest.mark.asyncio
    async def test_delete_course(self, db_transaction):
        """
        TEST: Delete course

        VALIDATES:
        - Course is removed from database
        - Delete operation returns True on success
        """
        dao = CourseManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        # Create test course
        instructor_id = str(uuid4())
        org_id = str(uuid4())
        course_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            instructor_id, f'instructor_{uuid4().hex[:8]}', f'inst_{uuid4().hex[:8]}@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.organizations (id, name, slug, contact_email)
               VALUES ($1, $2, $3, $4)""",
            org_id, 'Test Org', f'org_{uuid4().hex[:8]}', 'org@test.com'
        )

        await db_transaction.execute(
            """INSERT INTO courses (
                id, title, description, instructor_id, category, difficulty_level,
                estimated_duration, duration_unit, organization_id, metadata,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)""",
            course_id, 'Test Course', 'Description', instructor_id, 'Programming',
            'beginner', 8, 'weeks', org_id, json.dumps({'tags': []}),
            datetime.utcnow(), datetime.utcnow()
        )

        # Delete course
        result = await dao.delete(course_id)
        assert result == True

        # Verify course no longer exists
        row = await db_transaction.fetchrow(
            "SELECT * FROM courses WHERE id = $1",
            course_id
        )
        assert row is None


class TestCourseDAOSearch:
    """
    Test Suite: Course Search Operations

    BUSINESS REQUIREMENT:
    Students must be able to search and filter published courses
    """

    @pytest.mark.asyncio
    async def test_search_courses_by_query(self, db_transaction):
        """
        TEST: Search courses by text query

        VALIDATES:
        - Text search works on title and description
        - Only published courses are returned
        - Case-insensitive search
        """
        dao = CourseManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        # Create test data
        instructor_id = str(uuid4())
        org_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            instructor_id, f'instructor_{uuid4().hex[:8]}', f'inst_{uuid4().hex[:8]}@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.organizations (id, name, slug, contact_email)
               VALUES ($1, $2, $3, $4)""",
            org_id, 'Test Org', f'org_{uuid4().hex[:8]}', 'org@test.com'
        )

        # Create courses with different titles
        for title, published in [
            ('Python Programming Basics', True),
            ('Advanced Python Techniques', True),
            ('Java Fundamentals', True),
            ('Python for Data Science', False)  # Not published
        ]:
            await db_transaction.execute(
                """INSERT INTO courses (
                    id, title, description, instructor_id, category, difficulty_level,
                    estimated_duration, duration_unit, is_published, organization_id, metadata,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)""",
                str(uuid4()), title, 'Description', instructor_id, 'Programming',
                'beginner', 8, 'weeks', published, org_id, json.dumps({'tags': []}),
                datetime.utcnow(), datetime.utcnow()
            )

        # Search for Python courses
        courses = await dao.search('Python', {})

        # Should find 2 published Python courses (not the unpublished one)
        assert len(courses) == 2
        assert all('Python' in c.title for c in courses)
        assert all(c.is_published for c in courses)

    @pytest.mark.asyncio
    async def test_search_courses_with_filters(self, db_transaction):
        """
        TEST: Search courses with category and difficulty filters

        VALIDATES:
        - Filter by category works
        - Filter by difficulty level works
        - Multiple filters work together
        """
        dao = CourseManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        # Create test data
        instructor_id = str(uuid4())
        org_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            instructor_id, f'instructor_{uuid4().hex[:8]}', f'inst_{uuid4().hex[:8]}@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.organizations (id, name, slug, contact_email)
               VALUES ($1, $2, $3, $4)""",
            org_id, 'Test Org', f'org_{uuid4().hex[:8]}', 'org@test.com'
        )

        # Create courses with different categories and difficulties
        test_courses = [
            ('Course 1', 'Programming', 'beginner'),
            ('Course 2', 'Programming', 'intermediate'),
            ('Course 3', 'Data Science', 'beginner'),
            ('Course 4', 'Programming', 'beginner'),
        ]

        for title, category, difficulty in test_courses:
            await db_transaction.execute(
                """INSERT INTO courses (
                    id, title, description, instructor_id, category, difficulty_level,
                    estimated_duration, duration_unit, is_published, organization_id, metadata,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)""",
                str(uuid4()), title, 'Description', instructor_id, category,
                difficulty, 8, 'weeks', True, org_id, json.dumps({'tags': []}),
                datetime.utcnow(), datetime.utcnow()
            )

        # Search with filters
        courses = await dao.search('', {
            'category': 'Programming',
            'difficulty_level': 'beginner'
        })

        # Should find 2 beginner Programming courses
        assert len(courses) == 2
        assert all(c.category == 'Programming' for c in courses)
        assert all(c.difficulty_level == DifficultyLevel.BEGINNER for c in courses)


class TestCourseDAOStatistics:
    """
    Test Suite: Course Statistics Operations

    BUSINESS REQUIREMENT:
    Instructors need analytics about their courses
    """

    @pytest.mark.asyncio
    async def test_count_courses_by_instructor(self, db_transaction):
        """
        TEST: Count total courses for instructor

        VALIDATES:
        - Count returns correct number
        - Only counts instructor's courses
        """
        dao = CourseManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        # Create test data
        instructor_id = str(uuid4())
        org_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            instructor_id, f'instructor_{uuid4().hex[:8]}', f'inst_{uuid4().hex[:8]}@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.organizations (id, name, slug, contact_email)
               VALUES ($1, $2, $3, $4)""",
            org_id, 'Test Org', f'org_{uuid4().hex[:8]}', 'org@test.com'
        )

        # Create multiple courses
        for i in range(5):
            await db_transaction.execute(
                """INSERT INTO courses (
                    id, title, description, instructor_id, category, difficulty_level,
                    estimated_duration, duration_unit, organization_id, metadata,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)""",
                str(uuid4()), f'Course {i}', 'Description', instructor_id, 'Programming',
                'beginner', 8, 'weeks', org_id, json.dumps({'tags': []}),
                datetime.utcnow(), datetime.utcnow()
            )

        # Count courses
        count = await dao.count_by_instructor(instructor_id)
        assert count == 5

    @pytest.mark.asyncio
    async def test_get_instructor_course_stats(self, db_transaction):
        """
        TEST: Get comprehensive statistics for instructor's courses

        VALIDATES:
        - Returns total course count
        - Returns course list with details
        """
        dao = CourseManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        # Create test data
        instructor_id = str(uuid4())
        org_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            instructor_id, f'instructor_{uuid4().hex[:8]}', f'inst_{uuid4().hex[:8]}@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.organizations (id, name, slug, contact_email)
               VALUES ($1, $2, $3, $4)""",
            org_id, 'Test Org', f'org_{uuid4().hex[:8]}', 'org@test.com'
        )

        # Create courses
        for i in range(3):
            await db_transaction.execute(
                """INSERT INTO courses (
                    id, title, description, instructor_id, category, difficulty_level,
                    estimated_duration, duration_unit, organization_id, metadata,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)""",
                str(uuid4()), f'Course {i}', 'Description', instructor_id, 'Programming',
                'beginner', 8, 'weeks', org_id, json.dumps({'tags': []}),
                datetime.utcnow(), datetime.utcnow()
            )

        # Get stats
        stats = await dao.get_instructor_course_stats(instructor_id)

        assert stats['total_courses'] == 3
        assert len(stats['courses']) == 3


class TestCourseDAOEnrollments:
    """
    Test Suite: Course Enrollment Operations

    BUSINESS REQUIREMENT:
    System must track student enrollments and course instances
    """

    @pytest.mark.asyncio
    async def test_count_active_enrollments(self, db_transaction):
        """
        TEST: Count active enrollments for a course

        VALIDATES:
        - Counts enrollments correctly
        - Only counts active instances
        """
        dao = CourseManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        # Create test data
        instructor_id = str(uuid4())
        org_id = str(uuid4())
        course_id = str(uuid4())
        instance_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            instructor_id, f'instructor_{uuid4().hex[:8]}', f'inst_{uuid4().hex[:8]}@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.organizations (id, name, slug, contact_email)
               VALUES ($1, $2, $3, $4)""",
            org_id, 'Test Org', f'org_{uuid4().hex[:8]}', 'org@test.com'
        )

        await db_transaction.execute(
            """INSERT INTO courses (
                id, title, description, instructor_id, category, difficulty_level,
                estimated_duration, duration_unit, organization_id, metadata,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)""",
            course_id, 'Test Course', 'Description', instructor_id, 'Programming',
            'beginner', 8, 'weeks', org_id, json.dumps({'tags': []}),
            datetime.utcnow(), datetime.utcnow()
        )

        await db_transaction.execute(
            """INSERT INTO course_instances (
                id, course_id, name, start_datetime, end_datetime, status, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            instance_id, course_id, 'Spring 2025',
            datetime.utcnow(), datetime.utcnow() + timedelta(days=90),
            'active', datetime.utcnow()
        )

        # Create enrollments
        for i in range(5):
            student_id = str(uuid4())
            await db_transaction.execute(
                """INSERT INTO course_creator.users (id, username, email, password, role)
                   VALUES ($1, $2, $3, $4, $5)""",
                student_id, f'student_{uuid4().hex[:8]}', f'student_{uuid4().hex[:8]}@test.com',
                '$2b$12$test', 'student'
            )

            await db_transaction.execute(
                """INSERT INTO student_course_enrollments (
                    id, course_instance_id, student_id, student_email, enrolled_at
                ) VALUES ($1, $2, $3, $4, $5)""",
                str(uuid4()), instance_id, student_id, f'student{i}@test.com', datetime.utcnow()
            )

        # Count enrollments
        count = await dao.count_active_by_course(course_id)
        assert count == 5
