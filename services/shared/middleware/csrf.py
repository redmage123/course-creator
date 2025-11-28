"""
CSRF Protection Middleware for FastAPI

SECURITY CONTEXT:
Implements defense-in-depth CSRF protection using custom header validation.
While JWT-based authentication already provides CSRF protection (tokens can't be
read cross-origin), this middleware adds an additional layer of security.

IMPLEMENTATION:
Uses the 'X-Requested-With: XMLHttpRequest' pattern:
- Requires this custom header on all state-changing requests (POST, PUT, DELETE, PATCH)
- Cross-origin requests from malicious sites cannot set this header due to CORS preflight
- Only requests from our frontend (with the header) are allowed

OWASP REFERENCE:
- CWE-352: Cross-Site Request Forgery (CSRF)
- OWASP Testing Guide: Testing for CSRF

Author: Claude Code
Created: 2025-11-27
Version: 1.0.0
"""

import os
import logging
from typing import Callable, List, Optional

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate CSRF protection headers on state-changing requests.

    This middleware checks for the presence of 'X-Requested-With: XMLHttpRequest'
    header on POST, PUT, DELETE, and PATCH requests to prevent CSRF attacks.

    SAFE METHODS:
    - GET, HEAD, OPTIONS, TRACE are considered safe (read-only) and are allowed

    PROTECTED METHODS:
    - POST, PUT, DELETE, PATCH require the X-Requested-With header

    BYPASS PATHS:
    - Health check endpoints (/health, /healthz, /ready)
    - Authentication endpoints (configurable)
    - Webhook endpoints (configurable)
    """

    SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS', 'TRACE'}
    DEFAULT_EXEMPT_PATHS = {'/health', '/healthz', '/ready', '/metrics'}

    def __init__(
        self,
        app,
        exempt_paths: Optional[List[str]] = None,
        enabled: bool = True,
        header_name: str = 'X-Requested-With',
        header_value: str = 'XMLHttpRequest'
    ):
        """
        Initialize CSRF middleware.

        Args:
            app: FastAPI application instance
            exempt_paths: List of paths to exclude from CSRF validation
            enabled: Whether CSRF protection is enabled (can be disabled in dev)
            header_name: The header name to check (default: X-Requested-With)
            header_value: The expected header value (default: XMLHttpRequest)
        """
        super().__init__(app)
        self.exempt_paths = set(exempt_paths or []) | self.DEFAULT_EXEMPT_PATHS
        self.enabled = enabled and os.getenv('ENVIRONMENT', 'development').lower() != 'test'
        self.header_name = header_name
        self.header_value = header_value

        if self.enabled:
            logger.info(
                f"CSRF Protection enabled - requiring '{header_name}: {header_value}' "
                f"on state-changing requests"
            )
        else:
            logger.warning(
                "CSRF Protection disabled - only safe for testing environments"
            )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process incoming request and validate CSRF headers if needed.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware/route handler in the chain

        Returns:
            Response from the next handler

        Raises:
            HTTPException: 403 Forbidden if CSRF validation fails
        """
        # Skip if disabled
        if not self.enabled:
            return await call_next(request)

        # Skip safe methods
        if request.method.upper() in self.SAFE_METHODS:
            return await call_next(request)

        # Skip exempt paths
        path = request.url.path.rstrip('/')
        if path in self.exempt_paths or any(path.startswith(p) for p in self.exempt_paths):
            return await call_next(request)

        # Validate CSRF header
        csrf_header = request.headers.get(self.header_name)

        if not csrf_header or csrf_header != self.header_value:
            logger.warning(
                f"CSRF validation failed for {request.method} {path} - "
                f"missing or invalid {self.header_name} header"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "CSRF validation failed",
                    "message": f"Missing or invalid {self.header_name} header",
                    "required_header": f"{self.header_name}: {self.header_value}"
                }
            )

        return await call_next(request)


def get_csrf_middleware(
    exempt_paths: Optional[List[str]] = None,
    enabled: bool = True
) -> CSRFProtectionMiddleware:
    """
    Factory function to create CSRF middleware with configuration.

    Usage in main.py:
        from shared.middleware.csrf import get_csrf_middleware

        app.add_middleware(get_csrf_middleware(
            exempt_paths=['/api/v1/webhooks'],
            enabled=True
        ))

    Args:
        exempt_paths: Additional paths to exclude from CSRF validation
        enabled: Whether to enable CSRF protection

    Returns:
        Configured CSRFProtectionMiddleware instance
    """
    return lambda app: CSRFProtectionMiddleware(
        app,
        exempt_paths=exempt_paths,
        enabled=enabled
    )
