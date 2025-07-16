"""
Course Generator API Module

This module contains all FastAPI route handlers organized by functionality.
Each sub-module handles a specific domain of the course generation system.
"""

from fastapi import APIRouter
from .health import router as health_router
from .courses import router as courses_router
from .slides import router as slides_router
from .exercises import router as exercises_router
from .quizzes import router as quizzes_router
from .labs import router as labs_router
from .syllabus import router as syllabus_router
from .content import router as content_router
from .ai_assistant import router as ai_assistant_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(health_router, tags=["health"])
api_router.include_router(courses_router, prefix="/courses", tags=["courses"])
api_router.include_router(slides_router, prefix="/slides", tags=["slides"])
api_router.include_router(exercises_router, prefix="/exercises", tags=["exercises"])
api_router.include_router(quizzes_router, prefix="/quizzes", tags=["quizzes"])
api_router.include_router(labs_router, prefix="/lab", tags=["labs"])
api_router.include_router(syllabus_router, prefix="/syllabus", tags=["syllabus"])
api_router.include_router(content_router, prefix="/content", tags=["content"])
api_router.include_router(ai_assistant_router, prefix="/ai-assistant", tags=["ai-assistant"])

__all__ = ["api_router"]