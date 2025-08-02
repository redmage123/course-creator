"""
Course Generator API Module

This module contains all FastAPI route handlers organized by functionality.
Each sub-module handles a specific domain of the course generation system.
"""

from fastapi import APIRouter
from api.health import router as health_router
from api.syllabus import router as syllabus_router
from api.jobs import router as jobs_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(health_router, tags=["health"])
api_router.include_router(syllabus_router, prefix="/syllabus", tags=["syllabus"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])

__all__ = ["api_router"]