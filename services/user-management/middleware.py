"""
Middleware setup following SOLID principles.
Single Responsibility: Configure middleware components.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from omegaconf import DictConfig
from collections import defaultdict
from typing import Dict, List, Optional
import logging
import time

def setup_cors_middleware(app: FastAPI, config: DictConfig) -> None:
    """
    Setup CORS middleware with environment-based configuration.

    SECURITY:
    Never use wildcard (*) origins in production - enables CSRF attacks.
    Always use explicit origin list from environment variables.
    """
    import os

    # Get CORS origins from environment, not config (security requirement)
    cors_origins_env = os.getenv('CORS_ORIGINS', 'https://localhost:3000,https://localhost:3001')
    allowed_origins = [origin.strip() for origin in cors_origins_env.split(',')]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
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


class LoginRateLimiter:
    """
    Strict rate limiter specifically for authentication endpoints.

    Uses sliding window algorithm for accurate rate limiting.
    Tracks failed login attempts separately for enhanced security.

    SECURITY REQUIREMENTS (OWASP A04:2021, A07:2021):
    - Login endpoint: 5 requests per minute per IP (strict)
    - Progressive lockout after repeated violations
    """

    def __init__(self):
        # Dict[client_ip] -> List[request_timestamps]
        self._requests: Dict[str, List[float]] = defaultdict(list)
        # Dict[client_ip] -> failed_attempt_count (for progressive delays)
        self._failed_attempts: Dict[str, int] = defaultdict(int)
        # Dict[client_ip] -> lockout_until_timestamp
        self._lockouts: Dict[str, float] = {}

    def is_rate_limited(
        self,
        client_ip: str,
        limit: int = 5,
        window_seconds: int = 60
    ) -> tuple:
        """
        Check if client has exceeded rate limit.

        Args:
            client_ip: Client IP address
            limit: Max requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_limited, remaining_requests, retry_after_seconds)
        """
        now = time.time()

        # Check if IP is locked out
        if client_ip in self._lockouts:
            lockout_until = self._lockouts[client_ip]
            if now < lockout_until:
                retry_after = int(lockout_until - now)
                return True, 0, retry_after
            else:
                # Lockout expired
                del self._lockouts[client_ip]
                self._failed_attempts[client_ip] = 0

        # Clean old requests outside window
        window_start = now - window_seconds
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip]
            if ts > window_start
        ]

        request_count = len(self._requests[client_ip])

        if request_count >= limit:
            # Rate limited - potentially lock out after repeated violations
            self._failed_attempts[client_ip] += 1

            # Progressive lockout: after 3 rate limit hits, lock for increasing time
            if self._failed_attempts[client_ip] >= 3:
                lockout_time = min(
                    60 * (2 ** (self._failed_attempts[client_ip] - 3)),
                    3600  # Max 1 hour lockout
                )
                self._lockouts[client_ip] = now + lockout_time
                logging.warning(
                    f"IP {client_ip} locked out for {lockout_time}s "
                    f"after {self._failed_attempts[client_ip]} rate limit violations"
                )
                return True, 0, lockout_time

            return True, 0, window_seconds

        # Record this request
        self._requests[client_ip].append(now)
        return False, limit - request_count - 1, None

    def record_failed_login(self, client_ip: str) -> None:
        """Record a failed login attempt for progressive lockout."""
        self._failed_attempts[client_ip] = self._failed_attempts.get(client_ip, 0) + 1

        # Lock out after 5 consecutive failed logins
        if self._failed_attempts[client_ip] >= 5:
            lockout_time = min(
                300 * (2 ** (self._failed_attempts[client_ip] - 5)),
                3600  # Max 1 hour
            )
            self._lockouts[client_ip] = time.time() + lockout_time
            logging.warning(
                f"IP {client_ip} locked out for {lockout_time}s "
                f"after {self._failed_attempts[client_ip]} failed login attempts"
            )

    def record_successful_login(self, client_ip: str) -> None:
        """Reset failed attempts on successful login."""
        if client_ip in self._failed_attempts:
            del self._failed_attempts[client_ip]
        if client_ip in self._lockouts:
            del self._lockouts[client_ip]


# Global rate limiter instance
_login_limiter = LoginRateLimiter()


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request, handling proxies.

    Priority:
    1. X-Forwarded-For header (first IP in chain)
    2. X-Real-IP header
    3. Direct client IP
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    if request.client:
        return request.client.host

    return "unknown"


def setup_rate_limiting(app: FastAPI, config: Optional[DictConfig] = None) -> None:
    """
    Setup rate limiting middleware for authentication endpoints.

    SECURITY REQUIREMENTS:
    - Login endpoint: 5 requests per minute per IP
    - Password reset: 3 requests per minute per IP
    - Other auth endpoints: 10 requests per minute per IP

    Args:
        app: FastAPI application instance
        config: Application configuration (optional)
    """
    # Endpoint-specific rate limits (requests per minute)
    ENDPOINT_LIMITS = {
        "/auth/login": 5,
        "/auth/student-login": 5,
        "/auth/password/reset": 3,
        "/auth/password/reset/request": 3,
        "/auth/password/reset/verify": 10,
        "/auth/password/reset/complete": 3,
        "/auth/register": 10,
        "/auth/refresh": 20,
    }

    # Exempt paths from rate limiting
    EXEMPT_PATHS = ["/health", "/docs", "/openapi.json", "/redoc"]

    @app.middleware("http")
    async def rate_limit_auth(request: Request, call_next):
        """Apply rate limiting to authentication endpoints."""
        path = request.url.path
        method = request.method

        # Skip rate limiting for exempt paths
        if any(path.startswith(exempt) for exempt in EXEMPT_PATHS):
            return await call_next(request)

        # Skip rate limiting for non-POST on auth endpoints (except for auth paths)
        if path.startswith("/auth/") and method != "POST":
            return await call_next(request)

        # Only rate limit specific auth endpoints
        if path not in ENDPOINT_LIMITS:
            return await call_next(request)

        # Get client IP
        client_ip = get_client_ip(request)

        # Determine rate limit for this endpoint
        limit = ENDPOINT_LIMITS.get(path, 100)

        # Check rate limit
        is_limited, remaining, retry_after = _login_limiter.is_rate_limited(
            client_ip, limit=limit, window_seconds=60
        )

        if is_limited:
            logging.warning(
                f"Rate limit exceeded: {client_ip} on {path} "
                f"(limit: {limit}/min, retry after: {retry_after}s)"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": retry_after
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(retry_after or 60),
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        # Track failed logins for progressive lockout
        if path in ("/auth/login", "/auth/student-login"):
            if response.status_code == 401:
                _login_limiter.record_failed_login(client_ip)
            elif response.status_code == 200:
                _login_limiter.record_successful_login(client_ip)

        return response

    logging.info("Rate limiting middleware enabled for authentication endpoints")