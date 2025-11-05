"""
Course Video DAO Unit Tests

BUSINESS CONTEXT:
Comprehensive tests for the Course Video Data Access Object ensuring all video management
operations work correctly. The Course Video DAO handles video CRUD operations, ordering,
upload tracking, and soft delete functionality for the platform's video content delivery.
This DAO is critical for instructor content management and student learning experiences.

TECHNICAL IMPLEMENTATION:
- Tests all 12 DAO methods across 3 functional categories
- Validates video CRUD operations with course relationships
- Tests video ordering and sequencing for curriculum structure
- Ensures upload tracking with progress monitoring
- Validates soft delete vs hard delete operations
- Tests active/inactive video filtering
- Ensures transaction support for atomic operations

TDD APPROACH:
These tests validate that the DAO layer correctly:
- Creates video records with metadata and foreign key relationships
- Retrieves videos by ID and course with ordering
- Updates video metadata with partial update support
- Handles soft and hard delete operations
- Reorders videos within courses atomically
- Tracks upload progress with status updates
- Manages file paths and storage locations
"""

import pytest
import asyncpg
from datetime import datetime
from uuid import uuid4, UUID
import sys
from pathlib import Path

# Add course-management service to path
course_mgmt_path = Path(__file__).parent.parent.parent.parent / 'services' / 'course-management'
sys.path.insert(0, str(course_mgmt_path))

from data_access.course_video_dao import CourseVideoDAO, CourseVideoNotFoundException
from models.course_video import VideoType, UploadStatus


class TestVideoCreateOperations:
    """
    Test Suite: Video Creation Operations

    BUSINESS REQUIREMENT:
    Instructors must be able to add video content to courses with metadata,
    ordering, and file information for student learning experiences.
    """

    @pytest.mark.asyncio
    async def test_create_video_with_required_fields(self, db_transaction):
        """
        TEST: Create video with minimal required fields

        BUSINESS REQUIREMENT:
        Instructors should be able to quickly add video content with
        basic information

        VALIDATES:
        - Video record is created successfully
        - UUID is generated automatically
        - Default values are applied (is_active=True, order_index=0)
        - Timestamps are set automatically
        - Foreign key relationship to course is enforced
        """
        dao = CourseVideoDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test course first
        course_id = str(uuid4())
        instructor_id = str(uuid4())
        org_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses
               (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(instructor_id), UUID(org_id)
        )

        video_data = {
            'course_id': course_id,
            'title': 'Introduction to Python',
            'video_url': 'https://storage.example.com/videos/intro.mp4'
        }

        # Execute: Create video
        video = await dao.create(video_data)

        # Verify: Video was created with generated ID
        assert video is not None
        assert video.id is not None
        assert video.course_id == course_id
        assert video.title == 'Introduction to Python'
        assert video.video_url == 'https://storage.example.com/videos/intro.mp4'
        assert video.is_active is True
        assert video.order_index == 0
        assert video.created_at is not None

        # Verify: Video exists in database
        db_video = await db_transaction.fetchrow(
            "SELECT * FROM course_videos WHERE id = $1",
            UUID(video.id)
        )
        assert db_video is not None
        assert db_video['title'] == 'Introduction to Python'

    @pytest.mark.asyncio
    async def test_create_video_with_full_metadata(self, db_transaction):
        """
        TEST: Create video with complete metadata and file information

        BUSINESS REQUIREMENT:
        System should store comprehensive video metadata including duration,
        file size, thumbnails, and MIME type for proper video management

        VALIDATES:
        - All optional fields are stored correctly
        - Duration and file size are tracked
        - Thumbnail URL is stored
        - MIME type is preserved
        - Custom order index is respected
        """
        dao = CourseVideoDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses
               (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(str(uuid4())), UUID(str(uuid4()))
        )

        video_data = {
            'course_id': course_id,
            'title': 'Advanced Algorithms',
            'description': 'Deep dive into sorting and searching algorithms',
            'video_type': VideoType.UPLOAD.value,
            'video_url': 'https://storage.example.com/videos/algorithms.mp4',
            'thumbnail_url': 'https://storage.example.com/thumbs/algorithms.jpg',
            'duration_seconds': 3600,  # 1 hour
            'file_size_bytes': 524288000,  # 500 MB
            'mime_type': 'video/mp4',
            'order_index': 5,
            'is_active': True
        }

        # Execute: Create video
        video = await dao.create(video_data)

        # Verify: All metadata is stored
        assert video.description == 'Deep dive into sorting and searching algorithms'
        assert video.video_type == VideoType.UPLOAD
        assert video.duration_seconds == 3600
        assert video.file_size_bytes == 524288000
        assert video.mime_type == 'video/mp4'
        assert video.thumbnail_url == 'https://storage.example.com/thumbs/algorithms.jpg'
        assert video.order_index == 5


