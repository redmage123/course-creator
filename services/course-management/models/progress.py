"""
Progress Models

Pydantic models for progress tracking and reporting.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

from .common import TimestampMixin


class ProgressType(str, Enum):
    """Progress tracking types."""
    LESSON = "lesson"
    MODULE = "module"
    QUIZ = "quiz"
    EXERCISE = "exercise"
    OVERALL = "overall"


class ProgressStatus(str, Enum):
    """Progress status enumeration."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProgressBase(BaseModel):
    """Base progress model with common fields."""
    enrollment_id: str = Field(..., description="Enrollment ID")
    content_type: ProgressType
    content_id: str = Field(..., description="Content identifier")
    status: ProgressStatus = ProgressStatus.NOT_STARTED
    progress_percentage: float = Field(0.0, ge=0, le=100)
    time_spent: Optional[int] = Field(None, ge=0)  # in seconds
    
    @validator('progress_percentage')
    def validate_progress(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Progress percentage must be between 0 and 100')
        return v


class ProgressCreate(ProgressBase):
    """Progress creation model."""
    started_at: Optional[datetime] = None
    notes: Optional[str] = None


class ProgressUpdate(BaseModel):
    """Progress update model."""
    status: Optional[ProgressStatus] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    time_spent: Optional[int] = Field(None, ge=0)
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    @validator('progress_percentage')
    def validate_progress(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Progress percentage must be between 0 and 100')
        return v


class Progress(ProgressBase, TimestampMixin):
    """Complete progress model."""
    id: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    attempts: int = 0
    best_score: Optional[float] = None
    notes: Optional[str] = None
    
    # Related data (may be populated by joins)
    student_id: Optional[str] = None
    course_id: Optional[str] = None
    content_title: Optional[str] = None


class ProgressResponse(BaseModel):
    """Progress response model."""
    success: bool = True
    progress: Progress
    message: Optional[str] = None


class ProgressListResponse(BaseModel):
    """Progress list response model."""
    success: bool = True
    progress_records: List[Progress]
    total: int
    page: int = 1
    per_page: int = 100
    message: Optional[str] = None


class StudentProgressSummary(BaseModel):
    """Student progress summary model."""
    enrollment_id: str
    student_id: str
    course_id: str
    overall_progress: float
    lessons_completed: int
    lessons_total: int
    modules_completed: int
    modules_total: int
    quizzes_completed: int
    quizzes_total: int
    exercises_completed: int
    exercises_total: int
    total_time_spent: int  # in seconds
    last_activity: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


class CourseProgressSummary(BaseModel):
    """Course progress summary model."""
    course_id: str
    total_students: int
    active_students: int
    completed_students: int
    average_progress: float
    average_time_spent: int  # in seconds
    completion_rate: float
    progress_by_module: Dict[str, float]
    student_progress: List[StudentProgressSummary]


class ProgressStats(BaseModel):
    """Progress statistics model."""
    total_progress_records: int
    completed_items: int
    in_progress_items: int
    not_started_items: int
    average_completion_time: Optional[int] = None  # in seconds
    progress_by_type: Dict[str, dict]
    daily_activity: Dict[str, int]
    weekly_activity: Dict[str, int]


class ProgressSearchRequest(BaseModel):
    """Progress search request model."""
    enrollment_id: Optional[str] = None
    student_id: Optional[str] = None
    course_id: Optional[str] = None
    content_type: Optional[ProgressType] = None
    content_id: Optional[str] = None
    status: Optional[ProgressStatus] = None
    progress_min: Optional[float] = Field(None, ge=0, le=100)
    progress_max: Optional[float] = Field(None, ge=0, le=100)
    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None
    
    @validator('progress_max')
    def validate_progress_range(cls, v, values):
        if v is not None and 'progress_min' in values and values['progress_min'] is not None:
            if v < values['progress_min']:
                raise ValueError('Maximum progress must be greater than minimum progress')
        return v
    
    @validator('started_before')
    def validate_date_range(cls, v, values):
        if v is not None and 'started_after' in values and values['started_after'] is not None:
            if v < values['started_after']:
                raise ValueError('End date must be after start date')
        return v


class ProgressBatchUpdate(BaseModel):
    """Batch progress update model."""
    updates: List[Dict[str, any]] = Field(..., min_items=1, max_items=100)
    
    @validator('updates')
    def validate_updates(cls, v):
        for update in v:
            if 'id' not in update or 'progress_percentage' not in update:
                raise ValueError('Each update must contain id and progress_percentage')
        return v