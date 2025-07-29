"""
Enrollment Service Interface
Single Responsibility: Define enrollment management operations
Interface Segregation: Focused interface for enrollment operations only
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.enrollment import Enrollment, EnrollmentRequest, BulkEnrollmentRequest

class IEnrollmentService(ABC):
    """Interface for enrollment management operations"""

    @abstractmethod
    async def enroll_student(self, enrollment_request: EnrollmentRequest) -> Enrollment:
        """Enroll a single student in a course"""
        pass

    @abstractmethod
    async def bulk_enroll_students(self, bulk_request: BulkEnrollmentRequest) -> List[Enrollment]:
        """Enroll multiple students in a course"""
        pass

    @abstractmethod
    async def get_enrollment_by_id(self, enrollment_id: str) -> Optional[Enrollment]:
        """Get enrollment by ID"""
        pass

    @abstractmethod
    async def get_student_enrollments(self, student_id: str) -> List[Enrollment]:
        """Get all enrollments for a student"""
        pass

    @abstractmethod
    async def get_course_enrollments(self, course_id: str) -> List[Enrollment]:
        """Get all enrollments for a course"""
        pass

    @abstractmethod
    async def get_instructor_enrollments(self, instructor_id: str) -> List[Enrollment]:
        """Get all enrollments for courses taught by an instructor"""
        pass

    @abstractmethod
    async def update_progress(self, enrollment_id: str, progress: float) -> Enrollment:
        """Update student progress in a course"""
        pass

    @abstractmethod
    async def complete_enrollment(self, enrollment_id: str) -> Enrollment:
        """Mark enrollment as completed"""
        pass

    @abstractmethod
    async def suspend_enrollment(self, enrollment_id: str, reason: Optional[str] = None) -> Enrollment:
        """Suspend an enrollment"""
        pass

    @abstractmethod
    async def reactivate_enrollment(self, enrollment_id: str) -> Enrollment:
        """Reactivate a suspended enrollment"""
        pass

    @abstractmethod
    async def cancel_enrollment(self, enrollment_id: str) -> Enrollment:
        """Cancel an enrollment"""
        pass

    @abstractmethod
    async def issue_certificate(self, enrollment_id: str) -> Enrollment:
        """Issue certificate for completed enrollment"""
        pass

    @abstractmethod
    async def check_enrollment_exists(self, student_id: str, course_id: str) -> bool:
        """Check if student is already enrolled in course"""
        pass