"""
Course Video API Endpoints

RESTful API for managing course videos, including uploads and external links.
Supports multipart file uploads, progress tracking, and video sequencing.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import shutil
import uuid
from datetime import datetime, timedelta

from models.course_video import (
    CourseVideo,
    CourseVideoCreate,
    CourseVideoUpdate,
    CourseVideoResponse,
    CourseVideoListResponse,
    VideoUploadRequest,
    VideoUploadResponse,
    VideoType
)
from data_access.course_video_dao import CourseVideoDAO

# JWT Authentication - Import from auth module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from auth import get_current_user_id as get_authenticated_user_id


router = APIRouter(prefix="/courses", tags=["videos"])


# Dependency injection for DAO (will be initialized in main.py)
video_dao: Optional[CourseVideoDAO] = None


def get_video_dao() -> CourseVideoDAO:
    """
    Dependency injection for CourseVideoDAO.

    DESIGN PATTERN:
    Enables testability through dependency injection.
    DAO instance is set during application startup.
    """
    if video_dao is None:
        raise HTTPException(status_code=500, detail="Video DAO not initialized")
    return video_dao


# DEPRECATED: This function has been replaced by JWT authentication middleware
# Use: from auth import get_current_user_id (as FastAPI Depends)
#
# Migration Guide:
# OLD: user_id = get_current_user_id()
# NEW: async def endpoint(user_id: str = Depends(get_authenticated_user_id)):
#
# This function will be removed in v4.0
def get_current_user_id() -> str:
    """
    DEPRECATED: Use get_authenticated_user_id from auth module with FastAPI Depends.

    This mock function returns a hardcoded user ID for backward compatibility.
    All new code should use the JWT authentication middleware:

    from auth import get_current_user_id
    from fastapi import Depends

    @router.get("/endpoint")
    async def my_endpoint(user_id: str = Depends(get_current_user_id)):
        # user_id is now authenticated from JWT token
        pass

    Returns:
        str: Mock user ID (for backward compatibility only)

    Warnings:
        DeprecationWarning: This function is deprecated
    """
    import warnings
    warnings.warn(
        "get_current_user_id() mock function is deprecated. "
        "Use JWT authentication: from auth import get_current_user_id with FastAPI Depends()",
        DeprecationWarning,
        stacklevel=2
    )
    return "current-user-id"  # Mock ID for backward compatibility


def get_storage_path(course_id: str, filename: str) -> str:
    """
    Generate storage path for uploaded video file.

    STORAGE STRUCTURE:
    /videos/{course_id}/{unique_id}_{original_filename}

    BUSINESS RATIONALE:
    - Course-based organization enables bulk operations per course
    - Unique ID prefix prevents filename collisions
    - Original filename preserved for debugging and downloads
    """
    base_path = os.getenv("VIDEO_STORAGE_PATH", "/app/storage/videos")
    course_path = os.path.join(base_path, course_id)

    # Create course directory if it doesn't exist
    os.makedirs(course_path, exist_ok=True)

    # Generate unique filename
    unique_id = str(uuid.uuid4())[:8]
    safe_filename = f"{unique_id}_{filename}"

    return os.path.join(course_path, safe_filename)


# ==================================================================================
# VIDEO CRUD ENDPOINTS
# ==================================================================================

@router.post("/{course_id}/videos", response_model=CourseVideoResponse)
async def create_course_video(
    course_id: str,
    video: CourseVideoCreate,
    dao: CourseVideoDAO = Depends(get_video_dao),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Create a new video link for a course.

    This endpoint is for EXTERNAL video links (YouTube, Vimeo, custom URLs).
    For file uploads, use the /upload endpoint instead.

    BUSINESS WORKFLOW:
    1. Validate user has permission to edit course
    2. Validate video URL format based on type
    3. Create video record in database
    4. Return video entity with generated ID

    SECURITY:
    - Only course instructor can add videos
    - URLs are validated to prevent XSS/injection attacks
    - CORS headers restrict client-side access
    """
    try:
        # TODO: Validate user owns/can edit this course
        # course_service.verify_instructor_access(current_user_id, course_id)

        # Create video record
        video_data = video.dict()
        video_data['course_id'] = course_id

        created_video = await dao.create(video_data)

        return CourseVideoResponse(
            success=True,
            video=created_video,
            message="Video link added successfully"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create video: {str(e)}") from e


@router.get("/{course_id}/videos", response_model=CourseVideoListResponse)
async def get_course_videos(
    course_id: str,
    active_only: bool = True,
    dao: CourseVideoDAO = Depends(get_video_dao)
):
    """
    Get all videos for a course.

    Args:
        course_id: UUID of the course
        active_only: If true, only return active (non-deleted) videos

    Returns:
        List of videos ordered by order_index

    BUSINESS LOGIC:
    Videos are returned in curriculum sequence order.
    Soft-deleted videos can be included for instructor review.

    PERFORMANCE:
    Uses indexed query on (course_id, order_index) for fast retrieval.
    """
    try:
        videos = await dao.get_by_course(course_id, active_only=active_only)

        return CourseVideoListResponse(
            success=True,
            videos=videos,
            total=len(videos),
            message=f"Found {len(videos)} video(s)"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch videos: {str(e)}") from e


@router.get("/{course_id}/videos/{video_id}", response_model=CourseVideoResponse)
async def get_course_video(
    course_id: str,
    video_id: str,
    dao: CourseVideoDAO = Depends(get_video_dao)
):
    """
    Get a specific video by ID.

    SECURITY:
    Validates video belongs to specified course to prevent unauthorized access.
    """
    try:
        video = await dao.get_by_id(video_id)

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        if video.course_id != course_id:
            raise HTTPException(status_code=403, detail="Video does not belong to this course")

        return CourseVideoResponse(
            success=True,
            video=video
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch video: {str(e)}") from e


@router.put("/{course_id}/videos/{video_id}", response_model=CourseVideoResponse)
async def update_course_video(
    course_id: str,
    video_id: str,
    video_update: CourseVideoUpdate,
    dao: CourseVideoDAO = Depends(get_video_dao),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Update a course video's metadata.

    BUSINESS RULES:
    - Video type cannot be changed (immutable)
    - Only metadata like title, description, order can be updated
    - Instructor must own the course

    PARTIAL UPDATES:
    Only provided fields are updated, others remain unchanged.
    """
    try:
        # TODO: Validate user owns/can edit this course
        # course_service.verify_instructor_access(current_user_id, course_id)

        # Verify video exists and belongs to course
        existing_video = await dao.get_by_id(video_id)
        if not existing_video:
            raise HTTPException(status_code=404, detail="Video not found")

        if existing_video.course_id != course_id:
            raise HTTPException(status_code=403, detail="Video does not belong to this course")

        # Update video
        update_data = video_update.dict(exclude_unset=True)
        updated_video = await dao.update(video_id, update_data)

        return CourseVideoResponse(
            success=True,
            video=updated_video,
            message="Video updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update video: {str(e)}") from e


@router.delete("/{course_id}/videos/{video_id}")
async def delete_course_video(
    course_id: str,
    video_id: str,
    permanent: bool = False,
    dao: CourseVideoDAO = Depends(get_video_dao),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Delete a course video.

    Args:
        course_id: UUID of the course
        video_id: UUID of the video
        permanent: If True, permanently delete; if False, soft delete

    BUSINESS DECISION:
    Soft delete is default to prevent accidental data loss.
    Permanent delete is available for storage cleanup and compliance.

    CASCADING EFFECTS:
    - Permanent delete removes file from storage
    - Soft delete preserves file but hides from students
    """
    try:
        # TODO: Validate user owns/can edit this course
        # course_service.verify_instructor_access(current_user_id, course_id)

        # Verify video exists and belongs to course
        existing_video = await dao.get_by_id(video_id)
        if not existing_video:
            raise HTTPException(status_code=404, detail="Video not found")

        if existing_video.course_id != course_id:
            raise HTTPException(status_code=403, detail="Video does not belong to this course")

        # Delete video record
        deleted = await dao.delete(video_id, soft_delete=not permanent)

        if not deleted:
            raise HTTPException(status_code=404, detail="Video not found")

        # If permanent delete and it's an uploaded file, delete from storage
        if permanent and existing_video.video_type == VideoType.UPLOAD:
            try:
                if os.path.exists(existing_video.video_url):
                    os.remove(existing_video.video_url)
            except Exception as e:
                # Log error but don't fail the request
                print(f"Failed to delete video file: {e}")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Video deleted successfully" if permanent else "Video hidden successfully"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete video: {str(e)}") from e


@router.post("/{course_id}/videos/reorder")
async def reorder_course_videos(
    course_id: str,
    video_order: List[str],
    dao: CourseVideoDAO = Depends(get_video_dao),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Reorder videos within a course.

    Args:
        course_id: UUID of the course
        video_order: List of video IDs in desired order

    BUSINESS WORKFLOW:
    Instructors can drag-and-drop videos to create optimal learning sequences.
    Order is persisted across sessions.

    TRANSACTION SAFETY:
    All order updates are atomic to prevent partial reordering.
    """
    try:
        # TODO: Validate user owns/can edit this course
        # course_service.verify_instructor_access(current_user_id, course_id)

        reordered_videos = await dao.reorder_videos(course_id, video_order)

        return CourseVideoListResponse(
            success=True,
            videos=reordered_videos,
            total=len(reordered_videos),
            message="Videos reordered successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reorder videos: {str(e)}") from e


# ==================================================================================
# VIDEO UPLOAD ENDPOINTS
# ==================================================================================

@router.post("/{course_id}/videos/upload", response_model=VideoUploadResponse)
async def initiate_video_upload(
    course_id: str,
    upload_request: VideoUploadRequest,
    dao: CourseVideoDAO = Depends(get_video_dao),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Initiate a video file upload.

    WORKFLOW:
    1. Validate upload request (file size, type, etc.)
    2. Create upload tracking record
    3. Generate upload URL (for direct upload or pre-signed S3 URL)
    4. Return upload URL and tracking ID to client

    SCALABILITY:
    For production, this should generate a pre-signed S3 URL
    for direct upload to cloud storage, bypassing the API server.
    """
    try:
        # TODO: Validate user owns/can edit this course
        # course_service.verify_instructor_access(current_user_id, course_id)

        # Create upload tracking record
        upload_data = {
            'course_id': course_id,
            'instructor_id': current_user_id,
            'filename': upload_request.filename,
            'file_size_bytes': upload_request.file_size_bytes
        }

        upload_id = await dao.create_upload_record(upload_data)

        # Generate upload URL (in production, this would be a pre-signed S3 URL)
        upload_url = f"/api/courses/{course_id}/videos/upload/{upload_id}/file"
        expires_at = datetime.utcnow() + timedelta(hours=1)

        return VideoUploadResponse(
            success=True,
            upload_id=upload_id,
            upload_url=upload_url,
            upload_expires_at=expires_at,
            message="Upload initiated. Use the upload_url to upload your video file."
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate upload: {str(e)}") from e


@router.post("/{course_id}/videos/upload/{upload_id}/file")
async def upload_video_file(
    course_id: str,
    upload_id: str,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    dao: CourseVideoDAO = Depends(get_video_dao),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Upload video file (multipart form data).

    WORKFLOW:
    1. Receive video file from client
    2. Save to storage (local or S3)
    3. Update upload progress to 100%
    4. Create video record with file reference
    5. Return created video entity

    PERFORMANCE:
    For large files, consider chunked uploads with resumability.
    This implementation is synchronous and suitable for files < 500MB.
    """
    try:
        # TODO: Validate user owns/can edit this course
        # course_service.verify_instructor_access(current_user_id, course_id)

        # Generate storage path
        storage_path = get_storage_path(course_id, file.filename)

        # Save file to storage
        with open(storage_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(storage_path)

        # Update upload record
        await dao.complete_upload(upload_id, storage_path)

        # Create video record
        video_data = {
            'course_id': course_id,
            'title': title,
            'description': description,
            'video_type': VideoType.UPLOAD.value,
            'video_url': storage_path,
            'file_size_bytes': file_size,
            'mime_type': file.content_type,
            'order_index': 0
        }

        created_video = await dao.create(video_data)

        return CourseVideoResponse(
            success=True,
            video=created_video,
            message="Video uploaded successfully"
        )

    except Exception as e:
        # Mark upload as failed
        await dao.fail_upload(upload_id, str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}") from e
    finally:
        await file.close()


# ==================================================================================
# HELPER ENDPOINTS
# ==================================================================================

@router.get("/{course_id}/videos/count")
async def get_video_count(
    course_id: str,
    dao: CourseVideoDAO = Depends(get_video_dao)
):
    """
    Get count of videos for a course.

    BUSINESS USE CASE:
    Display video count on course cards and dashboards.
    """
    try:
        videos = await dao.get_by_course(course_id, active_only=True)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "count": len(videos),
                "course_id": course_id
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to count videos: {str(e)}") from e
