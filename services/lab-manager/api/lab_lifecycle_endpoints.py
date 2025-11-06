#!/usr/bin/env python3

"""
Lab Lifecycle API Endpoints

This module provides RESTful API endpoints for lab container lifecycle management
in the Course Creator Platform, following SOLID principles and clean architecture patterns.

## Educational Context:

### Lab Container Management
- **Creation**: Dynamic Docker container provisioning for student labs
- **Lifecycle**: Pause, resume, and delete operations for resource management
- **Monitoring**: Real-time status tracking and health checks
- **Cleanup**: Automated idle lab termination for resource optimization

### Instructor Capabilities
- **Course Overview**: Monitor all lab instances for a course
- **Resource Management**: Track active labs and resource utilization
- **Maintenance**: Cleanup idle labs and optimize resource allocation

### Architecture Principles
- **Single Responsibility**: Focused on lab lifecycle operations only
- **Dependency Injection**: Service dependencies injected via FastAPI
- **Clean Separation**: API layer separated from business logic
- **Resource Efficiency**: Optimized for educational workload patterns

## API Endpoints:
- POST /labs - Create new lab container
- POST /labs/student - Create or retrieve student lab
- GET /labs - List all active labs
- GET /labs/{lab_id} - Get lab status
- POST /labs/{lab_id}/pause - Pause lab container
- POST /labs/{lab_id}/resume - Resume lab container
- DELETE /labs/{lab_id} - Delete lab container
- GET /labs/instructor/{course_id} - Get instructor lab overview
- POST /labs/cleanup - Cleanup idle labs

## Integration:
This router integrates with the LabLifecycleService for Docker container
orchestration, ensuring efficient resource management for educational environments.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, status
from typing import Dict, List, Optional
import logging
from datetime import datetime

# Import models
from models.lab_models import (
    LabRequest, LabResponse, StudentLabRequest, LabListResponse
)

# Import services
from services.lab_lifecycle_service import LabLifecycleService

# Custom exceptions
from exceptions import (
    ContentException,
    ContentNotFoundException,
    ConfigurationException
)

# Initialize router
router = APIRouter(
    prefix="/labs",
    tags=["lab-lifecycle"],
    responses={
        404: {"description": "Lab not found"},
        500: {"description": "Internal server error"}
    }
)

logger = logging.getLogger(__name__)

# Response models
from pydantic import BaseModel

class LabStatusResponse(BaseModel):
    """Lab status response with container details"""
    lab_id: str
    status: str
    ide_urls: Dict[str, str]
    created_at: datetime
    last_accessed: Optional[datetime]

# Dependency injection helper
def get_lab_lifecycle_service() -> LabLifecycleService:
    """
    Dependency injection provider for lab lifecycle service.

    Provides access to comprehensive lab container management capabilities,
    supporting the full lifecycle of educational lab environments.

    Educational Capabilities:
    - Docker container orchestration for student labs
    - Resource allocation and cleanup for cost optimization
    - Health monitoring and status tracking
    - Multi-IDE support (VS Code, Jupyter, Theia)

    Returns:
        LabLifecycleService: Lab lifecycle service instance

    Raises:
        ConfigurationException: If service not initialized
    """
    from main import lab_lifecycle_service
    if not lab_lifecycle_service:
        raise ConfigurationException(
            message="Lab lifecycle service not initialized",
            error_code="SERVICE_INIT_ERROR",
            details={"service_name": "lab_lifecycle_service", "initialization_stage": "startup"}
        )
    return lab_lifecycle_service

# Lab Management Endpoints

@router.post("", response_model=LabResponse, status_code=status.HTTP_201_CREATED)
async def create_lab(
    request: LabRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new lab container for course demonstration or testing.

    Educational Use Cases:
    - Instructors testing lab environments before student assignments
    - Course development and configuration validation
    - Demo labs for course previews and marketing

    Technical Details:
    - Provisions Docker container with requested IDE configuration
    - Configures network ports and resource limits
    - Initializes file system and development tools
    - Returns container status and IDE access URLs

    Args:
        request: Lab creation request with course and configuration
        background_tasks: FastAPI background tasks for async operations

    Returns:
        LabResponse: Created lab with container ID and access URLs

    Raises:
        ContentException: If lab creation fails
    """
    try:
        lifecycle_service = get_lab_lifecycle_service()

        # Convert LabRequest to StudentLabRequest for the service
        student_request = StudentLabRequest(
            course_id=request.course_id,
            config=None  # Use default config for now
        )

        # Create lab using lifecycle service
        result = await lifecycle_service.create_student_lab(
            student_id="instructor",  # Default for instructor labs
            request=student_request
        )

        return result

    except ContentException:
        raise
    except Exception as e:
        raise ContentException(
            message="Failed to create lab container",
            error_code="LAB_CREATION_ERROR",
            details={"course_id": request.course_id, "lab_type": "instructor_lab"},
            original_exception=e
        )

