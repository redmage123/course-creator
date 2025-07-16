"""
Course Generator Repositories Module

This module contains all data access repositories for the course generation system.
Repositories handle database operations and data persistence following the 
Repository pattern for clean architecture.
"""

from .base_repository import BaseRepository
from .syllabus_repository import SyllabusRepository
from .slide_repository import SlideRepository
from .quiz_repository import QuizRepository
from .lab_repository import LabRepository
from .course_repository import CourseRepository

__all__ = [
    "BaseRepository",
    "SyllabusRepository",
    "SlideRepository", 
    "QuizRepository",
    "LabRepository",
    "CourseRepository"
]