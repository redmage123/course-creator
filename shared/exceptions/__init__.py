"""
Course Creator Platform - Global Exception Framework

BUSINESS REQUIREMENT:
Provide a unified exception handling framework across all microservices
to ensure consistent error reporting, logging, and API responses.

DESIGN PATTERN:
Hierarchical exception classes following SOLID principles:
- Single Responsibility: Each exception handles a specific error type
- Open/Closed: Easy to extend without modifying base classes
- Liskov Substitution: All exceptions can be handled as base type
- Interface Segregation: Minimal required interface
- Dependency Inversion: Services depend on abstractions

USAGE:
```python
from shared.exceptions import (
    CourseCreatorException,
    DatabaseException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    ServiceException,
    ConfigurationException,
    NotFoundException,
    ConflictException,
    RateLimitException
)

# Wrap base exceptions in custom wrappers
try:
    result = await database.query(sql)
except Exception as e:
    raise DatabaseException(
        message="Failed to execute query",
        operation="SELECT",
        table_name="users",
        original_exception=e
    )
```
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum


class ErrorSeverity(Enum):
    """
    Error severity levels for categorizing exceptions.

    USAGE:
    Used to determine logging level and alerting thresholds.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CourseCreatorException(Exception):
    """
    Base exception for all Course Creator Platform errors.

    DESIGN RATIONALE:
    All custom exceptions inherit from this class to enable:
    - Consistent error handling across services
    - Structured logging with context
    - Serialization for API responses
    - Original exception preservation for debugging

    ATTRIBUTES:
    - message: Human-readable error description
    - error_code: Machine-readable error identifier
    - details: Additional context as key-value pairs
    - original_exception: The underlying exception (if any)
    - timestamp: When the exception occurred
    - severity: Error severity level
    - service_name: Name of the service where error occurred
    """

    def __init__(
        self,
        message: str,
        error_code: str = "COURSE_CREATOR_ERROR",
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        service_name: Optional[str] = None
    ):
        """
        Initialize base exception with full context.

        Args:
            message: Human-readable error description
            error_code: Machine-readable error code (e.g., "AUTH_001")
            details: Additional context dictionary
            original_exception: The underlying exception being wrapped
            severity: Error severity level for logging/alerting
            service_name: Name of the originating service
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_exception = original_exception
        self.timestamp = datetime.now(timezone.utc)
        self.severity = severity
        self.service_name = service_name

        # Log the exception with proper context
        self._log_exception()

        super().__init__(self.message)

    def _log_exception(self) -> None:
        """
        Log the exception with structured context.

        IMPLEMENTATION:
        Uses Python's logging with extra context for
        structured log aggregation systems.
        """
        logger = logging.getLogger(f"course_creator.{self.service_name or 'unknown'}")

        log_context = {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "service": self.service_name
        }

        if self.original_exception:
            log_context["original_error"] = str(self.original_exception)
            log_context["original_type"] = type(self.original_exception).__name__

        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(self.severity, logging.ERROR)

        logger.log(
            log_level,
            f"[{self.error_code}] {self.message}",
            extra=log_context,
            exc_info=self.original_exception if self.original_exception else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for API responses.

        USAGE:
        Used by FastAPI exception handlers to serialize errors.

        Returns:
            Dictionary suitable for JSON serialization
        """
        result = {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }

        if self.service_name:
            result["service"] = self.service_name

        if self.details:
            result["details"] = self.details

        return result

    def to_http_response(self) -> tuple:
        """
        Convert exception to HTTP response tuple (body, status_code).

        Returns:
            Tuple of (response_dict, http_status_code)
        """
        status_codes = {
            "VALIDATION_ERROR": 400,
            "AUTHENTICATION_ERROR": 401,
            "AUTHORIZATION_ERROR": 403,
            "NOT_FOUND": 404,
            "CONFLICT": 409,
            "RATE_LIMIT_ERROR": 429,
            "DATABASE_ERROR": 503,
            "SERVICE_ERROR": 503,
            "CONFIGURATION_ERROR": 500,
        }

        # Default to 500 for unknown error codes
        status_code = 500
        for code_prefix, http_code in status_codes.items():
            if self.error_code.startswith(code_prefix):
                status_code = http_code
                break

        return self.to_dict(), status_code


