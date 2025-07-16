"""
Storage API

FastAPI routes for storage management operations.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends, status

from models.storage import StorageStats, StorageHealth, StorageQuota, StorageOperation
from services.storage_service import StorageService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_storage_service() -> StorageService:
    """Dependency injection for storage service."""
    # This would be replaced with actual dependency injection
    # For now, return None and handle in the endpoint
    return None


@router.get("/stats", response_model=StorageStats)
async def get_storage_stats(
    storage_service: StorageService = Depends(get_storage_service)
):
    """Get storage statistics."""
    try:
        result = await storage_service.get_storage_stats()
        return result
        
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/health", response_model=StorageHealth)
async def get_storage_health(
    storage_service: StorageService = Depends(get_storage_service)
):
    """Get storage health status."""
    try:
        result = await storage_service.get_storage_health()
        return result
        
    except Exception as e:
        logger.error(f"Error getting storage health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/quota/{user_id}", response_model=StorageQuota)
async def get_user_quota(
    user_id: str,
    storage_service: StorageService = Depends(get_storage_service)
):
    """Get user storage quota."""
    try:
        result = await storage_service.get_user_quota(user_id)
        
        if result:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User quota not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/quota/{user_id}")
async def set_user_quota(
    user_id: str,
    quota_limit: int = Query(..., description="Quota limit in bytes"),
    file_count_limit: Optional[int] = Query(None, description="File count limit"),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Set user storage quota."""
    try:
        success = await storage_service.set_user_quota(user_id, quota_limit, file_count_limit)
        
        if success:
            return {"message": "Quota updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update quota"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting user quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/operations", response_model=List[StorageOperation])
async def get_recent_operations(
    limit: int = Query(100, ge=1, le=1000),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Get recent storage operations."""
    try:
        result = await storage_service.get_recent_operations(limit)
        return result
        
    except Exception as e:
        logger.error(f"Error getting recent operations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/maintenance")
async def perform_maintenance(
    storage_service: StorageService = Depends(get_storage_service)
):
    """Perform storage maintenance tasks."""
    try:
        result = await storage_service.perform_maintenance()
        return result
        
    except Exception as e:
        logger.error(f"Error performing maintenance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/optimize")
async def optimize_storage(
    storage_service: StorageService = Depends(get_storage_service)
):
    """Optimize storage by cleaning up and compacting data."""
    try:
        result = await storage_service.optimize_storage()
        return result
        
    except Exception as e:
        logger.error(f"Error optimizing storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/backup")
async def create_backup(
    backup_type: str = Query("full", description="Backup type: full or incremental"),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Create storage backup."""
    try:
        if backup_type not in ["full", "incremental"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Backup type must be 'full' or 'incremental'"
            )
        
        result = await storage_service.create_backup(backup_type)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/restore")
async def restore_backup(
    backup_path: str = Query(..., description="Path to backup to restore"),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Restore from backup."""
    try:
        result = await storage_service.restore_backup(backup_path)
        return result
        
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/operations/cleanup")
async def cleanup_old_operations(
    retention_days: int = Query(30, ge=1, description="Retention period in days"),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Clean up old storage operation logs."""
    try:
        cleaned_count = await storage_service.cleanup_old_operations(retention_days)
        return {
            "message": f"Cleaned up {cleaned_count} old operations",
            "cleaned_count": cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up operations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )