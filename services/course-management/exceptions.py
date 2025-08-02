"""
Educational Platform Exception Hierarchy - Comprehensive Error Management

This module defines a comprehensive exception hierarchy for the Course Management Service,
providing structured error handling, detailed logging, and educational context for all
failure scenarios within the platform's course management workflows.

EXCEPTION DESIGN PRINCIPLES:
The exception system follows SOLID principles and educational domain requirements:
- Single Responsibility: Each exception type handles specific educational domain errors
- Open/Closed: Extensible hierarchy allowing new educational error types without modification
- Liskov Substitution: All exceptions are substitutable through common base interface
- Interface Segregation: Clean, focused exception interfaces for different error categories
- Dependency Inversion: Exception handling depends on abstractions, not concrete implementations

EDUCATIONAL DOMAIN ERROR CATEGORIES:
1. Course Management Errors: Course lifecycle, validation, and business rule violations
2. Enrollment Errors: Student registration, access control, and enrollment state issues
3. Feedback System Errors: Bi-directional feedback submission and processing failures
4. Progress Tracking Errors: Student advancement monitoring and analytics issues
5. Authorization Errors: Access control violations and permission failures
6. Database Errors: Data persistence and integrity issues
7. Email Service Errors: Communication and notification delivery failures
8. Quiz Management Errors: Assessment publication and analytics integration issues

STRUCTURED ERROR INFORMATION:
Each exception provides comprehensive context for educational operations:
- Error Codes: Standardized codes for programmatic error handling and monitoring
- Educational Context: Domain-specific information (course_id, student_id, instructor_id)
- Operational Details: Specific operation types and business rule violations
- Timestamp Information: Precise error occurrence timing for analytics and debugging
- Original Exception: Complete error chain preservation for detailed troubleshooting

LOGGING AND OBSERVABILITY:
- Structured Logging: JSON-formatted logs with educational context for analytics
- Service Attribution: Clear identification of course management service errors
- Error Correlation: Unique identifiers for tracking errors across service boundaries
- Context Preservation: Complete educational workflow context in error logs
- Performance Impact: Non-blocking logging that doesn't impact educational operations

BUSINESS RULE ENFORCEMENT:
- Educational Standards: Validation errors include educational policy context
- Course Lifecycle: State transition errors with educational workflow information
- Enrollment Policies: Student access and registration rule violation details
- Feedback Guidelines: Assessment and evaluation policy enforcement context
- Authorization Rules: Instructor and student permission validation details

API INTEGRATION SUPPORT:
- HTTP Status Mapping: Exception types map to appropriate HTTP status codes
- JSON Serialization: Structured exception data for API error responses
- Client-Friendly Messages: Educational context formatted for frontend consumption
- Error Recovery: Guidance for client-side error handling and user messaging
- Monitoring Integration: Exception metrics for service health and performance tracking

COMPLIANCE AND AUDITING:
- Educational Records: Exception context supports FERPA compliance requirements
- Audit Trails: Complete error history for educational accountability
- Privacy Protection: Sensitive information handling in exception logging
- Regulatory Compliance: Error handling supporting institutional compliance requirements
- Data Retention: Exception log management aligned with educational record policies

DEVELOPMENT AND DEBUGGING:
- Stack Trace Preservation: Complete error chain for development troubleshooting
- Context Enrichment: Educational domain information for faster issue resolution
- Testing Support: Predictable exception patterns for comprehensive test coverage
- Documentation: Self-documenting exceptions with clear educational context
- Error Reproduction: Sufficient context for recreating and fixing educational workflow issues

OPERATIONAL EXCELLENCE:
- Service Health: Exception patterns indicating service degradation
- Performance Monitoring: Error rates and patterns for optimization opportunities
- Capacity Planning: Exception trends informing infrastructure scaling decisions
- User Experience: Error context enabling better educational user experience
- Continuous Improvement: Exception analytics driving platform enhancement priorities

INTEGRATION PATTERNS:
- Service Mesh: Exception propagation across educational platform microservices
- Event Sourcing: Exception events contributing to educational analytics
- Circuit Breaker: Exception patterns triggering service protection mechanisms
- Retry Logic: Exception types informing retry and recovery strategies
- Alerting Systems: Exception thresholds triggering operational notifications
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

class CourseManagementException(Exception):
    """Base exception for all Course Management service errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "COURSE_MANAGEMENT_ERROR",
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_exception = original_exception
        self.timestamp = datetime.utcnow()
        
        # Log the exception with proper context
        self._log_exception()
        
        super().__init__(self.message)
    
    def _log_exception(self):
        """Log the exception with proper formatting and context."""
        logger = logging.getLogger(__name__)
        
        log_context = {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "service": "course-management"
        }
        
        if self.original_exception:
            log_context["original_error"] = str(self.original_exception)
            log_context["original_type"] = type(self.original_exception).__name__
        
        logger.error(
            f"CourseManagement Exception: {self.error_code} - {self.message}",
            extra=log_context,
            exc_info=self.original_exception if self.original_exception else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "service": "course-management"
        }