class DatabaseException(CourseCreatorException):
    """
    Exception for database operation failures.

    USE CASES:
    - Connection failures
    - Query execution errors
    - Transaction failures
    - Constraint violations
    """

    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        table_name: Optional[str] = None,
        record_id: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        service_name: Optional[str] = None
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
            original_exception=original_exception,
            severity=ErrorSeverity.HIGH,
            service_name=service_name
        )


class ValidationException(CourseCreatorException):
    """
    Exception for input validation failures.

    USE CASES:
    - Invalid request parameters
    - Missing required fields
    - Format validation failures
    - Business rule violations
    """

    def __init__(
        self,
        message: str = "Input validation failed",
        validation_errors: Optional[Dict[str, str]] = None,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        original_exception: Optional[Exception] = None,
        service_name: Optional[str] = None
    ):
        details = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
        if field_name:
            details["field_name"] = field_name
        if field_value is not None:
            # Sanitize value to avoid logging sensitive data
            details["field_value"] = str(field_value)[:100] if field_value else None

        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            original_exception=original_exception,
            severity=ErrorSeverity.LOW,
            service_name=service_name
        )


class AuthenticationException(CourseCreatorException):
    """
    Exception for authentication failures.

    USE CASES:
    - Invalid credentials
    - Expired tokens
    - Missing authentication
    - Invalid token format
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        auth_method: Optional[str] = None,
        reason: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        service_name: Optional[str] = None
    ):
        details = {}
        if auth_method:
            details["auth_method"] = auth_method
        if reason:
            details["reason"] = reason
        # Never include user credentials in exception details

        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
            original_exception=original_exception,
            severity=ErrorSeverity.MEDIUM,
            service_name=service_name
        )


class AuthorizationException(CourseCreatorException):
    """
    Exception for authorization failures.

    USE CASES:
    - Insufficient permissions
    - Resource access denied
    - Role requirement not met
    - Organization boundary violation
    """

    def __init__(
        self,
        message: str = "Authorization failed",
        resource: Optional[str] = None,
        required_permission: Optional[str] = None,
        user_role: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        service_name: Optional[str] = None
    ):
        details = {}
        if resource:
            details["resource"] = resource
        if required_permission:
            details["required_permission"] = required_permission
        if user_role:
            details["user_role"] = user_role
        # Never include user_id in authorization errors for security

        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            original_exception=original_exception,
            severity=ErrorSeverity.MEDIUM,
            service_name=service_name
        )


class NotFoundException(CourseCreatorException):
    """
    Exception when a requested resource is not found.

    USE CASES:
    - Entity not found by ID
    - Resource deleted
    - Invalid reference
    """

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        service_name: Optional[str] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            details=details,
            original_exception=original_exception,
            severity=ErrorSeverity.LOW,
            service_name=service_name
        )


class ConflictException(CourseCreatorException):
    """
    Exception for resource conflicts.

    USE CASES:
    - Duplicate resource creation
    - Concurrent modification conflicts
    - Unique constraint violations
    """

    def __init__(
        self,
        message: str = "Resource conflict",
        resource_type: Optional[str] = None,
        conflicting_field: Optional[str] = None,
        existing_value: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        service_name: Optional[str] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if conflicting_field:
            details["conflicting_field"] = conflicting_field
        if existing_value:
            details["existing_value"] = existing_value

        super().__init__(
            message=message,
            error_code="CONFLICT",
            details=details,
            original_exception=original_exception,
            severity=ErrorSeverity.LOW,
            service_name=service_name
        )


class ServiceException(CourseCreatorException):
    """
    Exception for inter-service communication failures.

    USE CASES:
    - Service unavailable
    - Timeout errors
    - Network failures
    - Invalid service response
    """

    def __init__(
        self,
        message: str = "Service operation failed",
        target_service: Optional[str] = None,
        operation: Optional[str] = None,
        status_code: Optional[int] = None,
        original_exception: Optional[Exception] = None,
        service_name: Optional[str] = None
    ):
        details = {}
        if target_service:
            details["target_service"] = target_service
        if operation:
            details["operation"] = operation
        if status_code:
            details["status_code"] = status_code

        super().__init__(
            message=message,
            error_code="SERVICE_ERROR",
            details=details,
            original_exception=original_exception,
            severity=ErrorSeverity.HIGH,
            service_name=service_name
        )


class ConfigurationException(CourseCreatorException):
    """
    Exception for configuration errors.

    USE CASES:
    - Missing required config
    - Invalid config values
    - Environment variable issues
    """

    def __init__(
        self,
        message: str = "Invalid or missing configuration",
        config_key: Optional[str] = None,
        config_section: Optional[str] = None,
        expected_type: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        service_name: Optional[str] = None
    ):
        details = {}
        if config_key:
            details["config_key"] = config_key
        if config_section:
            details["config_section"] = config_section
        if expected_type:
            details["expected_type"] = expected_type
        # Never include actual config values

        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            original_exception=original_exception,
            severity=ErrorSeverity.CRITICAL,
            service_name=service_name
        )


class RateLimitException(CourseCreatorException):
    """
    Exception for rate limiting violations.

    USE CASES:
    - Too many requests
    - API quota exceeded
    - Throttling active
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None,
        retry_after: Optional[int] = None,
        original_exception: Optional[Exception] = None,
        service_name: Optional[str] = None
    ):
        details = {}
        if limit:
            details["limit"] = limit
        if window_seconds:
            details["window_seconds"] = window_seconds
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details=details,
            original_exception=original_exception,
            severity=ErrorSeverity.LOW,
            service_name=service_name
        )


