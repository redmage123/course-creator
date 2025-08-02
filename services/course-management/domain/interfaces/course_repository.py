"""
Course Repository Interface
Single Responsibility: Define data access operations for courses
Dependency Inversion: Abstract interface for data persistence
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from domain.entities.course import Course, CourseStatistics

class ICourseRepository(ABC):
    """Interface for course data access operations"""

    @abstractmethod
    async def create(self, course: Course) -> Course:
        """Create a new course in the data store"""
        pass

    @abstractmethod
    async def get_by_id(self, course_id: str) -> Optional[Course]:
        """Get course by ID from the data store"""
        pass

    @abstractmethod
    async def get_by_instructor_id(self, instructor_id: str) -> List[Course]:
        """Get all courses for an instructor"""
        pass

    @abstractmethod
    async def get_published_courses(self, limit: int = 50, offset: int = 0) -> List[Course]:
        """Get paginated list of published courses"""
        pass

    @abstractmethod
    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Course]:
        """Search courses by query and optional filters"""
        pass

    @abstractmethod
    async def update(self, course: Course) -> Course:
        """Update an existing course"""
        pass

    @abstractmethod
    async def delete(self, course_id: str) -> bool:
        """Delete a course from the data store"""
        pass

    @abstractmethod
    async def exists(self, course_id: str) -> bool:
        """Check if course exists"""
        pass

    @abstractmethod
    async def count_by_instructor(self, instructor_id: str) -> int:
        """Count courses by instructor"""
        pass

    @abstractmethod
    async def get_statistics(self, course_id: str) -> Optional[CourseStatistics]:
        """Get course statistics"""
        pass

    @abstractmethod
    async def get_courses_by_category(self, category: str) -> List[Course]:
        """Get courses by category"""
        pass

    @abstractmethod
    async def get_courses_by_difficulty(self, difficulty: str) -> List[Course]:
        """Get courses by difficulty level"""
        pass