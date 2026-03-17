"""
Enhanced Error Handling and Validation Middleware
Comprehensive error handling, validation, and logging for Enhanced RBAC system
"""
import json
import logging
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from organization_management.domain.entities.enhanced_role import Permission

logger = logging.getLogger(__name__)


class ErrorCode:
    """Standardized error codes for the Enhanced RBAC system"""

    # Authentication & Authorization
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # Validation Errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    INVALID_UUID = "INVALID_UUID"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_ENUM_VALUE = "INVALID_ENUM_VALUE"

    # Resource Errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    DEPENDENCY_CONSTRAINT = "DEPENDENCY_CONSTRAINT"

    # Business Logic Errors
    ENROLLMENT_LIMIT_EXCEEDED = "ENROLLMENT_LIMIT_EXCEEDED"
    TRACK_NOT_PUBLISHED = "TRACK_NOT_PUBLISHED"
    ORGANIZATION_INACTIVE = "ORGANIZATION_INACTIVE"
    INVALID_OPERATION = "INVALID_OPERATION"

    # Integration Errors
    TEAMS_INTEGRATION_ERROR = "TEAMS_INTEGRATION_ERROR"
    ZOOM_INTEGRATION_ERROR = "ZOOM_INTEGRATION_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"

    # System Errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


class EnhancedHTTPException(HTTPException):
    """Enhanced HTTP exception with additional metadata"""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        headers: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code
        self.context = context or {}
        self.user_message = user_message or detail
        self.timestamp = datetime.utcnow()
        self.request_id = str(uuid.uuid4())


class ValidationErrorDetail:
    """Detailed validation error information"""

    def __init__(self, field: str, message: str, invalid_value: Any = None):
        self.field = field
        self.message = message
        self.invalid_value = invalid_value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "message": self.message,
            "invalid_value": str(self.invalid_value) if self.invalid_value is not None else None
        }


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Comprehensive error handling middleware"""

    def __init__(self, app, debug: bool = False):
        super().__init__(app)
        self.debug = debug

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        try:
            # Add request logging
            await self._log_request(request, request_id)

            # Process request
            response = await call_next(request)

            # Add response logging for errors
            if response.status_code >= 400:
                await self._log_error_response(request, response, request_id)

            return response

        except Exception as exc:
            return await self._handle_exception(request, exc, request_id)

    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request details"""
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "user_agent": request.headers.get("user-agent", ""),
                "client_ip": request.client.host if request.client else "unknown"
            }
        )

    async def _log_error_response(self, request: Request, response: Response, request_id: str):
        """Log error response details"""
        logger.error(
            f"Error response {request_id}: {response.status_code}",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "method": request.method,
                "path": request.url.path
            }
        )

    async def _handle_exception(self, request: Request, exc: Exception, request_id: str) -> JSONResponse:
        """Handle and format exceptions"""

        # Enhanced HTTP Exception
        if isinstance(exc, EnhancedHTTPException):
            return await self._handle_enhanced_http_exception(exc, request_id)

        # Standard HTTP Exception
        elif isinstance(exc, HTTPException):
            return await self._handle_http_exception(exc, request_id)

        # Validation Errors
        elif isinstance(exc, (RequestValidationError, PydanticValidationError)):
            return await self._handle_validation_error(exc, request_id)

        # Permission Errors
        elif isinstance(exc, PermissionError):
            return await self._handle_permission_error(exc, request_id)

        # Generic Exception
        else:
            return await self._handle_generic_exception(request, exc, request_id)

    async def _handle_enhanced_http_exception(self, exc: EnhancedHTTPException, request_id: str) -> JSONResponse:
        """Handle enhanced HTTP exceptions with full context"""

        logger.error(
            f"Enhanced HTTP Exception {request_id}: {exc.error_code} - {exc.detail}",
            extra={
                "request_id": request_id,
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "context": exc.context
            }
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_code": exc.error_code,
                "user_message": exc.user_message,
                "context": exc.context,
                "timestamp": exc.timestamp.isoformat(),
                "request_id": request_id
            },
            headers=exc.headers
        )

    async def _handle_http_exception(self, exc: HTTPException, request_id: str) -> JSONResponse:
        """Handle standard HTTP exceptions"""

        error_code = self._determine_error_code(exc.status_code, exc.detail)

        logger.error(
            f"HTTP Exception {request_id}: {error_code} - {exc.detail}",
            extra={
                "request_id": request_id,
                "error_code": error_code,
                "status_code": exc.status_code
            }
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_code": error_code,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id
            },
            headers=exc.headers
        )

    async def _handle_validation_error(self, exc: Union[RequestValidationError, PydanticValidationError], request_id: str) -> JSONResponse:
        """Handle validation errors with detailed field information"""

        validation_errors = []

        if isinstance(exc, RequestValidationError):
            for error in exc.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                validation_errors.append(ValidationErrorDetail(
                    field=field_path,
                    message=error["msg"],
                    invalid_value=error.get("input")
                ))

        elif hasattr(exc, 'errors'):
            for error in exc.errors():
                field_path = " -> ".join(str(loc) for loc in error.get("loc", []))
                validation_errors.append(ValidationErrorDetail(
                    field=field_path,
                    message=error.get("msg", str(error)),
                    invalid_value=error.get("input")
                ))

        else:
            validation_errors.append(ValidationErrorDetail(
                field="unknown",
                message=str(exc)
            ))

        logger.warning(
            f"Validation Error {request_id}: {len(validation_errors)} validation errors",
            extra={
                "request_id": request_id,
                "error_code": ErrorCode.VALIDATION_ERROR,
                "validation_errors": [err.to_dict() for err in validation_errors]
            }
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "error_code": ErrorCode.VALIDATION_ERROR,
                "validation_errors": [err.to_dict() for err in validation_errors],
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id
            }
        )

    async def _handle_permission_error(self, exc: PermissionError, request_id: str) -> JSONResponse:
        """Handle permission errors"""

        logger.warning(
            f"Permission Error {request_id}: {str(exc)}",
            extra={
                "request_id": request_id,
                "error_code": ErrorCode.PERMISSION_DENIED
            }
        )

        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": "Insufficient permissions for this operation",
                "error_code": ErrorCode.PERMISSION_DENIED,
                "user_message": "You don't have the required permissions to perform this action",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id
            }
        )

    async def _handle_generic_exception(self, request: Request, exc: Exception, request_id: str) -> JSONResponse:
        """Handle unexpected exceptions"""

        logger.error(
            f"Unhandled Exception {request_id}: {type(exc).__name__} - {str(exc)}",
            extra={
                "request_id": request_id,
                "error_code": ErrorCode.INTERNAL_ERROR,
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc() if self.debug else None
            }
        )

        response_content = {
            "detail": "An internal server error occurred",
            "error_code": ErrorCode.INTERNAL_ERROR,
            "user_message": "Something went wrong. Please try again later.",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }

        # Include debug information in development
        if self.debug:
            response_content["debug_info"] = {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc()
            }

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_content
        )

    def _determine_error_code(self, status_code: int, detail: str) -> str:
        """Determine appropriate error code based on status and detail"""

        detail_lower = detail.lower()

        if status_code == 401:
            if "token" in detail_lower:
                return ErrorCode.INVALID_TOKEN
            return ErrorCode.INVALID_TOKEN

        elif status_code == 403:
            if "permission" in detail_lower:
                return ErrorCode.PERMISSION_DENIED
            return ErrorCode.INSUFFICIENT_PERMISSIONS

        elif status_code == 404:
            return ErrorCode.NOT_FOUND

        elif status_code == 409:
            if "exists" in detail_lower:
                return ErrorCode.ALREADY_EXISTS
            return ErrorCode.RESOURCE_CONFLICT

        elif status_code == 422:
            return ErrorCode.VALIDATION_ERROR

        elif status_code == 429:
            return ErrorCode.RATE_LIMIT_EXCEEDED

        elif status_code >= 500:
            return ErrorCode.INTERNAL_ERROR

        else:
            return ErrorCode.INVALID_OPERATION


