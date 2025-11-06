"""
Content Management API Endpoints

This package contains modular API router implementations following SOLID principles.
Each router module focuses on a specific domain of educational content management.

Modules:
- syllabus_endpoints: Syllabus creation, management, and lifecycle operations
- content_endpoints: Content search, recommendations, validation, export
- analytics_endpoints: Content statistics and usage metrics

Architecture:
Following the Single Responsibility Principle, each router module handles
a specific domain of educational content management, promoting clean separation
of concerns and maintainable code organization.
"""

from .syllabus_endpoints import router as syllabus_router
from .content_endpoints import router as content_router
from .analytics_endpoints import router as analytics_router

__all__ = ['syllabus_router', 'content_router', 'analytics_router']