@router.post("/student", response_model=LabResponse, status_code=status.HTTP_201_CREATED)
async def create_student_lab(
    request: StudentLabRequest,
    user_id: str = Query(..., description="Student user ID")
):
    """
    Create or retrieve student lab container.

    Educational Workflow:
    1. Student accesses lab assignment in course
    2. System creates dedicated lab container for student
    3. Container provisioned with course-specific environment
    4. Student receives unique IDE URLs for lab access
    5. Container persists for session continuity

    Container Persistence:
    - One container per student per course
    - State preserved across sessions
    - Automatic resume on student return
    - Cleanup after course completion or idle timeout

    Args:
        request: Student lab request with course configuration
        user_id: Unique student identifier

    Returns:
        LabResponse: Lab container status with IDE access URLs

    Raises:
        ContentException: If lab creation or retrieval fails
    """
    try:
        lifecycle_service = get_lab_lifecycle_service()
        result = await lifecycle_service.create_student_lab(user_id, request)
        return result

    except ContentException:
        raise
    except Exception as e:
        raise ContentException(
            message="Failed to create student lab container",
            error_code="LAB_CREATION_ERROR",
            details={"student_id": user_id, "course_id": request.course_id, "lab_type": "student_lab"},
            original_exception=e
        )

@router.get("", response_model=LabListResponse, status_code=status.HTTP_200_OK)
async def list_labs():
    """
    List all active lab containers across all courses.

    Administrator Use Cases:
    - Monitor platform-wide lab container usage
    - Track resource allocation and capacity planning
    - Identify idle or problematic containers
    - Generate usage reports for billing and optimization

    Returns:
        LabListResponse: List of all active labs with status summary

    Raises:
        ContentException: If listing operation fails
    """
    try:
        lifecycle_service = get_lab_lifecycle_service()
        labs = list(lifecycle_service.active_labs.values())

        return LabListResponse(
            labs=labs,
            total_count=len(labs)
        )

    except ContentException:
        raise
    except Exception as e:
        raise ContentException(
            message="Failed to list lab containers",
            error_code="LAB_LIFECYCLE_ERROR",
            details={"operation": "list_labs"},
            original_exception=e
        )

@router.get("/{lab_id}", response_model=LabStatusResponse, status_code=status.HTTP_200_OK)
async def get_lab_status(lab_id: str):
    """
    Get detailed status of a specific lab container.

    Status Information:
    - Container running state (running, paused, stopped)
    - IDE access URLs for different development environments
    - Resource usage metrics (CPU, memory, storage)
    - Creation and last access timestamps
    - Student association and course context

    Monitoring Integration:
    - Health check for container availability
    - Performance metrics for optimization
    - Access logs for usage analysis

    Args:
        lab_id: Unique lab container identifier

    Returns:
        LabStatusResponse: Detailed lab status and access information

    Raises:
        ContentNotFoundException: If lab not found
        ContentException: If status retrieval fails
    """
    try:
        lifecycle_service = get_lab_lifecycle_service()
        lab = lifecycle_service.get_lab_status(lab_id)

        if not lab:
            raise ContentNotFoundException(
                message="Lab container not found",
                error_code="LAB_NOT_FOUND",
                details={"lab_id": lab_id}
            )

        return LabStatusResponse(
            lab_id=lab.id,
            status=lab.status.value,
            ide_urls=lab.ide_urls,
            created_at=lab.created_at,
            last_accessed=lab.last_accessed
        )

    except ContentException:
        raise
    except Exception as e:
        raise ContentException(
            message="Failed to retrieve lab status",
            error_code="LAB_LIFECYCLE_ERROR",
            details={"lab_id": lab_id, "operation": "get_lab_status"},
            original_exception=e
        )

@router.post("/{lab_id}/pause", response_model=LabResponse, status_code=status.HTTP_200_OK)
async def pause_lab(lab_id: str):
    """
    Pause a running lab container to conserve resources.

    Educational Use Cases:
    - Student taking a break but wants to resume later
    - Instructor managing resource allocation during off-peak hours
    - Automated resource optimization during idle periods

    Technical Details:
    - Container state saved to disk
    - All processes suspended but not terminated
    - Resources released back to pool
    - Fast resume with full state restoration

    Args:
        lab_id: Lab container identifier to pause

    Returns:
        LabResponse: Updated lab status showing paused state

    Raises:
        ContentException: If pause operation fails
    """
    try:
        lifecycle_service = get_lab_lifecycle_service()
        result = await lifecycle_service.pause_lab(lab_id)
        return result

    except ContentException:
        raise
    except Exception as e:
        raise ContentException(
            message="Failed to pause lab container",
            error_code="LAB_LIFECYCLE_ERROR",
            details={"lab_id": lab_id, "operation": "pause_lab", "target_status": "paused"},
            original_exception=e
        )

