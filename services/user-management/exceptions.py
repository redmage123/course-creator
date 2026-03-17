"""
Custom exceptions for User Management Service
Provides specific exception types with proper logging and error context
"""
import logging
from typing import Optional, Dict, Any


class UserManagementException(Exception):
    """Base exception class for User Management Service"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "USER_MANAGEMENT_ERROR",
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_exception = original_exception
        
        # Log the exception with proper context
        self._log_exception()
        
        super().__init__(self.message)
    
    def _log_exception(self):
        """Log the exception with full context"""
        logger = logging.getLogger(__name__)
        
        log_context = {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }
        
        if self.original_exception:
            log_context["original_exception"] = str(self.original_exception)
            log_context["original_exception_type"] = type(self.original_exception).__name__
        
        logger.error(f"UserManagementException occurred: {log_context}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        result = {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }
        
        if self.original_exception:
            result["original_error"] = str(self.original_exception)
        
        return result


class AuthenticationException(UserManagementException):
    """Authentication-related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
            original_exception=original_exception
        )


class AuthorizationException(UserManagementException):
    """Authorization-related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            original_exception=original_exception
        )


class UserNotFoundException(UserManagementException):
    """User not found errors"""
    
    def __init__(self, user_id: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        message = f"User not found: {user_id}"
        details = details or {}
        details["user_id"] = user_id
        
        super().__init__(
            message=message,
            error_code="USER_NOT_FOUND",
            details=details,
            original_exception=original_exception
        )


class UserValidationException(UserManagementException):
    """User data validation errors"""
    
    def __init__(self, message: str, validation_errors: Dict[str, str], original_exception: Optional[Exception] = None):
        details = {"validation_errors": validation_errors}
        
        super().__init__(
            message=message,
            error_code="USER_VALIDATION_ERROR",
            details=details,
            original_exception=original_exception
        )


class DatabaseException(UserManagementException):
    """Database operation errors"""
    
    def __init__(self, message: str, operation: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        details = details or {}
        details["database_operation"] = operation
        
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            original_exception=original_exception
        )


class SessionException(UserManagementException):
    """Session management errors"""
    
    def __init__(self, message: str, session_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        details = details or {}
        if session_id:
            details["session_id"] = session_id
        
        super().__init__(
            message=message,
            error_code="SESSION_ERROR",
            details=details,
            original_exception=original_exception
        )


class JWTException(UserManagementException):
    """JWT token errors"""
    
    def __init__(self, message: str, token_type: str = "access", details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        details = details or {}
        details["token_type"] = token_type
        
        super().__init__(
            message=message,
            error_code="JWT_ERROR",
            details=details,
            original_exception=original_exception
        )


class EmailServiceException(UserManagementException):
    """Email service errors"""
    
    def __init__(self, message: str, email_address: Optional[str] = None, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        details = details or {}
        if email_address:
            details["email_address"] = email_address
        
        super().__init__(
            message=message,
            error_code="EMAIL_SERVICE_ERROR",
            details=details,
            original_exception=original_exception
        )