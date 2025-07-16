"""
Content Service

Business logic for content storage operations.
"""

import logging
import os
import uuid
import shutil
from typing import List, Optional, Dict, Any
from datetime import datetime
import aiofiles

from models.content import (
    Content, ContentCreate, ContentUpdate, ContentSearchRequest, 
    ContentUploadResponse, ContentListResponse, ContentResponse,
    ContentStats, ContentStatus
)
from models.storage import StorageQuota, StorageOperation
from repositories.content_repository import ContentRepository
from repositories.storage_repository import StorageRepository

logger = logging.getLogger(__name__)


class ContentService:
    """Service for content management operations."""
    
    def __init__(
        self, 
        content_repo: ContentRepository, 
        storage_repo: StorageRepository,
        storage_config: Dict[str, Any]
    ):
        self.content_repo = content_repo
        self.storage_repo = storage_repo
        self.storage_config = storage_config
        self.base_path = storage_config.get("base_path", "/tmp/content")
        self.max_file_size = storage_config.get("max_file_size", 100 * 1024 * 1024)
        self.allowed_extensions = storage_config.get("allowed_extensions", [])
        self.blocked_extensions = storage_config.get("blocked_extensions", [])
        
        # Ensure storage directory exists
        os.makedirs(self.base_path, exist_ok=True)
    
    async def upload_content(self, file_content: bytes, filename: str, content_type: str, uploaded_by: str = None) -> Optional[ContentUploadResponse]:
        """Upload and store content file."""
        operation_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        try:
            # Validate file
            validation_result = self._validate_file(filename, len(file_content))
            if not validation_result["valid"]:
                await self._log_operation(
                    operation_id, "upload", filename, "error", 
                    size=len(file_content), 
                    error_message=validation_result["error"]
                )
                return None
            
            # Check user quota
            if uploaded_by:
                quota_check = await self._check_user_quota(uploaded_by, len(file_content))
                if not quota_check["allowed"]:
                    await self._log_operation(
                        operation_id, "upload", filename, "error",
                        size=len(file_content),
                        error_message=quota_check["error"]
                    )
                    return None
            
            # Generate unique content ID and file path
            content_id = str(uuid.uuid4())
            file_extension = os.path.splitext(filename)[1]
            stored_filename = f"{content_id}{file_extension}"
            file_path = os.path.join(self.base_path, stored_filename)
            
            # Save file to storage
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Create content record
            content_data = ContentCreate(
                filename=filename,
                content_type=content_type,
                size=len(file_content),
                uploaded_by=uploaded_by
            )
            
            url = f"/content/{content_id}"
            content = await self.content_repo.create_content(content_data, content_id, file_path, url)
            
            if content:
                # Update user quota
                if uploaded_by:
                    await self.storage_repo.update_user_quota(uploaded_by, len(file_content), 1)
                
                # Log successful operation
                duration = (datetime.utcnow() - start_time).total_seconds()
                await self._log_operation(
                    operation_id, "upload", filename, "success",
                    size=len(file_content),
                    duration=duration
                )
                
                return ContentUploadResponse(
                    content_id=content_id,
                    filename=filename,
                    size=len(file_content),
                    url=url,
                    upload_time=content.created_at
                )
            else:
                # Clean up file if database operation failed
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                await self._log_operation(
                    operation_id, "upload", filename, "error",
                    size=len(file_content),
                    error_message="Failed to create content record"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error uploading content: {e}")
            await self._log_operation(
                operation_id, "upload", filename, "error",
                size=len(file_content),
                error_message=str(e)
            )
            return None
    
    async def get_content(self, content_id: str) -> Optional[ContentResponse]:
        """Get content by ID."""
        try:
            content = await self.content_repo.get_content_by_id(content_id)
            if content:
                # Update access count
                await self.content_repo.update_access_count(content_id)
                
                return ContentResponse(
                    success=True,
                    content=content
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting content: {e}")
            return None
    
    async def get_content_file(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Get content file data."""
        try:
            content = await self.content_repo.get_content_by_id(content_id)
            if not content:
                return None
            
            # Check if file exists
            if not os.path.exists(content.path):
                logger.error(f"Content file not found: {content.path}")
                return None
            
            # Read file content
            async with aiofiles.open(content.path, 'rb') as f:
                file_content = await f.read()
            
            # Update access count
            await self.content_repo.update_access_count(content_id)
            
            return {
                "content": file_content,
                "filename": content.filename,
                "content_type": content.content_type,
                "size": content.size
            }
            
        except Exception as e:
            logger.error(f"Error getting content file: {e}")
            return None
    
    async def list_content(self, page: int = 1, per_page: int = 100, uploaded_by: str = None) -> ContentListResponse:
        """List content with pagination."""
        try:
            content_list = await self.content_repo.list_content(page, per_page, uploaded_by)
            total = await self.content_repo.count_content(uploaded_by)
            
            return ContentListResponse(
                success=True,
                content=content_list,
                total=total,
                page=page,
                per_page=per_page
            )
            
        except Exception as e:
            logger.error(f"Error listing content: {e}")
            return ContentListResponse(
                success=False,
                content=[],
                total=0,
                page=page,
                per_page=per_page,
                message=str(e)
            )
    
    async def search_content(self, search_request: ContentSearchRequest, page: int = 1, per_page: int = 100) -> ContentListResponse:
        """Search content with filters."""
        try:
            content_list = await self.content_repo.search_content(search_request, page, per_page)
            # Note: Would need to implement count with search filters for accurate total
            total = len(content_list)
            
            return ContentListResponse(
                success=True,
                content=content_list,
                total=total,
                page=page,
                per_page=per_page
            )
            
        except Exception as e:
            logger.error(f"Error searching content: {e}")
            return ContentListResponse(
                success=False,
                content=[],
                total=0,
                page=page,
                per_page=per_page,
                message=str(e)
            )
    
    async def update_content(self, content_id: str, update_data: ContentUpdate) -> Optional[ContentResponse]:
        """Update content metadata."""
        try:
            content = await self.content_repo.update_content(content_id, update_data)
            if content:
                return ContentResponse(
                    success=True,
                    content=content
                )
            return None
            
        except Exception as e:
            logger.error(f"Error updating content: {e}")
            return None
    
    async def delete_content(self, content_id: str) -> bool:
        """Delete content (soft delete)."""
        operation_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        try:
            content = await self.content_repo.get_content_by_id(content_id)
            if not content:
                return False
            
            # Soft delete in database
            success = await self.content_repo.delete_content(content_id)
            
            if success:
                # Update user quota
                if content.uploaded_by:
                    await self.storage_repo.update_user_quota(content.uploaded_by, -content.size, -1)
                
                # Log operation
                duration = (datetime.utcnow() - start_time).total_seconds()
                await self._log_operation(
                    operation_id, "delete", content.filename, "success",
                    size=content.size,
                    duration=duration
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting content: {e}")
            await self._log_operation(
                operation_id, "delete", content_id, "error",
                error_message=str(e)
            )
            return False
    
    async def permanently_delete_content(self, content_id: str) -> bool:
        """Permanently delete content and file."""
        operation_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        try:
            content = await self.content_repo.get_content_by_id(content_id)
            if not content:
                return False
            
            # Delete file from storage
            if os.path.exists(content.path):
                os.remove(content.path)
            
            # Delete from database
            success = await self.content_repo.hard_delete_content(content_id)
            
            if success:
                # Log operation
                duration = (datetime.utcnow() - start_time).total_seconds()
                await self._log_operation(
                    operation_id, "permanent_delete", content.filename, "success",
                    size=content.size,
                    duration=duration
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error permanently deleting content: {e}")
            await self._log_operation(
                operation_id, "permanent_delete", content_id, "error",
                error_message=str(e)
            )
            return False
    
    async def get_content_stats(self, uploaded_by: str = None) -> ContentStats:
        """Get content statistics."""
        try:
            stats_data = await self.content_repo.get_content_stats(uploaded_by)
            storage_stats = await self.storage_repo.get_storage_stats()
            
            return ContentStats(
                total_files=stats_data.get("total_files", 0),
                total_size=stats_data.get("total_size", 0),
                files_by_type=stats_data.get("files_by_type", {}),
                files_by_category=stats_data.get("files_by_category", {}),
                average_file_size=stats_data.get("average_file_size", 0.0),
                storage_used=storage_stats.used_space,
                storage_available=storage_stats.available_space,
                most_accessed_files=stats_data.get("most_accessed_files", []),
                upload_trends={}  # Would need to implement trend analysis
            )
            
        except Exception as e:
            logger.error(f"Error getting content stats: {e}")
            return ContentStats(
                total_files=0,
                total_size=0,
                files_by_type={},
                files_by_category={},
                average_file_size=0.0,
                storage_used=0,
                storage_available=0,
                most_accessed_files=[],
                upload_trends={}
            )
    
    async def get_user_quota(self, user_id: str) -> Optional[StorageQuota]:
        """Get user storage quota."""
        return await self.storage_repo.get_user_quota(user_id)
    
    async def create_backup(self, content_id: str, backup_path: str) -> bool:
        """Create backup of content."""
        operation_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        try:
            content = await self.content_repo.get_content_by_id(content_id)
            if not content:
                return False
            
            # Create backup directory if it doesn't exist
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Copy file to backup location
            shutil.copy2(content.path, backup_path)
            
            # Log operation
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self._log_operation(
                operation_id, "backup", content.filename, "success",
                size=content.size,
                duration=duration,
                metadata={"backup_path": backup_path}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            await self._log_operation(
                operation_id, "backup", content_id, "error",
                error_message=str(e)
            )
            return False
    
    def _validate_file(self, filename: str, file_size: int) -> Dict[str, Any]:
        """Validate file before upload."""
        if not filename:
            return {"valid": False, "error": "Filename is required"}
        
        # Check file size
        if file_size > self.max_file_size:
            return {"valid": False, "error": f"File size exceeds maximum allowed size of {self.max_file_size} bytes"}
        
        # Check file extension
        file_extension = os.path.splitext(filename)[1].lower()
        
        if self.blocked_extensions and file_extension in self.blocked_extensions:
            return {"valid": False, "error": f"File type {file_extension} is blocked"}
        
        if self.allowed_extensions and file_extension not in self.allowed_extensions:
            return {"valid": False, "error": f"File type {file_extension} is not allowed"}
        
        return {"valid": True}
    
    async def _check_user_quota(self, user_id: str, file_size: int) -> Dict[str, Any]:
        """Check if user has sufficient quota."""
        try:
            quota = await self.storage_repo.get_user_quota(user_id)
            if not quota:
                # User has no quota record, assume they have default quota
                return {"allowed": True}
            
            if quota.quota_used + file_size > quota.quota_limit:
                return {
                    "allowed": False, 
                    "error": f"Upload would exceed storage quota. Used: {quota.quota_used}, Limit: {quota.quota_limit}"
                }
            
            if quota.file_count_limit and quota.file_count_used >= quota.file_count_limit:
                return {
                    "allowed": False,
                    "error": f"Upload would exceed file count limit. Used: {quota.file_count_used}, Limit: {quota.file_count_limit}"
                }
            
            return {"allowed": True}
            
        except Exception as e:
            logger.error(f"Error checking user quota: {e}")
            return {"allowed": True}  # Allow upload if quota check fails
    
    async def _log_operation(self, operation_id: str, operation_type: str, file_path: str, 
                           status: str, size: int = None, duration: float = None, 
                           error_message: str = None, metadata: Dict[str, Any] = None):
        """Log storage operation."""
        try:
            operation = StorageOperation(
                id=operation_id,
                operation_type=operation_type,
                file_path=file_path,
                status=status,
                size=size,
                duration=duration,
                error_message=error_message,
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )
            
            await self.storage_repo.log_storage_operation(operation)
            
        except Exception as e:
            logger.error(f"Error logging storage operation: {e}")