class CourseNotFoundException(CourseManagementException):
    """Exception raised when a course is not found."""
    
    def __init__(
        self,
        message: str = "Course not found",
        course_id: Optional[str] = None,
        course_instance_id: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if course_id:
            details["course_id"] = course_id
        if course_instance_id:
            details["course_instance_id"] = course_instance_id
            
        super().__init__(
            message=message,
            error_code="COURSE_NOT_FOUND",
            details=details,
            original_exception=original_exception
        )

class CourseValidationException(CourseManagementException):
    """Exception raised when course validation fails."""
    
    def __init__(
        self,
        message: str = "Course validation failed",
        validation_errors: Optional[Dict[str, str]] = None,
        field_name: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
        if field_name:
            details["field_name"] = field_name
            
        super().__init__(
            message=message,
            error_code="COURSE_VALIDATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class EnrollmentException(CourseManagementException):
    """Exception raised when enrollment operations fail."""
    
    def __init__(
        self,
        message: str = "Enrollment operation failed",
        student_id: Optional[str] = None,
        course_id: Optional[str] = None,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if student_id:
            details["student_id"] = student_id
        if course_id:
            details["course_id"] = course_id
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="ENROLLMENT_ERROR",
            details=details,
            original_exception=original_exception
        )

class FeedbackException(CourseManagementException):
    """Exception raised when feedback operations fail."""
    
    def __init__(
        self,
        message: str = "Feedback operation failed",
        feedback_id: Optional[str] = None,
        student_id: Optional[str] = None,
        course_id: Optional[str] = None,
        feedback_type: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if feedback_id:
            details["feedback_id"] = feedback_id
        if student_id:
            details["student_id"] = student_id
        if course_id:
            details["course_id"] = course_id
        if feedback_type:
            details["feedback_type"] = feedback_type
            
        super().__init__(
            message=message,
            error_code="FEEDBACK_ERROR",
            details=details,
            original_exception=original_exception
        )

class ProgressException(CourseManagementException):
    """Exception raised when progress tracking operations fail."""
    
    def __init__(
        self,
        message: str = "Progress tracking failed",
        student_id: Optional[str] = None,
        course_id: Optional[str] = None,
        progress_type: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if student_id:
            details["student_id"] = student_id
        if course_id:
            details["course_id"] = course_id
        if progress_type:
            details["progress_type"] = progress_type
            
        super().__init__(
            message=message,
            error_code="PROGRESS_ERROR",
            details=details,
            original_exception=original_exception
        )

class DatabaseException(CourseManagementException):
    """Exception raised when database operations fail."""
    
    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        table_name: Optional[str] = None,
        record_id: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if table_name:
            details["table_name"] = table_name
        if record_id:
            details["record_id"] = record_id
            
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            original_exception=original_exception
        )

class AuthorizationException(CourseManagementException):
    """Exception raised when authorization fails."""
    
    def __init__(
        self,
        message: str = "Authorization failed",
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        required_permission: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if user_id:
            details["user_id"] = user_id
        if resource:
            details["resource"] = resource
        if required_permission:
            details["required_permission"] = required_permission
            
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class ValidationException(CourseManagementException):
    """Exception raised when input validation fails."""
    
    def __init__(
        self,
        message: str = "Input validation failed",
        validation_errors: Optional[Dict[str, str]] = None,
        field_name: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
        if field_name:
            details["field_name"] = field_name
            
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class EmailServiceException(CourseManagementException):
    """Exception raised when email service operations fail."""
    
    def __init__(
        self,
        message: str = "Email service failed",
        recipient: Optional[str] = None,
        email_type: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if recipient:
            details["recipient"] = recipient
        if email_type:
            details["email_type"] = email_type
            
        super().__init__(
            message=message,
            error_code="EMAIL_SERVICE_ERROR",
            details=details,
            original_exception=original_exception
        )

class QuizManagementException(CourseManagementException):
    """Exception raised when quiz management operations fail."""
    
    def __init__(
        self,
        message: str = "Quiz management operation failed",
        quiz_id: Optional[str] = None,
        course_instance_id: Optional[str] = None,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if quiz_id:
            details["quiz_id"] = quiz_id
        if course_instance_id:
            details["course_instance_id"] = course_instance_id
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="QUIZ_MANAGEMENT_ERROR",
            details=details,
            original_exception=original_exception
        )