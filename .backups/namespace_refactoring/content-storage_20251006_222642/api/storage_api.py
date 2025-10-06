"""
Storage API

FastAPI routes for storage management operations.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends, status

from models.storage import StorageStats, StorageHealth, StorageQuota, StorageOperation
from services.storage_service import StorageService
from exceptions import (
    ContentStorageException,
    StorageException,
    DatabaseException,
    ValidationException,
    ContentNotFoundException
)

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
        
    except StorageException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service error: {e.message}"
        )
    except DatabaseException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e.message}"
        )
    except Exception as e:
        raise ContentStorageException(
            message=f"Failed to retrieve storage statistics via API: Unexpected error in storage stats endpoint",
            error_code="API_STORAGE_STATS_ERROR",
            details={"endpoint": "/stats"},
            original_exception=e
        )


@router.get("/health", response_model=StorageHealth)
async def get_storage_health(
    storage_service: StorageService = Depends(get_storage_service)
):
    """Get storage health status."""
    try:
        result = await storage_service.get_storage_health()
        return result
        
    except StorageException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service error: {e.message}"
        )
    except DatabaseException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e.message}"
        )
    except Exception as e:
        raise ContentStorageException(
            message=f"Failed to retrieve storage health via API: Unexpected error in storage health endpoint",
            error_code="API_STORAGE_HEALTH_ERROR",
            details={"endpoint": "/health"},
            original_exception=e
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
    except StorageException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service error: {e.message}"
        )
    except DatabaseException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e.message}"
        )
    except Exception as e:
        raise ContentStorageException(
            message=f"Failed to retrieve user quota via API for user_id '{user_id}': Unexpected error in quota endpoint",
            error_code="API_USER_QUOTA_ERROR",
            details={"endpoint": f"/quota/{user_id}", "user_id": user_id},
            original_exception=e
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
    except StorageException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service error: {e.message}"
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {e.message}"
        )
    except Exception as e:
        raise ContentStorageException(
            message=f"Failed to set user quota via API for user_id '{user_id}': Unexpected error in quota update endpoint",
            error_code="API_SET_QUOTA_ERROR",
            details={"endpoint": f"/quota/{user_id}", "user_id": user_id, "quota_limit": quota_limit},
            original_exception=e
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
        
    except StorageException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service error: {e.message}"
        )
    except DatabaseException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e.message}"
        )
    except Exception as e:
        raise ContentStorageException(
            message=f"Failed to retrieve recent operations via API (limit: {limit}): Unexpected error in operations endpoint",
            error_code="API_RECENT_OPERATIONS_ERROR",
            details={"endpoint": "/operations", "limit": limit},
            original_exception=e
        )


@router.post("/maintenance")
async def perform_maintenance(
    storage_service: StorageService = Depends(get_storage_service)
):
    """Perform storage maintenance tasks."""
    try:
        result = await storage_service.perform_maintenance()
        return result
        
    except StorageException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service error: {e.message}"
        )
    except DatabaseException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e.message}"
        )
    except Exception as e:
        raise ContentStorageException(
            message=f"Failed to perform storage maintenance via API: Unexpected error in maintenance endpoint",
            error_code="API_MAINTENANCE_ERROR",
            details={"endpoint": "/maintenance"},
            original_exception=e
        )


@router.post("/optimize")
async def optimize_storage(
    storage_service: StorageService = Depends(get_storage_service)
):
    """Optimize storage by cleaning up and compacting data."""
    try:
        result = await storage_service.optimize_storage()
        return result
        
    except StorageException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service error: {e.message}"
        )
    except DatabaseException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e.message}"
        )
    except Exception as e:
        raise ContentStorageException(
            message=f"Failed to optimize storage via API: Unexpected error in storage optimization endpoint",
            error_code="API_STORAGE_OPTIMIZATION_ERROR",
            details={"endpoint": "/optimize"},
            original_exception=e
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
    except StorageException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service error: {e.message}"
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {e.message}"
        )
    except Exception as e:
        raise ContentStorageException(
            message=f"Failed to create backup via API (type: '{backup_type}'): Unexpected error in backup creation endpoint",
            error_code="API_CREATE_BACKUP_ERROR",
            details={"endpoint": "/backup", "backup_type": backup_type},
            original_exception=e
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
        
    except StorageException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service error: {e.message}"
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {e.message}"
        )
    except Exception as e:
        raise ContentStorageException(
            message=f"Failed to restore backup via API from path '{backup_path}': Unexpected error in backup restore endpoint",
            error_code="API_RESTORE_BACKUP_ERROR",
            details={"endpoint": "/restore", "backup_path": backup_path},
            original_exception=e
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
        
    except StorageException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service error: {e.message}"
        )
    except DatabaseException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e.message}"
        )
    except Exception as e:
        raise ContentStorageException(
            message=f"Failed to cleanup operations via API (retention: {retention_days} days): Unexpected error in cleanup endpoint",
            error_code="API_CLEANUP_OPERATIONS_ERROR",
            details={"endpoint": "/cleanup", "retention_days": retention_days},
            original_exception=e
        )