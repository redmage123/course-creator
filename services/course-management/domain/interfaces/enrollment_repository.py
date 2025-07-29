"""
Enrollment Repository Interface
Single Responsibility: Define data access operations for enrollments
Dependency Inversion: Abstract interface for data persistence
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..entities.enrollment import Enrollment, EnrollmentStatus

class IEnrollmentRepository(ABC):
    """Interface for enrollment data access operations"""

    @abstractmethod
    async def create(self, enrollment: Enrollment) -> Enrollment:
        """Create a new enrollment in the data store"""
        pass

    @abstractmethod
    async def get_by_id(self, enrollment_id: str) -> Optional[Enrollment]:
        """Get enrollment by ID from the data store"""
        pass

    @abstractmethod
    async def get_by_student_and_course(self, student_id: str, course_id: str) -> Optional[Enrollment]:
        """Get enrollment by student and course IDs"""
        pass

    @abstractmethod
    async def get_by_student_id(self, student_id: str) -> List[Enrollment]:
        """Get all enrollments for a student"""
        pass

    @abstractmethod
    async def get_by_course_id(self, course_id: str) -> List[Enrollment]:
        """Get all enrollments for a course"""
        pass

    @abstractmethod
    async def get_by_instructor_id(self, instructor_id: str) -> List[Enrollment]:
        """Get all enrollments for courses taught by an instructor"""
        pass

    @abstractmethod
    async def get_by_status(self, status: EnrollmentStatus) -> List[Enrollment]:
        """Get all enrollments with specific status"""
        pass

    @abstractmethod
    async def update(self, enrollment: Enrollment) -> Enrollment:
        """Update an existing enrollment"""
        pass

    @abstractmethod
    async def delete(self, enrollment_id: str) -> bool:
        """Delete an enrollment from the data store"""
        pass

    @abstractmethod
    async def exists(self, student_id: str, course_id: str) -> bool:
        """Check if enrollment exists for student and course"""
        pass

    @abstractmethod
    async def count_by_course(self, course_id: str) -> int:
        """Count enrollments for a course"""
        pass

    @abstractmethod
    async def count_active_by_course(self, course_id: str) -> int:
        """Count active enrollments for a course"""
        pass

    @abstractmethod
    async def count_completed_by_course(self, course_id: str) -> int:
        """Count completed enrollments for a course"""
        pass

    @abstractmethod
    async def get_completion_rate(self, course_id: str) -> float:
        """Get completion rate for a course"""
        pass

    @abstractmethod
    async def get_enrollments_by_date_range(self, start_date, end_date) -> List[Enrollment]:
        """Get enrollments within date range"""
        pass

    @abstractmethod
    async def get_recent_enrollments(self, limit: int = 10) -> List[Enrollment]:
        """Get most recent enrollments"""
        pass

    @abstractmethod
    async def bulk_create(self, enrollments: List[Enrollment]) -> List[Enrollment]:
        """Create multiple enrollments in a single operation"""
        pass