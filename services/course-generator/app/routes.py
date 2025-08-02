"""
Route setup following Single Responsibility Principle.
"""
from fastapi import FastAPI

from api.health import router as health_router
from api.syllabus import router as syllabus_router
from api.jobs import router as jobs_router
from api.cache import router as cache_router

def setup_routes(app: FastAPI) -> None:
    """Setup all API routes."""
    
    # Health check routes
    app.include_router(health_router, prefix="/health", tags=["health"])
    
    # Core business routes
    app.include_router(syllabus_router, prefix="/api/v1/syllabus", tags=["syllabus"])
    
    # Job management routes
    app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["jobs"])
    
    # Cache management routes
    app.include_router(cache_router, prefix="/api/v1/cache", tags=["cache"])