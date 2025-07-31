"""
Health API Routes

Simple health check and system status endpoints.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime
import logging

from ai.client import AIClient
from app.dependencies import get_container

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def root() -> Dict[str, Any]:
    """
    Root endpoint providing basic API information.
    
    Returns:
        Basic API information and status
    """
    return {
        "message": "Course Generator API",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Basic health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "course-generator",
        "version": "2.0.0"
    }


@router.get("/templates")
async def get_templates() -> Dict[str, Any]:
    """
    Get available course templates.
    
    Returns:
        Available course templates
        
    Note:
        This is a placeholder for the templates functionality
        that was in the original main.py
    """
    # TODO: Move template logic from main.py to a proper service
    return {
        "templates": [],
        "message": "Template functionality will be moved to CourseService"
    }