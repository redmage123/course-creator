"""
Common Exception Classes for Course Creator Platform

This module provides a comprehensive hierarchy of custom exceptions that all services
should use instead of generic exception handling. This design follows the SOLID principles
and ensures consistent error handling across the entire platform.

Business Context:
- Provides structured error information for debugging and monitoring
- Enables specific error handling strategies based on exception type
- Supports detailed logging and error reporting requirements
- Facilitates API error response standardization

Technical Rationale:
- Replaces all generic 'except Exception as e' patterns with specific exceptions
- Provides context-rich error information including error codes and details
- Supports nested exception handling for error tracing
- Enables different handling strategies for different error categories
"""

from typing import Dict, Any, Optional
from datetime import datetime


class CourseCreatorBaseException(Exception):
    """
    Base exception class for all Course Creator Platform exceptions.
    
    Business Context:
    All platform exceptions inherit from this base class to ensure consistent
    error handling and logging across all microservices. This supports the
    platform's requirement for comprehensive error tracking and debugging.
    
    Technical Rationale:
    - Provides common error structure with error codes and context details
    - Supports exception chaining for root cause analysis
    - Enables platform-wide error handling middleware
    - Facilitates structured logging and monitoring integration
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: str = None, 
        details: Dict[str, Any] = None,
        original_exception: Exception = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.details = details or {}
        self.original_exception = original_exception
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for API responses and logging.
        
        Returns structured error information suitable for JSON serialization
        and consistent error reporting across all platform services.
        """
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "original_error": str(self.original_exception) if self.original_exception else None
        }


# Authentication and Authorization Exceptions
class AuthenticationException(CourseCreatorBaseException):
    """
    Authentication-related exceptions for login, token validation, and session management.
    
    Business Context:
    Handles all authentication failures across the platform including login attempts,
    session validation, and token-based authentication. Critical for security monitoring
    and user access management.
    """
    pass


class AuthorizationException(CourseCreatorBaseException):
    """
    Authorization-related exceptions for role-based access control and permissions.
    
    Business Context:
    Manages access control violations and permission denials. Essential for the
    platform's RBAC system and multi-tenant organization security.
    """
    pass


class SessionException(CourseCreatorBaseException):
    """
    Session management exceptions for session creation, validation, and expiration.
    
    Business Context:
    Handles session lifecycle issues critical for user experience and security.
    Supports the platform's requirement for secure session management.
    """
    pass


class JWTException(CourseCreatorBaseException):
    """
    JWT token-related exceptions for token creation, validation, and parsing.
    
    Business Context:
    Manages JWT token issues critical for API authentication and inter-service
    communication security across the microservices architecture.
    """
    pass


# User Management Exceptions
class UserManagementException(CourseCreatorBaseException):
    """
    General user management exceptions for user operations and profile management.
    
    Business Context:
    Handles user lifecycle operations including registration, profile updates,
    and account management. Core to the platform's user management capabilities.
    """
    pass


class UserNotFoundException(CourseCreatorBaseException):
    """
    Exception for when a requested user cannot be found in the system.
    
    Business Context:
    Critical for user lookup operations and API responses. Helps distinguish
    between user not found vs. system errors for proper error handling.
    """
    pass


