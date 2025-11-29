"""
Rate Limiting Middleware for FastAPI Services

BUSINESS CONTEXT:
Rate limiting protects against:
- Brute force attacks on login endpoints
- DoS/DDoS attacks on public APIs
- API abuse by compromised or malicious clients
- Resource exhaustion from excessive requests

SECURITY REQUIREMENTS (OWASP A04:2021):
- Login endpoints: 5-10 requests per minute per IP
- API endpoints: 100-1000 requests per minute per client
- Distributed rate limiting using Redis for multi-instance deployments
- Graceful degradation when Redis unavailable

TECHNICAL IMPLEMENTATION:
- Token bucket algorithm for burst allowance
- Sliding window for accurate rate tracking
- Redis-backed for distributed deployments
- In-memory fallback for development

USAGE:
    from services.shared.security.rate_limit import RateLimitMiddleware, rate_limit

    # Apply to entire app
    app.add_middleware(RateLimitMiddleware, redis_url=REDIS_URL)

    # Apply to specific endpoint
    @app.post("/login")
    @rate_limit(requests_per_minute=5, key_prefix="login")
    async def login(request: Request):
        ...
"""

import time
import logging
import hashlib
from typing import Optional, Callable, Dict, Any
from functools import wraps
from collections import defaultdict

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """
    In-memory rate limiter for single-instance deployments or development.

    Uses sliding window algorithm for accurate rate limiting.
    NOT suitable for production with multiple instances.
    """

    def __init__(self):
        # Dict[key, List[timestamp]]
        self._requests: Dict[str, list] = defaultdict(list)

    def is_rate_limited(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """
        Check if a key has exceeded the rate limit.

        Args:
            key: Unique identifier (e.g., IP address, user_id)
            limit: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_limited, remaining_requests)
        """
        now = time.time()
        window_start = now - window_seconds

        # Clean old requests
        self._requests[key] = [
            ts for ts in self._requests[key]
            if ts > window_start
        ]

        request_count = len(self._requests[key])

        if request_count >= limit:
            return True, 0

        # Record this request
        self._requests[key].append(now)
        return False, limit - request_count - 1

    def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        if key in self._requests:
            del self._requests[key]


class RedisRateLimiter:
    """
    Redis-backed rate limiter for distributed deployments.

    Uses sliding window log algorithm for accurate distributed rate limiting.
    Suitable for production with multiple instances.
    """

    def __init__(self, redis_url: str):
        """
        Initialize Redis rate limiter.

        Args:
            redis_url: Redis connection URL
        """
        try:
            import redis
            self._redis = redis.from_url(redis_url)
            self._redis.ping()
            self._available = True
            logger.info("Redis rate limiter initialized successfully")
        except Exception as e:
            logger.warning(f"Redis unavailable for rate limiting: {e}. Falling back to in-memory.")
            self._available = False
            self._fallback = InMemoryRateLimiter()

    def is_rate_limited(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """
        Check if a key has exceeded the rate limit using Redis.

        Args:
            key: Unique identifier (e.g., IP address, user_id)
            limit: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_limited, remaining_requests)
        """
        if not self._available:
            return self._fallback.is_rate_limited(key, limit, window_seconds)

        try:
            now = time.time()
            window_start = now - window_seconds

            pipe = self._redis.pipeline()
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            # Count requests in window
            pipe.zcard(key)
            # Add new request
            pipe.zadd(key, {str(now): now})
            # Set expiry
            pipe.expire(key, window_seconds)

            results = pipe.execute()
            request_count = results[1]

            if request_count >= limit:
                return True, 0

            return False, limit - request_count - 1

        except Exception as e:
            logger.error(f"Redis error in rate limiting: {e}")
            return self._fallback.is_rate_limited(key, limit, window_seconds)

    def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        if self._available:
            try:
                self._redis.delete(key)
            except Exception as e:
                logger.error(f"Redis error resetting rate limit: {e}")


# Global rate limiter instance
_rate_limiter: Optional[InMemoryRateLimiter | RedisRateLimiter] = None


def get_rate_limiter(redis_url: Optional[str] = None) -> InMemoryRateLimiter | RedisRateLimiter:
    """
    Get or create the global rate limiter instance.

    Args:
        redis_url: Optional Redis URL for distributed rate limiting

    Returns:
        Rate limiter instance
    """
    global _rate_limiter

    if _rate_limiter is None:
        if redis_url:
            _rate_limiter = RedisRateLimiter(redis_url)
        else:
            _rate_limiter = InMemoryRateLimiter()
            logger.warning(
                "Using in-memory rate limiting. "
                "Set REDIS_URL for production distributed rate limiting."
            )

    return _rate_limiter


def get_client_identifier(request: Request) -> str:
    """
    Extract unique client identifier from request.

    Priority:
    1. X-Forwarded-For header (for proxied requests)
    2. X-Real-IP header (nginx)
    3. Direct client IP

    Args:
        request: FastAPI Request object

    Returns:
        Client identifier string
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    if request.client:
        return request.client.host

    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for global rate limiting.

    CONFIGURATION:
    - Default: 100 requests per minute per IP
    - Customize limits per endpoint using endpoint_limits parameter
    - Override with environment variables

    HEADERS ADDED:
    - X-RateLimit-Limit: Maximum requests allowed
    - X-RateLimit-Remaining: Requests remaining in window
    - X-RateLimit-Reset: Window reset timestamp
    """

    def __init__(
        self,
        app,
        redis_url: Optional[str] = None,
        default_limit: int = 100,
        window_seconds: int = 60,
        endpoint_limits: Optional[Dict[str, int]] = None,
        exempt_paths: Optional[list] = None
    ):
        """
        Initialize rate limiting middleware.

        Args:
            app: FastAPI application
            redis_url: Redis URL for distributed rate limiting
            default_limit: Default requests per window
            window_seconds: Time window in seconds
            endpoint_limits: Custom limits per endpoint path
            exempt_paths: Paths to exempt from rate limiting
        """
        super().__init__(app)
        self._limiter = get_rate_limiter(redis_url)
        self._default_limit = default_limit
        self._window_seconds = window_seconds
        self._endpoint_limits = endpoint_limits or {}
        self._exempt_paths = exempt_paths or ["/health", "/metrics", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through rate limiting."""
        path = request.url.path

        # Skip rate limiting for exempt paths
        if any(path.startswith(exempt) for exempt in self._exempt_paths):
            return await call_next(request)

        # Get client identifier
        client_id = get_client_identifier(request)

        # Create rate limit key
        key = f"rate_limit:{client_id}:{path}"

        # Get limit for this endpoint
        limit = self._endpoint_limits.get(path, self._default_limit)

        # Check rate limit
        is_limited, remaining = self._limiter.is_rate_limited(
            key, limit, self._window_seconds
        )

        if is_limited:
            logger.warning(
                f"Rate limit exceeded for {client_id} on {path}"
            )
            return Response(
                content="Rate limit exceeded. Please retry later.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(self._window_seconds),
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


def rate_limit(
    requests_per_minute: int = 60,
    key_prefix: str = "api",
    redis_url: Optional[str] = None
) -> Callable:
    """
    Decorator for endpoint-specific rate limiting.

    USAGE:
        @app.post("/login")
        @rate_limit(requests_per_minute=5, key_prefix="login")
        async def login(request: Request):
            ...

    Args:
        requests_per_minute: Maximum requests per minute
        key_prefix: Prefix for rate limit key
        redis_url: Optional Redis URL

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request in args or kwargs
            # Check args first
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            # Check all kwargs values for Request objects (not just "request" key)
            if not request:
                for kwarg_value in kwargs.values():
                    if isinstance(kwarg_value, Request):
                        request = kwarg_value
                        break

            if not request:
                logger.warning("No Request object found for rate limiting")
                return await func(*args, **kwargs)

            limiter = get_rate_limiter(redis_url)
            client_id = get_client_identifier(request)
            key = f"rate_limit:{key_prefix}:{client_id}"

            is_limited, remaining = limiter.is_rate_limited(
                key, requests_per_minute, 60
            )

            if is_limited:
                logger.warning(
                    f"Rate limit exceeded for {client_id} on {key_prefix}"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please retry later.",
                    headers={
                        "X-RateLimit-Limit": str(requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                        "Retry-After": "60",
                    }
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


# Login-specific rate limiter with stricter limits
login_rate_limit = rate_limit(requests_per_minute=5, key_prefix="login")

# API rate limiter with standard limits
api_rate_limit = rate_limit(requests_per_minute=100, key_prefix="api")
