"""
Middleware setup following SOLID principles.
Single Responsibility: Configure middleware components.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from omegaconf import DictConfig
import logging
import time

def setup_cors_middleware(app: FastAPI, config: DictConfig) -> None:
    """Setup CORS middleware"""
    allowed_origins = getattr(config, 'cors', {}).get('origins', ["*"])
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def setup_logging_middleware(app: FastAPI, config: DictConfig) -> None:
    """Setup logging middleware"""

    @app.middleware("http")
    async def log_requests(request, call_next):
        """Log HTTP requests and responses"""
        start_time = time.time()

        # Log request
        logging.info(
            f"Request: {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        logging.info(
            f"Response: {response.status_code} - "
            f"Time: {process_time:.4f}s - "
            f"Path: {request.url.path}"
        )

        return response

def setup_security_headers(app: FastAPI, config: DictConfig) -> None:
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
        config (DictConfig): Application configuration (unused but kept for consistency)

    Returns:
        None: Registers middleware on the FastAPI app
    """
    @app.middleware("http")
    async def add_security_headers(request, call_next):
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