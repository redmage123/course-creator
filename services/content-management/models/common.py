"""
Common models and base classes for Content Management Service.

This module provides shared models, base classes, and utilities
used throughout the content management service.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from abc import ABC, abstractmethod


class ContentType(str, Enum):
    """Content type enumeration"""
    SYLLABUS = "syllabus"
    SLIDES = "slides"
    MATERIALS = "materials"
    EXERCISES = "exercises"
    QUIZZES = "quizzes"
    LABS = "labs"
    EXPORTS = "exports"
    TEMP = "temp"


class ProcessingStatus(str, Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportFormat(str, Enum):
    """Export format enumeration"""
    POWERPOINT = "powerpoint"
    JSON = "json"
    PDF = "pdf"
    EXCEL = "excel"
    ZIP = "zip"
    SCORM = "scorm"


class DifficultyLevel(str, Enum):
    """Difficulty level enumeration"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class BaseContentModel(BaseModel):
    """Base model for all content"""
    model_config = {
        "use_enum_values": True,
        "validate_assignment": True,
        "arbitrary_types_allowed": True
    }
    
    id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    course_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if v is None:
            return []
        return [tag.strip().lower() for tag in v if tag.strip()]


class APIResponse(BaseModel):
    """Standard API response model"""
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    message: str
    error_code: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Success response model"""
    success: bool = True
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel):
    """Paginated response model"""
    items: List[Any]
    total_count: int
    page_size: int
    current_page: int
    total_pages: int
    has_next: bool
    has_previous: bool


class ProcessingTask(BaseModel):
    """Processing task model"""
    task_id: str
    task_type: str
    status: ProcessingStatus = ProcessingStatus.PENDING
    progress_percentage: int = Field(0, ge=0, le=100)
    message: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None


class FileUploadRequest(BaseModel):
    """File upload request model"""
    content_type: ContentType
    filename: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0, le=100*1024*1024)  # Max 100MB
    mime_type: Optional[str] = None
    process_with_ai: bool = False
    course_id: Optional[str] = None


class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., min_length=1)
    content_types: Optional[List[ContentType]] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    sort_by: str = "created_at"
    sort_order: str = Field("desc", pattern="^(asc|desc)$")
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class ExportRequest(BaseModel):
    """Export request model"""
    content_id: str
    format: ExportFormat
    options: Dict[str, Any] = Field(default_factory=dict)
    include_metadata: bool = True


# Abstract base classes for extensibility
class ContentProcessor(ABC):
    """Abstract base class for content processors"""
    
    @abstractmethod
    async def process(self, content: Any) -> Any:
        """Process content and return result"""
        pass
    
    @abstractmethod
    async def validate(self, content: Any) -> bool:
        """Validate content before processing"""
        pass


class ExportHandler(ABC):
    """Abstract base class for export handlers"""
    
    @abstractmethod
    async def export(self, content: Any, format: ExportFormat) -> bytes:
        """Export content to specified format"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[ExportFormat]:
        """Get list of supported export formats"""
        pass


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    async def generate_content(self, prompt: str, content_type: ContentType) -> Any:
        """Generate content using AI"""
        pass
    
    @abstractmethod
    async def analyze_content(self, content: Any) -> Dict[str, Any]:
        """Analyze content structure and extract insights"""
        pass


# Utility functions
def create_api_response(success: bool, message: str, data: Any = None, 
                       error_code: str = None) -> APIResponse:
    """Create standardized API response"""
    return APIResponse(
        success=success,
        message=message,
        data=data,
        error_code=error_code
    )


def create_error_response(message: str, error_code: str, 
                         details: Optional[Dict[str, Any]] = None) -> ErrorResponse:
    """Create error response"""
    return ErrorResponse(
        message=message,
        error_code=error_code,
        details=details
    )


def create_success_response(message: str, data: Any = None) -> SuccessResponse:
    """Create success response"""
    return SuccessResponse(
        message=message,
        data=data
    )


def create_paginated_response(items: List[Any], total_count: int, 
                            page_size: int, current_page: int) -> PaginatedResponse:
    """Create paginated response"""
    total_pages = (total_count + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=items,
        total_count=total_count,
        page_size=page_size,
        current_page=current_page,
        total_pages=total_pages,
        has_next=current_page < total_pages,
        has_previous=current_page > 1
    )


def validate_content_type_format(content_type: str, file_extension: str) -> bool:
    """Validate file format for content type"""
    format_mapping = {
        ContentType.SYLLABUS: ['.pdf', '.doc', '.docx', '.txt'],
        ContentType.SLIDES: ['.ppt', '.pptx', '.pdf', '.json'],
        ContentType.MATERIALS: ['.pdf', '.doc', '.docx', '.zip', '.jpg', '.png', '.mp4', '.mp3']
    }
    
    allowed_formats = format_mapping.get(ContentType(content_type), [])
    return file_extension.lower() in allowed_formats