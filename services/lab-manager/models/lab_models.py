"""
Data models for lab container management system.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field


class LabStatus(str, Enum):
    """Lab container status enumeration."""
    CREATING = "creating"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    PAUSED = "paused"


class IDEType(str, Enum):
    """Supported IDE types."""
    VSCODE = "vscode"
    JUPYTER = "jupyter"
    INTELLIJ = "intellij"
    TERMINAL = "terminal"


class LabConfig(BaseModel):
    """Configuration for a lab environment."""
    language: str = Field(default="python", description="Programming language")
    ide_type: IDEType = Field(default=IDEType.VSCODE, description="IDE type")
    packages: List[str] = Field(default_factory=list, description="Additional packages")
    environment_vars: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    cpu_limit: str = Field(default="1.0", description="CPU limit")
    memory_limit: str = Field(default="1g", description="Memory limit")
    enable_multi_ide: bool = Field(default=False, description="Enable multi-IDE support")


class ContainerSpec(BaseModel):
    """Specification for container creation."""
    image_name: str
    container_name: str
    ports: Dict[str, int]
    volumes: Dict[str, str]
    environment: Dict[str, str]
    cpu_limit: str = "1.0"
    memory_limit: str = "1g"


class LabEnvironment(BaseModel):
    """Lab environment model."""
    id: str
    student_id: str
    course_id: str
    container_name: str
    container_id: Optional[str] = None
    status: LabStatus = LabStatus.CREATING
    created_at: datetime
    last_accessed: Optional[datetime] = None
    config: LabConfig
    ports: Dict[str, int] = Field(default_factory=dict)
    ide_urls: Dict[str, str] = Field(default_factory=dict)
    persistent_storage_path: Optional[str] = None


class LabRequest(BaseModel):
    """Request model for lab creation."""
    course_id: str
    language: str = "python"
    ide_type: IDEType = IDEType.VSCODE
    packages: List[str] = Field(default_factory=list)
    environment_vars: Dict[str, str] = Field(default_factory=dict)
    enable_multi_ide: bool = False


class LabResponse(BaseModel):
    """Response model for lab operations."""
    success: bool
    message: str
    lab_id: Optional[str] = None
    urls: Dict[str, str] = Field(default_factory=dict)
    status: Optional[LabStatus] = None


class StudentLabRequest(BaseModel):
    """Request model for student lab access."""
    course_id: str
    config: Optional[LabConfig] = None


class LabListResponse(BaseModel):
    """Response model for lab listing."""
    labs: List[LabEnvironment]
    total_count: int


class LabHealthCheck(BaseModel):
    """Health check response for lab services."""
    container_status: str
    ide_services: Dict[str, bool] = Field(default_factory=dict)
    last_activity: Optional[datetime] = None
    uptime_seconds: Optional[int] = None


class FileUploadRequest(BaseModel):
    """Request model for file uploads to lab."""
    file_path: str
    content: str
    encoding: str = "utf-8"


class FileDownloadResponse(BaseModel):
    """Response model for file downloads from lab."""
    file_path: str
    content: str
    encoding: str
    size_bytes: int
    modified_at: datetime


class LabMetrics(BaseModel):
    """Lab usage metrics."""
    lab_id: str
    student_id: str
    course_id: str
    session_duration_minutes: int
    ide_usage: Dict[str, int] = Field(default_factory=dict)  # IDE -> minutes used
    files_created: int = 0
    files_modified: int = 0
    commands_executed: int = 0
    last_activity: datetime


class InstructorLabOverview(BaseModel):
    """Overview of labs for instructors."""
    course_id: str
    total_labs: int
    active_labs: int
    lab_summary: List[Dict[str, Union[str, int, datetime]]]
    resource_usage: Dict[str, Union[int, float]]


class LabAnalytics(BaseModel):
    """Analytics data for lab usage."""
    total_labs_created: int
    active_sessions: int
    average_session_duration: float
    most_used_ide: str
    resource_utilization: Dict[str, float]
    error_rate: float