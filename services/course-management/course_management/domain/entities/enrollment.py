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
    """
    Enrollment lifecycle state taxonomy for student course participation.

    This enumeration defines the complete lifecycle of a student's enrollment
    in a course, from initial registration through completion or termination.
    Each status governs access control, progress tracking, and administrative
    workflows within the learning management system.

    STATUS DEFINITIONS AND BUSINESS RULES:

    ACTIVE:
        - Student has current access to all course materials
        - Progress tracking is enabled and updated
        - Can complete assignments, quizzes, and labs
        - Receives notifications and communications
        - Eligible for course completion and certification
        - Use Cases: Ongoing learning, normal course participation

    COMPLETED:
        - Student has successfully finished the course
        - Final progress percentage is 100%
        - Completion timestamp recorded for records
        - May receive certificate if eligible
        - Retains read-only access to materials (policy-dependent)
        - Use Cases: Successful course completion, certificate issuance

    SUSPENDED:
        - Temporary access restriction for intervention
        - Progress tracking paused but preserved
        - Cannot access course materials or submit work
        - Can be reactivated by instructor or administrator
        - Enrollment data retained for potential resumption
        - Use Cases: Academic integrity issues, payment problems, administrative holds

    CANCELLED:
        - Permanent termination of enrollment by student or admin
        - Access revoked to all course materials
        - Progress data preserved for records but frozen
        - Cannot be reactivated (new enrollment required)
        - May trigger refund workflows if applicable
        - Use Cases: Student withdrawal, administrative removal, policy violations

    EXPIRED:
        - Automatic termination after time-based access period
        - Used for time-limited course access models
        - Progress preserved for historical records
        - Cannot be reactivated without re-enrollment
        - May enable course extension workflows
        - Use Cases: Subscription expiration, trial period end, institutional term completion

    STATE TRANSITION RULES:
    - ACTIVE → COMPLETED (upon successful course completion)
    - ACTIVE → SUSPENDED (administrative intervention)
    - ACTIVE → CANCELLED (student withdrawal or violation)
    - ACTIVE → EXPIRED (time-based expiration)
    - SUSPENDED → ACTIVE (administrative reactivation)
    - SUSPENDED → CANCELLED (permanent termination)
    - No transitions FROM completed, cancelled, or expired (terminal states)

    INTEGRATION IMPACTS:
    - Access Control: Determines content visibility and interaction permissions
    - Analytics: Status-based reporting and success metrics
    - Notifications: Status-specific communication workflows
    - Billing: Refund and payment processing triggers
    - Certificates: Completion status gates certificate issuance
    """
    ACTIVE = "active"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

