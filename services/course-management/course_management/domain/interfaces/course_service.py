"""
Course Service Interface
Single Responsibility: Define course management operations
Interface Segregation: Focused interface for course operations only
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from course_management.domain.entities.course import Course, CourseStatistics

class ICourseService(ABC):
    """Interface for course management operations"""

    @abstractmethod
    async def create_course(self, course: Course) -> Course:
        """Create a new course"""
        pass

    @abstractmethod
    async def get_course_by_id(self, course_id: str, organization_id: Optional[str] = None) -> Optional[Course]:
        """Get course by ID with optional organization filtering"""
        pass

    @abstractmethod
    async def get_courses_by_instructor(self, instructor_id: str, organization_id: Optional[str] = None) -> List[Course]:
        """Get all courses for an instructor within organization"""
        pass

    @abstractmethod
    async def update_course(self, course: Course) -> Course:
        """Update an existing course"""
        pass

    @abstractmethod
    async def delete_course(self, course_id: str, user_id: str, is_admin: bool = False) -> bool:
        """Delete a course (instructor owner or admin can delete)"""
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
    async def get_published_courses(self, limit: int = 50, offset: int = 0, organization_id: Optional[str] = None) -> List[Course]:
        """Get all published courses within organization"""
        pass

    @abstractmethod
    async def search_courses(self, query: str, category: Optional[str] = None, 
                            difficulty: Optional[str] = None, organization_id: Optional[str] = None) -> List[Course]:
        """Search courses by criteria within organization"""
        pass

    @abstractmethod
    async def get_course_statistics(self, course_id: str) -> Optional[CourseStatistics]:
        """Get statistics for a course"""
        pass