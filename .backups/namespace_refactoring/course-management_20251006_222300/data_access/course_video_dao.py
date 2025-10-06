"""
Course Video Data Access Object

Handles database operations for course videos with PostgreSQL.
Implements repository pattern for video entity persistence.
"""

import asyncpg
from typing import List, Optional
from datetime import datetime
import uuid

from models.course_video import CourseVideo, VideoType, UploadStatus


class CourseVideoNotFoundException(Exception):
    """
    Raised when a requested course video is not found.

    BUSINESS IMPACT: Prevents operations on non-existent videos
    """
    pass


class CourseVideoDAO:
    """
    Data Access Object for Course Video operations.

    RESPONSIBILITIES:
    - CRUD operations for course videos
    - Video ordering and sequencing
    - Upload progress tracking
    - Soft delete support via is_active flag

    TECHNICAL DESIGN:
    - Uses async/await for non-blocking database operations
    - Implements connection pooling for performance
    - Supports transactions for data consistency
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize DAO with database connection pool.

        Args:
            db_pool: Async PostgreSQL connection pool

        PERFORMANCE:
        Connection pooling enables efficient handling of concurrent requests
        without creating new connections for each operation
        """
        self.db_pool = db_pool

    async def create(self, video_data: dict) -> CourseVideo:
        """
        Create a new course video record.

        Args:
            video_data: Dictionary containing video fields

        Returns:
            Newly created CourseVideo entity

        BUSINESS WORKFLOW:
        1. Generate unique ID for new video
        2. Set creation and update timestamps
        3. Insert video record with foreign key to course
        4. Return complete video entity for client response

        DATABASE INTEGRITY:
        - Foreign key constraint ensures course exists
        - Cascading delete removes videos when course is deleted
        """
        video_id = str(uuid.uuid4())
        now = datetime.utcnow()

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO course_videos (
                    id, course_id, title, description, video_type,
                    video_url, thumbnail_url, duration_seconds,
                    file_size_bytes, mime_type, order_index,
                    is_active, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING *
                """,
                video_id,
                video_data.get('course_id'),
                video_data.get('title'),
                video_data.get('description'),
                video_data.get('video_type', VideoType.UPLOAD.value),
                video_data.get('video_url'),
                video_data.get('thumbnail_url'),
                video_data.get('duration_seconds'),
                video_data.get('file_size_bytes'),
                video_data.get('mime_type'),
                video_data.get('order_index', 0),
                video_data.get('is_active', True),
                now,
                now
            )

            return self._row_to_video(row)

    async def get_by_id(self, video_id: str) -> Optional[CourseVideo]:
        """
        Retrieve a course video by ID.

        Args:
            video_id: UUID of the video

        Returns:
            CourseVideo if found, None otherwise

        PERFORMANCE:
        Primary key lookup provides O(1) retrieval via index
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM course_videos
                WHERE id = $1
                """,
                video_id
            )

            return self._row_to_video(row) if row else None

    async def get_by_course(self, course_id: str, active_only: bool = True) -> List[CourseVideo]:
        """
        Get all videos for a specific course.

        Args:
            course_id: UUID of the course
            active_only: If True, only return active videos

        Returns:
            List of CourseVideo entities ordered by order_index

        BUSINESS LOGIC:
        - Videos are returned in sequential order for course curriculum
        - Soft-deleted videos can be excluded via active_only flag
        - Empty list returned if course has no videos

        PERFORMANCE:
        Compound index on (course_id, order_index) enables efficient ordered retrieval
        """
        async with self.db_pool.acquire() as conn:
            if active_only:
                rows = await conn.fetch(
                    """
                    SELECT * FROM course_videos
                    WHERE course_id = $1 AND is_active = true
                    ORDER BY order_index ASC, created_at ASC
                    """,
                    course_id
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM course_videos
                    WHERE course_id = $1
                    ORDER BY order_index ASC, created_at ASC
                    """,
                    course_id
                )

            return [self._row_to_video(row) for row in rows]

    async def update(self, video_id: str, update_data: dict) -> Optional[CourseVideo]:
        """
        Update an existing course video.

        Args:
            video_id: UUID of the video to update
            update_data: Dictionary of fields to update

        Returns:
            Updated CourseVideo if found, None otherwise

        BUSINESS RULES:
        - Only provided fields are updated (partial update support)
        - updated_at timestamp is automatically refreshed
        - video_type and course_id are immutable (cannot be changed)

        TECHNICAL IMPLEMENTATION:
        Dynamic SQL generation based on provided fields
        """
        if not update_data:
            return await self.get_by_id(video_id)

        # Build dynamic UPDATE query
        set_clauses = []
        values = []
        param_counter = 1

        for key, value in update_data.items():
            if key not in ['id', 'course_id', 'video_type', 'created_at']:  # Immutable fields
                set_clauses.append(f"{key} = ${param_counter}")
                values.append(value)
                param_counter += 1

        # Add updated_at timestamp
        set_clauses.append(f"updated_at = ${param_counter}")
        values.append(datetime.utcnow())
        param_counter += 1

        # Add video_id for WHERE clause
        values.append(video_id)

        query = f"""
            UPDATE course_videos
            SET {', '.join(set_clauses)}
            WHERE id = ${param_counter}
            RETURNING *
        """

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)
            return self._row_to_video(row) if row else None

    async def delete(self, video_id: str, soft_delete: bool = True) -> bool:
        """
        Delete a course video.

        Args:
            video_id: UUID of the video to delete
            soft_delete: If True, set is_active=False; if False, permanently delete

        Returns:
            True if deleted, False if not found

        BUSINESS DECISION:
        Soft delete is default to preserve video history and prevent accidental data loss.
        Hard delete is available for compliance (GDPR) or storage cleanup.

        CASCADING EFFECTS:
        - Hard delete removes video file from storage (handled by service layer)
        - Soft delete preserves file but hides video from students
        """
        async with self.db_pool.acquire() as conn:
            if soft_delete:
                result = await conn.execute(
                    """
                    UPDATE course_videos
                    SET is_active = false, updated_at = $2
                    WHERE id = $1
                    """,
                    video_id,
                    datetime.utcnow()
                )
            else:
                result = await conn.execute(
                    """
                    DELETE FROM course_videos
                    WHERE id = $1
                    """,
                    video_id
                )

            # PostgreSQL execute returns "DELETE N" or "UPDATE N" where N is row count
            return int(result.split()[-1]) > 0

    async def reorder_videos(self, course_id: str, video_order: List[str]) -> List[CourseVideo]:
        """
        Reorder videos within a course.

        Args:
            course_id: UUID of the course
            video_order: List of video IDs in desired order

        Returns:
            List of reordered CourseVideo entities

        BUSINESS WORKFLOW:
        Instructors can drag-and-drop videos to create optimal learning sequences.
        Order is persisted to maintain curriculum structure.

        TECHNICAL IMPLEMENTATION:
        Uses transaction to ensure atomic update of all video positions.
        """
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Update each video's order_index
                for index, video_id in enumerate(video_order):
                    await conn.execute(
                        """
                        UPDATE course_videos
                        SET order_index = $1, updated_at = $2
                        WHERE id = $3 AND course_id = $4
                        """,
                        index,
                        datetime.utcnow(),
                        video_id,
                        course_id
                    )

                # Return updated videos in new order
                return await self.get_by_course(course_id)

    def _row_to_video(self, row: asyncpg.Record) -> CourseVideo:
        """
        Convert database row to CourseVideo entity.

        Args:
            row: Database row from asyncpg query

        Returns:
            CourseVideo domain entity

        TECHNICAL MAPPING:
        - Converts PostgreSQL types to Python types
        - Handles enum conversion for video_type
        - Preserves all metadata for client serialization
        """
        if not row:
            return None

        return CourseVideo(
            id=str(row['id']),
            course_id=str(row['course_id']),
            title=row['title'],
            description=row['description'],
            video_type=VideoType(row['video_type']),
            video_url=row['video_url'],
            thumbnail_url=row['thumbnail_url'],
            duration_seconds=row['duration_seconds'],
            file_size_bytes=row['file_size_bytes'],
            mime_type=row['mime_type'],
            order_index=row['order_index'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    # ==================================================================================
    # VIDEO UPLOAD TRACKING METHODS
    # ==================================================================================

    async def create_upload_record(self, upload_data: dict) -> str:
        """
        Create upload tracking record for large video file.

        Args:
            upload_data: Upload metadata (course_id, instructor_id, filename, etc.)

        Returns:
            Upload ID for progress tracking

        BUSINESS WORKFLOW:
        1. Create upload record in PENDING status
        2. Generate signed upload URL (handled by service layer)
        3. Client uploads file with progress updates
        4. Record is updated to COMPLETED when finished
        """
        upload_id = str(uuid.uuid4())
        now = datetime.utcnow()

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO video_uploads (
                    id, course_id, instructor_id, filename,
                    file_size_bytes, upload_status, upload_progress,
                    created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                upload_id,
                upload_data.get('course_id'),
                upload_data.get('instructor_id'),
                upload_data.get('filename'),
                upload_data.get('file_size_bytes'),
                UploadStatus.PENDING.value,
                0,
                now
            )

        return upload_id

    async def update_upload_progress(self, upload_id: str, progress: int, status: Optional[str] = None):
        """
        Update upload progress percentage.

        Args:
            upload_id: UUID of upload record
            progress: Progress percentage (0-100)
            status: Optional status update

        REAL-TIME FEEDBACK:
        Enables progress bars and status updates in client UI
        """
        async with self.db_pool.acquire() as conn:
            if status:
                await conn.execute(
                    """
                    UPDATE video_uploads
                    SET upload_progress = $1, upload_status = $2
                    WHERE id = $3
                    """,
                    progress,
                    status,
                    upload_id
                )
            else:
                await conn.execute(
                    """
                    UPDATE video_uploads
                    SET upload_progress = $1
                    WHERE id = $2
                    """,
                    progress,
                    upload_id
                )

    async def complete_upload(self, upload_id: str, storage_path: str):
        """
        Mark upload as completed.

        Args:
            upload_id: UUID of upload record
            storage_path: Final storage location of uploaded file

        POST-PROCESSING:
        After upload completes:
        1. Mark record as COMPLETED
        2. Store file path for video record creation
        3. Trigger optional post-processing (transcoding, thumbnails)
        """
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE video_uploads
                SET upload_status = $1, upload_progress = 100,
                    storage_path = $2, completed_at = $3
                WHERE id = $4
                """,
                UploadStatus.COMPLETED.value,
                storage_path,
                datetime.utcnow(),
                upload_id
            )

    async def fail_upload(self, upload_id: str, error_message: str):
        """
        Mark upload as failed with error message.

        Args:
            upload_id: UUID of upload record
            error_message: Reason for failure

        ERROR HANDLING:
        Failed uploads can be retried or cleaned up based on business policy
        """
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE video_uploads
                SET upload_status = $1, error_message = $2
                WHERE id = $3
                """,
                UploadStatus.FAILED.value,
                error_message,
                upload_id
            )