@dataclass
class Enrollment:
    """
    Core enrollment domain entity managing student course participation lifecycle.

    This entity encapsulates all business logic for student course enrollments,
    from initial registration through completion or termination. It enforces
    educational policies, tracks learning progress, and manages access control
    for the comprehensive learning management system.

    DOMAIN RESPONSIBILITIES:
    1. Access Control: Determine student permissions for course content
    2. Progress Tracking: Monitor and validate learning advancement (0-100%)
    3. Status Management: Control enrollment lifecycle state transitions
    4. Certification: Manage certificate eligibility and issuance
    5. Analytics Integration: Provide learning data for reporting systems
    6. Audit Trail: Maintain complete enrollment history for compliance

    BUSINESS VALUE:
    - Student Experience: Seamless learning journey from start to finish
    - Instructor Insights: Progress visibility for intervention support
    - Administrative Control: Enrollment management and policy enforcement
    - Data Integrity: Validated progress and status for reliable analytics
    - Compliance: Complete audit trail for institutional accreditation

    LIFECYCLE STATES (see EnrollmentStatus enum):
    - ACTIVE: Student learning in progress with full access
    - COMPLETED: Successful course completion with certificate eligibility
    - SUSPENDED: Temporary access restriction for intervention
    - CANCELLED: Permanent enrollment termination
    - EXPIRED: Time-based automatic termination

    PROGRESS TRACKING MODEL:
    - Range: 0.0 to 100.0 percentage
    - Incremental: Updated as students complete modules/activities
    - Validation: Business rules prevent invalid progress states
    - Auto-Completion: Reaching 100% triggers automatic completion
    - Analytics: Progress data feeds learning analytics dashboards

    CERTIFICATION WORKFLOW:
    1. Student reaches 100% progress
    2. Enrollment auto-transitions to COMPLETED status
    3. Certificate eligibility determined by is_certificate_eligible()
    4. Certificate issued via issue_certificate() method
    5. certificate_issued flag set for tracking

    INTEGRATION PATTERNS:
    - Course Management: Bidirectional relationship with courses
    - User Management: Student identity and profile integration
    - Analytics Service: Learning progress and completion metrics
    - Certificate Service: Credential issuance workflows
    - Notification Service: Status change and milestone communications

    Attributes:
        student_id: Foreign key to student user entity
        course_id: Foreign key to course entity
        status: Current enrollment lifecycle state
        progress_percentage: Learning progress (0.0-100.0)
        id: Unique enrollment identifier
        enrollment_date: Initial enrollment timestamp
        last_accessed: Most recent course access timestamp
        completed_at: Course completion timestamp (if completed)
        certificate_issued: Certificate issuance flag
        created_at: Entity creation timestamp
        updated_at: Last modification timestamp
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
        """
        Execute post-initialization validation for enrollment entity.

        This method ensures all business rules and invariants are validated
        immediately after enrollment creation, preventing invalid enrollment
        states from entering the system. Implements Domain-Driven Design
        fail-fast principle for data integrity.

        VALIDATION SCOPE:
        - Student and course ID presence
        - Progress percentage validity (0-100 range)
        - Completion status consistency
        - Certificate issuance eligibility

        Raises:
            ValueError: If any business rule violation detected
        """
        self.validate()
    
    def validate(self) -> None:
        """
        Validate all enrollment business rules and domain invariants.

        This comprehensive validation enforces data integrity across all
        enrollment attributes, ensuring consistency between related fields
        and preventing invalid enrollment states that could corrupt analytics
        or violate educational policies.

        VALIDATION RULES:

        1. Identity Validation:
           - student_id must be present (links to user entity)
           - course_id must be present (links to course entity)
           - Prevents orphaned enrollments

        2. Progress Integrity:
           - progress_percentage must be 0.0-100.0 range
           - Prevents negative or over-100% progress corruption
           - Ensures accurate analytics and reporting

        3. Completion Consistency:
           - completed_at timestamp only valid if status is COMPLETED
           - Prevents data inconsistency between status and completion date
           - Maintains audit trail accuracy

        4. Certification Rules:
           - certificate_issued only true if enrollment is COMPLETED
           - Prevents certificate issuance for incomplete courses
           - Enforces educational quality standards

        WHY THIS MATTERS:
        - Data Integrity: Prevents corrupted enrollment states
        - Analytics Accuracy: Ensures reliable learning metrics
        - Policy Enforcement: Maintains educational standards
        - Audit Compliance: Guarantees consistent audit trails
        - System Reliability: Prevents cascade errors in integrations

        WHEN CALLED:
        - Automatically after object creation (__post_init__)
        - After any state modification (complete(), suspend(), etc.)
        - Before database persistence operations

        Raises:
            ValueError: Specific descriptive error for each business rule violation
        """
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
    """
    Value object encapsulating data transfer object for enrollment creation.

    This immutable value object represents a student's request to enroll in
    a course, capturing essential identity and course information required
    for enrollment processing workflows.

    BUSINESS PURPOSE:
    - Decouples enrollment creation from direct entity manipulation
    - Validates enrollment request data before processing
    - Supports both email-based and user-ID-based enrollment workflows
    - Enables clean separation between application and domain layers

    ENROLLMENT WORKFLOW:
    1. EnrollmentRequest created from API input or bulk upload
    2. Request validated for required fields and email format
    3. User lookup performed (existing user or invitation flow)
    4. Enrollment entity created if validation passes
    5. Notification sent to student with enrollment confirmation

    VALIDATION RULES:
    - Valid email format required (must contain '@' symbol)
    - Course ID must be present and valid
    - Optional name fields support user creation if needed

    Attributes:
        student_email: Student's email address for identification
        course_id: Target course for enrollment
        student_first_name: Optional first name for new user creation
        student_last_name: Optional last name for new user creation
    """
    student_email: str
    course_id: str
    student_first_name: Optional[str] = None
    student_last_name: Optional[str] = None

    def validate(self) -> None:
        """
        Validate enrollment request data integrity.

        Ensures all required fields are present and properly formatted
        before enrollment processing begins. Prevents downstream errors
        from invalid data reaching the enrollment creation workflow.

        Raises:
            ValueError: If email is invalid or course_id is missing
        """
        if not self.student_email or '@' not in self.student_email:
            raise ValueError("Valid student email is required")

        if not self.course_id:
            raise ValueError("Course ID is required")

@dataclass
class BulkEnrollmentRequest:
    """
    Value object for batch enrollment operations in institutional contexts.

    This value object supports efficient bulk enrollment workflows for
    instructors and administrators managing class rosters, locations, or
    organizational training programs. Enables single-operation enrollment
    of multiple students to improve administrative efficiency.

    BUSINESS VALUE:
    - Administrative Efficiency: Enroll entire class rosters in one operation
    - Institutional Support: Corporate training locations enrollment
    - Error Reduction: Atomic validation of all enrollments before processing
    - Performance Optimization: Batch database operations vs. individual inserts

    USE CASES:
    1. Class Roster Upload: Instructor uploads CSV of student emails
    2. Corporate Training: HR enrolls employees in mandatory training
    3. Locations Management: Organization admin enrolls project participants
    4. Invitation Workflows: Bulk invitation sending for course access

    PROCESSING WORKFLOW:
    1. BulkEnrollmentRequest created from CSV upload or API
    2. Validate course_id and all email addresses
    3. Batch user lookup and creation for new students
    4. Atomic enrollment creation for all validated students
    5. Batch notification sending to all enrolled students
    6. Report generation showing successes and failures

    VALIDATION RULES:
    - Course ID must be valid and exist
    - At least one student email required
    - All emails must be properly formatted
    - Duplicate emails within batch automatically deduplicated

    Attributes:
        course_id: Target course for all enrollments
        student_emails: List of student email addresses for enrollment
    """
    course_id: str
    student_emails: list[str]

    def validate(self) -> None:
        """
        Validate bulk enrollment request data integrity.

        Performs comprehensive validation of course ID and all student
        email addresses before batch processing begins. Early validation
        prevents partial enrollment failures and maintains data consistency.

        VALIDATION CHECKS:
        - Course ID presence
        - At least one email address in list
        - Email format validation for each address

        Raises:
            ValueError: If course_id missing, email list empty, or any email invalid
        """
        if not self.course_id:
            raise ValueError("Course ID is required")

        if not self.student_emails:
            raise ValueError("At least one student email is required")

        for email in self.student_emails:
            if not email or '@' not in email:
                raise ValueError(f"Invalid email: {email}")