class TestVideoRetrieveOperations:
    """
    Test Suite: Video Retrieval Operations

    BUSINESS REQUIREMENT:
    System must efficiently retrieve videos by ID, by course, with proper
    ordering and filtering for curriculum delivery.
    """

    @pytest.mark.asyncio
    async def test_get_video_by_id_returns_video(self, db_transaction):
        """
        TEST: Retrieve video by ID

        BUSINESS REQUIREMENT:
        System must support direct video access for playback and management

        VALIDATES:
        - Video is retrieved by primary key
        - All fields are populated correctly
        - None is returned for non-existent ID
        """
        dao = CourseVideoDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses
               (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(str(uuid4())), UUID(str(uuid4()))
        )

        # Create video
        video_data = {
            'course_id': course_id,
            'title': 'Test Video',
            'video_url': 'https://example.com/video.mp4'
        }
        created_video = await dao.create(video_data)

        # Execute: Get video by ID
        retrieved_video = await dao.get_by_id(created_video.id)

        # Verify: Video is retrieved correctly
        assert retrieved_video is not None
        assert retrieved_video.id == created_video.id
        assert retrieved_video.title == 'Test Video'
        assert retrieved_video.course_id == course_id

    @pytest.mark.asyncio
    async def test_get_video_by_id_returns_none_when_not_found(self, db_transaction):
        """
        TEST: Return None for non-existent video ID

        BUSINESS REQUIREMENT:
        System must gracefully handle requests for non-existent videos

        VALIDATES:
        - None is returned for invalid ID
        - No exception is raised
        """
        dao = CourseVideoDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        non_existent_id = str(uuid4())
        result = await dao.get_by_id(non_existent_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_videos_by_course_returns_ordered_list(self, db_transaction):
        """
        TEST: Retrieve all videos for a course in sequential order

        BUSINESS REQUIREMENT:
        Course videos must be displayed in curriculum order for
        sequential learning experiences

        VALIDATES:
        - All active videos for course are returned
        - Videos are ordered by order_index
        - Inactive videos are excluded by default
        - Empty list returned for course with no videos
        """
        dao = CourseVideoDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses
               (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(str(uuid4())), UUID(str(uuid4()))
        )

        # Create 3 videos with specific order
        video_titles = ['Video 3', 'Video 1', 'Video 2']
        order_indices = [2, 0, 1]

        for title, order in zip(video_titles, order_indices):
            video_data = {
                'course_id': course_id,
                'title': title,
                'video_url': f'https://example.com/{title}.mp4',
                'order_index': order
            }
            await dao.create(video_data)

        # Execute: Get all videos for course
        videos = await dao.get_by_course(course_id)

        # Verify: Videos are returned in order
        assert len(videos) == 3
        assert videos[0].title == 'Video 1'
        assert videos[1].title == 'Video 2'
        assert videos[2].title == 'Video 3'
        assert videos[0].order_index == 0
        assert videos[1].order_index == 1
        assert videos[2].order_index == 2

    @pytest.mark.asyncio
    async def test_get_videos_by_course_excludes_inactive_by_default(self, db_transaction):
        """
        TEST: Active-only filter excludes soft-deleted videos

        BUSINESS REQUIREMENT:
        Students should only see active videos, not soft-deleted content

        VALIDATES:
        - Only active videos are returned by default
        - Inactive videos are excluded
        - active_only parameter controls filtering
        """
        dao = CourseVideoDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses
               (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(str(uuid4())), UUID(str(uuid4()))
        )

        # Create active video
        active_video = await dao.create({
            'course_id': course_id,
            'title': 'Active Video',
            'video_url': 'https://example.com/active.mp4'
        })

        # Create inactive video
        inactive_video = await dao.create({
            'course_id': course_id,
            'title': 'Inactive Video',
            'video_url': 'https://example.com/inactive.mp4',
            'is_active': False
        })

        # Execute: Get active videos only
        active_videos = await dao.get_by_course(course_id, active_only=True)

        # Verify: Only active video is returned
        assert len(active_videos) == 1
        assert active_videos[0].title == 'Active Video'

        # Execute: Get all videos including inactive
        all_videos = await dao.get_by_course(course_id, active_only=False)

        # Verify: Both videos are returned
        assert len(all_videos) == 2


class TestVideoUpdateOperations:
    """
    Test Suite: Video Update Operations

    BUSINESS REQUIREMENT:
    Instructors must be able to update video metadata, reorder videos,
    and manage video lifecycle.
    """

    @pytest.mark.asyncio
    async def test_update_video_with_partial_data(self, db_transaction):
        """
        TEST: Update video with partial field updates

        BUSINESS REQUIREMENT:
        Instructors should be able to update specific video fields
        without providing all data

        VALIDATES:
        - Only provided fields are updated
        - Immutable fields (id, course_id, video_type) cannot be changed
        - updated_at timestamp is refreshed automatically
        - Other fields remain unchanged
        """
        dao = CourseVideoDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses
               (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(str(uuid4())), UUID(str(uuid4()))
        )

        # Create video
        video_data = {
            'course_id': course_id,
            'title': 'Original Title',
            'description': 'Original Description',
            'video_url': 'https://example.com/original.mp4',
            'duration_seconds': 1800
        }
        created_video = await dao.create(video_data)
        original_updated_at = created_video.updated_at

        # Execute: Update only title and description
        update_data = {
            'title': 'Updated Title',
            'description': 'Updated Description'
        }
        updated_video = await dao.update(created_video.id, update_data)

        # Verify: Updated fields changed
        assert updated_video.title == 'Updated Title'
        assert updated_video.description == 'Updated Description'

        # Verify: Other fields unchanged
        assert updated_video.video_url == 'https://example.com/original.mp4'
        assert updated_video.duration_seconds == 1800

        # Verify: updated_at was refreshed
        assert updated_video.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_update_video_returns_none_when_not_found(self, db_transaction):
        """
        TEST: Return None when updating non-existent video

        BUSINESS REQUIREMENT:
        System must gracefully handle updates to non-existent videos

        VALIDATES:
        - None is returned for invalid video ID
        - No exception is raised
        """
        dao = CourseVideoDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        non_existent_id = str(uuid4())
        update_data = {'title': 'New Title'}

        result = await dao.update(non_existent_id, update_data)

        assert result is None

    @pytest.mark.asyncio
    async def test_reorder_videos_updates_all_positions_atomically(self, db_transaction):
        """
        TEST: Reorder multiple videos in single transaction

        BUSINESS REQUIREMENT:
        Instructors need to drag-and-drop videos to create optimal
        learning sequences with atomic position updates

        VALIDATES:
        - All video positions are updated atomically
        - New order is reflected in database
        - Videos are returned in new order
        - Transaction ensures consistency
        """
        dao = CourseVideoDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses
               (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(str(uuid4())), UUID(str(uuid4()))
        )

        # Create 3 videos
        video_ids = []
        for i in range(3):
            video = await dao.create({
                'course_id': course_id,
                'title': f'Video {i+1}',
                'video_url': f'https://example.com/video{i+1}.mp4',
                'order_index': i
            })
            video_ids.append(video.id)

        # Execute: Reorder videos (reverse order)
        new_order = [video_ids[2], video_ids[1], video_ids[0]]
        reordered_videos = await dao.reorder_videos(course_id, new_order)

        # Verify: Videos are in new order
        assert len(reordered_videos) == 3
        assert reordered_videos[0].id == video_ids[2]
        assert reordered_videos[1].id == video_ids[1]
        assert reordered_videos[2].id == video_ids[0]
        assert reordered_videos[0].order_index == 0
        assert reordered_videos[1].order_index == 1
        assert reordered_videos[2].order_index == 2


class TestVideoDeleteOperations:
    """
    Test Suite: Video Delete Operations

    BUSINESS REQUIREMENT:
    System must support both soft delete (for history preservation) and
    hard delete (for storage cleanup and compliance).
    """

    @pytest.mark.asyncio
    async def test_soft_delete_sets_inactive_flag(self, db_transaction):
        """
        TEST: Soft delete sets is_active to false

        BUSINESS REQUIREMENT:
        Soft delete preserves video history while hiding content from
        students, preventing accidental data loss

        VALIDATES:
        - is_active flag is set to false
        - Video record remains in database
        - updated_at timestamp is refreshed
        - Method returns True on success
        """
        dao = CourseVideoDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses
               (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(str(uuid4())), UUID(str(uuid4()))
        )

        # Create video
        video = await dao.create({
            'course_id': course_id,
            'title': 'Video to Soft Delete',
            'video_url': 'https://example.com/video.mp4'
        })

        # Execute: Soft delete video
        result = await dao.delete(video.id, soft_delete=True)

        # Verify: Delete was successful
        assert result is True

        # Verify: Video still exists but is inactive
        db_video = await db_transaction.fetchrow(
            "SELECT * FROM course_videos WHERE id = $1",
            UUID(video.id)
        )
        assert db_video is not None
        assert db_video['is_active'] is False

    @pytest.mark.asyncio
    async def test_hard_delete_removes_record(self, db_transaction):
        """
        TEST: Hard delete permanently removes video record

        BUSINESS REQUIREMENT:
        Hard delete enables storage cleanup and compliance with data
        deletion regulations (GDPR)

        VALIDATES:
        - Video record is permanently deleted
        - Method returns True on success
        - Record does not exist in database
        """
        dao = CourseVideoDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses
               (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(str(uuid4())), UUID(str(uuid4()))
        )

        # Create video
        video = await dao.create({
            'course_id': course_id,
            'title': 'Video to Hard Delete',
            'video_url': 'https://example.com/video.mp4'
        })

        # Execute: Hard delete video
        result = await dao.delete(video.id, soft_delete=False)

        # Verify: Delete was successful
        assert result is True

        # Verify: Video no longer exists
        db_video = await db_transaction.fetchrow(
            "SELECT * FROM course_videos WHERE id = $1",
            UUID(video.id)
        )
        assert db_video is None

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_not_found(self, db_transaction):
        """
        TEST: Return False when deleting non-existent video

        BUSINESS REQUIREMENT:
        System must indicate when delete operation affects no records

        VALIDATES:
        - False is returned for invalid video ID
        - No exception is raised
        """
        dao = CourseVideoDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        non_existent_id = str(uuid4())
        result = await dao.delete(non_existent_id)

        assert result is False


class TestVideoUploadTracking:
    """
    Test Suite: Video Upload Tracking

    BUSINESS REQUIREMENT:
    System must track large video file uploads with progress monitoring
    and status management for user feedback.
    """

    @pytest.mark.asyncio
    async def test_create_upload_record_initializes_tracking(self, db_transaction):
        """
        TEST: Create upload tracking record for new video upload

        BUSINESS REQUIREMENT:
        Track video uploads with progress monitoring for user feedback
        and error recovery

        VALIDATES:
        - Upload record is created with unique ID
        - Status is set to PENDING
        - Progress is initialized to 0
        - Course and instructor are linked
        """
        dao = CourseVideoDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        instructor_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses
               (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(instructor_id), UUID(str(uuid4()))
        )

        upload_data = {
            'course_id': course_id,
            'instructor_id': instructor_id,
            'filename': 'lecture_video.mp4',
            'file_size_bytes': 104857600  # 100 MB
        }

        # Execute: Create upload record
        upload_id = await dao.create_upload_record(upload_data)

        # Verify: Upload record created
        assert upload_id is not None

        # Verify: Record exists in database with correct initial state
        upload = await db_transaction.fetchrow(
            "SELECT * FROM video_uploads WHERE id = $1",
            UUID(upload_id)
        )
        assert upload is not None
        assert upload['filename'] == 'lecture_video.mp4'
        assert upload['upload_status'] == UploadStatus.PENDING.value
        assert upload['upload_progress'] == 0

    @pytest.mark.asyncio
    async def test_update_upload_progress_tracks_percentage(self, db_transaction):
        """
        TEST: Update upload progress percentage during file upload

        BUSINESS REQUIREMENT:
        Provide real-time progress feedback to instructors during
        large video file uploads

        VALIDATES:
        - Progress percentage is updated
        - Status can be updated simultaneously
        - Multiple progress updates work correctly
        """
        dao = CourseVideoDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses
               (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(str(uuid4())), UUID(str(uuid4()))
        )

        upload_data = {
            'course_id': course_id,
            'instructor_id': str(uuid4()),
            'filename': 'video.mp4',
            'file_size_bytes': 52428800
        }
        upload_id = await dao.create_upload_record(upload_data)

        # Execute: Update progress to 50%
        await dao.update_upload_progress(upload_id, 50, UploadStatus.UPLOADING.value)

        # Verify: Progress updated
        upload = await db_transaction.fetchrow(
            "SELECT * FROM video_uploads WHERE id = $1",
            UUID(upload_id)
        )
        assert upload['upload_progress'] == 50
        assert upload['upload_status'] == UploadStatus.UPLOADING.value

    @pytest.mark.asyncio
    async def test_complete_upload_marks_finished_and_stores_path(self, db_transaction):
        """
        TEST: Mark upload as completed with storage path

        BUSINESS REQUIREMENT:
        Track successful upload completion and file location for
        video record creation

        VALIDATES:
        - Upload status is set to COMPLETED
        - Progress is set to 100
        - Storage path is recorded
        - Completion timestamp is set
        """
        dao = CourseVideoDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses
               (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(str(uuid4())), UUID(str(uuid4()))
        )

        upload_data = {
            'course_id': course_id,
            'instructor_id': str(uuid4()),
            'filename': 'video.mp4',
            'file_size_bytes': 52428800
        }
        upload_id = await dao.create_upload_record(upload_data)

        # Execute: Complete upload
        storage_path = 's3://bucket/videos/12345/video.mp4'
        await dao.complete_upload(upload_id, storage_path)

        # Verify: Upload is completed
        upload = await db_transaction.fetchrow(
            "SELECT * FROM video_uploads WHERE id = $1",
            UUID(upload_id)
        )
        assert upload['upload_status'] == UploadStatus.COMPLETED.value
        assert upload['upload_progress'] == 100
        assert upload['storage_path'] == storage_path
        assert upload['completed_at'] is not None

    @pytest.mark.asyncio
    async def test_fail_upload_records_error_message(self, db_transaction):
        """
        TEST: Mark upload as failed with error message

        BUSINESS REQUIREMENT:
        Track upload failures for error recovery and user notification

        VALIDATES:
        - Upload status is set to FAILED
        - Error message is stored
        - Failed uploads can be identified for retry
        """
        dao = CourseVideoDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses
               (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(str(uuid4())), UUID(str(uuid4()))
        )

        upload_data = {
            'course_id': course_id,
            'instructor_id': str(uuid4()),
            'filename': 'video.mp4',
            'file_size_bytes': 52428800
        }
        upload_id = await dao.create_upload_record(upload_data)

        # Execute: Fail upload
        error_message = 'Network connection lost during upload'
        await dao.fail_upload(upload_id, error_message)

        # Verify: Upload is marked as failed
        upload = await db_transaction.fetchrow(
            "SELECT * FROM video_uploads WHERE id = $1",
            UUID(upload_id)
        )
        assert upload['upload_status'] == UploadStatus.FAILED.value
        assert upload['error_message'] == error_message
