"""
Course Generator Models Package

Contains Pydantic models for syllabus generation requests and responses.
"""

from models.syllabus import (
    SyllabusRequest,
    SyllabusResponse,
    ContentSourceType,
    ExternalSourceConfig,
    CourseLevel,
)

__all__ = [
    'SyllabusRequest',
    'SyllabusResponse',
    'ContentSourceType',
    'ExternalSourceConfig',
    'CourseLevel',
]
