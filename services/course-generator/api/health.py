"""
Health API Routes

Simple health check and system status endpoints.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime
import logging

from ..ai.client import AIClient
from ..dependencies import get_ai_client, get_db_pool

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
async def health_check(
    ai_client: AIClient = Depends(get_ai_client),
    db_pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """
    Health check endpoint providing system status.
    
    Args:
        ai_client: AI client instance
        db_pool: Database connection pool
        
    Returns:
        Comprehensive health status
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check AI client status
    try:
        ai_status = {
            "available": ai_client.is_available,
            "model_info": ai_client.get_model_info()
        }
        health_status["services"]["ai"] = ai_status
    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        health_status["services"]["ai"] = {
            "available": False,
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check database status
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        health_status["services"]["database"] = {
            "available": True,
            "pool_size": db_pool.get_size(),
            "pool_max_size": db_pool.get_max_size()
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["services"]["database"] = {
            "available": False,
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    return health_status


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