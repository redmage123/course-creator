"""
Content Management API Endpoints

This package contains modular API router implementations following SOLID principles.
Each router module focuses on a specific domain of educational content management.

Modules:
- syllabus_endpoints: Syllabus creation, management, and lifecycle operations
- content_endpoints: Content search, recommendations, validation, export
- analytics_endpoints: Content statistics and usage metrics
- interactive_content: Interactive content types (simulations, flashcards, etc.)
- content_version: Content versioning, branching, and approval workflows
- advanced_assessment_endpoints: Advanced assessments (rubrics, peer review, portfolios)

Architecture:
Following the Single Responsibility Principle, each router module handles
a specific domain of educational content management, promoting clean separation
of concerns and maintainable code organization.
"""

from .syllabus_endpoints import router as syllabus_router
from .content_endpoints import router as content_router
from .analytics_endpoints import router as analytics_router
from .interactive_content import router as interactive_content_router
from .content_version import router as content_version_router
from .advanced_assessment_endpoints import router as advanced_assessment_router

__all__ = [
    'syllabus_router',
    'content_router',
    'analytics_router',
    'interactive_content_router',
    'content_version_router',
    'advanced_assessment_router'
]
