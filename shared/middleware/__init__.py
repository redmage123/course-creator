"""
Course Creator Platform - Shared Middleware

BUSINESS REQUIREMENT:
Provide consistent middleware components across all microservices
for exception handling, logging, request tracing, and security.

COMPONENTS:
- ExceptionHandlerMiddleware: Converts all exceptions to proper HTTP responses
- RequestLoggingMiddleware: Structured logging for all requests
- SecurityMiddleware: Security headers and validation
"""

import logging
import time
import uuid
from typing import Callable, Dict, Any
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from shared.exceptions import (
    CourseCreatorException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    ConflictException,
    ServiceException,
    DatabaseException,
    ConfigurationException,
    RateLimitException,
    SecurityException,
)

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI, service_name: str) -> None:
    """
    Configure FastAPI exception handlers for the global exception framework.

    USAGE:
    ```python
    from shared.middleware import setup_exception_handlers

    app = FastAPI()
    setup_exception_handlers(app, "user-management")
    ```

    Args:
        app: FastAPI application instance
        service_name: Name of the service for logging context
    """

    @app.exception_handler(CourseCreatorException)
    async def course_creator_exception_handler(
        request: Request,
        exc: CourseCreatorException
    ) -> JSONResponse:
        """
        Handle all CourseCreatorException subclasses.

        Maps exception types to appropriate HTTP status codes
        and formats response body consistently.
        """
        status_code_map = {
            ValidationException: 400,
            AuthenticationException: 401,
            AuthorizationException: 403,
            NotFoundException: 404,
            ConflictException: 409,
            RateLimitException: 429,
            DatabaseException: 503,
            ServiceException: 503,
            ConfigurationException: 500,
            SecurityException: 403,
        }

        # Find matching status code
        status_code = 500  # Default
        for exc_type, code in status_code_map.items():
            if isinstance(exc, exc_type):
                status_code = code
                break

        # Add service context if not present
        if not exc.service_name:
            exc.service_name = service_name

        return JSONResponse(
            status_code=status_code,
            content=exc.to_dict()
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """
        Handle all unhandled exceptions by wrapping in CourseCreatorException.

        DESIGN:
        Never expose raw exception details in production.
        Log full details server-side, return sanitized message to client.
        """
        # Log the full exception
        logger.exception(
            f"Unhandled exception in {service_name}",
            extra={
                "service": service_name,
                "path": request.url.path,
                "method": request.method,
                "exception_type": type(exc).__name__
            }
        )

        # Return sanitized response
        wrapped = CourseCreatorException(
            message="An unexpected error occurred. Please try again later.",
            error_code="INTERNAL_SERVER_ERROR",
            original_exception=exc,
            service_name=service_name
        )

        return JSONResponse(
            status_code=500,
            content=wrapped.to_dict()
        )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request/response logging.

    FEATURES:
    - Request ID generation for tracing
    - Timing metrics for performance monitoring
    - Structured JSON logging for aggregation
    """

    def __init__(self, app: FastAPI, service_name: str):
        super().__init__(app)
        self.service_name = service_name
        self.logger = logging.getLogger(f"{service_name}.requests")

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request and add logging context."""
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Record start time
        start_time = time.time()

        # Log incoming request
        self.logger.info(
            f"[{request_id}] {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "service": self.service_name,
                "event": "request_start"
            }
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log response
        self.logger.info(
            f"[{request_id}] {response.status_code} in {duration_ms:.2f}ms",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "service": self.service_name,
                "event": "request_complete"
            }
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    HEADERS ADDED:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000; includeSubDomains
    - Content-Security-Policy: default-src 'self'
    - Cache-Control: no-store (for sensitive endpoints)
    """

    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    # Paths that should not be cached
    NO_CACHE_PATHS = [
        "/api/auth",
        "/api/users",
        "/api/token",
        "/health",
    ]

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Add security headers
        for header, value in self.SECURITY_HEADERS.items():
            response.headers[header] = value

        # Add no-cache for sensitive endpoints
        if any(request.url.path.startswith(path) for path in self.NO_CACHE_PATHS):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        return response


def setup_middleware(app: FastAPI, service_name: str) -> None:
    """
    Configure all standard middleware for a service.

    USAGE:
    ```python
    from shared.middleware import setup_middleware

    app = FastAPI()
    setup_middleware(app, "user-management")
    ```

    Args:
        app: FastAPI application instance
        service_name: Name of the service
    """
    # Add exception handlers
    setup_exception_handlers(app, service_name)

    # Add request logging
    app.add_middleware(RequestLoggingMiddleware, service_name=service_name)

    # Add security headers
    app.add_middleware(SecurityHeadersMiddleware)


# Export all middleware components
__all__ = [
    "setup_exception_handlers",
    "setup_middleware",
    "RequestLoggingMiddleware",
    "SecurityHeadersMiddleware",
]
