"""
Content Management DAO Unit Tests

BUSINESS CONTEXT:
Comprehensive tests for Content Management Data Access Object ensuring all content
creation, retrieval, search, versioning, and quality tracking operations work correctly.
The content management DAO is crucial for educational content lifecycle management,
version control, and quality assurance.

TECHNICAL IMPLEMENTATION:
- Tests all 9+ DAO methods for content operations
- Validates content creation with metadata
- Tests content search and filtering capabilities
- Validates version history tracking
- Tests quality scoring and analytics
- Ensures status workflow management works correctly

TDD APPROACH:
These tests validate that the DAO layer correctly:
- Creates content with all metadata and relationships
- Retrieves content by ID with optional body inclusion
- Searches content with complex filter criteria
- Manages content status transitions (draft, review, published)
- Tracks content quality scores and improvement
- Maintains version history for content changes
- Provides analytics for content effectiveness
- Handles content type filtering and organization
"""

import pytest
import asyncpg
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import sys
from pathlib import Path
import json
from decimal import Decimal

# Add content-management service to path
content_mgmt_path = Path(__file__).parent.parent.parent.parent / 'services' / 'content-management'
sys.path.insert(0, str(content_mgmt_path))

from data_access.content_management_dao import ContentManagementDAO
from content_management.exceptions import DatabaseException, ValidationException


class TestContentCreation:
    """
    Test Suite: Content Creation Operations

    BUSINESS REQUIREMENT:
    System must create educational content with metadata, ownership tracking,
    and proper categorization for content management workflows.
    """

    @pytest.mark.asyncio
    async def test_create_content_with_required_fields(self, db_transaction):
        """
        TEST: Create content with only required fields

        BUSINESS REQUIREMENT:
        Educational content must be creatable with minimal required information

        VALIDATES:
        - Content record is created in database
        - Content ID is returned
        - Required fields are stored correctly
        - Default status is set appropriately
        """
        dao = ContentManagementDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test user and course
        user_id = str(uuid4())
        course_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(user_id), f'contentcreator_{uuid4().hex[:8]}', f'creator@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.courses (id, title, description, instructor_id,
                   category, difficulty_level, estimated_duration, duration_unit, is_published)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            UUID(course_id), 'Test Course', 'Description', UUID(user_id),
            'Programming', 'beginner', 8, 'weeks', True
        )

        # Prepare content data
        content_id = str(uuid4())
        content_data = {
            'id': content_id,
            'title': 'Introduction to Python Variables',
            'content_type': 'lesson',
            'body': 'Variables are containers for storing data values...',
            'created_by': user_id,
            'course_id': course_id,
            'status': 'draft'
        }

        # Execute: Create content
        result_id = await dao.create_content(content_data)

        # Verify: Content was created
        assert result_id == content_id

        # Verify: Content exists in database
        content = await db_transaction.fetchrow(
            """SELECT * FROM course_creator.content WHERE id = $1""",
            UUID(content_id)
        )
        assert content is not None
        assert content['title'] == 'Introduction to Python Variables'
        assert content['content_type'] == 'lesson'
        assert content['status'] == 'draft'

    @pytest.mark.asyncio
    async def test_create_content_with_full_metadata(self, db_transaction):
        """
        TEST: Create content with comprehensive metadata and tags

        BUSINESS REQUIREMENT:
        Content should support rich metadata for search and organization
        """
        dao = ContentManagementDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test user
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(user_id), f'metacreator_{uuid4().hex[:8]}', f'metacreator@test.com',
            '$2b$12$test', 'instructor'
        )

        # Prepare content with full metadata
        content_id = str(uuid4())
        content_data = {
            'id': content_id,
            'title': 'Advanced Python: Decorators',
            'content_type': 'lesson',
            'body': 'Decorators modify function behavior...',
            'created_by': user_id,
            'course_id': str(uuid4()),
            'status': 'draft',
            'tags': ['python', 'advanced', 'decorators', 'functions'],
            'metadata': {
                'difficulty': 'advanced',
                'estimated_time_minutes': 45,
                'prerequisites': ['basic-python', 'functions']
            },
            'version': '1.0',
            'language': 'en'
        }

        # Execute: Create content
        result_id = await dao.create_content(content_data)

        # Verify: All metadata was stored
        content = await db_transaction.fetchrow(
            """SELECT * FROM course_creator.content WHERE id = $1""",
            UUID(result_id)
        )

        # Verify tags and metadata
        tags = json.loads(content['tags']) if isinstance(content['tags'], str) else content['tags']
        assert 'python' in tags
        assert 'decorators' in tags

        metadata = json.loads(content['metadata']) if isinstance(content['metadata'], str) else content['metadata']
        assert metadata['difficulty'] == 'advanced'
        assert metadata['estimated_time_minutes'] == 45


