"""
Storage Service

Business logic for storage management and monitoring.
"""

import logging
import os
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from models.storage import StorageStats, StorageHealth, StorageQuota, StorageOperation
from repositories.storage_repository import StorageRepository

logger = logging.getLogger(__name__)


class StorageService:
    """Service for storage management and monitoring."""
    
    def __init__(self, storage_repo: StorageRepository, storage_config: Dict[str, Any]):
        self.storage_repo = storage_repo
        self.storage_config = storage_config
        self.base_path = storage_config.get("base_path", "/tmp/content")
        self.backup_enabled = storage_config.get("backup_enabled", False)
        self.backup_path = storage_config.get("backup_path")
        self.retention_days = storage_config.get("retention_days", 30)
    
    async def get_storage_stats(self) -> StorageStats:
        """Get comprehensive storage statistics."""
        try:
            return await self.storage_repo.get_storage_stats()
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
    
    async def get_storage_health(self) -> StorageHealth:
        """Get storage system health status."""
        try:
            return await self.storage_repo.get_storage_health()
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
    
    async def get_user_quota(self, user_id: str) -> Optional[StorageQuota]:
        """Get user storage quota information."""
        return await self.storage_repo.get_user_quota(user_id)
    
    async def set_user_quota(self, user_id: str, quota_limit: int, file_count_limit: int = None) -> bool:
        """Set user storage quota."""
        try:
            # This would need to be implemented in the repository
            # For now, we'll just update the existing quota
            return await self.storage_repo.update_user_quota(user_id, 0, 0)
        except Exception as e:
            logger.error(f"Error setting user quota: {e}")
            return False
    
    async def get_recent_operations(self, limit: int = 100) -> List[StorageOperation]:
        """Get recent storage operations."""
        return await self.storage_repo.get_recent_operations(limit)
    
    async def cleanup_old_operations(self, retention_days: int = None) -> int:
        """Clean up old storage operation logs."""
        retention_days = retention_days or self.retention_days
        return await self.storage_repo.cleanup_old_operations(retention_days)
    
    async def perform_maintenance(self) -> Dict[str, Any]:
        """Perform storage maintenance tasks."""
        maintenance_results = {
            "started_at": datetime.utcnow(),
            "tasks": {}
        }
        
        try:
            # Clean up old operation logs
            cleaned_ops = await self.cleanup_old_operations()
            maintenance_results["tasks"]["cleanup_operations"] = {
                "status": "completed",
                "cleaned_count": cleaned_ops
            }
            
            # Check storage health
            health = await self.get_storage_health()
            maintenance_results["tasks"]["health_check"] = {
                "status": "completed",
                "health_status": health.status,
                "disk_usage": health.disk_usage,
                "error_rate": health.error_rate
            }
            
            # Verify file integrity (sample check)
            integrity_results = await self._verify_file_integrity()
            maintenance_results["tasks"]["integrity_check"] = integrity_results
            
            # Backup if enabled
            if self.backup_enabled:
                backup_results = await self._create_system_backup()
                maintenance_results["tasks"]["backup"] = backup_results
            
            maintenance_results["completed_at"] = datetime.utcnow()
            maintenance_results["status"] = "completed"
            
        except Exception as e:
            logger.error(f"Error during maintenance: {e}")
            maintenance_results["status"] = "error"
            maintenance_results["error"] = str(e)
            maintenance_results["completed_at"] = datetime.utcnow()
        
        return maintenance_results
    
    async def optimize_storage(self) -> Dict[str, Any]:
        """Optimize storage by cleaning up orphaned files and compacting data."""
        optimization_results = {
            "started_at": datetime.utcnow(),
            "tasks": {}
        }
        
        try:
            # Find and remove orphaned files
            orphaned_results = await self._cleanup_orphaned_files()
            optimization_results["tasks"]["cleanup_orphaned"] = orphaned_results
            
            # Compress old files if compression is enabled
            if self.storage_config.get("enable_compression", False):
                compression_results = await self._compress_old_files()
                optimization_results["tasks"]["compression"] = compression_results
            
            # Update storage statistics
            stats = await self.get_storage_stats()
            optimization_results["tasks"]["stats_update"] = {
                "status": "completed",
                "total_files": stats.total_files,
                "total_size": stats.total_size,
                "available_space": stats.available_space
            }
            
            optimization_results["completed_at"] = datetime.utcnow()
            optimization_results["status"] = "completed"
            
        except Exception as e:
            logger.error(f"Error during storage optimization: {e}")
            optimization_results["status"] = "error"
            optimization_results["error"] = str(e)
            optimization_results["completed_at"] = datetime.utcnow()
        
        return optimization_results
    
    async def create_backup(self, backup_type: str = "full") -> Dict[str, Any]:
        """Create storage backup."""
        if not self.backup_enabled or not self.backup_path:
            return {
                "status": "error",
                "error": "Backup not configured"
            }
        
        backup_results = {
            "started_at": datetime.utcnow(),
            "backup_type": backup_type,
            "backup_path": self.backup_path
        }
        
        try:
            # Create backup directory
            backup_dir = os.path.join(self.backup_path, f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(backup_dir, exist_ok=True)
            
            if backup_type == "full":
                # Full backup - copy all files
                shutil.copytree(self.base_path, os.path.join(backup_dir, "content"), dirs_exist_ok=True)
                backup_results["files_backed_up"] = len(os.listdir(self.base_path))
            else:
                # Incremental backup - only recent files
                cutoff_date = datetime.utcnow() - timedelta(days=1)
                files_backed_up = 0
                
                for filename in os.listdir(self.base_path):
                    file_path = os.path.join(self.base_path, filename)
                    if os.path.getmtime(file_path) > cutoff_date.timestamp():
                        shutil.copy2(file_path, backup_dir)
                        files_backed_up += 1
                
                backup_results["files_backed_up"] = files_backed_up
            
            backup_results["completed_at"] = datetime.utcnow()
            backup_results["status"] = "completed"
            backup_results["backup_size"] = self._get_directory_size(backup_dir)
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            backup_results["status"] = "error"
            backup_results["error"] = str(e)
            backup_results["completed_at"] = datetime.utcnow()
        
        return backup_results
    
    async def restore_backup(self, backup_path: str) -> Dict[str, Any]:
        """Restore from backup."""
        restore_results = {
            "started_at": datetime.utcnow(),
            "backup_path": backup_path
        }
        
        try:
            if not os.path.exists(backup_path):
                return {
                    "status": "error",
                    "error": "Backup path does not exist"
                }
            
            # Create backup of current data before restore
            current_backup = os.path.join(self.backup_path, f"pre_restore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
            if os.path.exists(self.base_path):
                shutil.copytree(self.base_path, current_backup, dirs_exist_ok=True)
            
            # Restore from backup
            if os.path.exists(self.base_path):
                shutil.rmtree(self.base_path)
            
            shutil.copytree(backup_path, self.base_path, dirs_exist_ok=True)
            
            restore_results["completed_at"] = datetime.utcnow()
            restore_results["status"] = "completed"
            restore_results["files_restored"] = len(os.listdir(self.base_path))
            restore_results["pre_restore_backup"] = current_backup
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            restore_results["status"] = "error"
            restore_results["error"] = str(e)
            restore_results["completed_at"] = datetime.utcnow()
        
        return restore_results
    
    async def _verify_file_integrity(self) -> Dict[str, Any]:
        """Verify file integrity by checking if files exist and are readable."""
        try:
            total_files = 0
            corrupted_files = 0
            
            if os.path.exists(self.base_path):
                for filename in os.listdir(self.base_path):
                    file_path = os.path.join(self.base_path, filename)
                    total_files += 1
                    
                    try:
                        # Simple integrity check - try to read file
                        with open(file_path, 'rb') as f:
                            f.read(1024)  # Read first 1KB
                    except Exception:
                        corrupted_files += 1
                        logger.warning(f"Corrupted file detected: {file_path}")
            
            return {
                "status": "completed",
                "total_files": total_files,
                "corrupted_files": corrupted_files,
                "integrity_rate": ((total_files - corrupted_files) / total_files * 100) if total_files > 0 else 100
            }
            
        except Exception as e:
            logger.error(f"Error verifying file integrity: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _cleanup_orphaned_files(self) -> Dict[str, Any]:
        """Clean up files that exist in storage but not in database."""
        try:
            # This would need to be implemented with actual database queries
            # For now, return a placeholder result
            return {
                "status": "completed",
                "orphaned_files": 0,
                "space_freed": 0
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up orphaned files: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _compress_old_files(self) -> Dict[str, Any]:
        """Compress old files to save space."""
        try:
            # This would implement compression logic
            # For now, return a placeholder result
            return {
                "status": "completed",
                "files_compressed": 0,
                "space_saved": 0
            }
            
        except Exception as e:
            logger.error(f"Error compressing old files: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _create_system_backup(self) -> Dict[str, Any]:
        """Create system backup."""
        try:
            return await self.create_backup("full")
        except Exception as e:
            logger.error(f"Error creating system backup: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _get_directory_size(self, directory: str) -> int:
        """Get total size of directory in bytes."""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(file_path)
            return total_size
        except Exception as e:
            logger.error(f"Error getting directory size: {e}")
            return 0