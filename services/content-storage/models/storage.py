"""
Storage Models

Pydantic models for storage configuration and management.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from models.common import TimestampMixin


class StorageBackend(str, Enum):
    """Storage backend types."""
    LOCAL = "local"
    S3 = "s3"
    AZURE = "azure"
    GCS = "gcs"


class StorageConfig(BaseModel):
    """Storage configuration model."""
    backend: StorageBackend = StorageBackend.LOCAL
    base_path: str = Field(..., description="Base storage path")
    max_file_size: int = Field(100 * 1024 * 1024, description="Maximum file size in bytes")
    allowed_extensions: List[str] = Field(default_factory=list)
    blocked_extensions: List[str] = Field(default_factory=list)
    enable_compression: bool = False
    enable_encryption: bool = False
    backup_enabled: bool = False
    backup_path: Optional[str] = None
    
    # S3 specific
    s3_bucket: Optional[str] = None
    s3_region: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    
    # Azure specific
    azure_account_name: Optional[str] = None
    azure_account_key: Optional[str] = None
    azure_container: Optional[str] = None
    
    # GCS specific
    gcs_bucket: Optional[str] = None
    gcs_credentials_path: Optional[str] = None
    
    @validator('max_file_size')
    def validate_max_file_size(cls, v):
        if v <= 0:
            raise ValueError('Maximum file size must be positive')
        if v > 1024 * 1024 * 1024:  # 1GB limit
            raise ValueError('Maximum file size cannot exceed 1GB')
        return v


class StorageQuota(BaseModel):
    """Storage quota model."""
    user_id: Optional[str] = None
    quota_limit: int = Field(..., description="Quota limit in bytes")
    quota_used: int = Field(0, description="Quota used in bytes")
    file_count_limit: Optional[int] = None
    file_count_used: int = 0
    
    @property
    def quota_remaining(self) -> int:
        return max(0, self.quota_limit - self.quota_used)
    
    @property
    def quota_percentage(self) -> float:
        if self.quota_limit == 0:
            return 0.0
        return (self.quota_used / self.quota_limit) * 100
    
    @property
    def is_quota_exceeded(self) -> bool:
        return self.quota_used >= self.quota_limit


class StorageStats(BaseModel):
    """Storage statistics model."""
    total_files: int
    total_size: int
    available_space: int
    used_space: int
    files_by_type: Dict[str, int]
    size_by_type: Dict[str, int]
    upload_rate: float  # files per day
    storage_efficiency: float  # compression ratio
    
    @property
    def storage_utilization(self) -> float:
        total_space = self.used_space + self.available_space
        if total_space == 0:
            return 0.0
        return (self.used_space / total_space) * 100


class StorageHealth(BaseModel):
    """Storage health model."""
    status: str = Field(..., description="Overall health status")
    disk_usage: float = Field(..., description="Disk usage percentage")
    available_inodes: int = Field(..., description="Available inodes")
    read_latency: float = Field(..., description="Average read latency in ms")
    write_latency: float = Field(..., description="Average write latency in ms")
    error_rate: float = Field(..., description="Error rate percentage")
    last_backup: Optional[datetime] = None
    backup_status: str = "unknown"
    
    @property
    def is_healthy(self) -> bool:
        return (
            self.status == "healthy" and
            self.disk_usage < 90 and
            self.error_rate < 5
        )


class StorageOperation(BaseModel, TimestampMixin):
    """Storage operation model."""
    id: str
    operation_type: str = Field(..., description="Type of operation")
    file_path: str
    status: str = Field(..., description="Operation status")
    size: Optional[int] = None
    duration: Optional[float] = None  # in seconds
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StorageBackupConfig(BaseModel):
    """Storage backup configuration model."""
    enabled: bool = False
    backup_path: str
    schedule: str = Field("0 2 * * *", description="Cron schedule for backups")
    retention_days: int = Field(30, ge=1, description="Backup retention in days")
    compression: bool = True
    encryption: bool = False
    incremental: bool = True
    
    @validator('schedule')
    def validate_cron_schedule(cls, v):
        # Basic validation for cron format
        parts = v.split()
        if len(parts) != 5:
            raise ValueError('Cron schedule must have 5 parts')
        return v