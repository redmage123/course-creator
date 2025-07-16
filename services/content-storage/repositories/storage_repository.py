"""
Storage Repository

Repository pattern implementation for storage operations and statistics.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncpg
import os

from models.storage import StorageStats, StorageQuota, StorageHealth, StorageOperation

logger = logging.getLogger(__name__)


class StorageRepository:
    """Repository for storage operations and statistics."""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    async def get_storage_stats(self) -> StorageStats:
        """Get comprehensive storage statistics."""
        try:
            async with self.db_pool.acquire() as conn:
                # Total files and size
                total_query = """
                    SELECT 
                        COUNT(*) as total_files,
                        COALESCE(SUM(size), 0) as total_size
                    FROM content 
                    WHERE status != 'deleted'
                """
                total_row = await conn.fetchrow(total_query)
                
                # Files by type
                type_query = """
                    SELECT content_type, COUNT(*) as count
                    FROM content 
                    WHERE status != 'deleted'
                    GROUP BY content_type
                """
                type_rows = await conn.fetch(type_query)
                
                # Size by type
                size_query = """
                    SELECT content_type, COALESCE(SUM(size), 0) as total_size
                    FROM content 
                    WHERE status != 'deleted'
                    GROUP BY content_type
                """
                size_rows = await conn.fetch(size_query)
                
                # Calculate upload rate (files per day over last 7 days)
                upload_rate_query = """
                    SELECT COUNT(*) as recent_uploads
                    FROM content 
                    WHERE status != 'deleted' 
                    AND created_at >= $1
                """
                week_ago = datetime.utcnow() - timedelta(days=7)
                upload_rate_row = await conn.fetchrow(upload_rate_query, week_ago)
                
                # Get disk usage (this would need to be implemented based on storage backend)
                available_space = self._get_available_disk_space()
                used_space = total_row["total_size"]
                
                return StorageStats(
                    total_files=total_row["total_files"],
                    total_size=total_row["total_size"],
                    available_space=available_space,
                    used_space=used_space,
                    files_by_type={row["content_type"]: row["count"] for row in type_rows},
                    size_by_type={row["content_type"]: row["total_size"] for row in size_rows},
                    upload_rate=upload_rate_row["recent_uploads"] / 7.0,  # per day
                    storage_efficiency=1.0  # placeholder - would calculate compression ratio
                )
                
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return StorageStats(
                total_files=0,
                total_size=0,
                available_space=0,
                used_space=0,
                files_by_type={},
                size_by_type={},
                upload_rate=0.0,
                storage_efficiency=1.0
            )
    
    async def get_user_quota(self, user_id: str) -> Optional[StorageQuota]:
        """Get user storage quota."""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT 
                        user_id,
                        quota_limit,
                        quota_used,
                        file_count_limit,
                        file_count_used
                    FROM storage_quotas 
                    WHERE user_id = $1
                """
                row = await conn.fetchrow(query, user_id)
                
                if row:
                    return StorageQuota(
                        user_id=row["user_id"],
                        quota_limit=row["quota_limit"],
                        quota_used=row["quota_used"],
                        file_count_limit=row["file_count_limit"],
                        file_count_used=row["file_count_used"]
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting user quota: {e}")
            return None
    
    async def update_user_quota(self, user_id: str, size_delta: int, file_count_delta: int = 0) -> bool:
        """Update user quota usage."""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    UPDATE storage_quotas 
                    SET 
                        quota_used = quota_used + $1,
                        file_count_used = file_count_used + $2
                    WHERE user_id = $3
                    RETURNING user_id
                """
                row = await conn.fetchrow(query, size_delta, file_count_delta, user_id)
                
                if not row:
                    # Create quota record if it doesn't exist
                    default_quota = 1024 * 1024 * 1024  # 1GB default
                    insert_query = """
                        INSERT INTO storage_quotas (user_id, quota_limit, quota_used, file_count_used)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (user_id) DO UPDATE SET
                            quota_used = storage_quotas.quota_used + $3,
                            file_count_used = storage_quotas.file_count_used + $4
                    """
                    await conn.execute(insert_query, user_id, default_quota, max(0, size_delta), max(0, file_count_delta))
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating user quota: {e}")
            return False
    
    async def get_storage_health(self) -> StorageHealth:
        """Get storage system health metrics."""
        try:
            # Get disk usage
            disk_usage = self._get_disk_usage_percentage()
            
            # Get available inodes (Unix-specific)
            available_inodes = self._get_available_inodes()
            
            # Calculate read/write latency (placeholder - would need actual metrics)
            read_latency = 5.0  # ms
            write_latency = 10.0  # ms
            
            # Calculate error rate from recent operations
            error_rate = await self._calculate_error_rate()
            
            # Determine overall status
            status = "healthy"
            if disk_usage > 90 or error_rate > 10:
                status = "critical"
            elif disk_usage > 80 or error_rate > 5:
                status = "warning"
            
            return StorageHealth(
                status=status,
                disk_usage=disk_usage,
                available_inodes=available_inodes,
                read_latency=read_latency,
                write_latency=write_latency,
                error_rate=error_rate,
                last_backup=await self._get_last_backup_time(),
                backup_status="unknown"
            )
            
        except Exception as e:
            logger.error(f"Error getting storage health: {e}")
            return StorageHealth(
                status="error",
                disk_usage=0.0,
                available_inodes=0,
                read_latency=0.0,
                write_latency=0.0,
                error_rate=100.0
            )
    
    async def log_storage_operation(self, operation: StorageOperation) -> bool:
        """Log a storage operation."""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    INSERT INTO storage_operations (
                        id, operation_type, file_path, status, size, 
                        duration, error_message, metadata, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """
                await conn.execute(
                    query,
                    operation.id,
                    operation.operation_type,
                    operation.file_path,
                    operation.status,
                    operation.size,
                    operation.duration,
                    operation.error_message,
                    operation.metadata,
                    operation.created_at or datetime.utcnow()
                )
                return True
                
        except Exception as e:
            logger.error(f"Error logging storage operation: {e}")
            return False
    
    async def get_recent_operations(self, limit: int = 100) -> List[StorageOperation]:
        """Get recent storage operations."""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT * FROM storage_operations 
                    ORDER BY created_at DESC 
                    LIMIT $1
                """
                rows = await conn.fetch(query, limit)
                
                return [
                    StorageOperation(
                        id=row["id"],
                        operation_type=row["operation_type"],
                        file_path=row["file_path"],
                        status=row["status"],
                        size=row["size"],
                        duration=row["duration"],
                        error_message=row["error_message"],
                        metadata=row["metadata"] or {},
                        created_at=row["created_at"]
                    )
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Error getting recent operations: {e}")
            return []
    
    async def cleanup_old_operations(self, retention_days: int = 30) -> int:
        """Clean up old storage operation logs."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            async with self.db_pool.acquire() as conn:
                query = "DELETE FROM storage_operations WHERE created_at < $1"
                result = await conn.execute(query, cutoff_date)
                
                # Extract count from result string like "DELETE 123"
                deleted_count = int(result.split()[-1]) if result.split()[-1].isdigit() else 0
                logger.info(f"Cleaned up {deleted_count} old storage operations")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up old operations: {e}")
            return 0
    
    def _get_available_disk_space(self) -> int:
        """Get available disk space in bytes."""
        try:
            import shutil
            # This would use the configured storage path
            storage_path = "/tmp"  # placeholder
            return shutil.disk_usage(storage_path).free
        except Exception:
            return 0
    
    def _get_disk_usage_percentage(self) -> float:
        """Get disk usage percentage."""
        try:
            import shutil
            storage_path = "/tmp"  # placeholder
            total, used, free = shutil.disk_usage(storage_path)
            return (used / total) * 100 if total > 0 else 0.0
        except Exception:
            return 0.0
    
    def _get_available_inodes(self) -> int:
        """Get available inodes (Unix-specific)."""
        try:
            import os
            storage_path = "/tmp"  # placeholder
            statvfs = os.statvfs(storage_path)
            return statvfs.f_favail
        except Exception:
            return 0
    
    async def _calculate_error_rate(self) -> float:
        """Calculate error rate from recent operations."""
        try:
            async with self.db_pool.acquire() as conn:
                # Get operations from last hour
                hour_ago = datetime.utcnow() - timedelta(hours=1)
                query = """
                    SELECT 
                        COUNT(*) as total_ops,
                        COUNT(CASE WHEN status = 'error' THEN 1 END) as error_ops
                    FROM storage_operations 
                    WHERE created_at >= $1
                """
                row = await conn.fetchrow(query, hour_ago)
                
                if row and row["total_ops"] > 0:
                    return (row["error_ops"] / row["total_ops"]) * 100
                
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating error rate: {e}")
            return 0.0
    
    async def _get_last_backup_time(self) -> Optional[datetime]:
        """Get timestamp of last backup."""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT MAX(created_at) as last_backup
                    FROM storage_operations 
                    WHERE operation_type = 'backup' AND status = 'success'
                """
                row = await conn.fetchrow(query)
                return row["last_backup"] if row else None
                
        except Exception as e:
            logger.error(f"Error getting last backup time: {e}")
            return None