class SecurityException(CourseCreatorException):
    """
    Exception for security-related issues.

    USE CASES:
    - SSL/TLS failures
    - Token tampering detected
    - Security policy violations
    - Suspicious activity detected
    """

    def __init__(
        self,
        message: str = "Security violation detected",
        violation_type: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        service_name: Optional[str] = None
    ):
        details = {}
        if violation_type:
            details["violation_type"] = violation_type
        # Minimal details for security exceptions

        super().__init__(
            message=message,
            error_code="SECURITY_ERROR",
            details=details,
            original_exception=original_exception,
            severity=ErrorSeverity.CRITICAL,
            service_name=service_name
        )


class DAOException(CourseCreatorException):
    """
    Base exception for Data Access Object operations.

    USE CASES:
    - DAO initialization failures
    - Connection pool issues
    - Query building errors

    DESIGN:
    All DAO-specific exceptions should inherit from this class.
    """

    def __init__(
        self,
        message: str = "Data access operation failed",
        dao_name: Optional[str] = None,
        operation: Optional[str] = None,
        entity_type: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        service_name: Optional[str] = None
    ):
        details = {}
        if dao_name:
            details["dao_name"] = dao_name
        if operation:
            details["operation"] = operation
        if entity_type:
            details["entity_type"] = entity_type

        super().__init__(
            message=message,
            error_code="DAO_ERROR",
            details=details,
            original_exception=original_exception,
            severity=ErrorSeverity.HIGH,
            service_name=service_name
        )


class DAOConnectionException(DAOException):
    """Exception for DAO connection failures."""

    def __init__(
        self,
        message: str = "Database connection failed",
        host: Optional[str] = None,
        port: Optional[int] = None,
        original_exception: Optional[Exception] = None,
        service_name: Optional[str] = None
    ):
        details = {}
        if host:
            details["host"] = host
        if port:
            details["port"] = port
        # Never include credentials

        # Call parent but override error code
        super().__init__(
            message=message,
            dao_name="connection",
            operation="connect",
            original_exception=original_exception,
            service_name=service_name
        )
        self.error_code = "DAO_CONNECTION_ERROR"


class DAOQueryException(DAOException):
    """Exception for DAO query failures."""

    def __init__(
        self,
        message: str = "Query execution failed",
        query_type: Optional[str] = None,
        table_name: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        service_name: Optional[str] = None
    ):
        details = {}
        if query_type:
            details["query_type"] = query_type
        if table_name:
            details["table_name"] = table_name
        # Never include actual query or parameters

        super().__init__(
            message=message,
            operation=query_type,
            entity_type=table_name,
            original_exception=original_exception,
            service_name=service_name
        )
        self.error_code = "DAO_QUERY_ERROR"


# Export all exception classes
__all__ = [
    "ErrorSeverity",
    "CourseCreatorException",
    "DatabaseException",
    "ValidationException",
    "AuthenticationException",
    "AuthorizationException",
    "NotFoundException",
    "ConflictException",
    "ServiceException",
    "ConfigurationException",
    "RateLimitException",
    "SecurityException",
    "DAOException",
    "DAOConnectionException",
    "DAOQueryException",
]