class UserValidationException(CourseCreatorBaseException):
    """
    User data validation exceptions for registration and profile update operations.
    
    Business Context:
    Handles validation errors for user input including email format, username
    constraints, and profile data validation. Essential for data integrity.
    """
    
    def __init__(self, message: str, validation_errors: Dict[str, str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.validation_errors = validation_errors or {}
        self.details["validation_errors"] = self.validation_errors


class DuplicateUserException(CourseCreatorBaseException):
    """
    Exception for duplicate user registration attempts (email/username conflicts).
    
    Business Context:
    Prevents duplicate user accounts and provides clear feedback for registration
    conflicts. Critical for user account uniqueness and system integrity.
    """
    pass


# Organization Management Exceptions
class OrganizationException(CourseCreatorBaseException):
    """
    Organization management exceptions for multi-tenant operations.
    
    Business Context:
    Handles organization lifecycle, RBAC operations, and tenant management.
    Core to the platform's multi-tenant architecture and organization features.
    """
    pass


class OrganizationNotFoundException(CourseCreatorBaseException):
    """
    Exception for when a requested organization cannot be found.
    
    Business Context:
    Critical for organization lookup operations and tenant validation.
    Essential for multi-tenant security and access control.
    """
    pass


class OrganizationValidationException(CourseCreatorBaseException):
    """
    Organization data validation exceptions for registration and updates.
    
    Business Context:
    Ensures organization data integrity and validates business rules for
    organization creation and management operations.
    """
    pass


# Content Management Exceptions
class ContentException(CourseCreatorBaseException):
    """
    Content management exceptions for content operations and lifecycle.
    
    Business Context:
    Handles content creation, storage, retrieval, and management operations.
    Critical for the platform's content management and course delivery capabilities.
    """
    pass


class ContentNotFoundException(CourseCreatorBaseException):
    """
    Exception for when requested content cannot be found.
    
    Business Context:
    Handles content lookup failures and helps distinguish between missing
    content vs. access permission issues for proper error handling.
    """
    pass


class ContentValidationException(CourseCreatorBaseException):
    """
    Content validation exceptions for content creation and update operations.
    
    Business Context:
    Ensures content meets platform standards and business rules. Critical
    for content quality and platform content management requirements.
    """
    pass


class FileStorageException(CourseCreatorBaseException):
    """
    File storage and upload exceptions for content storage operations.
    
    Business Context:
    Handles file upload, storage, and retrieval issues. Essential for the
    platform's content storage capabilities and user file management.
    """
    pass


# Course Management Exceptions
class CourseException(CourseCreatorBaseException):
    """
    Course management exceptions for course operations and lifecycle.
    
    Business Context:
    Handles course creation, publishing, enrollment, and management operations.
    Core to the platform's educational course delivery capabilities.
    """
    pass


class CourseNotFoundException(CourseCreatorBaseException):
    """
    Exception for when a requested course cannot be found.
    
    Business Context:
    Critical for course lookup operations and enrollment management.
    Helps provide clear feedback for course access attempts.
    """
    pass


class CourseValidationException(CourseCreatorBaseException):
    """
    Course validation exceptions for course creation and update operations.
    
    Business Context:
    Ensures courses meet educational standards and platform requirements.
    Critical for course quality and educational content validation.
    """
    pass


class EnrollmentException(CourseCreatorBaseException):
    """
    Course enrollment exceptions for student enrollment operations.
    
    Business Context:
    Handles enrollment processes, capacity limits, and access control.
    Essential for the platform's course enrollment and access management.
    """
    pass


# Database and Infrastructure Exceptions
class DatabaseException(CourseCreatorBaseException):
    """
    Database operation exceptions for SQL operations and connection issues.
    
    Business Context:
    Handles database connectivity, query execution, and data persistence issues.
    Critical for platform reliability and data integrity across all services.
    """
    pass


class DatabaseConnectionException(CourseCreatorBaseException):
    """
    Database connection exceptions for connection pool and connectivity issues.
    
    Business Context:
    Handles database connectivity problems that could affect platform availability.
    Essential for infrastructure monitoring and service reliability.
    """
    pass


class DatabaseQueryException(CourseCreatorBaseException):
    """
    Database query execution exceptions for SQL execution and constraint violations.
    
    Business Context:
    Handles SQL execution errors, constraint violations, and data integrity issues.
    Critical for data consistency and platform reliability.
    """
    pass


# External Service Exceptions
class ExternalServiceException(CourseCreatorBaseException):
    """
    External service integration exceptions for third-party service interactions.
    
    Business Context:
    Handles communication issues with external APIs and service dependencies.
    Important for platform integration reliability and service monitoring.
    """
    pass


class EmailServiceException(CourseCreatorBaseException):
    """
    Email service exceptions for email delivery and notification operations.
    
    Business Context:
    Handles email delivery issues for user notifications, password resets,
    and platform communications. Critical for user engagement features.
    """
    pass


class AIServiceException(CourseCreatorBaseException):
    """
    AI service exceptions for course generation and RAG operations.
    
    Business Context:
    Handles AI service failures for course generation, content analysis,
    and RAG-enhanced features. Critical for platform's AI capabilities.
    """
    pass


# Lab and Container Management Exceptions
class LabException(CourseCreatorBaseException):
    """
    Lab container management exceptions for Docker operations and lab lifecycle.
    
    Business Context:
    Handles lab container creation, management, and lifecycle operations.
    Critical for the platform's hands-on learning lab capabilities.
    """
    pass


class ContainerException(CourseCreatorBaseException):
    """
    Docker container exceptions for container operations and resource management.
    
    Business Context:
    Handles Docker container lifecycle, resource allocation, and networking issues.
    Essential for the platform's containerized lab environment.
    """
    pass


class LabResourceException(CourseCreatorBaseException):
    """
    Lab resource management exceptions for resource allocation and limits.
    
    Business Context:
    Handles resource allocation, capacity limits, and lab environment constraints.
    Critical for platform resource management and lab scalability.
    """
    pass


# API and HTTP Exceptions
class APIException(CourseCreatorBaseException):
    """
    API operation exceptions for HTTP operations and service communication.
    
    Business Context:
    Handles API communication issues between microservices and external clients.
    Essential for platform service reliability and API error handling.
    """
    pass


class ValidationException(CourseCreatorBaseException):
    """
    Data validation exceptions for input validation and business rule enforcement.
    
    Business Context:
    Handles input validation across all platform operations. Critical for
    data integrity, security, and user experience consistency.
    """
    
    def __init__(self, message: str, field_errors: Dict[str, str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.field_errors = field_errors or {}
        self.details["field_errors"] = self.field_errors


class ConfigurationException(CourseCreatorBaseException):
    """
    Configuration and environment exceptions for service configuration issues.
    
    Business Context:
    Handles configuration problems that could affect service startup and operation.
    Critical for deployment reliability and environment management.
    """
    pass


# Rate Limiting and Security Exceptions
class RateLimitException(CourseCreatorBaseException):
    """
    Rate limiting exceptions for API throttling and abuse prevention.
    
    Business Context:
    Handles rate limiting enforcement for API protection and resource management.
    Important for platform security and service quality protection.
    """
    pass


class SecurityException(CourseCreatorBaseException):
    """
    Security-related exceptions for security policy violations and threats.
    
    Business Context:
    Handles security policy violations, suspicious activity, and threat detection.
    Critical for platform security and compliance requirements.
    """
    pass


# Business Logic Exceptions
class BusinessRuleException(CourseCreatorBaseException):
    """
    Business rule violations for domain-specific business logic enforcement.
    
    Business Context:
    Handles violations of business rules and domain constraints. Essential for
    maintaining business logic integrity across platform operations.
    """
    pass


class QuotaExceededException(CourseCreatorBaseException):
    """
    Resource quota exceptions for usage limits and capacity constraints.
    
    Business Context:
    Handles resource usage limits, storage quotas, and capacity constraints.
    Important for resource management and service level compliance.
    """
    pass


class RAGException(CourseCreatorBaseException):
    """
    Exception raised for Retrieval-Augmented Generation operations.
    
    Business Context:
    RAG service failures impact AI-powered features across the platform including content
    generation quality, lab assistance effectiveness, and personalized learning recommendations.
    These exceptions help identify vector database issues, embedding failures, and context
    retrieval problems that degrade AI performance.
    
    Technical Context:
    - ChromaDB connection and query failures
    - Vector embedding generation errors
    - Context retrieval and ranking issues
    - Knowledge base ingestion problems
    """
    pass


class EmbeddingException(RAGException):
    """
    Exception raised for text embedding generation failures.
    
    Business Context:
    Embedding generation failures prevent effective semantic search and context retrieval,
    directly impacting the quality of AI-generated educational content and assistance.
    These exceptions help identify API failures, model issues, and text processing problems.
    
    Technical Context:
    - OpenAI API embedding failures
    - Local embedding model errors
    - Text preprocessing issues
    - Token limit exceeded errors
    """
    pass


# Factory functions for common exception patterns
def create_not_found_exception(resource_type: str, resource_id: str, **kwargs) -> CourseCreatorBaseException:
    """
    Factory function for creating standardized not found exceptions.
    
    Business Context:
    Provides consistent not found error messages across all platform services.
    Improves user experience and debugging capabilities.
    
    Args:
        resource_type: Type of resource (e.g., 'User', 'Course', 'Organization')
        resource_id: Identifier of the missing resource
        **kwargs: Additional exception parameters
    
    Returns:
        Appropriate not found exception for the resource type
    """
    message = f"{resource_type} with ID '{resource_id}' not found"
    error_code = f"{resource_type.upper()}_NOT_FOUND"
    
    # Map resource types to specific exception classes
    exception_map = {
        'user': UserNotFoundException,
        'course': CourseNotFoundException,
        'organization': OrganizationNotFoundException,
        'content': ContentNotFoundException,
    }
    
    exception_class = exception_map.get(resource_type.lower(), CourseCreatorBaseException)
    return exception_class(message, error_code=error_code, **kwargs)


def create_validation_exception(resource_type: str, validation_errors: Dict[str, str], **kwargs) -> ValidationException:
    """
    Factory function for creating standardized validation exceptions.
    
    Business Context:
    Provides consistent validation error handling across all platform services.
    Ensures uniform validation feedback for user experience consistency.
    
    Args:
        resource_type: Type of resource being validated
        validation_errors: Dictionary of field-specific validation errors
        **kwargs: Additional exception parameters
    
    Returns:
        ValidationException with structured error information
    """
    message = f"Validation failed for {resource_type}"
    error_code = f"{resource_type.upper()}_VALIDATION_ERROR"
    
    return ValidationException(
        message, 
        field_errors=validation_errors,
        error_code=error_code,
        **kwargs
    )