"""
Shared Middleware Module

This module provides common middleware components used across all microservices
in the Course Creator Platform.

Available middleware:
- CSRFProtectionMiddleware: Validates X-Requested-With header for CSRF protection
"""

from services.shared.middleware.csrf import CSRFProtectionMiddleware

__all__ = ['CSRFProtectionMiddleware']
