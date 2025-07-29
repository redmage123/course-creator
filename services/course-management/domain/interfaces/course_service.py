"""
Course Service Interface
Single Responsibility: Define course management operations
Interface Segregation: Focused interface for course operations only
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.course import Course, CourseStatistics

class ICourseService(ABC):
    """Interface for course management operations"""

    @abstractmethod
    async def create_course(self, course: Course) -> Course:
        """Create a new course"""
        pass

    @abstractmethod
    async def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """Get course by ID"""
        pass

    @abstractmethod
    async def get_courses_by_instructor(self, instructor_id: str) -> List[Course]:
        """Get all courses for an instructor"""
        pass

    @abstractmethod
    async def update_course(self, course: Course) -> Course:
        """Update an existing course"""
        pass

    @abstractmethod
    async def delete_course(self, course_id: str, instructor_id: str) -> bool:
        """Delete a course (only if instructor owns it)"""
        pass

    @abstractmethod
    async def publish_course(self, course_id: str, instructor_id: str) -> Course:
        """Publish a course"""
        pass

    @abstractmethod
    async def unpublish_course(self, course_id: str, instructor_id: str) -> Course:
        """Unpublish a course"""
        pass

    @abstractmethod
    async def get_published_courses(self, limit: int = 50, offset: int = 0) -> List[Course]:
        """Get all published courses"""
        pass

    @abstractmethod
    async def search_courses(self, query: str, category: Optional[str] = None, 
                            difficulty: Optional[str] = None) -> List[Course]:
        """Search courses by criteria"""
        pass

    @abstractmethod
    async def get_course_statistics(self, course_id: str) -> Optional[CourseStatistics]:
        """Get statistics for a course"""
        pass