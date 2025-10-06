"""
Custom exceptions for Lab Container Management Service following SOLID principles.
Single Responsibility: Each exception handles a specific error type.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

class LabContainerException(Exception):
    """Base exception for all Lab Container Management service errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "LAB_CONTAINER_ERROR",
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
            "service": "lab-containers"
        }
        
        if self.original_exception:
            log_context["original_error"] = str(self.original_exception)
            log_context["original_type"] = type(self.original_exception).__name__
        
        logger.error(
            f"LabContainer Exception: {self.error_code} - {self.message}",
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
            "service": "lab-containers"
        }

class DockerServiceException(LabContainerException):
    """Exception raised when Docker service operations fail."""
    
    def __init__(
        self,
        message: str = "Docker service operation failed",
        container_id: Optional[str] = None,
        image_name: Optional[str] = None,
        operation: Optional[str] = None,
        docker_error: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if container_id:
            details["container_id"] = container_id
        if image_name:
            details["image_name"] = image_name
        if operation:
            details["operation"] = operation
        if docker_error:
            details["docker_error"] = docker_error
            
        super().__init__(
            message=message,
            error_code="DOCKER_SERVICE_ERROR",
            details=details,
            original_exception=original_exception
        )

class LabCreationException(LabContainerException):
    """Exception raised when lab creation fails."""
    
    def __init__(
        self,
        message: str = "Lab creation failed",
        student_id: Optional[str] = None,
        course_id: Optional[str] = None,
        lab_type: Optional[str] = None,
        resource_requirements: Optional[Dict[str, str]] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if student_id:
            details["student_id"] = student_id
        if course_id:
            details["course_id"] = course_id
        if lab_type:
            details["lab_type"] = lab_type
        if resource_requirements:
            details["resource_requirements"] = resource_requirements
            
        super().__init__(
            message=message,
            error_code="LAB_CREATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class LabNotFoundException(LabContainerException):
    """Exception raised when lab is not found."""
    
    def __init__(
        self,
        message: str = "Lab not found",
        lab_id: Optional[str] = None,
        student_id: Optional[str] = None,
        course_id: Optional[str] = None,
        search_criteria: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if lab_id:
            details["lab_id"] = lab_id
        if student_id:
            details["student_id"] = student_id
        if course_id:
            details["course_id"] = course_id
        if search_criteria:
            details["search_criteria"] = search_criteria
            
        super().__init__(
            message=message,
            error_code="LAB_NOT_FOUND",
            details=details,
            original_exception=original_exception
        )

class LabLifecycleException(LabContainerException):
    """Exception raised when lab lifecycle operations fail."""
    
    def __init__(
        self,
        message: str = "Lab lifecycle operation failed",
        lab_id: Optional[str] = None,
        current_status: Optional[str] = None,
        target_status: Optional[str] = None,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if lab_id:
            details["lab_id"] = lab_id
        if current_status:
            details["current_status"] = current_status
        if target_status:
            details["target_status"] = target_status
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="LAB_LIFECYCLE_ERROR",
            details=details,
            original_exception=original_exception
        )

class IDEServiceException(LabContainerException):
    """Exception raised when IDE service operations fail."""
    
    def __init__(
        self,
        message: str = "IDE service operation failed",
        lab_id: Optional[str] = None,
        ide_type: Optional[str] = None,
        port: Optional[int] = None,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if lab_id:
            details["lab_id"] = lab_id
        if ide_type:
            details["ide_type"] = ide_type
        if port is not None:
            details["port"] = port
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="IDE_SERVICE_ERROR",
            details=details,
            original_exception=original_exception
        )

class ResourceLimitException(LabContainerException):
    """Exception raised when resource limits are exceeded."""
    
    def __init__(
        self,
        message: str = "Resource limit exceeded",
        resource_type: Optional[str] = None,
        current_usage: Optional[str] = None,
        limit: Optional[str] = None,
        requested_amount: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if current_usage:
            details["current_usage"] = current_usage
        if limit:
            details["limit"] = limit
        if requested_amount:
            details["requested_amount"] = requested_amount
            
        super().__init__(
            message=message,
            error_code="RESOURCE_LIMIT_ERROR",
            details=details,
            original_exception=original_exception
        )

class ValidationException(LabContainerException):
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

class ServiceInitializationException(LabContainerException):
    """Exception raised when service initialization fails."""
    
    def __init__(
        self,
        message: str = "Service initialization failed",
        service_name: Optional[str] = None,
        initialization_stage: Optional[str] = None,
        configuration_error: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if service_name:
            details["service_name"] = service_name
        if initialization_stage:
            details["initialization_stage"] = initialization_stage
        if configuration_error:
            details["configuration_error"] = configuration_error
            
        super().__init__(
            message=message,
            error_code="SERVICE_INITIALIZATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class ContainerImageException(LabContainerException):
    """Exception raised when container image operations fail."""
    
    def __init__(
        self,
        message: str = "Container image operation failed",
        image_name: Optional[str] = None,
        image_tag: Optional[str] = None,
        operation: Optional[str] = None,
        registry_url: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if image_name:
            details["image_name"] = image_name
        if image_tag:
            details["image_tag"] = image_tag
        if operation:
            details["operation"] = operation
        if registry_url:
            details["registry_url"] = registry_url
            
        super().__init__(
            message=message,
            error_code="CONTAINER_IMAGE_ERROR",
            details=details,
            original_exception=original_exception
        )

class NetworkException(LabContainerException):
    """Exception raised when network operations fail."""
    
    def __init__(
        self,
        message: str = "Network operation failed",
        container_id: Optional[str] = None,
        network_name: Optional[str] = None,
        port_mapping: Optional[str] = None,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if container_id:
            details["container_id"] = container_id
        if network_name:
            details["network_name"] = network_name
        if port_mapping:
            details["port_mapping"] = port_mapping
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            details=details,
            original_exception=original_exception
        )