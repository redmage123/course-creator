"""
Enrollment Models

Pydantic models for enrollment data validation and serialization.
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

from models.common import TimestampMixin


class EnrollmentStatus(str, Enum):
    """Enrollment status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class EnrollmentBase(BaseModel):
    """Base enrollment model with common fields."""
    student_id: str = Field(..., description="Student user ID")
    course_id: str = Field(..., description="Course ID")
    status: EnrollmentStatus = EnrollmentStatus.ACTIVE
    progress_percentage: float = Field(0.0, ge=0, le=100)
    
    @validator('progress_percentage')
    def validate_progress(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Progress percentage must be between 0 and 100')
        return v


class EnrollmentCreate(EnrollmentBase):
    """Enrollment creation model."""
    enrollment_date: Optional[datetime] = None
    notes: Optional[str] = None


class EnrollmentUpdate(BaseModel):
    """Enrollment update model."""
    status: Optional[EnrollmentStatus] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    last_accessed: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    certificate_issued: Optional[bool] = None
    notes: Optional[str] = None
    
    @validator('progress_percentage')
    def validate_progress(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Progress percentage must be between 0 and 100')
        return v


class Enrollment(EnrollmentBase, TimestampMixin):
    """Complete enrollment model."""
    id: str
    enrollment_date: datetime
    last_accessed: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    certificate_issued: bool = False
    notes: Optional[str] = None
    
    # Related data (may be populated by joins)
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    course_title: Optional[str] = None
    course_instructor: Optional[str] = None


class EnrollmentRequest(BaseModel):
    """Enrollment request model."""
    student_email: EmailStr
    course_id: str
    notes: Optional[str] = None


class StudentRegistrationRequest(BaseModel):
    """Multiple student registration request model."""
    course_id: str
    student_emails: List[EmailStr] = Field(..., min_items=1, max_items=100)
    notes: Optional[str] = None
    
    @validator('student_emails')
    def validate_unique_emails(cls, v):
        if len(v) != len(set(v)):
            raise ValueError('Student emails must be unique')
        return v


class EnrollmentResponse(BaseModel):
    """Enrollment response model."""
    success: bool = True
    enrollment: Enrollment
    message: Optional[str] = None


class EnrollmentListResponse(BaseModel):
    """Enrollment list response model."""
    success: bool = True
    enrollments: List[Enrollment]
    total: int
    page: int = 1
    per_page: int = 100
    message: Optional[str] = None


class BulkEnrollmentResponse(BaseModel):
    """Bulk enrollment response model."""
    success: bool = True
    enrolled_students: List[str]
    failed_enrollments: List[dict]
    total_attempted: int
    total_successful: int
    total_failed: int
    message: Optional[str] = None


class EnrollmentStats(BaseModel):
    """Enrollment statistics model."""
    total_enrollments: int
    active_enrollments: int
    completed_enrollments: int
    cancelled_enrollments: int
    average_completion_rate: float
    enrollments_by_month: dict
    top_courses: List[dict]


class EnrollmentSearchRequest(BaseModel):
    """Enrollment search request model."""
    student_id: Optional[str] = None
    course_id: Optional[str] = None
    status: Optional[EnrollmentStatus] = None
    instructor_id: Optional[str] = None
    enrollment_date_from: Optional[datetime] = None
    enrollment_date_to: Optional[datetime] = None
    progress_min: Optional[float] = Field(None, ge=0, le=100)
    progress_max: Optional[float] = Field(None, ge=0, le=100)
    
    @validator('progress_max')
    def validate_progress_range(cls, v, values):
        if v is not None and 'progress_min' in values and values['progress_min'] is not None:
            if v < values['progress_min']:
                raise ValueError('Maximum progress must be greater than minimum progress')
        return v
    
    @validator('enrollment_date_to')
    def validate_date_range(cls, v, values):
        if v is not None and 'enrollment_date_from' in values and values['enrollment_date_from'] is not None:
            if v < values['enrollment_date_from']:
                raise ValueError('End date must be after start date')
        return v