"""
Custom Exceptions for Course Management Service

BUSINESS CONTEXT:
Provides specific exception types for different error scenarios in course
and sub-project management. Enables precise error handling and user-friendly
error messages.

@module exceptions
"""


class CourseManagementException(Exception):
    """Base exception for all course management errors"""
    pass


class NotFoundException(CourseManagementException):
    """Base exception for entities not found"""
    pass


class DuplicateException(CourseManagementException):
    """Base exception for duplicate entities"""
    pass


class ValidationException(CourseManagementException):
    """Base exception for validation errors"""
    pass


# Sub-Project Exceptions
class SubProjectNotFoundException(NotFoundException):
    """Raised when a sub-project cannot be found"""
    def __init__(self, sub_project_id: str):
        super().__init__(f"Sub-project not found: {sub_project_id}")
        self.sub_project_id = sub_project_id


class DuplicateSubProjectException(DuplicateException):
    """Raised when attempting to create a duplicate sub-project"""
    def __init__(self, slug: str):
        super().__init__(f"Sub-project with slug '{slug}' already exists")
        self.slug = slug


class InvalidLocationException(ValidationException):
    """Raised when locations data is invalid"""
    def __init__(self, message: str = "Invalid locations data"):
        super().__init__(message)


class InvalidDateRangeException(ValidationException):
    """Raised when date range is invalid (start > end)"""
    def __init__(self, start_date, end_date):
        super().__init__(f"Invalid date range: start_date ({start_date}) must be before end_date ({end_date})")
        self.start_date = start_date
        self.end_date = end_date


class SubProjectCapacityException(ValidationException):
    """Raised when sub-project is at capacity"""
    def __init__(self, current: int, max_capacity: int):
        super().__init__(f"Sub-project at capacity: {current}/{max_capacity}")
        self.current = current
        self.max_capacity = max_capacity


class InvalidStatusTransitionException(ValidationException):
    """Raised when status transition is invalid"""
    def __init__(self, from_status: str, to_status: str):
        super().__init__(f"Invalid status transition: {from_status} → {to_status}")
        self.from_status = from_status
        self.to_status = to_status


# Project Exceptions
class ProjectNotFoundException(NotFoundException):
    """Raised when a project cannot be found"""
    def __init__(self, project_id: str):
        super().__init__(f"Project not found: {project_id}")
        self.project_id = project_id


class DuplicateProjectException(DuplicateException):
    """Raised when attempting to create a duplicate project"""
    def __init__(self, slug: str):
        super().__init__(f"Project with slug '{slug}' already exists")
        self.slug = slug


# Course Exceptions
class CourseNotFoundException(NotFoundException):
    """Raised when a course cannot be found"""
    def __init__(self, course_id: str):
        super().__init__(f"Course not found: {course_id}")
        self.course_id = course_id


class DuplicateCourseException(DuplicateException):
    """Raised when attempting to create a duplicate course"""
    def __init__(self, slug: str):
        super().__init__(f"Course with slug '{slug}' already exists")
        self.slug = slug


# Database Exceptions
class DatabaseConnectionException(CourseManagementException):
    """Raised when database connection fails"""
    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message)


class DatabaseQueryException(CourseManagementException):
    """Raised when database query fails"""
    def __init__(self, query: str, error: str):
        super().__init__(f"Query failed: {error}")
        self.query = query
        self.error = error
