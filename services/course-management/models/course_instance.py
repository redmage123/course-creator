"""
Course Instance Models

BUSINESS CONTEXT:
Course instances represent scheduled sessions of a course with specific start/end dates,
enrollment limits, and instructor assignments. Multiple instances of the same course
can run concurrently or sequentially.

TECHNICAL IMPLEMENTATION:
Pydantic models for course instance data validation and serialization.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

from models.common import TimestampMixin


class InstanceStatus(str, Enum):
    """
    Course instance status enumeration.

    BUSINESS LOGIC:
    - SCHEDULED: Instance created but not yet started
    - ACTIVE: Instance is currently running
    - COMPLETED: Instance has finished
    - CANCELLED: Instance was cancelled before completion
    """
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CourseInstanceBase(BaseModel):
    """
    Base course instance model with common fields.

    BUSINESS RULES:
    - Start date must be in the future for new instances
    - End date must be after start date
    - Max students must be positive if specified
    """
    course_id: str = Field(..., description="Reference to the published course")
    instructor_id: Optional[str] = Field(None, description="Instructor assigned to this instance")
    start_date: date = Field(..., description="Instance start date")
    end_date: date = Field(..., description="Instance end date")
    max_students: Optional[int] = Field(None, ge=1, description="Maximum enrollment limit")
    status: InstanceStatus = InstanceStatus.SCHEDULED

    @validator('end_date')
    def validate_end_date(cls, v, values):
        """
        Validate that end date is after start date.

        BUSINESS RULE: Course instances must have a valid date range
        """
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class CourseInstanceCreate(CourseInstanceBase):
    """
    Course instance creation model.

    BUSINESS CONTEXT:
    Used when instructors create a new scheduled session of a course.
    """
    pass


class CourseInstanceUpdate(BaseModel):
    """
    Course instance update model.

    BUSINESS CONTEXT:
    Allows updating instance details like dates, enrollment limits, and status.
    """
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_students: Optional[int] = Field(None, ge=1)
    status: Optional[InstanceStatus] = None

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            if v <= values['start_date']:
                raise ValueError('End date must be after start date')
        return v


class CourseInstance(CourseInstanceBase, TimestampMixin):
    """
    Complete course instance model.

    BUSINESS CONTEXT:
    Represents a scheduled course session with all metadata including
    enrollment statistics and course details.
    """
    id: str

    # Enrollment statistics
    enrolled_count: int = 0
    active_enrollments: int = 0
    completed_count: int = 0

    # Course details (denormalized for performance)
    course_title: Optional[str] = None
    course_code: Optional[str] = None
    course_description: Optional[str] = None

    # Instructor details (denormalized for performance)
    instructor_name: Optional[str] = None
    instructor_email: Optional[str] = None

    # Metadata
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    cancellation_reason: Optional[str] = None


class CourseInstanceResponse(BaseModel):
    """Course instance response model."""
    success: bool = True
    instance: CourseInstance
    message: Optional[str] = None


class CourseInstanceListResponse(BaseModel):
    """Course instance list response model."""
    success: bool = True
    instances: List[CourseInstance]
    total: int
    page: int = 1
    per_page: int = 100
    message: Optional[str] = None


class CourseInstanceSearchRequest(BaseModel):
    """
    Course instance search request model.

    BUSINESS CONTEXT:
    Allows filtering instances by instructor, status, date range, and course.
    """
    instructor_id: Optional[str] = None
    course_id: Optional[str] = None
    status: Optional[InstanceStatus] = None
    start_date_from: Optional[date] = None
    start_date_to: Optional[date] = None
    include_cancelled: bool = False
