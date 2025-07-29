"""
Route setup following Single Responsibility Principle.
"""
from fastapi import FastAPI

from ..api.health import router as health_router
from ..api.syllabus import router as syllabus_router
from ..api.jobs import router as jobs_router
from ..api.courses import router as courses_router
from ..api.exercises import router as exercises_router
from ..api.labs import router as labs_router

def setup_routes(app: FastAPI) -> None:
    """Setup all API routes."""
    
    # Health check routes
    app.include_router(health_router, prefix="/health", tags=["health"])
    
    # Core business routes
    app.include_router(syllabus_router, prefix="/api/v1/syllabus", tags=["syllabus"])
    app.include_router(courses_router, prefix="/api/v1/courses", tags=["courses"])
    app.include_router(exercises_router, prefix="/api/v1/exercises", tags=["exercises"])
    app.include_router(labs_router, prefix="/api/v1/labs", tags=["labs"])
    
    # Job management routes
    app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["jobs"])