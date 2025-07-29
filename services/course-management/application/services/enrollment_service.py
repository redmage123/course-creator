"""
Enrollment Service Implementation
Single Responsibility: Implement enrollment management business logic
Dependency Inversion: Depends on repository abstractions, not concrete implementations
"""
import uuid
from datetime import datetime
from typing import List, Optional
from ...domain.entities.enrollment import Enrollment, EnrollmentRequest, BulkEnrollmentRequest, EnrollmentStatus
from ...domain.interfaces.enrollment_repository import IEnrollmentRepository
from ...domain.interfaces.enrollment_service import IEnrollmentService
from ...domain.interfaces.course_repository import ICourseRepository

class EnrollmentService(IEnrollmentService):
    """
    Enrollment service implementation with business logic
    """
    
    def __init__(self, enrollment_repository: IEnrollmentRepository, course_repository: ICourseRepository):
        self._enrollment_repository = enrollment_repository
        self._course_repository = course_repository
    
    async def enroll_student(self, enrollment_request: EnrollmentRequest) -> Enrollment:
        """Enroll a single student in a course with business validation"""
        # Validate request
        enrollment_request.validate()
        
        # Check if course exists and is published
        course = await self._course_repository.get_by_id(enrollment_request.course_id)
        if not course:
            raise ValueError(f"Course with ID {enrollment_request.course_id} not found")
        
        if not course.is_published:
            raise ValueError("Cannot enroll in unpublished course")
        
        # For now, we'll assume we have the student_id from the email
        # In a real implementation, this would involve user service integration
        student_id = self._get_student_id_from_email(enrollment_request.student_email)
        
        # Check if student is already enrolled
        existing_enrollment = await self._enrollment_repository.get_by_student_and_course(
            student_id, enrollment_request.course_id
        )
        if existing_enrollment and existing_enrollment.can_access_course():
            raise ValueError("Student is already enrolled in this course")
        
        # Create enrollment
        enrollment = Enrollment(
            id=str(uuid.uuid4()),
            student_id=student_id,
            course_id=enrollment_request.course_id,
            enrollment_date=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return await self._enrollment_repository.create(enrollment)
    
    async def bulk_enroll_students(self, bulk_request: BulkEnrollmentRequest) -> List[Enrollment]:
        """Enroll multiple students in a course"""
        # Validate request
        bulk_request.validate()
        
        # Check if course exists and is published
        course = await self._course_repository.get_by_id(bulk_request.course_id)
        if not course:
            raise ValueError(f"Course with ID {bulk_request.course_id} not found")
        
        if not course.is_published:
            raise ValueError("Cannot enroll in unpublished course")
        
        enrollments = []
        for email in bulk_request.student_emails:
            try:
                # Create individual enrollment request
                enrollment_request = EnrollmentRequest(
                    student_email=email,
                    course_id=bulk_request.course_id
                )
                
                enrollment = await self.enroll_student(enrollment_request)
                enrollments.append(enrollment)
                
            except ValueError as e:
                # Skip students who are already enrolled or have invalid data
                # In a real implementation, you might want to collect these errors
                continue
        
        return enrollments
    
    async def get_enrollment_by_id(self, enrollment_id: str) -> Optional[Enrollment]:
        """Get enrollment by ID"""
        if not enrollment_id:
            return None
        
        return await self._enrollment_repository.get_by_id(enrollment_id)
    
    async def get_student_enrollments(self, student_id: str) -> List[Enrollment]:
        """Get all enrollments for a student"""
        if not student_id:
            return []
        
        return await self._enrollment_repository.get_by_student_id(student_id)
    
    async def get_course_enrollments(self, course_id: str) -> List[Enrollment]:
        """Get all enrollments for a course"""
        if not course_id:
            return []
        
        return await self._enrollment_repository.get_by_course_id(course_id)
    
    async def get_instructor_enrollments(self, instructor_id: str) -> List[Enrollment]:
        """Get all enrollments for courses taught by an instructor"""
        if not instructor_id:
            return []
        
        return await self._enrollment_repository.get_by_instructor_id(instructor_id)
    
    async def update_progress(self, enrollment_id: str, progress: float) -> Enrollment:
        """Update student progress in a course"""
        if not enrollment_id:
            raise ValueError("Enrollment ID is required")
        
        # Get enrollment
        enrollment = await self._enrollment_repository.get_by_id(enrollment_id)
        if not enrollment:
            raise ValueError(f"Enrollment with ID {enrollment_id} not found")
        
        # Use business logic from entity
        enrollment.update_progress(progress)
        
        return await self._enrollment_repository.update(enrollment)
    
    async def complete_enrollment(self, enrollment_id: str) -> Enrollment:
        """Mark enrollment as completed"""
        if not enrollment_id:
            raise ValueError("Enrollment ID is required")
        
        # Get enrollment
        enrollment = await self._enrollment_repository.get_by_id(enrollment_id)
        if not enrollment:
            raise ValueError(f"Enrollment with ID {enrollment_id} not found")
        
        # Use business logic from entity
        enrollment.complete()
        
        return await self._enrollment_repository.update(enrollment)
    
    async def suspend_enrollment(self, enrollment_id: str, reason: Optional[str] = None) -> Enrollment:
        """Suspend an enrollment"""
        if not enrollment_id:
            raise ValueError("Enrollment ID is required")
        
        # Get enrollment
        enrollment = await self._enrollment_repository.get_by_id(enrollment_id)
        if not enrollment:
            raise ValueError(f"Enrollment with ID {enrollment_id} not found")
        
        # Use business logic from entity
        enrollment.suspend(reason)
        
        return await self._enrollment_repository.update(enrollment)
    
    async def reactivate_enrollment(self, enrollment_id: str) -> Enrollment:
        """Reactivate a suspended enrollment"""
        if not enrollment_id:
            raise ValueError("Enrollment ID is required")
        
        # Get enrollment
        enrollment = await self._enrollment_repository.get_by_id(enrollment_id)
        if not enrollment:
            raise ValueError(f"Enrollment with ID {enrollment_id} not found")
        
        # Use business logic from entity
        enrollment.reactivate()
        
        return await self._enrollment_repository.update(enrollment)
    
    async def cancel_enrollment(self, enrollment_id: str) -> Enrollment:
        """Cancel an enrollment"""
        if not enrollment_id:
            raise ValueError("Enrollment ID is required")
        
        # Get enrollment
        enrollment = await self._enrollment_repository.get_by_id(enrollment_id)
        if not enrollment:
            raise ValueError(f"Enrollment with ID {enrollment_id} not found")
        
        # Use business logic from entity
        enrollment.cancel()
        
        return await self._enrollment_repository.update(enrollment)
    
    async def issue_certificate(self, enrollment_id: str) -> Enrollment:
        """Issue certificate for completed enrollment"""
        if not enrollment_id:
            raise ValueError("Enrollment ID is required")
        
        # Get enrollment
        enrollment = await self._enrollment_repository.get_by_id(enrollment_id)
        if not enrollment:
            raise ValueError(f"Enrollment with ID {enrollment_id} not found")
        
        # Check eligibility
        if not enrollment.is_certificate_eligible():
            raise ValueError("Student is not eligible for certificate")
        
        # Use business logic from entity
        enrollment.issue_certificate()
        
        return await self._enrollment_repository.update(enrollment)
    
    async def check_enrollment_exists(self, student_id: str, course_id: str) -> bool:
        """Check if student is already enrolled in course"""
        if not student_id or not course_id:
            return False
        
        return await self._enrollment_repository.exists(student_id, course_id)
    
    # Additional business methods
    async def get_active_enrollments(self, student_id: str) -> List[Enrollment]:
        """Get active enrollments for a student"""
        enrollments = await self.get_student_enrollments(student_id)
        return [e for e in enrollments if e.is_active()]
    
    async def get_completed_enrollments(self, student_id: str) -> List[Enrollment]:
        """Get completed enrollments for a student"""
        enrollments = await self.get_student_enrollments(student_id)
        return [e for e in enrollments if e.is_completed()]
    
    async def get_course_completion_rate(self, course_id: str) -> float:
        """Get completion rate for a course"""
        return await self._enrollment_repository.get_completion_rate(course_id)
    
    async def get_enrollment_statistics(self, course_id: str) -> dict:
        """Get enrollment statistics for a course"""
        total = await self._enrollment_repository.count_by_course(course_id)
        active = await self._enrollment_repository.count_active_by_course(course_id)
        completed = await self._enrollment_repository.count_completed_by_course(course_id)
        completion_rate = await self._enrollment_repository.get_completion_rate(course_id)
        
        return {
            'total_enrollments': total,
            'active_enrollments': active,
            'completed_enrollments': completed,
            'completion_rate': completion_rate
        }
    
    def _get_student_id_from_email(self, email: str) -> str:
        """
        Helper method to get student ID from email
        In a real implementation, this would integrate with the user service
        """
        # For now, return a mock ID based on email
        # This should be replaced with actual user service integration
        return f"student_{hash(email) % 10000}"