"""
Course Publishing Models

Pydantic models for course publishing workflow, instances, and enhanced enrollment system.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import pytz

from .common import TimestampMixin


class CourseStatus(str, Enum):
    """Course lifecycle status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class CourseVisibility(str, Enum):
    """Course visibility settings."""
    PRIVATE = "private"  # Only instructor can see
    PUBLIC = "public"    # Visible to all instructors


class CourseInstanceStatus(str, Enum):
    """Course instance status."""
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EnrollmentStatus(str, Enum):
    """Student enrollment status."""
    ENROLLED = "enrolled"
    ACTIVE = "active"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    WITHDRAWN = "withdrawn"


class EmailType(str, Enum):
    """Email notification types."""
    ENROLLMENT = "enrollment"
    REMINDER = "reminder"
    WELCOME = "welcome"
    COMPLETION = "completion"


# Course Publishing Models
class CoursePublishRequest(BaseModel):
    """Request to publish a course."""
    visibility: CourseVisibility = CourseVisibility.PRIVATE
    publish_message: Optional[str] = None


class CourseArchiveRequest(BaseModel):
    """Request to archive a course."""
    archive_reason: Optional[str] = None


# Course Instance Models
class CourseInstanceBase(BaseModel):
    """Base course instance model."""
    course_id: str = Field(..., description="ID of the published course")
    instance_name: str = Field(..., min_length=1, max_length=255, description="Name for this course instance")
    description: Optional[str] = Field(None, description="Instance-specific description")
    
    # Scheduling
    start_date: datetime = Field(..., description="Course start date and time")
    end_date: datetime = Field(..., description="Course end date and time")
    timezone: str = Field(default="UTC", description="Timezone for the course schedule")
    
    max_students: Optional[int] = Field(None, ge=1, description="Maximum number of students (optional)")
    
    @validator('timezone')
    def validate_timezone(cls, v):
        """Validate timezone string."""
        try:
            pytz.timezone(v)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f'Invalid timezone: {v}')
        return v
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Ensure end date is after start date."""
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @validator('start_date')
    def validate_start_date(cls, v):
        """Ensure start date is in the future."""
        if v <= datetime.now(timezone.utc):
            raise ValueError('Start date must be in the future')
        return v


class CourseInstanceCreate(CourseInstanceBase):
    """Course instance creation model."""
    pass


class CourseInstanceUpdate(BaseModel):
    """Course instance update model."""
    instance_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    timezone: Optional[str] = None
    max_students: Optional[int] = Field(None, ge=1)
    
    @validator('timezone')
    def validate_timezone(cls, v):
        if v is not None:
            try:
                pytz.timezone(v)
            except pytz.exceptions.UnknownTimeZoneError:
                raise ValueError(f'Invalid timezone: {v}')
        return v


class CourseInstance(CourseInstanceBase, TimestampMixin):
    """Complete course instance model."""
    id: str
    instructor_id: str
    status: CourseInstanceStatus = CourseInstanceStatus.SCHEDULED
    current_enrollments: int = 0
    duration_days: Optional[int] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    
    # Related data
    course_title: Optional[str] = None
    instructor_name: Optional[str] = None


class CourseInstanceCancel(BaseModel):
    """Request to cancel a course instance."""
    cancellation_reason: str = Field(..., min_length=1, description="Reason for cancelling the course")


# Student Enrollment Models
class StudentEnrollmentRequest(BaseModel):
    """Request to enroll a student in a course instance."""
    course_instance_id: str = Field(..., description="Course instance ID")
    student_first_name: str = Field(..., min_length=1, max_length=100, description="Student's first name")
    student_last_name: str = Field(..., min_length=1, max_length=100, description="Student's last name")
    student_email: EmailStr = Field(..., description="Student's email address")
    notes: Optional[str] = Field(None, description="Enrollment notes")


class BulkEnrollmentRequest(BaseModel):
    """Request to enroll multiple students."""
    course_instance_id: str = Field(..., description="Course instance ID")
    students: List[Dict[str, str]] = Field(..., min_items=1, max_items=100, description="List of students to enroll")
    notes: Optional[str] = Field(None, description="Enrollment notes")
    
    @validator('students')
    def validate_students(cls, v):
        """Validate student data structure."""
        required_fields = {'first_name', 'last_name', 'email'}
        for i, student in enumerate(v):
            if not isinstance(student, dict):
                raise ValueError(f'Student {i+1} must be a dictionary')
            
            missing_fields = required_fields - set(student.keys())
            if missing_fields:
                raise ValueError(f'Student {i+1} missing required fields: {missing_fields}')
            
            # Validate email format
            try:
                EmailStr.validate(student['email'])
            except ValueError:
                raise ValueError(f'Student {i+1} has invalid email: {student["email"]}')
        
        # Check for duplicate emails
        emails = [s['email'] for s in v]
        if len(emails) != len(set(emails)):
            raise ValueError('Duplicate email addresses in student list')
        
        return v


class StudentCourseEnrollment(BaseModel):
    """Complete student enrollment model."""
    id: str
    course_instance_id: str
    student_id: Optional[str] = None  # May be null if user doesn't exist yet
    
    # Student info
    student_email: str
    student_first_name: str
    student_last_name: str
    
    # Access credentials
    unique_access_url: str
    access_token: str
    password_reset_required: bool = True
    
    # Status and progress
    enrollment_status: EnrollmentStatus = EnrollmentStatus.ENROLLED
    progress_percentage: float = Field(0.0, ge=0, le=100)
    
    # Timestamps
    enrolled_at: datetime
    first_login_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metadata
    enrolled_by: str  # Instructor ID
    certificate_issued: bool = False
    notes: Optional[str] = None
    
    # Related data
    course_title: Optional[str] = None
    instance_name: Optional[str] = None
    instructor_name: Optional[str] = None


class EnrollmentUpdateRequest(BaseModel):
    """Request to update student enrollment."""
    enrollment_status: Optional[EnrollmentStatus] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


# Quiz Publishing Models
class QuizPublicationRequest(BaseModel):
    """Request to publish/unpublish a quiz."""
    quiz_id: str = Field(..., description="Quiz ID to publish/unpublish")
    course_instance_id: str = Field(..., description="Course instance ID")
    is_published: bool = Field(..., description="Whether to publish or unpublish")
    
    # Optional scheduling
    available_from: Optional[datetime] = Field(None, description="When quiz becomes available")
    available_until: Optional[datetime] = Field(None, description="When quiz becomes unavailable")
    time_limit_minutes: Optional[int] = Field(None, ge=1, description="Time limit in minutes")
    max_attempts: int = Field(3, ge=1, description="Maximum attempts allowed")
    
    @validator('available_until')
    def validate_availability_window(cls, v, values):
        """Ensure availability window is valid."""
        if v is not None and 'available_from' in values and values['available_from'] is not None:
            if v <= values['available_from']:
                raise ValueError('available_until must be after available_from')
        return v


class QuizPublication(BaseModel):
    """Quiz publication status model."""
    id: str
    quiz_id: str
    course_instance_id: str
    is_published: bool
    published_at: Optional[datetime] = None
    unpublished_at: Optional[datetime] = None
    published_by: str
    
    # Settings
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    time_limit_minutes: Optional[int] = None
    max_attempts: int = 3
    
    # Related data
    quiz_title: Optional[str] = None
    course_title: Optional[str] = None


# Content Visibility Models
class ContentVisibilityRequest(BaseModel):
    """Request to control content visibility."""
    course_instance_id: str
    content_type: str = Field(..., pattern=r'^(syllabus|slides|lab|quiz|lesson)$')
    content_id: str
    is_visible: bool
    visible_from: Optional[datetime] = None
    visible_until: Optional[datetime] = None


# Email Notification Models
class EnrollmentEmailData(BaseModel):
    """Data for generating enrollment emails."""
    student_name: str
    course_name: str
    instance_name: str
    start_date: datetime
    end_date: datetime
    timezone: str
    duration_days: int
    login_url: str
    temporary_password: str
    instructor_first_name: Optional[str] = None
    instructor_last_name: Optional[str] = None
    instructor_organization: Optional[str] = None
    instructor_full_name: Optional[str] = None


class EmailNotification(BaseModel):
    """Email notification model."""
    id: str
    enrollment_id: str
    recipient_email: str
    email_type: EmailType
    email_subject: str
    email_body: str
    sent_at: Optional[datetime] = None
    delivery_status: str = "pending"
    error_message: Optional[str] = None
    created_at: datetime
    sent_by: str


# Response Models
class CoursePublishResponse(BaseModel):
    """Response for course publish operations."""
    success: bool = True
    course: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class CourseInstanceResponse(BaseModel):
    """Response for course instance operations."""
    success: bool = True
    instance: Optional[CourseInstance] = None
    message: Optional[str] = None


class CourseInstanceListResponse(BaseModel):
    """Response for course instance list."""
    success: bool = True
    instances: List[CourseInstance]
    total: int
    page: int = 1
    per_page: int = 100
    message: Optional[str] = None


class EnrollmentResponse(BaseModel):
    """Response for enrollment operations."""
    success: bool = True
    enrollment: Optional[StudentCourseEnrollment] = None
    message: Optional[str] = None


class BulkEnrollmentResponse(BaseModel):
    """Response for bulk enrollment operations."""
    success: bool = True
    enrolled_students: List[Dict[str, str]] = []
    failed_enrollments: List[Dict[str, str]] = []
    total_attempted: int
    total_successful: int
    total_failed: int
    message: Optional[str] = None


class EnrollmentListResponse(BaseModel):
    """Response for enrollment list."""
    success: bool = True
    enrollments: List[StudentCourseEnrollment]
    total: int
    page: int = 1
    per_page: int = 100
    message: Optional[str] = None


class PublishedCoursesResponse(BaseModel):
    """Response for published courses list."""
    success: bool = True
    courses: List[Dict[str, Any]]
    total: int
    page: int = 1
    per_page: int = 100
    message: Optional[str] = None


class QuizPublicationResponse(BaseModel):
    """Response for quiz publication operations."""
    success: bool = True
    publication: Optional[QuizPublication] = None
    message: Optional[str] = None


# Student Access Models
class StudentLoginRequest(BaseModel):
    """Student login via unique URL."""
    access_token: str = Field(..., description="Access token from enrollment URL")
    password: str = Field(..., description="Temporary or permanent password")


class StudentLoginResponse(BaseModel):
    """Student login response."""
    success: bool = True
    access_token: str
    student_info: Optional[Dict[str, Any]] = None
    course_info: Optional[Dict[str, Any]] = None
    requires_password_reset: bool = False
    message: Optional[str] = None


class StudentDashboardData(BaseModel):
    """Data for student dashboard."""
    course_info: Dict[str, Any]
    instance_info: Dict[str, Any]
    enrollment_info: Dict[str, Any]
    syllabus: Optional[Dict[str, Any]] = None
    slides: List[Dict[str, Any]] = []
    labs: List[Dict[str, Any]] = []
    published_quizzes: List[Dict[str, Any]] = []
    progress: Dict[str, Any]