class TestContentRetrieval:
    """
    Test Suite: Content Retrieval Operations

    BUSINESS REQUIREMENT:
    System must efficiently retrieve content by ID with optional body inclusion
    for performance optimization.
    """

    @pytest.mark.asyncio
    async def test_get_content_by_id_with_body(self, db_transaction):
        """
        TEST: Retrieve content by ID including full body

        BUSINESS REQUIREMENT:
        Content must be retrievable with complete body for editing
        """
        dao = ContentManagementDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test content
        content_id = str(uuid4())
        user_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(user_id), f'getuser_{uuid4().hex[:8]}', f'getuser@test.com',
            '$2b$12$test', 'instructor'
        )

        body_content = 'This is the full body content of the lesson.'
        await db_transaction.execute(
            """INSERT INTO course_creator.content
               (id, title, content_type, body, created_by, course_id, status, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            UUID(content_id), 'Test Content', 'lesson', body_content, UUID(user_id),
            uuid4(), 'published', datetime.utcnow(), datetime.utcnow()
        )

        # Execute: Get content with body
        content = await dao.get_content_by_id(content_id, include_body=True)

        # Verify: Content was retrieved with body
        assert content is not None
        assert content['title'] == 'Test Content'
        assert content['body'] == body_content

    @pytest.mark.asyncio
    async def test_get_content_by_id_without_body(self, db_transaction):
        """
        TEST: Retrieve content metadata without body for performance

        BUSINESS REQUIREMENT:
        Content lists should load quickly without full body text
        """
        dao = ContentManagementDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test content
        content_id = str(uuid4())
        user_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(user_id), f'metauser_{uuid4().hex[:8]}', f'metauser@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.content
               (id, title, content_type, body, created_by, course_id, status, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            UUID(content_id), 'Metadata Test', 'lesson', 'Large body content...', UUID(user_id),
            uuid4(), 'published', datetime.utcnow(), datetime.utcnow()
        )

        # Execute: Get content without body
        content = await dao.get_content_by_id(content_id, include_body=False)

        # Verify: Content metadata retrieved, body excluded
        assert content is not None
        assert content['title'] == 'Metadata Test'
        assert 'body' not in content or content['body'] is None

    @pytest.mark.asyncio
    async def test_get_content_by_id_not_found(self, db_transaction):
        """
        TEST: Retrieve non-existent content returns None

        BUSINESS REQUIREMENT:
        System must gracefully handle missing content lookups
        """
        dao = ContentManagementDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Execute: Get non-existent content
        non_existent_id = str(uuid4())
        content = await dao.get_content_by_id(non_existent_id)

        # Verify: Returns None
        assert content is None


class TestContentSearch:
    """
    Test Suite: Content Search Operations

    BUSINESS REQUIREMENT:
    System must provide powerful search capabilities with filtering by type,
    status, creator, tags, and full-text search.
    """

    @pytest.mark.asyncio
    async def test_search_content_by_type(self, db_transaction):
        """
        TEST: Search content filtered by content type

        BUSINESS REQUIREMENT:
        Instructors need to find specific types of content (lessons, quizzes, labs)
        """
        dao = ContentManagementDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test user
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(user_id), f'searchuser_{uuid4().hex[:8]}', f'search@test.com',
            '$2b$12$test', 'instructor'
        )

        # Create content of different types
        for content_type in ['lesson', 'quiz', 'lesson']:
            await db_transaction.execute(
                """INSERT INTO course_creator.content
                   (id, title, content_type, body, created_by, course_id, status, created_at, updated_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                uuid4(), f'Content {content_type}', content_type, 'Body', UUID(user_id),
                uuid4(), 'published', datetime.utcnow(), datetime.utcnow()
            )

        # Execute: Search for lessons only
        search_params = {'content_type': 'lesson'}
        results = await dao.search_content(search_params, limit=10, offset=0)

        # Verify: Only lessons returned
        assert len(results) >= 2
        for content in results:
            assert content['content_type'] == 'lesson'

    @pytest.mark.asyncio
    async def test_search_content_by_status(self, db_transaction):
        """
        TEST: Search content filtered by status

        BUSINESS REQUIREMENT:
        Admins need to find draft, review, or published content
        """
        dao = ContentManagementDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test user
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(user_id), f'statususer_{uuid4().hex[:8]}', f'status@test.com',
            '$2b$12$test', 'instructor'
        )

        # Create content with different statuses
        for status in ['draft', 'published', 'draft']:
            await db_transaction.execute(
                """INSERT INTO course_creator.content
                   (id, title, content_type, body, created_by, course_id, status, created_at, updated_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                uuid4(), f'Content {status}', 'lesson', 'Body', UUID(user_id),
                uuid4(), status, datetime.utcnow(), datetime.utcnow()
            )

        # Execute: Search for draft content only
        search_params = {'status': 'draft'}
        results = await dao.search_content(search_params, limit=10, offset=0)

        # Verify: Only drafts returned
        assert len(results) >= 2
        for content in results:
            assert content['status'] == 'draft'


class TestContentStatusManagement:
    """
    Test Suite: Content Status Update Operations

    BUSINESS REQUIREMENT:
    System must manage content workflow through status transitions
    (draft → review → published → archived).
    """

    @pytest.mark.asyncio
    async def test_update_content_status_to_published(self, db_transaction):
        """
        TEST: Update content status to published

        BUSINESS REQUIREMENT:
        Content must transition through approval workflow
        """
        dao = ContentManagementDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test content in draft
        content_id = str(uuid4())
        user_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(user_id), f'statuschange_{uuid4().hex[:8]}', f'statuschange@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.content
               (id, title, content_type, body, created_by, course_id, status, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            UUID(content_id), 'Draft Content', 'lesson', 'Body', UUID(user_id),
            uuid4(), 'draft', datetime.utcnow(), datetime.utcnow()
        )

        # Execute: Update status to published
        result = await dao.update_content_status(
            content_id,
            'published',
            updated_by=user_id
        )

        # Verify: Status was updated
        assert result is True

        content = await db_transaction.fetchrow(
            """SELECT status FROM course_creator.content WHERE id = $1""",
            UUID(content_id)
        )
        assert content['status'] == 'published'


class TestContentQualityTracking:
    """
    Test Suite: Content Quality Scoring Operations

    BUSINESS REQUIREMENT:
    System must track content quality scores for continuous improvement
    and content curation.
    """

    @pytest.mark.asyncio
    async def test_update_content_quality_score(self, db_transaction):
        """
        TEST: Update quality score for content

        BUSINESS REQUIREMENT:
        Content quality must be measurable and improvable
        """
        dao = ContentManagementDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test content
        content_id = str(uuid4())
        user_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(user_id), f'qualityuser_{uuid4().hex[:8]}', f'quality@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.content
               (id, title, content_type, body, created_by, course_id, status,
                quality_score, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
            UUID(content_id), 'Quality Content', 'lesson', 'Body', UUID(user_id),
            uuid4(), 'published', Decimal('75.0'), datetime.utcnow(), datetime.utcnow()
        )

        # Execute: Update quality score
        new_score = 85.5
        quality_notes = 'Improved clarity and examples'
        result = await dao.update_content_quality_score(
            content_id,
            new_score,
            quality_notes=quality_notes
        )

        # Verify: Quality score was updated
        assert result is True

        content = await db_transaction.fetchrow(
            """SELECT quality_score FROM course_creator.content WHERE id = $1""",
            UUID(content_id)
        )
        assert float(content['quality_score']) == new_score


class TestContentAnalytics:
    """
    Test Suite: Content Analytics Operations

    BUSINESS REQUIREMENT:
    System must provide analytics on content usage, engagement, and effectiveness
    for data-driven content improvement.
    """

    @pytest.mark.asyncio
    async def test_get_content_analytics(self, db_transaction):
        """
        TEST: Retrieve comprehensive content analytics

        BUSINESS REQUIREMENT:
        Instructors need usage metrics to improve content
        """
        dao = ContentManagementDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test content
        content_id = str(uuid4())
        user_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(user_id), f'analyticsuser_{uuid4().hex[:8]}', f'analytics@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.content
               (id, title, content_type, body, created_by, course_id, status,
                views, likes, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)""",
            UUID(content_id), 'Analytics Content', 'lesson', 'Body', UUID(user_id),
            uuid4(), 'published', 150, 45, datetime.utcnow(), datetime.utcnow()
        )

        # Execute: Get content analytics
        analytics = await dao.get_content_analytics(
            content_id,
            start_date=datetime.utcnow() - timedelta(days=30)
        )

        # Verify: Analytics are returned
        assert analytics is not None
        assert 'views' in analytics
        assert analytics['views'] >= 150


