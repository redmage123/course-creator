from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, constr, validator

# Base Models
class TimestampedModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UUIDModel(BaseModel):
    id: UUID

# Course Schemas
class CourseBase(BaseModel):
    title: constr(min_length=1, max_length=255)
    description: str
    duration_hours: float = Field(gt=0)
    level: str = Field(pattern='^(beginner|intermediate|advanced)$')
    price: float = Field(ge=0)
    is_published: bool = False

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[constr(min_length=1, max_length=255)]
    description: Optional[str]
    duration_hours: Optional[float] = Field(gt=0)
    level: Optional[str] = Field(pattern='^(beginner|intermediate|advanced)$')
    price: Optional[float] = Field(ge=0)
    is_published: Optional[bool]

class CourseResponse(CourseBase, UUIDModel, TimestampedModel):
    pass

# Course Module Schemas
class CourseModuleBase(BaseModel):
    course_id: UUID
    title: constr(min_length=1, max_length=255)
    description: str
    order: int = Field(ge=0)

class CourseModuleCreate(CourseModuleBase):
    pass

class CourseModuleUpdate(BaseModel):
    title: Optional[constr(min_length=1, max_length=255)]
    description: Optional[str]
    order: Optional[int] = Field(ge=0)

class CourseModuleResponse(CourseModuleBase, UUIDModel, TimestampedModel):
    pass

# Course Lesson Schemas
class CourseLessonBase(BaseModel):
    module_id: UUID
    title: constr(min_length=1, max_length=255)
    content: str
    duration_minutes: int = Field(gt=0)
    order: int = Field(ge=0)

class CourseLessonCreate(CourseLessonBase):
    pass

class CourseLessonUpdate(BaseModel):
    title: Optional[constr(min_length=1, max_length=255)]
    content: Optional[str]
    duration_minutes: Optional[int] = Field(gt=0)
    order: Optional[int] = Field(ge=0)

class CourseLessonResponse(CourseLessonBase, UUIDModel, TimestampedModel):
    pass

# Enrollment Schemas
class EnrollmentBase(BaseModel):
    user_id: UUID
    course_id: UUID
    status: str = Field(pattern='^(active|completed|cancelled)$')
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)

class EnrollmentCreate(EnrollmentBase):
    pass

class EnrollmentUpdate(BaseModel):
    status: Optional[str] = Field(pattern='^(active|completed|cancelled)$')

class EnrollmentResponse(EnrollmentBase, UUIDModel, TimestampedModel):
    pass

# Progress Schemas
class ProgressBase(BaseModel):
    enrollment_id: UUID
    lesson_id: UUID
    status: str = Field(pattern='^(not_started|in_progress|completed)$')
    completion_date: Optional[datetime]
    time_spent_minutes: int = Field(ge=0)

class ProgressCreate(ProgressBase):
    pass

class ProgressUpdate(BaseModel):
    status: Optional[str] = Field(pattern='^(not_started|in_progress|completed)$')
    completion_date: Optional[datetime]
    time_spent_minutes: Optional[int] = Field(ge=0)

class ProgressResponse(ProgressBase, UUIDModel, TimestampedModel):
    pass

# List Response Schemas
class CourseListResponse(BaseModel):
    items: List[CourseResponse]
    total: int

class CourseModuleListResponse(BaseModel):
    items: List[CourseModuleResponse]
    total: int

class CourseLessonListResponse(BaseModel):
    items: List[CourseLessonResponse]
    total: int

class EnrollmentListResponse(BaseModel):
    items: List[EnrollmentResponse]
    total: int

class ProgressListResponse(BaseModel):
    items: List[ProgressResponse]
    total: int