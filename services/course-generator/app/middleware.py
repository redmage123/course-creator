"""
Middleware setup following Single Responsibility Principle.
"""
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from omegaconf import DictConfig

logger = logging.getLogger(__name__)

def setup_middleware(app: FastAPI, config: DictConfig) -> None:
    """Setup all middleware for the application."""
    setup_security_headers(app)
    setup_cors_middleware(app, config)
    setup_logging_middleware(app)
    setup_timing_middleware(app)

def setup_cors_middleware(app: FastAPI, config: DictConfig) -> None:
    """Setup CORS middleware."""
    cors_config = config.get("cors", {})
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_config.get("origins", ["*"]),
        allow_credentials=cors_config.get("credentials", True),
        allow_methods=cors_config.get("methods", ["*"]),
        allow_headers=cors_config.get("headers", ["*"]),
    )

def setup_logging_middleware(app: FastAPI) -> None:
    """Setup request logging middleware."""
    
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all incoming requests."""
        start_time = time.time()
        
        logger.info(f"Request: {request.method} {request.url}")
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} - "
            f"Process time: {process_time:.4f}s"
        )
        
        return response

def setup_timing_middleware(app: FastAPI) -> None:
    """Setup timing header middleware."""

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        """Add process time header to responses."""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

def setup_security_headers(app: FastAPI) -> None:
    """
    Setup security headers middleware for GDPR/CCPA compliance and OWASP best practices.

    BUSINESS REQUIREMENT:
    All HTTP responses must include security headers to prevent common web vulnerabilities
    including XSS attacks, clickjacking, MIME sniffing, and protocol downgrade attacks.

    COMPLIANCE:
    - OWASP A05:2021 - Security Misconfiguration
    - GDPR/CCPA - Data protection through secure transmission
    - PCI DSS - Requirement 6.5 for secure web applications

    HEADERS APPLIED:
    - X-Content-Type-Options: nosniff (prevents MIME type sniffing)
    - X-Frame-Options: DENY (prevents clickjacking attacks)
    - Strict-Transport-Security: enforces HTTPS with 1-year max-age
    - Referrer-Policy: strict-origin-when-cross-origin (privacy protection)

    Args:
        app (FastAPI): The FastAPI application instance

    Returns:
        None: Registers middleware on the FastAPI app
    """
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """
        Add security headers to all HTTP responses.

        This middleware intercepts every HTTP response and injects security headers
        that protect against common web vulnerabilities. These headers are critical
        for security compliance and are verified by E2E security tests.

        TECHNICAL DETAILS:
        - Runs after route handlers but before response is sent to client
        - Headers are added to all responses (HTML, JSON, etc.)
        - Does not affect response body or status code
        - Headers follow OWASP recommendations for secure applications

        Why These Headers:
        - X-Content-Type-Options prevents browsers from MIME-sniffing responses away
          from declared content-type, reducing XSS attack surface
        - X-Frame-Options prevents page from being embedded in iframes, protecting
          against clickjacking attacks
        - Strict-Transport-Security forces HTTPS for 1 year, preventing protocol
          downgrade attacks and cookie hijacking
        - Referrer-Policy controls referrer information, protecting user privacy
          and preventing information leakage to third parties

        Args:
            request: The incoming HTTP request
            call_next: The next middleware/handler in the chain

        Returns:
            Response with security headers injected
        """
        # Process request through the application
        response = await call_next(request)

        # Inject security headers into response
        # These headers are required by E2E security compliance tests
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response