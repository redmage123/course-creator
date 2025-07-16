"""
Unit tests for Content Storage Service

Tests all components of the content storage service including:
- Content models validation
- Storage models validation
- Content repositories
- Storage repositories
- Content services
- Storage services
- API routes
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import HTTPException, UploadFile
from io import BytesIO
import uuid
import os
import tempfile

# Import the modules to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/content-storage'))

from models.content import (
    Content, ContentCreate, ContentUpdate, ContentSearchRequest,
    ContentUploadResponse, ContentListResponse, ContentResponse,
    ContentStats, ContentType, ContentStatus, ContentMetadata
)
from models.storage import (
    StorageStats, StorageHealth, StorageQuota, StorageOperation,
    StorageConfig, StorageBackend
)
from models.common import BaseModel, ErrorResponse, SuccessResponse
from repositories.content_repository import ContentRepository
from repositories.storage_repository import StorageRepository
from services.content_service import ContentService
from services.storage_service import StorageService


class TestContentModels:
    """Test content data models."""
    
    def test_content_base_model_validation(self):
        """Test basic content model validation."""
        content_data = {
            "filename": "test.pdf",
            "content_type": "application/pdf",
            "size": 1024
        }
        
        content_create = ContentCreate(**content_data)
        assert content_create.filename == "test.pdf"
        assert content_create.content_type == "application/pdf"
        assert content_create.size == 1024
        assert content_create.uploaded_by is None
        assert content_create.tags == []
        assert content_create.metadata == {}
    
    def test_content_filename_validation(self):
        """Test filename validation."""
        # Valid filename
        content = ContentCreate(
            filename="valid_file.pdf",
            content_type="application/pdf",
            size=1024
        )
        assert content.filename == "valid_file.pdf"
        
        # Invalid filename with dangerous characters
        with pytest.raises(ValueError):
            ContentCreate(
                filename="file/with/path.pdf",
                content_type="application/pdf",
                size=1024
            )
        
        # Empty filename
        with pytest.raises(ValueError):
            ContentCreate(
                filename="",
                content_type="application/pdf",
                size=1024
            )
    
    def test_content_size_validation(self):
        """Test content size validation."""
        # Valid size
        content = ContentCreate(
            filename="test.pdf",
            content_type="application/pdf",
            size=1024
        )
        assert content.size == 1024
        
        # Invalid size (negative)
        with pytest.raises(ValueError):
            ContentCreate(
                filename="test.pdf",
                content_type="application/pdf",
                size=-1
            )
    
    def test_content_type_determination(self):
        """Test content type determination."""
        # Image content
        content = Content(
            id=str(uuid.uuid4()),
            filename="image.jpg",
            content_type="image/jpeg",
            size=1024,
            path="/path/to/image.jpg",
            url="/content/123",
            content_category=ContentType.IMAGE,
            storage_path="/storage/path",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        assert content.content_category == ContentType.IMAGE
        
        # Document content
        content = Content(
            id=str(uuid.uuid4()),
            filename="document.pdf",
            content_type="application/pdf",
            size=2048,
            path="/path/to/document.pdf",
            url="/content/456",
            content_category=ContentType.DOCUMENT,
            storage_path="/storage/path",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        assert content.content_category == ContentType.DOCUMENT
    
    def test_content_search_request_validation(self):
        """Test content search request validation."""
        # Valid search request
        search_req = ContentSearchRequest(
            query="test",
            content_type="application/pdf",
            size_min=1024,
            size_max=2048
        )
        assert search_req.query == "test"
        assert search_req.size_min == 1024
        assert search_req.size_max == 2048
        
        # Invalid size range
        with pytest.raises(ValueError):
            ContentSearchRequest(
                size_min=2048,
                size_max=1024
            )
        
        # Invalid date range
        with pytest.raises(ValueError):
            ContentSearchRequest(
                uploaded_after=datetime.utcnow(),
                uploaded_before=datetime.utcnow() - timedelta(days=1)
            )
    
    def test_content_metadata_model(self):
        """Test content metadata model."""
        metadata = ContentMetadata(
            width=1920,
            height=1080,
            duration=120.5,
            pages=10,
            format="PDF",
            compression="zip",
            checksum="abc123",
            extracted_text="Sample text",
            thumbnail_path="/thumbnails/thumb.jpg"
        )
        
        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.duration == 120.5
        assert metadata.pages == 10
        assert metadata.format == "PDF"


class TestStorageModels:
    """Test storage data models."""
    
    def test_storage_config_validation(self):
        """Test storage configuration validation."""
        config = StorageConfig(
            backend=StorageBackend.LOCAL,
            base_path="/storage",
            max_file_size=100 * 1024 * 1024,
            allowed_extensions=[".pdf", ".jpg", ".png"],
            enable_compression=True,
            enable_encryption=False
        )
        
        assert config.backend == StorageBackend.LOCAL
        assert config.base_path == "/storage"
        assert config.max_file_size == 100 * 1024 * 1024
        assert config.allowed_extensions == [".pdf", ".jpg", ".png"]
        assert config.enable_compression is True
        assert config.enable_encryption is False
    
    def test_storage_config_file_size_validation(self):
        """Test storage config file size validation."""
        # Valid file size
        config = StorageConfig(
            base_path="/storage",
            max_file_size=50 * 1024 * 1024
        )
        assert config.max_file_size == 50 * 1024 * 1024
        
        # Invalid file size (too large)
        with pytest.raises(ValueError):
            StorageConfig(
                base_path="/storage",
                max_file_size=2 * 1024 * 1024 * 1024  # 2GB
            )
        
        # Invalid file size (negative)
        with pytest.raises(ValueError):
            StorageConfig(
                base_path="/storage",
                max_file_size=-1
            )
    
    def test_storage_quota_model(self):
        """Test storage quota model."""
        quota = StorageQuota(
            user_id="user123",
            quota_limit=1024 * 1024 * 1024,  # 1GB
            quota_used=512 * 1024 * 1024,    # 512MB
            file_count_limit=100,
            file_count_used=50
        )
        
        assert quota.user_id == "user123"
        assert quota.quota_limit == 1024 * 1024 * 1024
        assert quota.quota_used == 512 * 1024 * 1024
        assert quota.quota_remaining == 512 * 1024 * 1024
        assert quota.quota_percentage == 50.0
        assert quota.is_quota_exceeded is False
    
    def test_storage_quota_exceeded(self):
        """Test storage quota exceeded detection."""
        quota = StorageQuota(
            quota_limit=1024 * 1024 * 1024,
            quota_used=1024 * 1024 * 1024 + 1  # Slightly over limit
        )
        
        assert quota.is_quota_exceeded is True
        assert quota.quota_remaining == 0
        assert quota.quota_percentage > 100.0
    
    def test_storage_stats_model(self):
        """Test storage statistics model."""
        stats = StorageStats(
            total_files=1000,
            total_size=5 * 1024 * 1024 * 1024,  # 5GB
            available_space=10 * 1024 * 1024 * 1024,  # 10GB
            used_space=5 * 1024 * 1024 * 1024,  # 5GB
            files_by_type={"pdf": 500, "jpg": 300, "png": 200},
            size_by_type={"pdf": 3 * 1024 * 1024 * 1024, "jpg": 1024 * 1024 * 1024, "png": 1024 * 1024 * 1024},
            upload_rate=10.5,
            storage_efficiency=0.85
        )
        
        assert stats.total_files == 1000
        assert stats.total_size == 5 * 1024 * 1024 * 1024
        assert stats.storage_utilization == 33.333333333333336  # 5GB / 15GB * 100
        assert stats.files_by_type["pdf"] == 500
        assert stats.upload_rate == 10.5
    
    def test_storage_health_model(self):
        """Test storage health model."""
        health = StorageHealth(
            status="healthy",
            disk_usage=75.0,
            available_inodes=100000,
            read_latency=5.0,
            write_latency=10.0,
            error_rate=2.0,
            last_backup=datetime.utcnow() - timedelta(hours=6),
            backup_status="success"
        )
        
        assert health.status == "healthy"
        assert health.disk_usage == 75.0
        assert health.error_rate == 2.0
        assert health.is_healthy is True
        
        # Test unhealthy conditions
        unhealthy_health = StorageHealth(
            status="warning",
            disk_usage=95.0,  # Over 90%
            available_inodes=1000,
            read_latency=5.0,
            write_latency=10.0,
            error_rate=2.0
        )
        
        assert unhealthy_health.is_healthy is False


class TestContentRepository:
    """Test content repository operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db_pool = AsyncMock()
        self.content_repository = ContentRepository(self.mock_db_pool)
    
    @pytest.mark.asyncio
    async def test_create_content(self):
        """Test content creation."""
        content_data = ContentCreate(
            filename="test.pdf",
            content_type="application/pdf",
            size=1024,
            uploaded_by="user123"
        )
        
        content_id = str(uuid.uuid4())
        file_path = "/storage/test.pdf"
        url = "/content/123"
        
        # Mock database response
        mock_row = {
            "id": content_id,
            "filename": content_data.filename,
            "content_type": content_data.content_type,
            "size": content_data.size,
            "path": file_path,
            "url": url,
            "content_category": "document",
            "status": "ready",
            "uploaded_by": content_data.uploaded_by,
            "description": None,
            "tags": [],
            "storage_path": file_path,
            "storage_backend": "local",
            "backup_path": None,
            "is_public": False,
            "access_permissions": [],
            "access_count": 0,
            "last_accessed": None,
            "metadata": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        content = await self.content_repository.create_content(content_data, content_id, file_path, url)
        
        assert content is not None
        assert content.id == content_id
        assert content.filename == content_data.filename
        assert content.content_type == content_data.content_type
        assert content.size == content_data.size
        assert content.uploaded_by == content_data.uploaded_by
    
    @pytest.mark.asyncio
    async def test_get_content_by_id(self):
        """Test getting content by ID."""
        content_id = str(uuid.uuid4())
        
        mock_row = {
            "id": content_id,
            "filename": "test.pdf",
            "content_type": "application/pdf",
            "size": 1024,
            "path": "/storage/test.pdf",
            "url": "/content/123",
            "content_category": "document",
            "status": "ready",
            "uploaded_by": "user123",
            "description": None,
            "tags": [],
            "storage_path": "/storage/test.pdf",
            "storage_backend": "local",
            "backup_path": None,
            "is_public": False,
            "access_permissions": [],
            "access_count": 5,
            "last_accessed": datetime.utcnow(),
            "metadata": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        content = await self.content_repository.get_content_by_id(content_id)
        
        assert content is not None
        assert content.id == content_id
        assert content.filename == "test.pdf"
        assert content.access_count == 5
    
    @pytest.mark.asyncio
    async def test_search_content(self):
        """Test content search."""
        search_req = ContentSearchRequest(
            query="test",
            content_type="application/pdf",
            size_min=1024,
            size_max=2048
        )
        
        mock_rows = [
            {
                "id": str(uuid.uuid4()),
                "filename": "test1.pdf",
                "content_type": "application/pdf",
                "size": 1500,
                "path": "/storage/test1.pdf",
                "url": "/content/1",
                "content_category": "document",
                "status": "ready",
                "uploaded_by": "user123",
                "description": None,
                "tags": [],
                "storage_path": "/storage/test1.pdf",
                "storage_backend": "local",
                "backup_path": None,
                "is_public": False,
                "access_permissions": [],
                "access_count": 0,
                "last_accessed": None,
                "metadata": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = mock_rows
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        content_list = await self.content_repository.search_content(search_req)
        
        assert len(content_list) == 1
        assert content_list[0].filename == "test1.pdf"
        assert content_list[0].content_type == "application/pdf"
        assert content_list[0].size == 1500
    
    @pytest.mark.asyncio
    async def test_update_content(self):
        """Test content update."""
        content_id = str(uuid.uuid4())
        update_data = ContentUpdate(
            filename="updated.pdf",
            description="Updated description",
            tags=["tag1", "tag2"]
        )
        
        mock_row = {
            "id": content_id,
            "filename": "updated.pdf",
            "content_type": "application/pdf",
            "size": 1024,
            "path": "/storage/updated.pdf",
            "url": "/content/123",
            "content_category": "document",
            "status": "ready",
            "uploaded_by": "user123",
            "description": "Updated description",
            "tags": ["tag1", "tag2"],
            "storage_path": "/storage/updated.pdf",
            "storage_backend": "local",
            "backup_path": None,
            "is_public": False,
            "access_permissions": [],
            "access_count": 0,
            "last_accessed": None,
            "metadata": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        content = await self.content_repository.update_content(content_id, update_data)
        
        assert content is not None
        assert content.filename == "updated.pdf"
        assert content.description == "Updated description"
        assert content.tags == ["tag1", "tag2"]
    
    @pytest.mark.asyncio
    async def test_delete_content(self):
        """Test content deletion (soft delete)."""
        content_id = str(uuid.uuid4())
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"id": content_id}
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        result = await self.content_repository.delete_content(content_id)
        
        assert result is True
        mock_conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_content_stats(self):
        """Test getting content statistics."""
        mock_stats_row = {
            "total_files": 100,
            "total_size": 1024 * 1024 * 1024,
            "average_file_size": 10 * 1024 * 1024
        }
        
        mock_type_rows = [
            {"content_type": "application/pdf", "count": 50},
            {"content_type": "image/jpeg", "count": 30},
            {"content_type": "image/png", "count": 20}
        ]
        
        mock_category_rows = [
            {"content_category": "document", "count": 50},
            {"content_category": "image", "count": 50}
        ]
        
        mock_accessed_rows = [
            {"filename": "popular.pdf", "access_count": 100, "last_accessed": datetime.utcnow()},
            {"filename": "another.jpg", "access_count": 50, "last_accessed": datetime.utcnow()}
        ]
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_stats_row
        mock_conn.fetch.side_effect = [mock_type_rows, mock_category_rows, mock_accessed_rows]
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        stats = await self.content_repository.get_content_stats()
        
        assert stats["total_files"] == 100
        assert stats["total_size"] == 1024 * 1024 * 1024
        assert stats["average_file_size"] == 10 * 1024 * 1024
        assert stats["files_by_type"]["application/pdf"] == 50
        assert stats["files_by_category"]["document"] == 50
        assert len(stats["most_accessed_files"]) == 2


class TestStorageRepository:
    """Test storage repository operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db_pool = AsyncMock()
        self.storage_repository = StorageRepository(self.mock_db_pool)
    
    @pytest.mark.asyncio
    async def test_get_storage_stats(self):
        """Test getting storage statistics."""
        mock_total_row = {
            "total_files": 1000,
            "total_size": 5 * 1024 * 1024 * 1024
        }
        
        mock_type_rows = [
            {"content_type": "application/pdf", "count": 500},
            {"content_type": "image/jpeg", "count": 300}
        ]
        
        mock_size_rows = [
            {"content_type": "application/pdf", "total_size": 3 * 1024 * 1024 * 1024},
            {"content_type": "image/jpeg", "total_size": 2 * 1024 * 1024 * 1024}
        ]
        
        mock_upload_rate_row = {
            "recent_uploads": 70
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.side_effect = [mock_total_row, mock_upload_rate_row]
        mock_conn.fetch.side_effect = [mock_type_rows, mock_size_rows]
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        with patch.object(self.storage_repository, '_get_available_disk_space', return_value=10 * 1024 * 1024 * 1024):
            stats = await self.storage_repository.get_storage_stats()
        
        assert stats.total_files == 1000
        assert stats.total_size == 5 * 1024 * 1024 * 1024
        assert stats.available_space == 10 * 1024 * 1024 * 1024
        assert stats.used_space == 5 * 1024 * 1024 * 1024
        assert stats.files_by_type["application/pdf"] == 500
        assert stats.size_by_type["application/pdf"] == 3 * 1024 * 1024 * 1024
        assert stats.upload_rate == 10.0  # 70 uploads / 7 days
    
    @pytest.mark.asyncio
    async def test_get_user_quota(self):
        """Test getting user quota."""
        user_id = "user123"
        
        mock_row = {
            "user_id": user_id,
            "quota_limit": 1024 * 1024 * 1024,
            "quota_used": 512 * 1024 * 1024,
            "file_count_limit": 100,
            "file_count_used": 50
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        quota = await self.storage_repository.get_user_quota(user_id)
        
        assert quota is not None
        assert quota.user_id == user_id
        assert quota.quota_limit == 1024 * 1024 * 1024
        assert quota.quota_used == 512 * 1024 * 1024
        assert quota.file_count_limit == 100
        assert quota.file_count_used == 50
    
    @pytest.mark.asyncio
    async def test_update_user_quota(self):
        """Test updating user quota."""
        user_id = "user123"
        size_delta = 10 * 1024 * 1024  # 10MB
        file_count_delta = 1
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"user_id": user_id}
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        result = await self.storage_repository.update_user_quota(user_id, size_delta, file_count_delta)
        
        assert result is True
        mock_conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_storage_health(self):
        """Test getting storage health."""
        with patch.object(self.storage_repository, '_get_disk_usage_percentage', return_value=75.0), \
             patch.object(self.storage_repository, '_get_available_inodes', return_value=100000), \
             patch.object(self.storage_repository, '_calculate_error_rate', return_value=2.0), \
             patch.object(self.storage_repository, '_get_last_backup_time', return_value=datetime.utcnow()):
            
            health = await self.storage_repository.get_storage_health()
        
        assert health.status == "healthy"
        assert health.disk_usage == 75.0
        assert health.available_inodes == 100000
        assert health.error_rate == 2.0
        assert health.is_healthy is True
    
    @pytest.mark.asyncio
    async def test_log_storage_operation(self):
        """Test logging storage operation."""
        operation = StorageOperation(
            id=str(uuid.uuid4()),
            operation_type="upload",
            file_path="/storage/test.pdf",
            status="success",
            size=1024,
            duration=2.5,
            error_message=None,
            metadata={"user_id": "user123"},
            created_at=datetime.utcnow()
        )
        
        mock_conn = AsyncMock()
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        result = await self.storage_repository.log_storage_operation(operation)
        
        assert result is True
        mock_conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_old_operations(self):
        """Test cleaning up old operations."""
        retention_days = 30
        
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "DELETE 25"
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        deleted_count = await self.storage_repository.cleanup_old_operations(retention_days)
        
        assert deleted_count == 25
        mock_conn.execute.assert_called_once()


class TestContentService:
    """Test content service business logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_content_repo = AsyncMock()
        self.mock_storage_repo = AsyncMock()
        self.storage_config = {
            "base_path": "/tmp/content",
            "max_file_size": 100 * 1024 * 1024,
            "allowed_extensions": [".pdf", ".jpg", ".png"],
            "blocked_extensions": [".exe", ".bat"]
        }
        self.content_service = ContentService(
            self.mock_content_repo,
            self.mock_storage_repo,
            self.storage_config
        )
    
    @pytest.mark.asyncio
    async def test_upload_content(self):
        """Test content upload."""
        file_content = b"test file content"
        filename = "test.pdf"
        content_type = "application/pdf"
        uploaded_by = "user123"
        
        # Mock user quota check
        mock_quota = StorageQuota(
            user_id=uploaded_by,
            quota_limit=1024 * 1024 * 1024,
            quota_used=500 * 1024 * 1024,
            file_count_limit=100,
            file_count_used=50
        )
        self.mock_storage_repo.get_user_quota.return_value = mock_quota
        
        # Mock content creation
        mock_content = Content(
            id=str(uuid.uuid4()),
            filename=filename,
            content_type=content_type,
            size=len(file_content),
            path="/storage/test.pdf",
            url="/content/123",
            content_category=ContentType.DOCUMENT,
            storage_path="/storage/test.pdf",
            uploaded_by=uploaded_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.mock_content_repo.create_content.return_value = mock_content
        
        # Mock storage operations
        self.mock_storage_repo.update_user_quota.return_value = True
        self.mock_storage_repo.log_storage_operation.return_value = True
        
        with patch('aiofiles.open', create=True) as mock_aiofiles:
            mock_file = AsyncMock()
            mock_aiofiles.return_value.__aenter__.return_value = mock_file
            
            result = await self.content_service.upload_content(file_content, filename, content_type, uploaded_by)
        
        assert result is not None
        assert result.filename == filename
        assert result.size == len(file_content)
        
        # Verify dependencies were called
        self.mock_storage_repo.get_user_quota.assert_called_once_with(uploaded_by)
        self.mock_content_repo.create_content.assert_called_once()
        self.mock_storage_repo.update_user_quota.assert_called_once()
        self.mock_storage_repo.log_storage_operation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_content_quota_exceeded(self):
        """Test content upload when quota is exceeded."""
        file_content = b"test file content"
        filename = "test.pdf"
        content_type = "application/pdf"
        uploaded_by = "user123"
        
        # Mock quota exceeded
        mock_quota = StorageQuota(
            user_id=uploaded_by,
            quota_limit=1024 * 1024,  # 1MB
            quota_used=1024 * 1024,   # 1MB (full)
            file_count_limit=100,
            file_count_used=50
        )
        self.mock_storage_repo.get_user_quota.return_value = mock_quota
        
        result = await self.content_service.upload_content(file_content, filename, content_type, uploaded_by)
        
        assert result is None
        
        # Verify quota was checked but content was not created
        self.mock_storage_repo.get_user_quota.assert_called_once_with(uploaded_by)
        self.mock_content_repo.create_content.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_upload_content_invalid_file_type(self):
        """Test content upload with invalid file type."""
        file_content = b"malicious content"
        filename = "malware.exe"
        content_type = "application/exe"
        uploaded_by = "user123"
        
        result = await self.content_service.upload_content(file_content, filename, content_type, uploaded_by)
        
        assert result is None
        
        # Verify content was not created
        self.mock_content_repo.create_content.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_content(self):
        """Test getting content."""
        content_id = str(uuid.uuid4())
        
        mock_content = Content(
            id=content_id,
            filename="test.pdf",
            content_type="application/pdf",
            size=1024,
            path="/storage/test.pdf",
            url="/content/123",
            content_category=ContentType.DOCUMENT,
            storage_path="/storage/test.pdf",
            access_count=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.mock_content_repo.get_content_by_id.return_value = mock_content
        self.mock_content_repo.update_access_count.return_value = True
        
        result = await self.content_service.get_content(content_id)
        
        assert result is not None
        assert result.success is True
        assert result.content.id == content_id
        assert result.content.filename == "test.pdf"
        
        # Verify access count was updated
        self.mock_content_repo.update_access_count.assert_called_once_with(content_id)
    
    @pytest.mark.asyncio
    async def test_get_content_file(self):
        """Test getting content file data."""
        content_id = str(uuid.uuid4())
        file_content = b"test file content"
        
        mock_content = Content(
            id=content_id,
            filename="test.pdf",
            content_type="application/pdf",
            size=len(file_content),
            path="/storage/test.pdf",
            url="/content/123",
            content_category=ContentType.DOCUMENT,
            storage_path="/storage/test.pdf",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.mock_content_repo.get_content_by_id.return_value = mock_content
        self.mock_content_repo.update_access_count.return_value = True
        
        with patch('aiofiles.open', create=True) as mock_aiofiles, \
             patch('os.path.exists', return_value=True):
            mock_file = AsyncMock()
            mock_file.read.return_value = file_content
            mock_aiofiles.return_value.__aenter__.return_value = mock_file
            
            result = await self.content_service.get_content_file(content_id)
        
        assert result is not None
        assert result["content"] == file_content
        assert result["filename"] == "test.pdf"
        assert result["content_type"] == "application/pdf"
        assert result["size"] == len(file_content)
        
        # Verify access count was updated
        self.mock_content_repo.update_access_count.assert_called_once_with(content_id)
    
    @pytest.mark.asyncio
    async def test_delete_content(self):
        """Test content deletion."""
        content_id = str(uuid.uuid4())
        
        mock_content = Content(
            id=content_id,
            filename="test.pdf",
            content_type="application/pdf",
            size=1024,
            path="/storage/test.pdf",
            url="/content/123",
            content_category=ContentType.DOCUMENT,
            storage_path="/storage/test.pdf",
            uploaded_by="user123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.mock_content_repo.get_content_by_id.return_value = mock_content
        self.mock_content_repo.delete_content.return_value = True
        self.mock_storage_repo.update_user_quota.return_value = True
        self.mock_storage_repo.log_storage_operation.return_value = True
        
        result = await self.content_service.delete_content(content_id)
        
        assert result is True
        
        # Verify dependencies were called
        self.mock_content_repo.get_content_by_id.assert_called_once_with(content_id)
        self.mock_content_repo.delete_content.assert_called_once_with(content_id)
        self.mock_storage_repo.update_user_quota.assert_called_once_with("user123", -1024, -1)
        self.mock_storage_repo.log_storage_operation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_content_stats(self):
        """Test getting content statistics."""
        mock_content_stats = {
            "total_files": 100,
            "total_size": 1024 * 1024 * 1024,
            "files_by_type": {"pdf": 50, "jpg": 30},
            "files_by_category": {"document": 50, "image": 50},
            "average_file_size": 10 * 1024 * 1024,
            "most_accessed_files": []
        }
        
        mock_storage_stats = StorageStats(
            total_files=100,
            total_size=1024 * 1024 * 1024,
            available_space=2 * 1024 * 1024 * 1024,
            used_space=1024 * 1024 * 1024,
            files_by_type={"pdf": 50, "jpg": 30},
            size_by_type={"pdf": 512 * 1024 * 1024, "jpg": 512 * 1024 * 1024},
            upload_rate=10.0,
            storage_efficiency=0.85
        )
        
        self.mock_content_repo.get_content_stats.return_value = mock_content_stats
        self.mock_storage_repo.get_storage_stats.return_value = mock_storage_stats
        
        result = await self.content_service.get_content_stats()
        
        assert result.total_files == 100
        assert result.total_size == 1024 * 1024 * 1024
        assert result.storage_used == 1024 * 1024 * 1024
        assert result.storage_available == 2 * 1024 * 1024 * 1024
        assert result.files_by_type["pdf"] == 50
        assert result.files_by_category["document"] == 50


class TestStorageService:
    """Test storage service business logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_storage_repo = AsyncMock()
        self.storage_config = {
            "base_path": "/tmp/content",
            "backup_enabled": True,
            "backup_path": "/tmp/backup",
            "retention_days": 30
        }
        self.storage_service = StorageService(self.mock_storage_repo, self.storage_config)
    
    @pytest.mark.asyncio
    async def test_get_storage_stats(self):
        """Test getting storage statistics."""
        mock_stats = StorageStats(
            total_files=1000,
            total_size=5 * 1024 * 1024 * 1024,
            available_space=10 * 1024 * 1024 * 1024,
            used_space=5 * 1024 * 1024 * 1024,
            files_by_type={"pdf": 500, "jpg": 300},
            size_by_type={"pdf": 3 * 1024 * 1024 * 1024, "jpg": 2 * 1024 * 1024 * 1024},
            upload_rate=10.0,
            storage_efficiency=0.85
        )
        
        self.mock_storage_repo.get_storage_stats.return_value = mock_stats
        
        result = await self.storage_service.get_storage_stats()
        
        assert result.total_files == 1000
        assert result.total_size == 5 * 1024 * 1024 * 1024
        assert result.storage_utilization == 33.333333333333336  # 5GB / 15GB * 100
    
    @pytest.mark.asyncio
    async def test_get_storage_health(self):
        """Test getting storage health."""
        mock_health = StorageHealth(
            status="healthy",
            disk_usage=75.0,
            available_inodes=100000,
            read_latency=5.0,
            write_latency=10.0,
            error_rate=2.0,
            last_backup=datetime.utcnow() - timedelta(hours=6),
            backup_status="success"
        )
        
        self.mock_storage_repo.get_storage_health.return_value = mock_health
        
        result = await self.storage_service.get_storage_health()
        
        assert result.status == "healthy"
        assert result.disk_usage == 75.0
        assert result.is_healthy is True
    
    @pytest.mark.asyncio
    async def test_perform_maintenance(self):
        """Test performing maintenance."""
        self.mock_storage_repo.cleanup_old_operations.return_value = 25
        
        mock_health = StorageHealth(
            status="healthy",
            disk_usage=75.0,
            available_inodes=100000,
            read_latency=5.0,
            write_latency=10.0,
            error_rate=2.0
        )
        self.mock_storage_repo.get_storage_health.return_value = mock_health
        
        with patch.object(self.storage_service, '_verify_file_integrity') as mock_verify, \
             patch.object(self.storage_service, '_create_system_backup') as mock_backup:
            
            mock_verify.return_value = {
                "status": "completed",
                "total_files": 100,
                "corrupted_files": 0,
                "integrity_rate": 100.0
            }
            
            mock_backup.return_value = {
                "status": "completed",
                "files_backed_up": 100,
                "backup_size": 1024 * 1024 * 1024
            }
            
            result = await self.storage_service.perform_maintenance()
        
        assert result["status"] == "completed"
        assert result["tasks"]["cleanup_operations"]["cleaned_count"] == 25
        assert result["tasks"]["health_check"]["health_status"] == "healthy"
        assert result["tasks"]["integrity_check"]["total_files"] == 100
        assert result["tasks"]["backup"]["files_backed_up"] == 100
    
    @pytest.mark.asyncio
    async def test_optimize_storage(self):
        """Test storage optimization."""
        mock_stats = StorageStats(
            total_files=1000,
            total_size=5 * 1024 * 1024 * 1024,
            available_space=10 * 1024 * 1024 * 1024,
            used_space=5 * 1024 * 1024 * 1024,
            files_by_type={"pdf": 500, "jpg": 300},
            size_by_type={"pdf": 3 * 1024 * 1024 * 1024, "jpg": 2 * 1024 * 1024 * 1024},
            upload_rate=10.0,
            storage_efficiency=0.85
        )
        
        self.mock_storage_repo.get_storage_stats.return_value = mock_stats
        
        with patch.object(self.storage_service, '_cleanup_orphaned_files') as mock_cleanup:
            mock_cleanup.return_value = {
                "status": "completed",
                "orphaned_files": 5,
                "space_freed": 50 * 1024 * 1024
            }
            
            result = await self.storage_service.optimize_storage()
        
        assert result["status"] == "completed"
        assert result["tasks"]["cleanup_orphaned"]["orphaned_files"] == 5
        assert result["tasks"]["stats_update"]["total_files"] == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])