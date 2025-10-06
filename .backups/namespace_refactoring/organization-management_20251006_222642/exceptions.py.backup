"""
Custom exceptions for Organization Management Service following SOLID principles.
Single Responsibility: Each exception handles a specific error type.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

class OrganizationManagementException(Exception):
    """Base exception for all Organization Management service errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "ORGANIZATION_MANAGEMENT_ERROR",
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
            "service": "organization-management"
        }
        
        if self.original_exception:
            log_context["original_error"] = str(self.original_exception)
            log_context["original_type"] = type(self.original_exception).__name__
        
        logger.error(
            f"OrganizationManagement Exception: {self.error_code} - {self.message}",
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
            "service": "organization-management"
        }

class OrganizationException(OrganizationManagementException):
    """Exception raised when organization operations fail."""
    
    def __init__(
        self,
        message: str = "Organization operation failed",
        organization_id: Optional[str] = None,
        organization_slug: Optional[str] = None,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if organization_id:
            details["organization_id"] = organization_id
        if organization_slug:
            details["organization_slug"] = organization_slug
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="ORGANIZATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class ProjectException(OrganizationManagementException):
    """Exception raised when project operations fail."""
    
    def __init__(
        self,
        message: str = "Project operation failed",
        project_id: Optional[str] = None,
        project_slug: Optional[str] = None,
        organization_id: Optional[str] = None,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if project_id:
            details["project_id"] = project_id
        if project_slug:
            details["project_slug"] = project_slug
        if organization_id:
            details["organization_id"] = organization_id
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="PROJECT_ERROR",
            details=details,
            original_exception=original_exception
        )

class MembershipException(OrganizationManagementException):
    """Exception raised when membership operations fail."""
    
    def __init__(
        self,
        message: str = "Membership operation failed",
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        organization_id: Optional[str] = None,
        project_id: Optional[str] = None,
        role: Optional[str] = None,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if user_id:
            details["user_id"] = user_id
        if user_email:
            details["user_email"] = user_email
        if organization_id:
            details["organization_id"] = organization_id
        if project_id:
            details["project_id"] = project_id
        if role:
            details["role"] = role
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="MEMBERSHIP_ERROR",
            details=details,
            original_exception=original_exception
        )

class AuthenticationException(OrganizationManagementException):
    """Exception raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        auth_method: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if user_id:
            details["user_id"] = user_id
        if user_email:
            details["user_email"] = user_email
        if auth_method:
            details["auth_method"] = auth_method
            
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class AuthorizationException(OrganizationManagementException):
    """Exception raised when authorization fails."""
    
    def __init__(
        self,
        message: str = "Authorization failed",
        user_id: Optional[str] = None,
        required_role: Optional[str] = None,
        user_role: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if user_id:
            details["user_id"] = user_id
        if required_role:
            details["required_role"] = required_role
        if user_role:
            details["user_role"] = user_role
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        if action:
            details["action"] = action
            
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class ValidationException(OrganizationManagementException):
    """Exception raised when input validation fails."""
    
    def __init__(
        self,
        message: str = "Input validation failed",
        validation_errors: Optional[Dict[str, str]] = None,
        field_name: Optional[str] = None,
        input_value: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
        if field_name:
            details["field_name"] = field_name
        if input_value:
            details["input_value"] = input_value
            
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class OrganizationNotFoundException(OrganizationManagementException):
    """Exception raised when organization is not found."""
    
    def __init__(
        self,
        message: str = "Organization not found",
        organization_id: Optional[str] = None,
        organization_slug: Optional[str] = None,
        search_criteria: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if organization_id:
            details["organization_id"] = organization_id
        if organization_slug:
            details["organization_slug"] = organization_slug
        if search_criteria:
            details["search_criteria"] = search_criteria
            
        super().__init__(
            message=message,
            error_code="ORGANIZATION_NOT_FOUND",
            details=details,
            original_exception=original_exception
        )

class ProjectNotFoundException(OrganizationManagementException):
    """Exception raised when project is not found."""
    
    def __init__(
        self,
        message: str = "Project not found",
        project_id: Optional[str] = None,
        project_slug: Optional[str] = None,
        organization_id: Optional[str] = None,
        search_criteria: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if project_id:
            details["project_id"] = project_id
        if project_slug:
            details["project_slug"] = project_slug
        if organization_id:
            details["organization_id"] = organization_id
        if search_criteria:
            details["search_criteria"] = search_criteria
            
        super().__init__(
            message=message,
            error_code="PROJECT_NOT_FOUND",
            details=details,
            original_exception=original_exception
        )

class DatabaseException(OrganizationManagementException):
    """Exception raised when database operations fail."""
    
    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        table_name: Optional[str] = None,
        record_id: Optional[str] = None,
        query_type: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if table_name:
            details["table_name"] = table_name
        if record_id:
            details["record_id"] = record_id
        if query_type:
            details["query_type"] = query_type
            
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            original_exception=original_exception
        )

class InstructorManagementException(OrganizationManagementException):
    """Exception raised when instructor management operations fail."""
    
    def __init__(
        self,
        message: str = "Instructor management operation failed",
        instructor_id: Optional[str] = None,
        instructor_email: Optional[str] = None,
        organization_id: Optional[str] = None,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if instructor_id:
            details["instructor_id"] = instructor_id
        if instructor_email:
            details["instructor_email"] = instructor_email
        if organization_id:
            details["organization_id"] = organization_id
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="INSTRUCTOR_MANAGEMENT_ERROR",
            details=details,
            original_exception=original_exception
        )

class DuplicateResourceException(OrganizationManagementException):
    """Exception raised when attempting to create duplicate resources."""
    
    def __init__(
        self,
        message: str = "Duplicate resource detected",
        resource_type: Optional[str] = None,
        resource_identifier: Optional[str] = None,
        duplicate_field: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_identifier:
            details["resource_identifier"] = resource_identifier
        if duplicate_field:
            details["duplicate_field"] = duplicate_field
            
        super().__init__(
            message=message,
            error_code="DUPLICATE_RESOURCE_ERROR",
            details=details,
            original_exception=original_exception
        )