"""
Course Management Models

Pydantic models for course management operations.
"""

from .course import Course, CourseCreate, CourseUpdate, CourseBase, CourseResponse
from .enrollment import Enrollment, EnrollmentCreate, EnrollmentUpdate, EnrollmentRequest, StudentRegistrationRequest
from .progress import Progress, ProgressUpdate, ProgressResponse
from .common import BaseModel, PaginatedResponse

__all__ = [
    "Course",
    "CourseCreate",
    "CourseUpdate",
    "CourseBase",
    "CourseResponse",
    "Enrollment",
    "EnrollmentCreate",
    "EnrollmentUpdate",
    "EnrollmentRequest",
    "StudentRegistrationRequest",
    "Progress",
    "ProgressUpdate",
    "ProgressResponse",
    "BaseModel",
    "PaginatedResponse"
]