class TestContentVersioning:
    """
    Test Suite: Content Version History Operations

    BUSINESS REQUIREMENT:
    System must maintain version history for content changes, enabling
    rollback and change tracking.
    """

    @pytest.mark.asyncio
    async def test_create_content_version(self, db_transaction):
        """
        TEST: Create new version of content

        BUSINESS REQUIREMENT:
        Content changes must be versioned for audit and rollback
        """
        dao = ContentManagementDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test content
        content_id = str(uuid4())
        user_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(user_id), f'versionuser_{uuid4().hex[:8]}', f'version@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.content
               (id, title, content_type, body, created_by, course_id, status,
                version, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
            UUID(content_id), 'Versioned Content', 'lesson', 'Version 1 body',
            UUID(user_id), uuid4(), 'published', '1.0',
            datetime.utcnow(), datetime.utcnow()
        )

        # Execute: Create new version
        version_id = str(uuid4())
        version_data = {
            'id': version_id,
            'version_number': '2.0',
            'body': 'Version 2 body with improvements',
            'changed_by': user_id,
            'change_notes': 'Added more examples and clarifications'
        }

        result_id = await dao.create_content_version(content_id, version_data)

        # Verify: Version was created
        assert result_id == version_id

        # Verify: Version exists
        version = await db_transaction.fetchrow(
            """SELECT * FROM course_creator.content_versions WHERE id = $1""",
            UUID(version_id)
        )
        assert version is not None
        assert version['version_number'] == '2.0'

    @pytest.mark.asyncio
    async def test_get_content_version_history(self, db_transaction):
        """
        TEST: Retrieve complete version history for content

        BUSINESS REQUIREMENT:
        Users need to view all content changes over time
        """
        dao = ContentManagementDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test content
        content_id = str(uuid4())
        user_id = str(uuid4())

        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(user_id), f'historyuser_{uuid4().hex[:8]}', f'history@test.com',
            '$2b$12$test', 'instructor'
        )

        await db_transaction.execute(
            """INSERT INTO course_creator.content
               (id, title, content_type, body, created_by, course_id, status, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            UUID(content_id), 'History Content', 'lesson', 'Body', UUID(user_id),
            uuid4(), 'published', datetime.utcnow(), datetime.utcnow()
        )

        # Create multiple versions
        for i in range(3):
            await db_transaction.execute(
                """INSERT INTO course_creator.content_versions
                   (id, content_id, version_number, body, changed_by, change_notes, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                uuid4(), UUID(content_id), f'1.{i}', f'Version {i} body',
                UUID(user_id), f'Change notes {i}', datetime.utcnow()
            )

        # Execute: Get version history
        history = await dao.get_content_version_history(content_id)

        # Verify: All versions returned
        assert len(history) >= 3


class TestContentByType:
    """
    Test Suite: Content Type Filtering Operations

    BUSINESS REQUIREMENT:
    System must efficiently retrieve content filtered by type for
    content organization and curriculum building.
    """

    @pytest.mark.asyncio
    async def test_get_content_by_type_lessons(self, db_transaction):
        """
        TEST: Retrieve all content of specific type

        BUSINESS REQUIREMENT:
        Instructors need to find all lessons for course organization
        """
        dao = ContentManagementDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test user
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.users (id, username, email, password, role)
               VALUES ($1, $2, $3, $4, $5)""",
            UUID(user_id), f'typeuser_{uuid4().hex[:8]}', f'type@test.com',
            '$2b$12$test', 'instructor'
        )

        # Create content of different types
        types_created = []
        for content_type in ['lesson', 'quiz', 'lab', 'lesson']:
            content_id = str(uuid4())
            types_created.append((content_id, content_type))

            await db_transaction.execute(
                """INSERT INTO course_creator.content
                   (id, title, content_type, body, created_by, course_id, status, created_at, updated_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                UUID(content_id), f'Content {content_type}', content_type, 'Body',
                UUID(user_id), uuid4(), 'published', datetime.utcnow(), datetime.utcnow()
            )

        # Execute: Get lessons only
        lessons = await dao.get_content_by_type('lesson', created_by=user_id, limit=10)

        # Verify: Only lessons returned
        assert len(lessons) >= 2
        for content in lessons:
            assert content['content_type'] == 'lesson'
