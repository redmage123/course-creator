"""
Course Generator Repositories Module

This module contains all data access repositories for the course generation system.
Repositories handle database operations and data persistence following the 
Repository pattern for clean architecture.
"""

from repositories.base_repository import BaseRepository
from repositories.syllabus_repository import SyllabusRepository
from repositories.slide_repository import SlideRepository
from repositories.quiz_repository import QuizRepository
from repositories.lab_repository import LabRepository
from repositories.course_repository import CourseRepository

__all__ = [
    "BaseRepository",
    "SyllabusRepository",
    "SlideRepository", 
    "QuizRepository",
    "LabRepository",
    "CourseRepository"
]