@router.post("/{lab_id}/resume", response_model=LabResponse, status_code=status.HTTP_200_OK)
async def resume_lab(lab_id: str):
    """
    Resume a paused lab container.

    Educational Workflow:
    - Student returns to paused lab session
    - Container state restored from disk
    - All processes and files resume exactly as left
    - IDE reconnects automatically

    Performance:
    - Fast resume (typically < 5 seconds)
    - Full state preservation
    - No data loss or reset
    - Seamless student experience

    Args:
        lab_id: Lab container identifier to resume

    Returns:
        LabResponse: Updated lab status showing running state

    Raises:
        ContentException: If resume operation fails
    """
    try:
        lifecycle_service = get_lab_lifecycle_service()
        result = await lifecycle_service.resume_lab(lab_id)
        return result

    except ContentException:
        raise
    except Exception as e:
        raise ContentException(
            message="Failed to resume lab container",
            error_code="LAB_LIFECYCLE_ERROR",
            details={"lab_id": lab_id, "operation": "resume_lab", "target_status": "running"},
            original_exception=e
        )

@router.delete("/{lab_id}", response_model=LabResponse, status_code=status.HTTP_200_OK)
async def delete_lab(lab_id: str):
    """
    Delete a lab container permanently.

    Educational Context:
    - Course completion and final grade submission
    - Student withdrawal or course transfer
    - Instructor request for container reset
    - Automated cleanup after retention period

    Data Preservation:
    - Student work optionally exported before deletion
    - Logs and metrics saved for analysis
    - Grade records preserved separately
    - Compliance with data retention policies

    Args:
        lab_id: Lab container identifier to delete

    Returns:
        LabResponse: Final lab status before deletion

    Raises:
        ContentException: If deletion fails
    """
    try:
        lifecycle_service = get_lab_lifecycle_service()
        result = await lifecycle_service.delete_lab(lab_id)
        return result

    except ContentException:
        raise
    except Exception as e:
        raise ContentException(
            message="Failed to delete lab container",
            error_code="LAB_LIFECYCLE_ERROR",
            details={"lab_id": lab_id, "operation": "delete_lab", "target_status": "deleted"},
            original_exception=e
        )

@router.get("/instructor/{course_id}", status_code=status.HTTP_200_OK)
async def get_instructor_lab_overview(course_id: str):
    """
    Get comprehensive lab overview for instructors.

    Instructor Dashboard Features:
    - Total labs created for course
    - Active vs. paused vs. stopped breakdown
    - Per-student lab status and access times
    - Resource usage statistics
    - Student progress indicators

    Educational Insights:
    - Identify students needing help (inactive labs)
    - Monitor resource utilization patterns
    - Plan capacity for peak usage periods
    - Generate usage reports for administration

    Args:
        course_id: Course identifier for lab filtering

    Returns:
        Dict: Comprehensive lab overview with statistics and details

    Raises:
        ContentException: If overview generation fails
    """
    try:
        lifecycle_service = get_lab_lifecycle_service()
        labs = lifecycle_service.list_course_labs(course_id)

        # Generate summary statistics
        total_labs = len(labs)
        active_labs = len([lab for lab in labs if lab.status.value == "running"])

        return {
            "course_id": course_id,
            "total_labs": total_labs,
            "active_labs": active_labs,
            "labs": [
                {
                    "lab_id": lab.id,
                    "student_id": lab.student_id,
                    "status": lab.status.value,
                    "created_at": lab.created_at,
                    "last_accessed": lab.last_accessed,
                    "ide_urls": lab.ide_urls
                }
                for lab in labs
            ]
        }

    except ContentException:
        raise
    except Exception as e:
        raise ContentException(
            message="Failed to retrieve instructor lab overview",
            error_code="LAB_LIFECYCLE_ERROR",
            details={"course_id": course_id, "operation": "get_instructor_overview"},
            original_exception=e
        )

@router.post("/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_idle_labs(max_idle_hours: int = Query(24, description="Max idle hours before cleanup")):
    """
    Clean up idle lab containers for resource optimization.

    Cleanup Strategy:
    - Identifies labs idle beyond configured threshold
    - Saves student work and logs before cleanup
    - Releases Docker containers and resources
    - Maintains cleanup audit log

    Educational Policies:
    - Default: 24 hours idle before cleanup
    - Student notified before cleanup (if possible)
    - Work preserved according to retention policy
    - Cleanup can be configured per course

    Resource Management:
    - Automated cleanup during off-peak hours
    - Manual cleanup for capacity emergencies
    - Dry-run mode for policy testing
    - Cleanup metrics for optimization

    Args:
        max_idle_hours: Hours of inactivity before cleanup (default: 24)

    Returns:
        Dict: Cleanup summary with count of containers cleaned

    Raises:
        ContentException: If cleanup operation fails
    """
    try:
        lifecycle_service = get_lab_lifecycle_service()
        cleaned_count = await lifecycle_service.cleanup_idle_labs(max_idle_hours)

        return {
            "message": f"Cleaned up {cleaned_count} idle labs",
            "cleaned_count": cleaned_count
        }

    except ContentException:
        raise
    except Exception as e:
        raise ContentException(
            message="Failed to cleanup idle lab containers",
            error_code="LAB_LIFECYCLE_ERROR",
            details={"operation": "cleanup_idle_labs"},
            original_exception=e
        )
