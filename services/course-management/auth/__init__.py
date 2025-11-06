"""
Auth module for course-management service.

BUSINESS CONTEXT:
Provides JWT authentication and authorization for course management endpoints.
Ensures only authenticated users with valid tokens can access course resources.

TECHNICAL IMPLEMENTATION:
Exports get_current_user_id function for FastAPI dependency injection.
"""

from auth.jwt_middleware import get_current_user_id

__all__ = ['get_current_user_id']