class ValidationHelper:
    """Helper class for common validations"""

    @staticmethod
    def validate_uuid(value: str, field_name: str = "id") -> str:
        """Validate UUID format"""
        try:
            uuid.UUID(value)
            return value
        except ValueError:
            raise EnhancedHTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format for {field_name}",
                error_code=ErrorCode.INVALID_UUID,
                context={"field": field_name, "value": value}
            )

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise EnhancedHTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid email format",
                error_code=ErrorCode.INVALID_EMAIL,
                context={"email": email}
            )
        return email

    @staticmethod
    def validate_permission(permission: str) -> Permission:
        """Validate permission enum"""
        try:
            return Permission(permission)
        except ValueError:
            valid_permissions = [p.value for p in Permission]
            raise EnhancedHTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid permission: {permission}",
                error_code=ErrorCode.INVALID_ENUM_VALUE,
                context={
                    "invalid_permission": permission,
                    "valid_permissions": valid_permissions
                }
            )

    @staticmethod
    def validate_pagination(skip: int, limit: int, max_limit: int = 100) -> tuple[int, int]:
        """Validate pagination parameters"""
        if skip < 0:
            raise EnhancedHTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Skip parameter must be non-negative",
                error_code=ErrorCode.INVALID_INPUT,
                context={"skip": skip}
            )

        if limit <= 0:
            raise EnhancedHTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Limit parameter must be positive",
                error_code=ErrorCode.INVALID_INPUT,
                context={"limit": limit}
            )

        if limit > max_limit:
            raise EnhancedHTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Limit parameter cannot exceed {max_limit}",
                error_code=ErrorCode.INVALID_INPUT,
                context={"limit": limit, "max_limit": max_limit}
            )

        return skip, limit


class BusinessLogicValidator:
    """Validator for business logic rules"""

    @staticmethod
    def validate_enrollment_capacity(current_count: int, max_capacity: int, new_enrollments: int):
        """Validate enrollment capacity"""
        if current_count + new_enrollments > max_capacity:
            raise EnhancedHTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enrollment would exceed track capacity",
                error_code=ErrorCode.ENROLLMENT_LIMIT_EXCEEDED,
                context={
                    "current_count": current_count,
                    "max_capacity": max_capacity,
                    "requested_enrollments": new_enrollments
                }
            )

    @staticmethod
    def validate_track_published(track_status: str):
        """Validate track is published for enrollment"""
        if track_status != "published":
            raise EnhancedHTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Track must be published before enrollment",
                error_code=ErrorCode.TRACK_NOT_PUBLISHED,
                context={"current_status": track_status}
            )

    @staticmethod
    def validate_organization_active(is_active: bool):
        """Validate organization is active"""
        if not is_active:
            raise EnhancedHTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization is not active",
                error_code=ErrorCode.ORGANIZATION_INACTIVE,
                user_message="This organization is currently inactive. Please contact support."
            )


def create_error_response(
    status_code: int,
    detail: str,
    error_code: str,
    context: Optional[Dict[str, Any]] = None,
    user_message: Optional[str] = None
) -> JSONResponse:
    """Create standardized error response"""

    return JSONResponse(
        status_code=status_code,
        content={
            "detail": detail,
            "error_code": error_code,
            "user_message": user_message or detail,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid.uuid4())
        }
    )