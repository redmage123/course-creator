"""
Unit Tests for Lab Manager Models

BUSINESS REQUIREMENT:
Validates lab environment data models for hands-on programming exercises including
container specifications, IDE configurations, student access, and resource management.

TECHNICAL IMPLEMENTATION:
Tests Pydantic models, validation rules, enumerations, and business logic
for lab container lifecycle management.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'lab-manager'))

from models.lab_models import (
    LabStatus, IDEType, LabConfig, ContainerSpec, LabEnvironment,
    LabRequest, LabResponse, StudentLabRequest, LabListResponse,
    LabHealthCheck, FileUploadRequest, FileDownloadResponse,
    LabMetrics, InstructorLabOverview, LabAnalytics
)


class TestLabStatusEnum:
    """Test lab status enumeration."""

    def test_lab_status_values(self):
        """Test all lab status values exist."""
        assert LabStatus.CREATING == "creating"
        assert LabStatus.STARTING == "starting"
        assert LabStatus.RUNNING == "running"
        assert LabStatus.STOPPING == "stopping"
        assert LabStatus.STOPPED == "stopped"
        assert LabStatus.ERROR == "error"
        assert LabStatus.PAUSED == "paused"

    def test_lab_status_lifecycle(self):
        """Test lab status transitions represent valid lifecycle."""
        lifecycle = [
            LabStatus.CREATING,
            LabStatus.STARTING,
            LabStatus.RUNNING,
            LabStatus.PAUSED,
            LabStatus.RUNNING,
            LabStatus.STOPPING,
            LabStatus.STOPPED
        ]

        for status in lifecycle:
            assert isinstance(status, str)


class TestIDETypeEnum:
    """Test IDE type enumeration."""

    def test_ide_types(self):
        """Test all IDE types exist."""
        assert IDEType.VSCODE == "vscode"
        assert IDEType.JUPYTER == "jupyter"
        assert IDEType.INTELLIJ == "intellij"
        assert IDEType.TERMINAL == "terminal"

    def test_ide_type_values(self):
        """Test IDE types have correct string values."""
        ide_types = [IDEType.VSCODE, IDEType.JUPYTER, IDEType.INTELLIJ, IDEType.TERMINAL]

        for ide_type in ide_types:
            assert isinstance(ide_type.value, str)
            assert len(ide_type.value) > 0


class TestLabConfig:
    """Test lab configuration model."""

    def test_create_lab_config_defaults(self):
        """Test creating lab config with default values."""
        config = LabConfig()

        assert config.language == "python"
        assert config.ide_type == IDEType.VSCODE
        assert config.packages == []
        assert config.environment_vars == {}
        assert config.cpu_limit == "1.0"
        assert config.memory_limit == "1g"
        assert config.enable_multi_ide is False

    def test_create_lab_config_custom(self):
        """Test creating lab config with custom values."""
        config = LabConfig(
            language="javascript",
            ide_type=IDEType.JUPYTER,
            packages=["numpy", "pandas"],
            environment_vars={"DEBUG": "true"},
            cpu_limit="2.0",
            memory_limit="2g",
            enable_multi_ide=True
        )

        assert config.language == "javascript"
        assert config.ide_type == IDEType.JUPYTER
        assert len(config.packages) == 2
        assert config.environment_vars["DEBUG"] == "true"
        assert config.cpu_limit == "2.0"
        assert config.memory_limit == "2g"
        assert config.enable_multi_ide is True

    def test_lab_config_packages_list(self):
        """Test lab config packages as list."""
        config = LabConfig(packages=["flask", "requests", "pytest"])

        assert len(config.packages) == 3
        assert "flask" in config.packages
        assert "pytest" in config.packages


class TestContainerSpec:
    """Test container specification model."""

    def test_create_container_spec(self):
        """Test creating container specification."""
        spec = ContainerSpec(
            image_name="course-creator/python-lab:latest",
            container_name="student_lab_123",
            ports={"8080": 8080, "3000": 3000},
            volumes={"/workspace": "/home/student/workspace"},
            environment={"LANG": "python", "COURSE_ID": "course123"}
        )

        assert spec.image_name == "course-creator/python-lab:latest"
        assert spec.container_name == "student_lab_123"
        assert spec.ports["8080"] == 8080
        assert "/workspace" in spec.volumes
        assert spec.environment["LANG"] == "python"

    def test_container_spec_resource_limits(self):
        """Test container resource limits."""
        spec = ContainerSpec(
            image_name="test-image",
            container_name="test-container",
            ports={},
            volumes={},
            environment={},
            cpu_limit="2.5",
            memory_limit="4g"
        )

        assert spec.cpu_limit == "2.5"
        assert spec.memory_limit == "4g"


class TestLabEnvironment:
    """Test lab environment model."""

    def test_create_lab_environment(self):
        """Test creating lab environment."""
        config = LabConfig(language="python")
        now = datetime.utcnow()

        lab = LabEnvironment(
            id="lab_123",
            student_id="student_456",
            course_id="course_789",
            container_name="lab_container_123",
            status=LabStatus.CREATING,
            created_at=now,
            config=config
        )

        assert lab.id == "lab_123"
        assert lab.student_id == "student_456"
        assert lab.course_id == "course_789"
        assert lab.status == LabStatus.CREATING
        assert lab.container_id is None
        assert lab.config.language == "python"

    def test_lab_environment_with_urls(self):
        """Test lab environment with IDE URLs."""
        config = LabConfig(enable_multi_ide=True)
        lab = LabEnvironment(
            id="lab_123",
            student_id="student_456",
            course_id="course_789",
            container_name="lab_container",
            status=LabStatus.RUNNING,
            created_at=datetime.utcnow(),
            config=config,
            ide_urls={
                "vscode": "http://localhost:8080",
                "jupyter": "http://localhost:8888"
            }
        )

        assert len(lab.ide_urls) == 2
        assert "vscode" in lab.ide_urls
        assert "jupyter" in lab.ide_urls

    def test_lab_environment_status_update(self):
        """Test updating lab environment status."""
        config = LabConfig()
        lab = LabEnvironment(
            id="lab_123",
            student_id="student_456",
            course_id="course_789",
            container_name="lab_container",
            status=LabStatus.CREATING,
            created_at=datetime.utcnow(),
            config=config
        )

        # Update status
        lab.status = LabStatus.RUNNING
        lab.last_accessed = datetime.utcnow()

        assert lab.status == LabStatus.RUNNING
        assert lab.last_accessed is not None


class TestLabRequest:
    """Test lab request model."""

    def test_create_lab_request_minimal(self):
        """Test creating lab request with minimal data."""
        request = LabRequest(course_id="course_123")

        assert request.course_id == "course_123"
        assert request.language == "python"
        assert request.ide_type == IDEType.VSCODE
        assert request.packages == []
        assert request.enable_multi_ide is False

    def test_create_lab_request_full(self):
        """Test creating lab request with full configuration."""
        request = LabRequest(
            course_id="course_123",
            language="javascript",
            ide_type=IDEType.JUPYTER,
            packages=["express", "react"],
            environment_vars={"NODE_ENV": "development"},
            enable_multi_ide=True
        )

        assert request.course_id == "course_123"
        assert request.language == "javascript"
        assert request.ide_type == IDEType.JUPYTER
        assert len(request.packages) == 2
        assert request.environment_vars["NODE_ENV"] == "development"
        assert request.enable_multi_ide is True


class TestLabResponse:
    """Test lab response model."""

    def test_lab_response_success(self):
        """Test successful lab response."""
        response = LabResponse(
            success=True,
            message="Lab created successfully",
            lab_id="lab_123",
            urls={"vscode": "http://localhost:8080"},
            status=LabStatus.RUNNING
        )

        assert response.success is True
        assert "successfully" in response.message
        assert response.lab_id == "lab_123"
        assert len(response.urls) == 1
        assert response.status == LabStatus.RUNNING

    def test_lab_response_error(self):
        """Test error lab response."""
        response = LabResponse(
            success=False,
            message="Failed to create lab: Insufficient resources",
            status=LabStatus.ERROR
        )

        assert response.success is False
        assert "Failed" in response.message
        assert response.lab_id is None
        assert response.status == LabStatus.ERROR


class TestStudentLabRequest:
    """Test student lab request model."""

    def test_student_lab_request_minimal(self):
        """Test student lab request with minimal data."""
        request = StudentLabRequest(course_id="course_123")

        assert request.course_id == "course_123"
        assert request.config is None

    def test_student_lab_request_with_config(self):
        """Test student lab request with custom config."""
        config = LabConfig(language="java", ide_type=IDEType.INTELLIJ)
        request = StudentLabRequest(
            course_id="course_123",
            config=config
        )

        assert request.course_id == "course_123"
        assert request.config.language == "java"
        assert request.config.ide_type == IDEType.INTELLIJ


class TestLabHealthCheck:
    """Test lab health check model."""

    def test_lab_health_check(self):
        """Test lab health check response."""
        health = LabHealthCheck(
            container_status="running",
            ide_services={"vscode": True, "jupyter": True},
            last_activity=datetime.utcnow(),
            uptime_seconds=3600
        )

        assert health.container_status == "running"
        assert health.ide_services["vscode"] is True
        assert health.ide_services["jupyter"] is True
        assert health.uptime_seconds == 3600

    def test_lab_health_check_unhealthy(self):
        """Test unhealthy lab status."""
        health = LabHealthCheck(
            container_status="stopped",
            ide_services={"vscode": False}
        )

        assert health.container_status == "stopped"
        assert health.ide_services["vscode"] is False
        assert health.last_activity is None


class TestFileOperations:
    """Test file upload and download models."""

    def test_file_upload_request(self):
        """Test file upload request model."""
        upload = FileUploadRequest(
            file_path="/workspace/main.py",
            content="print('Hello, World!')",
            encoding="utf-8"
        )

        assert upload.file_path == "/workspace/main.py"
        assert "Hello, World!" in upload.content
        assert upload.encoding == "utf-8"

    def test_file_download_response(self):
        """Test file download response model."""
        download = FileDownloadResponse(
            file_path="/workspace/output.txt",
            content="Test output",
            encoding="utf-8",
            size_bytes=120,
            modified_at=datetime.utcnow()
        )

        assert download.file_path == "/workspace/output.txt"
        assert download.content == "Test output"
        assert download.size_bytes == 120
        assert download.modified_at is not None


class TestLabMetrics:
    """Test lab metrics model."""

    def test_lab_metrics_creation(self):
        """Test creating lab metrics."""
        metrics = LabMetrics(
            lab_id="lab_123",
            student_id="student_456",
            course_id="course_789",
            session_duration_minutes=45,
            ide_usage={"vscode": 30, "jupyter": 15},
            files_created=5,
            files_modified=12,
            commands_executed=50,
            last_activity=datetime.utcnow()
        )

        assert metrics.lab_id == "lab_123"
        assert metrics.session_duration_minutes == 45
        assert metrics.ide_usage["vscode"] == 30
        assert metrics.files_created == 5
        assert metrics.commands_executed == 50

    def test_lab_metrics_defaults(self):
        """Test lab metrics with default values."""
        metrics = LabMetrics(
            lab_id="lab_123",
            student_id="student_456",
            course_id="course_789",
            session_duration_minutes=30,
            last_activity=datetime.utcnow()
        )

        assert metrics.files_created == 0
        assert metrics.files_modified == 0
        assert metrics.commands_executed == 0
        assert metrics.ide_usage == {}


class TestInstructorLabOverview:
    """Test instructor lab overview model."""

    def test_instructor_overview(self):
        """Test instructor lab overview."""
        overview = InstructorLabOverview(
            course_id="course_123",
            total_labs=50,
            active_labs=12,
            lab_summary=[
                {"student_id": "student_1", "status": "running", "created_at": datetime.utcnow()},
                {"student_id": "student_2", "status": "paused", "created_at": datetime.utcnow()}
            ],
            resource_usage={"cpu_percent": 45.5, "memory_mb": 2048}
        )

        assert overview.course_id == "course_123"
        assert overview.total_labs == 50
        assert overview.active_labs == 12
        assert len(overview.lab_summary) == 2
        assert overview.resource_usage["cpu_percent"] == 45.5


class TestLabAnalytics:
    """Test lab analytics model."""

    def test_lab_analytics(self):
        """Test lab analytics data."""
        analytics = LabAnalytics(
            total_labs_created=100,
            active_sessions=15,
            average_session_duration=42.5,
            most_used_ide="vscode",
            resource_utilization={"cpu": 0.6, "memory": 0.75},
            error_rate=0.02
        )

        assert analytics.total_labs_created == 100
        assert analytics.active_sessions == 15
        assert analytics.average_session_duration == 42.5
        assert analytics.most_used_ide == "vscode"
        assert analytics.resource_utilization["cpu"] == 0.6
        assert analytics.error_rate == 0.02

    def test_lab_analytics_calculations(self):
        """Test analytics calculations."""
        total_labs = 100
        errors = 3
        error_rate = errors / total_labs

        analytics = LabAnalytics(
            total_labs_created=total_labs,
            active_sessions=20,
            average_session_duration=35.0,
            most_used_ide="jupyter",
            resource_utilization={},
            error_rate=error_rate
        )

        assert analytics.error_rate == 0.03


class TestLabListResponse:
    """Test lab list response model."""

    def test_lab_list_response(self):
        """Test lab listing response."""
        config = LabConfig()
        lab1 = LabEnvironment(
            id="lab_1",
            student_id="student_1",
            course_id="course_123",
            container_name="container_1",
            status=LabStatus.RUNNING,
            created_at=datetime.utcnow(),
            config=config
        )

        lab2 = LabEnvironment(
            id="lab_2",
            student_id="student_2",
            course_id="course_123",
            container_name="container_2",
            status=LabStatus.PAUSED,
            created_at=datetime.utcnow(),
            config=config
        )

        response = LabListResponse(
            labs=[lab1, lab2],
            total_count=2
        )

        assert len(response.labs) == 2
        assert response.total_count == 2
        assert response.labs[0].status == LabStatus.RUNNING
        assert response.labs[1].status == LabStatus.PAUSED


# Run tests with: pytest tests/unit/lab_manager/test_lab_models.py -v
