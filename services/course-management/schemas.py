"""
Course Management Service Pydantic Schemas

This module defines Pydantic data validation schemas for the course management service,
providing request/response serialization, validation, and API documentation for course,
enrollment, and progress tracking operations.

Business Context:
-----------------
The course management service handles:
- Course catalog management (CRUD operations on courses)
- Course structure organization (modules containing lessons)
- Student enrollment tracking and status management
- Learning progress monitoring per student per lesson
- Course publication workflow and pricing

Technical Implementation:
------------------------
Uses Pydantic for:
- Automatic request body validation with detailed error messages
- Response serialization with type safety
- OpenAPI (Swagger) schema generation for API documentation
- Data transformation between API layer and database models

Schema Patterns:
- Base classes provide common fields (timestamps, UUIDs)
- Create schemas for POST requests (all required fields)
- Update schemas for PATCH requests (all optional fields)
- Response schemas for GET requests (all fields including generated ones)
- List response schemas for paginated endpoints

Validation Rules:
- String length constraints (min/max) prevent database overflow
- Pattern validation (regex) ensures enum-like consistency
- Numeric constraints (gt, ge, Field) enforce business rules
- Email validation for user contact information

Dependencies:
- Pydantic: Data validation and serialization framework
- UUID: Universally unique identifiers for all entities
- datetime: Timestamp tracking for audit trails
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, constr, validator

# Base Models
class TimestampedModel(BaseModel):
    """
    Base model providing automatic timestamp tracking for entity lifecycle events.

    Attributes:
        created_at: UTC timestamp when entity was first created
        updated_at: UTC timestamp when entity was last modified

    Business Context:
        Timestamps enable audit trails, sorting by recency, and identifying stale data.
        All entities inherit these fields for consistent temporal tracking.
    """
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UUIDModel(BaseModel):
    """
    Base model providing UUID primary key for all entities.

    Attributes:
        id: Universally unique identifier (UUID v4)

    Business Context:
        UUIDs prevent ID collision in distributed systems, enable offline entity creation,
        and avoid exposing sequential ID patterns that leak business metrics.
    """
    id: UUID

# Course Schemas
class CourseBase(BaseModel):
    """
    Base schema for course entities with common validation rules.

    Attributes:
        title: Course name (1-255 characters, required)
        description: Detailed course description (unlimited length)
        duration_hours: Estimated completion time in hours (must be positive)
        level: Difficulty level (beginner/intermediate/advanced)
        price: Course price in USD (must be non-negative, 0 for free courses)
        is_published: Publication status (default: False for draft courses)

    Business Context:
        Courses are the primary product in the learning platform. Instructors create
        courses, set pricing, and publish when ready. Students browse published courses
        by level and enroll. Duration helps students plan their learning schedule.

    Validation Rules:
        - Title must not be empty and fits in database VARCHAR(255)
        - Duration must be positive (1 hour minimum assumed)
        - Level restricted to three valid values for consistent filtering
        - Price allows free courses (0) but not negative pricing
        - Unpublished courses are only visible to instructors/admins
    """
    title: constr(min_length=1, max_length=255)
    description: str
    duration_hours: float = Field(gt=0)
    level: str = Field(pattern='^(beginner|intermediate|advanced)$')
    price: float = Field(ge=0)
    is_published: bool = False

class CourseCreate(CourseBase):
    """
    Schema for creating new courses via POST /courses.

    Inherits all fields from CourseBase. All fields are required except is_published
    which defaults to False (draft state).

    Business Context:
        Instructors create courses in draft mode, add content (modules/lessons), preview,
        and then publish. Requires all metadata up front to ensure course quality.
    """
    pass

class CourseUpdate(BaseModel):
    """
    Schema for updating existing courses via PATCH /courses/{id}.

    All fields are optional, allowing partial updates. Only provided fields are modified.

    Business Context:
        Instructors update course metadata as content evolves. Price changes, description
        updates, and publication status changes are common. Partial updates prevent
        accidental overwrites of unchanged fields.
    """
    title: Optional[constr(min_length=1, max_length=255)]
    description: Optional[str]
    duration_hours: Optional[float] = Field(gt=0)
    level: Optional[str] = Field(pattern='^(beginner|intermediate|advanced)$')
    price: Optional[float] = Field(ge=0)
    is_published: Optional[bool]

class CourseResponse(CourseBase, UUIDModel, TimestampedModel):
    """
    Schema for course responses via GET /courses and GET /courses/{id}.

    Combines base course fields with UUID identifier and timestamps for complete
    representation of persisted courses.

    Business Context:
        API clients receive full course details including system-generated fields
        (id, timestamps) for caching, updates, and audit purposes.
    """
    pass

# Course Module Schemas
class CourseModuleBase(BaseModel):
    """
    Base schema for course modules (sections within a course).

    Attributes:
        course_id: UUID of parent course
        title: Module name (1-255 characters)
        description: Module overview and learning objectives
        order: Display order within course (0-indexed, non-negative)

    Business Context:
        Modules organize lessons into logical sections (e.g., "Introduction to Python",
        "Data Structures", "Algorithms"). Sequential ordering enables curriculum design.
    """
    course_id: UUID
    title: constr(min_length=1, max_length=255)
    description: str
    order: int = Field(ge=0)

class CourseModuleCreate(CourseModuleBase):
    """Schema for creating new course modules via POST /modules."""
    pass

class CourseModuleUpdate(BaseModel):
    """Schema for updating course modules via PATCH /modules/{id}. All fields optional."""
    title: Optional[constr(min_length=1, max_length=255)]
    description: Optional[str]
    order: Optional[int] = Field(ge=0)

class CourseModuleResponse(CourseModuleBase, UUIDModel, TimestampedModel):
    """Schema for module responses via GET /modules and GET /modules/{id}."""
    pass

# Course Lesson Schemas
class CourseLessonBase(BaseModel):
    """
    Base schema for individual lessons within course modules.

    Attributes:
        module_id: UUID of parent module
        title: Lesson name (1-255 characters)
        content: Lesson content (Markdown/HTML, unlimited length)
        duration_minutes: Estimated time to complete lesson (positive integer)
        order: Display order within module (0-indexed, non-negative)

    Business Context:
        Lessons are the atomic learning units containing video, text, code examples,
        and exercises. Duration helps students allocate learning time. Sequential
        ordering enables prerequisite enforcement and progress tracking.
    """
    module_id: UUID
    title: constr(min_length=1, max_length=255)
    content: str
    duration_minutes: int = Field(gt=0)
    order: int = Field(ge=0)

class CourseLessonCreate(CourseLessonBase):
    """Schema for creating new lessons via POST /lessons."""
    pass

class CourseLessonUpdate(BaseModel):
    """Schema for updating lessons via PATCH /lessons/{id}. All fields optional."""
    title: Optional[constr(min_length=1, max_length=255)]
    content: Optional[str]
    duration_minutes: Optional[int] = Field(gt=0)
    order: Optional[int] = Field(ge=0)

class CourseLessonResponse(CourseLessonBase, UUIDModel, TimestampedModel):
    """Schema for lesson responses via GET /lessons and GET /lessons/{id}."""
    pass

# Enrollment Schemas
class EnrollmentBase(BaseModel):
    """
    Base schema for student course enrollments.

    Attributes:
        user_id: UUID of enrolled student
        course_id: UUID of enrolled course
        status: Enrollment status (active/completed/cancelled)
        enrolled_at: UTC timestamp when student enrolled

    Business Context:
        Enrollments track which students have access to which courses. Status enables
        lifecycle management: active (currently learning), completed (certificate earned),
        cancelled (dropped course). Enrollment timestamp enables locations analysis.

    Status Transitions:
        - Created as 'active' when student enrolls
        - Changes to 'completed' when all lessons finished
        - Changes to 'cancelled' if student drops or refunds
    """
    user_id: UUID
    course_id: UUID
    status: str = Field(pattern='^(active|completed|cancelled)$')
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)

class EnrollmentCreate(EnrollmentBase):
    """Schema for creating enrollments via POST /enrollments."""
    pass

class EnrollmentUpdate(BaseModel):
    """Schema for updating enrollment status via PATCH /enrollments/{id}."""
    status: Optional[str] = Field(pattern='^(active|completed|cancelled)$')

class EnrollmentResponse(EnrollmentBase, UUIDModel, TimestampedModel):
    """Schema for enrollment responses via GET /enrollments."""
    pass

# Progress Schemas
class ProgressBase(BaseModel):
    """
    Base schema for student progress tracking per lesson.

    Attributes:
        enrollment_id: UUID of student's course enrollment
        lesson_id: UUID of specific lesson being tracked
        status: Progress status (not_started/in_progress/completed)
        completion_date: UTC timestamp when lesson was completed (null if incomplete)
        time_spent_minutes: Total time student spent on this lesson (non-negative)

    Business Context:
        Granular progress tracking enables:
        - Resume functionality (return to last incomplete lesson)
        - Progress analytics (completion rates per lesson)
        - Adaptive learning (identify struggling students)
        - Certificate eligibility (require 100% completion)
        - Time investment analysis (actual vs estimated duration)

    Status Transitions:
        - not_started: Lesson visible but never opened
        - in_progress: Lesson opened but not marked complete
        - completed: Student marked lesson as finished (or auto-completed)
    """
    enrollment_id: UUID
    lesson_id: UUID
    status: str = Field(pattern='^(not_started|in_progress|completed)$')
    completion_date: Optional[datetime]
    time_spent_minutes: int = Field(ge=0)

class ProgressCreate(ProgressBase):
    """Schema for creating progress records via POST /progress."""
    pass

class ProgressUpdate(BaseModel):
    """Schema for updating progress via PATCH /progress/{id}. Used when marking complete."""
    status: Optional[str] = Field(pattern='^(not_started|in_progress|completed)$')
    completion_date: Optional[datetime]
    time_spent_minutes: Optional[int] = Field(ge=0)

class ProgressResponse(ProgressBase, UUIDModel, TimestampedModel):
    """Schema for progress responses via GET /progress."""
    pass

# List Response Schemas
class CourseListResponse(BaseModel):
    """
    Paginated response schema for course listings.

    Attributes:
        items: List of course objects matching query/filters
        total: Total count of courses (before pagination)

    Business Context:
        Pagination improves performance for large course catalogs. Total count enables
        UI pagination controls (page 1 of N).
    """
    items: List[CourseResponse]
    total: int

class CourseModuleListResponse(BaseModel):
    """Paginated response schema for module listings within a course."""
    items: List[CourseModuleResponse]
    total: int

class CourseLessonListResponse(BaseModel):
    """Paginated response schema for lesson listings within a module."""
    items: List[CourseLessonResponse]
    total: int

class EnrollmentListResponse(BaseModel):
    """Paginated response schema for student enrollment listings."""
    items: List[EnrollmentResponse]
    total: int

class ProgressListResponse(BaseModel):
    """Paginated response schema for progress tracking records."""
    items: List[ProgressResponse]
    total: int