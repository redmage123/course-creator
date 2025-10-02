"""
Course Video Models

Pydantic models for course video data validation and serialization.
Supports both uploaded video files and external video links (YouTube, Vimeo, etc.)
"""

from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum


class VideoType(str, Enum):
    """
    Video type enumeration.

    Supports different video sources:
    - UPLOAD: Video file uploaded to platform storage (local or S3)
    - LINK: Generic external video link
    - YOUTUBE: YouTube video URL
    - VIMEO: Vimeo video URL
    """
    UPLOAD = "upload"
    LINK = "link"
    YOUTUBE = "youtube"
    VIMEO = "vimeo"


class UploadStatus(str, Enum):
    """
    Video upload status tracking.

    Lifecycle states for video upload process:
    - PENDING: Upload queued but not started
    - UPLOADING: File transfer in progress
    - PROCESSING: Post-upload processing (transcoding, thumbnail generation)
    - COMPLETED: Upload and processing complete
    - FAILED: Upload or processing failed
    """
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CourseVideoBase(BaseModel):
    """
    Base course video model with common fields.

    BUSINESS CONTEXT:
    Videos are a critical component of modern educational content delivery.
    This model supports both self-hosted videos and external platform links
    to provide flexibility in content delivery strategies.

    TECHNICAL CONSIDERATIONS:
    - Title is required for accessibility and course organization
    - Description provides context for search and student understanding
    - Order index enables structured video sequences in course curriculum
    - Video type determines storage and playback strategy
    """
    title: str = Field(..., min_length=1, max_length=255, description="Video title")
    description: Optional[str] = Field(None, max_length=2000, description="Video description")
    video_type: VideoType = Field(default=VideoType.UPLOAD, description="Type of video source")
    video_url: str = Field(..., description="URL or path to video file")
    thumbnail_url: Optional[str] = Field(None, description="URL to video thumbnail image")
    duration_seconds: Optional[int] = Field(None, ge=0, description="Video duration in seconds")
    order_index: int = Field(default=0, ge=0, description="Display order within course")
    is_active: bool = Field(default=True, description="Whether video is active/visible")

    @validator('title')
    def validate_title(cls, v):
        """
        Validate video title.

        BUSINESS RULE: Titles must be meaningful for student navigation
        """
        if not v.strip():
            raise ValueError('Video title cannot be empty')
        return v.strip()

    @validator('video_url')
    def validate_video_url(cls, v, values):
        """
        Validate video URL based on video type.

        BUSINESS RULES:
        - YouTube videos must use valid YouTube URL formats
        - Vimeo videos must use valid Vimeo URL formats
        - External links must be valid HTTP/HTTPS URLs
        - Upload paths are validated separately during storage
        """
        if not v or not v.strip():
            raise ValueError('Video URL cannot be empty')

        video_type = values.get('video_type')
        v = v.strip()

        if video_type == VideoType.YOUTUBE:
            if not ('youtube.com' in v or 'youtu.be' in v):
                raise ValueError('Invalid YouTube URL format')
        elif video_type == VideoType.VIMEO:
            if 'vimeo.com' not in v:
                raise ValueError('Invalid Vimeo URL format')
        elif video_type == VideoType.LINK:
            if not (v.startswith('http://') or v.startswith('https://')):
                raise ValueError('External video links must be HTTP/HTTPS URLs')

        return v


class CourseVideoCreate(CourseVideoBase):
    """
    Course video creation model.

    WORKFLOW:
    1. Instructor specifies video source (upload vs external link)
    2. For uploads: Video file is uploaded separately via multipart form
    3. For links: URL is validated and metadata extracted
    4. Video is associated with course and ordered appropriately
    """
    course_id: str = Field(..., description="Course ID this video belongs to")


class CourseVideoUpdate(BaseModel):
    """
    Course video update model.

    BUSINESS RULES:
    - All fields are optional to support partial updates
    - Video type cannot be changed after creation (immutable)
    - URL changes require re-validation for external links
    """
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = Field(None, ge=0)
    order_index: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

    @validator('title')
    def validate_title(cls, v):
        """Validate title if provided"""
        if v is not None and not v.strip():
            raise ValueError('Video title cannot be empty')
        return v.strip() if v else v


class CourseVideo(CourseVideoBase):
    """
    Complete course video model with all fields.

    PERSISTENCE:
    - Includes database-generated fields (id, timestamps)
    - Contains computed fields for client display
    - Supports both uploaded and linked video content
    """
    id: str
    course_id: str
    file_size_bytes: Optional[int] = Field(None, description="File size for uploaded videos")
    mime_type: Optional[str] = Field(None, description="MIME type for uploaded videos")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class CourseVideoResponse(BaseModel):
    """Single video response model"""
    success: bool = True
    video: CourseVideo
    message: Optional[str] = None


class CourseVideoListResponse(BaseModel):
    """
    Multiple videos response model.

    PAGINATION:
    - Supports large course libraries with many videos
    - Returns videos ordered by order_index for sequential learning
    """
    success: bool = True
    videos: List[CourseVideo]
    total: int
    message: Optional[str] = None


class VideoUploadRequest(BaseModel):
    """
    Video upload request metadata.

    WORKFLOW:
    1. Client requests upload URL with video metadata
    2. Server validates request and generates signed upload URL
    3. Client uploads file directly to storage (S3 or local)
    4. Server processes uploaded file and creates video record
    """
    course_id: str
    filename: str = Field(..., min_length=1, max_length=500)
    file_size_bytes: int = Field(..., gt=0, description="File size in bytes")
    mime_type: str = Field(..., description="Video MIME type")
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)

    @validator('mime_type')
    def validate_mime_type(cls, v):
        """
        Validate video MIME type.

        BUSINESS RULE: Only accept common video formats for platform compatibility
        """
        allowed_types = [
            'video/mp4',
            'video/mpeg',
            'video/quicktime',
            'video/x-msvideo',
            'video/x-matroska',
            'video/webm',
            'video/ogg'
        ]
        if v not in allowed_types:
            raise ValueError(f'Unsupported video type. Allowed types: {", ".join(allowed_types)}')
        return v

    @validator('file_size_bytes')
    def validate_file_size(cls, v):
        """
        Validate file size.

        BUSINESS RULE: Limit video size to prevent storage abuse
        Max size: 2GB (2,147,483,648 bytes)
        """
        max_size = 2 * 1024 * 1024 * 1024  # 2GB
        if v > max_size:
            raise ValueError(f'Video file too large. Maximum size: 2GB')
        return v


class VideoUploadProgress(BaseModel):
    """
    Video upload progress tracking.

    REAL-TIME UPDATES:
    - Clients can poll this endpoint for upload status
    - Enables progress bars and status notifications
    - Tracks both upload and post-processing phases
    """
    id: str
    course_id: str
    filename: str
    file_size_bytes: Optional[int]
    upload_status: UploadStatus
    upload_progress: int = Field(default=0, ge=0, le=100, description="Upload progress percentage")
    error_message: Optional[str] = None
    storage_path: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class VideoUploadResponse(BaseModel):
    """
    Response for video upload initiation.

    SIGNED URL PATTERN:
    - Returns a pre-signed URL for direct upload to storage
    - Includes upload ID for tracking progress
    - URL expires after configured time period
    """
    success: bool = True
    upload_id: str
    upload_url: str
    upload_expires_at: datetime
    message: Optional[str] = None
