"""
Custom exceptions for Content Storage Service following SOLID principles.
Single Responsibility: Each exception handles a specific error type.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

class ContentStorageException(Exception):
    """Base exception for all Content Storage service errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "CONTENT_STORAGE_ERROR",
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
            "service": "content-storage"
        }
        
        if self.original_exception:
            log_context["original_error"] = str(self.original_exception)
            log_context["original_type"] = type(self.original_exception).__name__
        
        logger.error(
            f"ContentStorage Exception: {self.error_code} - {self.message}",
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
            "service": "content-storage"
        }

class FileOperationException(ContentStorageException):
    """Exception raised when file operations fail."""
    
    def __init__(
        self,
        message: str = "File operation failed",
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        file_size: Optional[int] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if file_path:
            details["file_path"] = file_path
        if operation:
            details["operation"] = operation
        if file_size is not None:
            details["file_size"] = file_size
            
        super().__init__(
            message=message,
            error_code="FILE_OPERATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class StorageException(ContentStorageException):
    """Exception raised when storage operations fail."""
    
    def __init__(
        self,
        message: str = "Storage operation failed",
        storage_type: Optional[str] = None,
        bucket_name: Optional[str] = None,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if storage_type:
            details["storage_type"] = storage_type
        if bucket_name:
            details["bucket_name"] = bucket_name
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="STORAGE_ERROR",
            details=details,
            original_exception=original_exception
        )

class DatabaseException(ContentStorageException):
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

class ValidationException(ContentStorageException):
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

class ContentNotFoundException(ContentStorageException):
    """Exception raised when content is not found."""
    
    def __init__(
        self,
        message: str = "Content not found",
        content_id: Optional[str] = None,
        content_type: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if content_id:
            details["content_id"] = content_id
        if content_type:
            details["content_type"] = content_type
            
        super().__init__(
            message=message,
            error_code="CONTENT_NOT_FOUND",
            details=details,
            original_exception=original_exception
        )

class AuthenticationException(ContentStorageException):
    """Exception raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        user_id: Optional[str] = None,
        auth_method: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if user_id:
            details["user_id"] = user_id
        if auth_method:
            details["auth_method"] = auth_method
            
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class AuthorizationException(ContentStorageException):
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

class ConfigurationException(ContentStorageException):
    """Exception raised when configuration is invalid or missing."""
    
    def __init__(
        self,
        message: str = "Invalid or missing configuration",
        config_key: Optional[str] = None,
        config_section: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if config_key:
            details["config_key"] = config_key
        if config_section:
            details["config_section"] = config_section
            
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class ContentProcessingException(ContentStorageException):
    """Exception raised when content processing fails."""
    
    def __init__(
        self,
        message: str = "Content processing failed",
        content_type: Optional[str] = None,
        processing_stage: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if content_type:
            details["content_type"] = content_type
        if processing_stage:
            details["processing_stage"] = processing_stage
            
        super().__init__(
            message=message,
            error_code="CONTENT_PROCESSING_ERROR",
            details=details,
            original_exception=original_exception
        )
        # Note: Exception hierarchy provides comprehensive error handling
        # and monitoring capabilities for educational content management