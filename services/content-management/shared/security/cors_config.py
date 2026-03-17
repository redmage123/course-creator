"""
Shared CORS Configuration Module

This module provides centralized CORS configuration for all microservices
in the Course Creator Platform. It enforces security best practices by:
1. Loading allowed origins from environment variables
2. Rejecting wildcard (*) origins in production
3. Providing sensible defaults for development

Business Context:
- CORS (Cross-Origin Resource Sharing) controls which websites can access APIs
- Wildcard CORS (allow_origins=["*"]) is a security vulnerability that enables:
  - Cross-Site Request Forgery (CSRF) attacks
  - Credential theft via malicious websites
  - Data exfiltration to unauthorized domains
- Multi-tenant platforms MUST restrict origins to authorized frontends only

Technical Implementation:
- Origins loaded from CORS_ORIGINS environment variable (comma-separated)
- Development mode allows localhost origins by default
- Production mode requires explicit configuration
- Validates all origins are HTTPS (except localhost for dev)

Security Standards:
- OWASP Top 10: A05:2021 Security Misconfiguration
- OWASP CORS Cheat Sheet recommendations
- CWE-942: Overly Permissive Cross-domain Whitelist

Author: Claude Code
Created: 2025-11-27
Version: 1.0.0
"""

import os
import logging
from typing import List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class CORSConfigurationError(Exception):
    """
    Custom exception for CORS configuration errors.

    Raised when CORS configuration is invalid or insecure,
    such as wildcard origins in production.
    """
    pass


@lru_cache(maxsize=1)
def get_cors_origins() -> List[str]:
    """
    Get the list of allowed CORS origins from environment configuration.

    Environment Variables:
    - CORS_ORIGINS: Comma-separated list of allowed origins
    - ENVIRONMENT: 'development' or 'production' (affects defaults)

    Development Defaults (when CORS_ORIGINS not set):
    - https://localhost:3000
    - https://localhost:3001
    - https://127.0.0.1:3000
    - https://127.0.0.1:3001

    Production Behavior:
    - CORS_ORIGINS MUST be set explicitly
    - Wildcard (*) origins are rejected with error
    - All origins must use HTTPS protocol

    Returns:
        List[str]: List of allowed origin URLs

    Raises:
        CORSConfigurationError: If configuration is invalid or insecure

    Example:
        # Environment: CORS_ORIGINS=https://app.example.com,https://admin.example.com
        origins = get_cors_origins()
        # Returns: ['https://app.example.com', 'https://admin.example.com']
    """
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    cors_origins_env = os.getenv('CORS_ORIGINS', '')

    # Parse origins from environment
    if cors_origins_env:
        origins = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]
    else:
        origins = []

    # Validate no wildcard in production
    if '*' in origins:
        if environment == 'production':
            raise CORSConfigurationError(
                "SECURITY ERROR: Wildcard CORS (*) is not allowed in production. "
                "Set CORS_ORIGINS to explicit list of allowed frontend URLs."
            )
        else:
            logger.warning(
                "SECURITY WARNING: Wildcard CORS (*) detected in non-production environment. "
                "This should be fixed before deploying to production."
            )
            # Remove wildcard and use defaults instead
            origins = [o for o in origins if o != '*']

    # Development defaults
    if not origins and environment == 'development':
        origins = [
            'https://localhost:3000',
            'https://localhost:3001',
            'https://127.0.0.1:3000',
            'https://127.0.0.1:3001',
            'http://localhost:3000',  # Allow HTTP for local dev convenience
            'http://localhost:3001',
        ]
        logger.info(f"CORS: Using development defaults: {origins}")

    # Production requires explicit configuration
    if not origins and environment == 'production':
        raise CORSConfigurationError(
            "SECURITY ERROR: CORS_ORIGINS must be set in production. "
            "Example: CORS_ORIGINS=https://app.yoursite.com,https://admin.yoursite.com"
        )

    # Validate HTTPS for production origins
    if environment == 'production':
        for origin in origins:
            if not origin.startswith('https://'):
                raise CORSConfigurationError(
                    f"SECURITY ERROR: Production CORS origin must use HTTPS: {origin}"
                )

    logger.info(f"CORS: Configured allowed origins: {origins}")
    return origins


def get_cors_config() -> dict:
    """
    Get complete CORS middleware configuration.

    Returns a dictionary suitable for FastAPI CORSMiddleware:
    - allow_origins: List of allowed origins (from environment)
    - allow_credentials: True (required for auth cookies/headers)
    - allow_methods: All standard HTTP methods
    - allow_headers: All headers (required for Authorization header)

    Returns:
        dict: Configuration for CORSMiddleware

    Example:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from shared.security.cors_config import get_cors_config

        app = FastAPI()
        app.add_middleware(CORSMiddleware, **get_cors_config())
    """
    return {
        'allow_origins': get_cors_origins(),
        'allow_credentials': True,
        'allow_methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
        'allow_headers': ['*'],  # Required for Authorization header
        'expose_headers': ['X-Request-ID', 'X-Correlation-ID'],
    }


def validate_origin(origin: str, allowed_origins: Optional[List[str]] = None) -> bool:
    """
    Validate if a specific origin is allowed.

    This is useful for programmatic origin checking in custom middleware
    or for debugging CORS issues.

    Args:
        origin: The origin URL to validate
        allowed_origins: Optional list of allowed origins (uses env config if not provided)

    Returns:
        bool: True if origin is allowed, False otherwise

    Example:
        if validate_origin('https://attacker.com'):
            # This should return False
            pass
    """
    if allowed_origins is None:
        allowed_origins = get_cors_origins()

    return origin in allowed_origins


# Clear cache helper for testing
def clear_cors_cache():
    """Clear the cached CORS origins (useful for testing)."""
    get_cors_origins.cache_clear()
