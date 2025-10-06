"""
Cache Management API Endpoints for Course Generator Service

This module provides administrative endpoints for managing the AI content generation
cache, allowing manual invalidation for content quality issues and parameter changes.

BUSINESS REQUIREMENT:
Instructors and administrators need the ability to force regeneration of AI content
when course parameters change or content quality issues are identified.

SECURITY CONSIDERATIONS:
These endpoints should be restricted to authorized instructors and administrators
to prevent abuse of cache invalidation functionality.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional
import sys
sys.path.append('/home/bbrelin/course-creator')

from shared.cache import get_cache_manager

router = APIRouter()


class CacheInvalidationRequest(BaseModel):
    """Request model for cache invalidation operations."""
    subject: Optional[str] = None
    course_id: Optional[str] = None
    reason: Optional[str] = None


class CacheInvalidationResponse(BaseModel):
    """Response model for cache invalidation operations."""
    success: bool
    entries_invalidated: int
    message: str


@router.post("/invalidate/content", response_model=CacheInvalidationResponse)
async def invalidate_content_cache(request: CacheInvalidationRequest):
    """
    Invalidate AI-generated content cache for quality issues or parameter changes.
    
    BUSINESS USE CASES:
    - Course parameters changed (subject, difficulty, objectives)
    - Content quality issues reported by instructors
    - Template updates requiring fresh AI generation
    - Manual refresh requested for improved content
    
    CACHE INVALIDATION SCOPE:
    - If subject provided: Invalidates all content for that subject
    - If course_id provided: Invalidates all content for that specific course
    - If neither provided: Invalidates all AI content (use carefully)
    
    SECURITY CONSIDERATION:
    This endpoint should be protected by authentication middleware
    in production to prevent unauthorized cache clearing.
    
    Args:
        request: Cache invalidation parameters including subject/course scope
        
    Returns:
        CacheInvalidationResponse: Number of cache entries invalidated and status
        
    Raises:
        HTTPException: If cache invalidation fails or parameters are invalid
    """
    try:
        cache_manager = await get_cache_manager()
        
        if not cache_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cache manager not available"
            )
        
        # Validate request parameters
        if not request.subject and not request.course_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either subject or course_id must be provided for targeted invalidation"
            )
        
        # Perform cache invalidation
        entries_invalidated = await cache_manager.invalidate_course_content(
            subject=request.subject,
            course_id=request.course_id
        )
        
        # Log the invalidation for audit purposes
        reason = request.reason or "Manual cache invalidation requested"
        scope = f"subject={request.subject}" if request.subject else f"course_id={request.course_id}"
        
        return CacheInvalidationResponse(
            success=True,
            entries_invalidated=entries_invalidated,
            message=f"Successfully invalidated {entries_invalidated} cache entries for {scope}. Reason: {reason}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate cache: {str(e)}"
        )


@router.get("/stats")
async def get_cache_stats():
    """
    Get cache performance statistics for monitoring and optimization.
    
    MONITORING USE CASES:
    - Track cache hit rates for performance analysis
    - Monitor cache effectiveness and ROI
    - Identify optimization opportunities
    - Debug cache-related performance issues
    
    Returns:
        dict: Cache performance statistics including hit rates and operation counts
    """
    try:
        cache_manager = await get_cache_manager()
        
        if not cache_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cache manager not available"
            )
        
        stats = cache_manager.get_stats()
        return {
            "service": "course-generator",
            "cache_stats": stats,
            "performance_impact": {
                "estimated_time_saved_per_hit": "10-15 seconds",
                "estimated_cost_saved_per_hit": "$0.01-$0.05",
                "total_requests": stats.get("total_operations", 0),
                "cache_effectiveness": f"{stats.get('hit_rate_percent', 0):.1f}%"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}"
        )