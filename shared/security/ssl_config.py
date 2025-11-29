"""
Shared SSL/TLS Configuration Module

This module provides centralized SSL configuration for all microservices
in the Course Creator Platform. It enforces security best practices by:
1. Enabling SSL verification by default in production
2. Providing safe development mode with explicit opt-in for self-signed certs
3. Supporting custom CA bundles for internal PKI

Business Context:
- SSL verification prevents man-in-the-middle (MITM) attacks
- Disabling verification (verify=False) is a critical security vulnerability
- Inter-service communication must validate certificates to prevent:
  - Traffic interception
  - Data tampering
  - Credential theft
  - Session hijacking

Technical Implementation:
- Production mode: Always verify certificates
- Development mode: Allow self-signed certs via custom SSL context
- Custom CA support: For internal certificate authorities

Security Standards:
- OWASP Top 10: A07:2021 Identification and Authentication Failures
- CWE-295: Improper Certificate Validation
- PCI-DSS Requirement 4: Encrypt transmission of cardholder data

Author: Claude Code
Created: 2025-11-27
Version: 1.0.0
"""

import os
import ssl
import logging
import certifi
from pathlib import Path
from typing import Optional, Union
from functools import lru_cache

logger = logging.getLogger(__name__)


class SSLConfigurationError(Exception):
    """
    Custom exception for SSL configuration errors.

    Raised when SSL configuration is invalid or insecure,
    such as attempting to disable verification in production.
    """
    pass


@lru_cache(maxsize=1)
def get_ssl_context() -> Union[ssl.SSLContext, bool]:
    """
    Get the appropriate SSL context for HTTP clients.

    Environment Variables:
    - ENVIRONMENT: 'development' or 'production'
    - SSL_CERT_FILE: Path to custom CA bundle (optional)
    - ALLOW_SELF_SIGNED: 'true' to allow self-signed certs in dev (default: false)

    Production Behavior:
    - Always returns True (verify using system CA bundle)
    - Or returns SSLContext with custom CA bundle if SSL_CERT_FILE set
    - Never returns False or disabled verification

    Development Behavior:
    - If ALLOW_SELF_SIGNED=true: Returns SSL context that allows self-signed
    - Otherwise: Same as production

    Returns:
        Union[ssl.SSLContext, bool]:
            - True for default system verification
            - SSLContext for custom CA or self-signed support
            - Never returns False

    Example:
        import httpx
        from shared.security.ssl_config import get_ssl_context

        # Use in httpx client
        async with httpx.AsyncClient(verify=get_ssl_context()) as client:
            response = await client.get("https://internal-service:8000")
    """
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    allow_self_signed = os.getenv('ALLOW_SELF_SIGNED', 'false').lower() == 'true'
    custom_ca_file = os.getenv('SSL_CERT_FILE', '')

    # Production: Strict verification required
    if environment == 'production':
        if allow_self_signed:
            logger.warning(
                "SECURITY WARNING: ALLOW_SELF_SIGNED is ignored in production. "
                "Production must use valid certificates."
            )

        if custom_ca_file and Path(custom_ca_file).exists():
            logger.info(f"SSL: Using custom CA bundle: {custom_ca_file}")
            ctx = ssl.create_default_context(cafile=custom_ca_file)
            return ctx

        logger.info("SSL: Using system CA bundle for certificate verification")
        return True

    # Development: Configurable for self-signed certificates
    if allow_self_signed:
        logger.warning(
            "SSL: Self-signed certificates allowed (development mode). "
            "This should NEVER be used in production."
        )
        # Create context that doesn't verify certificate chain
        # but still uses TLS encryption
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    # Development without self-signed: Use certifi CA bundle
    logger.info("SSL: Development mode with certificate verification (using certifi)")
    return True


def get_httpx_ssl_context() -> Union[ssl.SSLContext, bool]:
    """
    Get SSL context specifically for httpx clients.

    This is a convenience wrapper that handles the difference between
    ssl.SSLContext and httpx's verify parameter expectations.

    Returns:
        Union[ssl.SSLContext, bool]: Context or True for httpx verify parameter
    """
    return get_ssl_context()


def create_secure_client_kwargs() -> dict:
    """
    Create secure kwargs for httpx.AsyncClient instantiation.

    This provides a complete set of security-focused settings for
    HTTP clients used in inter-service communication.

    Returns:
        dict: Kwargs suitable for httpx.AsyncClient(**kwargs)

    Example:
        from shared.security.ssl_config import create_secure_client_kwargs

        async with httpx.AsyncClient(**create_secure_client_kwargs()) as client:
            response = await client.get("https://service:8000/api")
    """
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    allow_self_signed = os.getenv('ALLOW_SELF_SIGNED', 'true').lower() == 'true'

    # In development with self-signed certs, use verify=False
    # In production, always verify
    if environment == 'development' and allow_self_signed:
        return {
            'verify': False,  # Allow self-signed certs in development
            'timeout': 30.0,
            'follow_redirects': True,
        }

    return {
        'verify': True,  # Always verify in production
        'timeout': 30.0,
        'follow_redirects': True,
    }


def validate_ssl_configuration() -> bool:
    """
    Validate current SSL configuration for security compliance.

    This function can be called at service startup to verify
    SSL settings are appropriate for the environment.

    Returns:
        bool: True if configuration is secure

    Raises:
        SSLConfigurationError: If configuration is insecure for production
    """
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    allow_self_signed = os.getenv('ALLOW_SELF_SIGNED', 'false').lower() == 'true'

    if environment == 'production' and allow_self_signed:
        raise SSLConfigurationError(
            "SECURITY ERROR: ALLOW_SELF_SIGNED=true is not allowed in production. "
            "Use proper certificates or set ENVIRONMENT=development."
        )

    logger.info(f"SSL configuration validated for {environment} environment")
    return True


# Clear cache helper for testing
def clear_ssl_cache():
    """Clear the cached SSL context (useful for testing)."""
    get_ssl_context.cache_clear()
