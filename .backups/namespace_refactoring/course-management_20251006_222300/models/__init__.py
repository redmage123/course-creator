"""
Course Management Models

Pydantic models for course management operations.
"""

from models.course import Course, CourseCreate, CourseUpdate, CourseBase, CourseResponse
from models.enrollment import Enrollment, EnrollmentCreate, EnrollmentUpdate, EnrollmentRequest, StudentRegistrationRequest
from models.progress import Progress, ProgressUpdate, ProgressResponse
from models.common import BaseModel, PaginatedResponse

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