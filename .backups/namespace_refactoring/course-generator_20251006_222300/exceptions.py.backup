"""
Custom exceptions for Course Generator Service following SOLID principles.
Single Responsibility: Each exception handles a specific error type.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

class CourseGeneratorException(Exception):
    """Base exception for all Course Generator service errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "COURSE_GENERATOR_ERROR",
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
            "service": "course-generator"
        }
        
        if self.original_exception:
            log_context["original_error"] = str(self.original_exception)
            log_context["original_type"] = type(self.original_exception).__name__
        
        logger.error(
            f"CourseGenerator Exception: {self.error_code} - {self.message}",
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
            "service": "course-generator"
        }

class ContentGenerationException(CourseGeneratorException):
    """Exception raised when content generation fails."""
    
    def __init__(
        self,
        message: str = "Failed to generate course content",
        content_type: Optional[str] = None,
        ai_service: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if content_type:
            details["content_type"] = content_type
        if ai_service:
            details["ai_service"] = ai_service
            
        super().__init__(
            message=message,
            error_code="CONTENT_GENERATION_FAILED",
            details=details,
            original_exception=original_exception
        )

class AIServiceException(CourseGeneratorException):
    """Exception raised when AI service communication fails."""
    
    def __init__(
        self,
        message: str = "AI service communication failed",
        service_name: Optional[str] = None,
        api_endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if service_name:
            details["service_name"] = service_name
        if api_endpoint:
            details["api_endpoint"] = api_endpoint
        if status_code:
            details["status_code"] = status_code
            
        super().__init__(
            message=message,
            error_code="AI_SERVICE_ERROR",
            details=details,
            original_exception=original_exception
        )

class FileProcessingException(CourseGeneratorException):
    """Exception raised when file processing fails."""
    
    def __init__(
        self,
        message: str = "File processing failed",
        file_path: Optional[str] = None,
        file_type: Optional[str] = None,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if file_path:
            details["file_path"] = file_path
        if file_type:
            details["file_type"] = file_type
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="FILE_PROCESSING_ERROR",
            details=details,
            original_exception=original_exception
        )

class ConfigurationException(CourseGeneratorException):
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

class ValidationException(CourseGeneratorException):
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

class DatabaseException(CourseGeneratorException):
    """Exception raised when database operations fail."""
    
    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        table_name: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if table_name:
            details["table_name"] = table_name
            
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            original_exception=original_exception
        )

class TemplateException(CourseGeneratorException):
    """Exception raised when template processing fails."""
    
    def __init__(
        self,
        message: str = "Template processing failed",
        template_name: Optional[str] = None,
        template_type: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if template_name:
            details["template_name"] = template_name
        if template_type:
            details["template_type"] = template_type
            
        super().__init__(
            message=message,
            error_code="TEMPLATE_ERROR",
            details=details,
            original_exception=original_exception
        )

class ExportException(CourseGeneratorException):
    """Exception raised when content export fails."""
    
    def __init__(
        self,
        message: str = "Content export failed",
        export_format: Optional[str] = None,
        course_id: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if export_format:
            details["export_format"] = export_format
        if course_id:
            details["course_id"] = course_id
            
        super().__init__(
            message=message,
            error_code="EXPORT_ERROR",
            details=details,
            original_exception=original_exception
        )