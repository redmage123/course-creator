"""
API Routes Module for Demo Service

This module contains all API route handlers for the demo service,
including privacy compliance endpoints.
"""

from .privacy_routes import router as privacy_router

__all__ = ['privacy_router']
