"""
Course Models

Pydantic models for course data validation and serialization.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

from models.common import TimestampMixin


class DifficultyLevel(str, Enum):
    """Course difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CourseStatus(str, Enum):
    """Course status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DurationUnit(str, Enum):
    """Duration unit enumeration."""
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"


class CourseBase(BaseModel):
    """Base course model with common fields."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    estimated_duration: Optional[int] = Field(None, ge=1)  # duration number
    duration_unit: DurationUnit = DurationUnit.WEEKS  # duration unit
    price: float = Field(0.0, ge=0)
    thumbnail_url: Optional[str] = None
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()


class CourseCreate(CourseBase):
    """Course creation model."""
    instructor_id: str = Field(..., description="Instructor user ID")


class CourseUpdate(BaseModel):
    """Course update model."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    difficulty_level: Optional[DifficultyLevel] = None
    estimated_duration: Optional[int] = Field(None, ge=1)
    duration_unit: Optional[DurationUnit] = None
    price: Optional[float] = Field(None, ge=0)
    is_published: Optional[bool] = None
    thumbnail_url: Optional[str] = None
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip() if v else v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip() if v else v


class Course(CourseBase, TimestampMixin):
    """Complete course model."""
    id: str
    instructor_id: str
    is_published: bool = False
    status: CourseStatus = CourseStatus.DRAFT
    
    # Statistics
    total_enrollments: Optional[int] = 0
    active_enrollments: Optional[int] = 0
    completion_rate: Optional[float] = 0.0
    
    # Metadata
    last_updated_by: Optional[str] = None
    published_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None


class CourseResponse(BaseModel):
    """Course response model."""
    success: bool = True
    course: Course
    message: Optional[str] = None


class CourseListResponse(BaseModel):
    """Course list response model."""
    success: bool = True
    courses: List[Course]
    total: int
    page: int = 1
    per_page: int = 100
    message: Optional[str] = None


class CourseStats(BaseModel):
    """Course statistics model."""
    total_courses: int
    published_courses: int
    draft_courses: int
    archived_courses: int
    total_enrollments: int
    average_rating: Optional[float] = None
    courses_by_difficulty: dict
    courses_by_category: dict


class CourseSearchRequest(BaseModel):
    """Course search request model."""
    query: Optional[str] = None
    category: Optional[str] = None
    difficulty_level: Optional[DifficultyLevel] = None
    instructor_id: Optional[str] = None
    is_published: Optional[bool] = None
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)
    duration_min: Optional[int] = Field(None, ge=0)
    duration_max: Optional[int] = Field(None, ge=0)
    
    @validator('price_max')
    def validate_price_range(cls, v, values):
        if v is not None and 'price_min' in values and values['price_min'] is not None:
            if v < values['price_min']:
                raise ValueError('Maximum price must be greater than minimum price')
        return v
    
    @validator('duration_max')
    def validate_duration_range(cls, v, values):
        if v is not None and 'duration_min' in values and values['duration_min'] is not None:
            if v < values['duration_min']:
                raise ValueError('Maximum duration must be greater than minimum duration')
        return v


class CoursePublishRequest(BaseModel):
    """Course publish request model."""
    publish: bool = True
    publish_message: Optional[str] = None