"""
Course Generator API Module

WHAT: FastAPI route handlers organized by functionality
WHERE: Used by course-generator service for all HTTP endpoints
WHY: Provides REST API interface for content generation operations

This module contains all FastAPI route handlers organized by functionality.
Each sub-module handles a specific domain of the course generation system.

Route Organization:
- /health - Service health checks
- /syllabus - Syllabus generation (legacy)
- /jobs - Job management (legacy)
- /api/v2/generation - Content Generation V2 (Enhancement 4)
"""

from fastapi import APIRouter
from api.health import router as health_router
from api.syllabus import router as syllabus_router
from api.jobs import router as jobs_router
from api.content_generation_v2 import router as content_generation_v2_router
from api.screenshot_endpoints import router as screenshot_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(health_router, tags=["health"])
api_router.include_router(syllabus_router, prefix="/syllabus", tags=["syllabus"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])

# Content Generation V2 endpoints (Enhancement 4)
api_router.include_router(
    content_generation_v2_router,
    prefix="/api/v2/generation",
    tags=["content-generation-v2"]
)

# Screenshot-to-Course Generation endpoints
api_router.include_router(
    screenshot_router,
    prefix="/api/v1/screenshots",
    tags=["screenshot-course-generation"]
)

__all__ = ["api_router"]