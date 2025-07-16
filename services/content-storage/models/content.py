"""
Content Models

Pydantic models for content data validation and serialization.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from .common import TimestampMixin


class ContentType(str, Enum):
    """Content type enumeration."""
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    ARCHIVE = "archive"
    OTHER = "other"


class ContentStatus(str, Enum):
    """Content status enumeration."""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"
    DELETED = "deleted"


class ContentBase(BaseModel):
    """Base content model with common fields."""
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., description="MIME type")
    size: int = Field(..., ge=0, description="File size in bytes")
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v.strip():
            raise ValueError('Filename cannot be empty')
        
        # Check for dangerous characters
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        for char in dangerous_chars:
            if char in v:
                raise ValueError(f'Filename contains invalid character: {char}')
        
        return v.strip()


class ContentCreate(ContentBase):
    """Content creation model."""
    uploaded_by: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContentUpdate(BaseModel):
    """Content update model."""
    filename: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[ContentStatus] = None
    
    @validator('filename')
    def validate_filename(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Filename cannot be empty')
        return v.strip() if v else v


class ContentMetadata(BaseModel):
    """Content metadata model."""
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None  # for video/audio
    pages: Optional[int] = None  # for documents
    format: Optional[str] = None
    compression: Optional[str] = None
    checksum: Optional[str] = None
    extracted_text: Optional[str] = None
    thumbnail_path: Optional[str] = None


class Content(ContentBase, TimestampMixin):
    """Complete content model."""
    id: str
    path: str
    url: str
    content_category: ContentType
    status: ContentStatus = ContentStatus.READY
    uploaded_by: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: ContentMetadata = Field(default_factory=ContentMetadata)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    # File system info
    storage_backend: str = "local"
    storage_path: str
    backup_path: Optional[str] = None
    
    # Security
    is_public: bool = False
    access_permissions: List[str] = Field(default_factory=list)
    
    @validator('content_category', pre=True, always=True)
    def determine_content_category(cls, v, values):
        if v:
            return v
        
        # Auto-detect from content_type
        content_type = values.get('content_type', '').lower()
        if content_type.startswith('image/'):
            return ContentType.IMAGE
        elif content_type.startswith('video/'):
            return ContentType.VIDEO
        elif content_type.startswith('audio/'):
            return ContentType.AUDIO
        elif content_type in ['application/pdf', 'application/msword', 'text/plain']:
            return ContentType.DOCUMENT
        elif content_type in ['application/zip', 'application/x-tar', 'application/gzip']:
            return ContentType.ARCHIVE
        else:
            return ContentType.OTHER


class ContentUploadResponse(BaseModel):
    """Content upload response model."""
    success: bool = True
    content_id: str
    filename: str
    size: int
    url: str
    upload_time: datetime
    message: Optional[str] = None


class ContentListResponse(BaseModel):
    """Content list response model."""
    success: bool = True
    content: List[Content]
    total: int
    page: int = 1
    per_page: int = 100
    message: Optional[str] = None


class ContentResponse(BaseModel):
    """Content response model."""
    success: bool = True
    content: Content
    message: Optional[str] = None


class ContentSearchRequest(BaseModel):
    """Content search request model."""
    query: Optional[str] = None
    content_type: Optional[str] = None
    content_category: Optional[ContentType] = None
    uploaded_by: Optional[str] = None
    tags: Optional[List[str]] = None
    size_min: Optional[int] = Field(None, ge=0)
    size_max: Optional[int] = Field(None, ge=0)
    uploaded_after: Optional[datetime] = None
    uploaded_before: Optional[datetime] = None
    status: Optional[ContentStatus] = None
    
    @validator('size_max')
    def validate_size_range(cls, v, values):
        if v is not None and 'size_min' in values and values['size_min'] is not None:
            if v < values['size_min']:
                raise ValueError('Maximum size must be greater than minimum size')
        return v
    
    @validator('uploaded_before')
    def validate_date_range(cls, v, values):
        if v is not None and 'uploaded_after' in values and values['uploaded_after'] is not None:
            if v < values['uploaded_after']:
                raise ValueError('End date must be after start date')
        return v


class ContentStats(BaseModel):
    """Content statistics model."""
    total_files: int
    total_size: int
    files_by_type: Dict[str, int]
    files_by_category: Dict[str, int]
    average_file_size: float
    storage_used: int
    storage_available: int
    most_accessed_files: List[Dict[str, Any]]
    upload_trends: Dict[str, int]