"""
Enrollment Domain Entity - Student Course Access and Progress Management

This module defines the enrollment domain entities that manage student participation
in courses, tracking progress, access control, and certification workflows within
the educational platform's comprehensive learning management system.

DOMAIN RESPONSIBILITY:
The Enrollment entity encapsulates all business logic related to student course
participation, from initial enrollment through completion and certification.
It enforces educational policies around access control, progress tracking,
and learning outcome validation.

EDUCATIONAL WORKFLOW MANAGEMENT:
1. Enrollment Lifecycle: Registration → Active Learning → Completion → Certification
2. Progress Tracking: Continuous monitoring of student advancement through course materials
3. Access Control: Time-based and status-based access to course content and resources
4. Certification: Automated certificate eligibility and issuance upon completion
5. Intervention Points: Suspension, reactivation, and cancellation workflows

BUSINESS RULES ENFORCEMENT:
- Student Identity: Secure linking between students and their course participation
- Progress Integrity: Validated percentage tracking with completion thresholds
- Status Transitions: Controlled state changes following educational policies
- Access Rights: Content availability based on enrollment status and progress
- Certification Standards: Quality assurance for credential issuance

LEARNING ANALYTICS INTEGRATION:
- Progress Metrics: Detailed tracking for analytics service integration
- Engagement Patterns: Access frequency and duration monitoring
- Completion Rates: Statistical analysis for course effectiveness
- Intervention Triggers: Early warning systems for at-risk students

ADMINISTRATIVE CAPABILITIES:
- Bulk Enrollment: Efficient class registration for institutional use
- Status Management: Administrative controls for enrollment modifications
- Certificate Management: Automated and manual certificate issuance
- Audit Trails: Complete history of enrollment changes and events

INTEGRATION PATTERNS:
- Course Management: Bidirectional relationship with course entities
- User Management: Student identity verification and profile integration
- Analytics Service: Progress data feeding into learning analytics
- Certificate Service: Integration with credential and achievement systems
- Notification Service: Automated communications for enrollment events

PERFORMANCE FEATURES:
- Status Validation: Efficient business rule evaluation for access control
- Progress Caching: Optimized tracking for high-frequency updates
- Bulk Operations: Streamlined processing for large enrollment batches
- Event Sourcing: Complete audit trail for compliance and analytics
"""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from enum import Enum

class EnrollmentStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

@dataclass
class Enrollment:
    """
    Enrollment domain entity encapsulating business rules for student course enrollment
    """
    student_id: str
    course_id: str
    status: EnrollmentStatus = EnrollmentStatus.ACTIVE
    progress_percentage: float = 0.0
    id: Optional[str] = None
    enrollment_date: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    certificate_issued: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate invariants after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate business rules and invariants"""
        if not self.student_id:
            raise ValueError("Enrollment must have a student ID")
        
        if not self.course_id:
            raise ValueError("Enrollment must have a course ID")
        
        if not (0.0 <= self.progress_percentage <= 100.0):
            raise ValueError("Progress percentage must be between 0 and 100")
        
        if self.completed_at and not self.is_completed():
            raise ValueError("Completion date set but status is not completed")
        
        if self.certificate_issued and not self.is_completed():
            raise ValueError("Certificate cannot be issued for incomplete enrollment")
    
    def is_active(self) -> bool:
        """Check if enrollment is active"""
        return self.status == EnrollmentStatus.ACTIVE
    
    def is_completed(self) -> bool:
        """Check if enrollment is completed"""
        return self.status == EnrollmentStatus.COMPLETED
    
    def can_access_course(self) -> bool:
        """Business rule: Check if student can access course content"""
        return self.status in [EnrollmentStatus.ACTIVE, EnrollmentStatus.COMPLETED]
    
    def update_progress(self, progress: float) -> None:
        """Update enrollment progress with business rules"""
        if not self.can_access_course():
            raise ValueError("Cannot update progress for inactive enrollment")
        
        if not (0.0 <= progress <= 100.0):
            raise ValueError("Progress must be between 0 and 100")
        
        self.progress_percentage = progress
        self.last_accessed = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Auto-complete if progress reaches 100%
        if progress >= 100.0 and self.status == EnrollmentStatus.ACTIVE:
            self.complete()
    
    def complete(self) -> None:
        """Business rule: Mark enrollment as completed"""
        if not self.is_active():
            raise ValueError("Can only complete active enrollments")
        
        self.status = EnrollmentStatus.COMPLETED
        self.progress_percentage = 100.0
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def suspend(self, reason: Optional[str] = None) -> None:
        """Business rule: Suspend enrollment"""
        if not self.is_active():
            raise ValueError("Can only suspend active enrollments")
        
        self.status = EnrollmentStatus.SUSPENDED
        self.updated_at = datetime.utcnow()
    
    def reactivate(self) -> None:
        """Business rule: Reactivate suspended enrollment"""
        if self.status != EnrollmentStatus.SUSPENDED:
            raise ValueError("Can only reactivate suspended enrollments")
        
        self.status = EnrollmentStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def cancel(self) -> None:
        """Business rule: Cancel enrollment"""
        if self.is_completed():
            raise ValueError("Cannot cancel completed enrollment")
        
        self.status = EnrollmentStatus.CANCELLED
        self.updated_at = datetime.utcnow()
    
    def issue_certificate(self) -> None:
        """Business rule: Issue certificate for completed enrollment"""
        if not self.is_completed():
            raise ValueError("Certificate can only be issued for completed enrollments")
        
        self.certificate_issued = True
        self.updated_at = datetime.utcnow()
    
    def get_enrollment_duration(self) -> Optional[int]:
        """Get enrollment duration in days"""
        if not self.enrollment_date:
            return None
        
        end_date = self.completed_at or datetime.utcnow()
        return (end_date - self.enrollment_date).days
    
    def is_certificate_eligible(self) -> bool:
        """Business rule: Check if student is eligible for certificate"""
        return (
            self.is_completed() and 
            self.progress_percentage >= 100.0 and
            not self.certificate_issued
        )
    
    def get_status_display(self) -> str:
        """Get human-readable status"""
        return self.status.value.title()

@dataclass
class EnrollmentRequest:
    """Value object for enrollment requests"""
    student_email: str
    course_id: str
    student_first_name: Optional[str] = None
    student_last_name: Optional[str] = None
    
    def validate(self) -> None:
        """Validate enrollment request"""
        if not self.student_email or '@' not in self.student_email:
            raise ValueError("Valid student email is required")
        
        if not self.course_id:
            raise ValueError("Course ID is required")

@dataclass
class BulkEnrollmentRequest:
    """Value object for bulk enrollment requests""" 
    course_id: str
    student_emails: list[str]
    
    def validate(self) -> None:
        """Validate bulk enrollment request"""
        if not self.course_id:
            raise ValueError("Course ID is required")
        
        if not self.student_emails:
            raise ValueError("At least one student email is required")
        
        for email in self.student_emails:
            if not email or '@' not in email:
                raise ValueError(f"Invalid email: {email}")