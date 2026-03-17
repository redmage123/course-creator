"""
Sub-Project API Endpoints - Multi-Locations Training Program Management

This module provides REST API endpoints for managing sub-projects (locations), enabling
organizations to create and manage multiple instances of training programs across different
locations with independent scheduling and capacity management.

BUSINESS CONTEXT:
Sub-projects (locations) are locations-specific instances of parent projects that enable:
- Running the same training program in multiple cities simultaneously
- Independent scheduling per locations (different start/end dates)
- Locations-specific capacity management
- Track customization per locations
- Multi-locations analytics and comparison

API DESIGN PRINCIPLES:
- REST

ful conventions with hierarchical resource paths
- Organization-scoped access control and multi-tenancy
- Comprehensive input validation with detailed error messages
- Filtering and pagination support for large datasets
- Consistent response formats across all endpoints

ENDPOINT CATEGORIES:
1. Core CRUD Operations: Create, read, update, delete sub-projects
2. Enrollment Management: Student enrollment with capacity checking
3. Track Assignment: Linking tracks to locations with date overrides
4. Discovery & Filtering: Locations-based and date-based searches
5. Analytics & Comparison: Cross-locations performance analysis

MULTI-TENANT SECURITY:
- All endpoints require organization_id for tenant isolation
- Parent project ownership is validated
- RBAC integration ensures only authorized users can manage locations
- API keys and JWT authentication supported

ERROR HANDLING STRATEGY:
- 400: Validation errors with detailed field-level feedback
- 404: Resource not found (sub-project, parent project)
- 422: Business logic violations (capacity, status transitions)
- 500: Database or service failures with safe error messages
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from uuid import UUID
import logging
import psycopg2

from course_management.application.services.sub_project_service import SubProjectService
from course_management.domain.entities.sub_project import SubProject
from course_management.infrastructure.exceptions import (
    SubProjectNotFoundException,
    DuplicateSubProjectException,
    InvalidLocationException,
    InvalidDateRangeException,
    SubProjectCapacityException,
    ProjectNotFoundException
)
from data_access.sub_project_dao import SubProjectDAO

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1", tags=["sub-projects"])


# ============================================================================
# PYDANTIC MODELS (DTOs)
# ============================================================================

class SubProjectCreateRequest(BaseModel):
    """
    Data Transfer Object for sub-project creation requests.

    BUSINESS CONTEXT:
    This DTO captures all required information for creating a new locations of a
    training program in a specific locations with customized scheduling.

    VALIDATION STRATEGY:
    - Name and slug uniqueness enforced at database level
    - Locations country is mandatory for geographic tracking
    - Date validation ensures start_date <= end_date
    - Capacity must be non-negative
    - Timezone defaults to UTC if not specified

    BUSINESS RULES:
    - All sub-projects must belong to a parent project
    - Organization ID links locations to organization for multi-tenancy
    - Status defaults to 'draft' for gradual rollout
    - Metadata provides flexible storage for future extensions
    """
    parent_project_id: str = Field(..., description="Parent project UUID")
    organization_id: str = Field(..., description="Organization UUID for multi-tenancy")
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable locations name")
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$", description="URL-friendly identifier")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed locations description")

    # Locations (required)
    location_country: str = Field(..., min_length=1, max_length=100, description="ISO country name (required)")
    location_region: Optional[str] = Field(None, max_length=100, description="State/Province (optional)")
    location_city: Optional[str] = Field(None, max_length=100, description="City name (optional)")
    location_address: Optional[str] = Field(None, max_length=500, description="Physical address (optional)")
    timezone: str = Field(default="UTC", description="IANA timezone (default: UTC)")

    # Schedule (optional)
    start_date: Optional[date] = Field(None, description="Locations start date (YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="Locations end date (YYYY-MM-DD)")
    duration_weeks: Optional[int] = Field(None, ge=1, description="Duration in weeks (auto-calculated if dates provided)")

    # Capacity (optional)
    max_participants: Optional[int] = Field(None, ge=0, description="Maximum enrollment capacity")
    current_participants: int = Field(default=0, ge=0, description="Current enrollment count")

    # Status
    status: str = Field(default="draft", pattern="^(draft|active|completed|cancelled|archived)$")

    # Flexible storage
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata (JSON)")


class SubProjectUpdateRequest(BaseModel):
    """
    Data Transfer Object for sub-project update requests.

    BUSINESS CONTEXT:
    Allows updating locations information while enforcing business rules and
    maintaining data integrity. Supports partial updates (only specified fields updated).

    UPDATE PATTERNS:
    - Metadata updates: name, description, locations details
    - Schedule updates: start/end dates (with validation)
    - Capacity updates: max_participants (with current validation)
    - Status transitions: validated through state machine
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)

    # Locations updates
    location_region: Optional[str] = Field(None, max_length=100)
    location_city: Optional[str] = Field(None, max_length=100)
    location_address: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = None

    # Schedule updates
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_weeks: Optional[int] = Field(None, ge=1)

    # Capacity updates
    max_participants: Optional[int] = Field(None, ge=0)

    # Status update (validated separately)
    status: Optional[str] = Field(None, pattern="^(draft|active|completed|cancelled|archived)$")

    # Metadata updates
    metadata: Optional[Dict[str, Any]] = None


class SubProjectResponse(BaseModel):
    """
    Data Transfer Object for sub-project API responses.

    BUSINESS CONTEXT:
    Returns complete locations information including calculated fields like
    capacity percentage and duration. Clients use this data for display
    in management interfaces and analytics dashboards.
    """
    id: str
    parent_project_id: str
    organization_id: str
    name: str
    slug: str
    description: Optional[str]

    # Locations
    location_country: str
    location_region: Optional[str]
    location_city: Optional[str]
    location_address: Optional[str]
    timezone: str

    # Schedule
    start_date: Optional[date]
    end_date: Optional[date]
    duration_weeks: Optional[int]

    # Capacity
    max_participants: Optional[int]
    current_participants: int
    capacity_percentage: float

    # Status
    status: str

    # Audit
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]

    # Metadata
    metadata: Dict[str, Any]


class TrackAssignmentRequest(BaseModel):
    """
    Data Transfer Object for track assignment requests.

    BUSINESS CONTEXT:
    Assigns a track to a sub-project with optional date overrides to customize
    track scheduling for this specific locations.
    """
    track_id: str = Field(..., description="Track UUID to assign")
    start_date: Optional[date] = Field(None, description="Override track start date for this locations")
    end_date: Optional[date] = Field(None, description="Override track end date for this locations")
    primary_instructor_id: Optional[str] = Field(None, description="Instructor assigned to this track")
    sequence_order: int = Field(default=0, ge=0, description="Order of track in curriculum sequence")


class EnrollmentRequest(BaseModel):
    """
    Data Transfer Object for student enrollment requests.

    BUSINESS CONTEXT:
    Enrolls a student in a specific locations with capacity validation.
    """
    student_id: str = Field(..., description="Student UUID")


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

# Module-level variable to store database connection pool
db_pool = None


def set_db_pool(pool):
    """
    Set the database connection pool for sub-project endpoints.

    This function should be called during application startup to provide
    the database connection pool to the sub-project endpoints.
    """
    global db_pool
    db_pool = pool
    logger.info("Sub-project endpoints initialized with database pool")


def get_db_connection():
    """Get synchronous database connection for sub-project operations"""
    global db_pool
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database pool not initialized")

    try:
        # Get connection from asyncpg pool (will be synchronous connection for psycopg2)
        # For now, create a new psycopg2 connection
        # In production, this should use a proper connection pool
        import os
        db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres_password@localhost:5433/course_creator')
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.error(f"Failed to get database connection: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


def get_sub_project_service() -> SubProjectService:
    """Dependency injection for sub-project service"""
    try:
        conn = get_db_connection()
        dao = SubProjectDAO(conn)
        return SubProjectService(dao)
    except Exception as e:
        logger.error(f"Failed to initialize sub-project service: {e}")
        raise HTTPException(status_code=500, detail="Service initialization failed")


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post(
    "/organizations/{org_id}/projects/{project_id}/sub-projects",
    response_model=SubProjectResponse,
    status_code=201
)
async def create_sub_project(
    org_id: str,
    project_id: str,
    request: SubProjectCreateRequest,
    service: SubProjectService = Depends(get_sub_project_service)
):
    """
    Create a new sub-project (locations) for a parent project.

    BUSINESS WORKFLOW:
    1. Validates parent project exists and belongs to organization
    2. Validates locations data (country required)
    3. Validates date range (start <= end if both provided)
    4. Creates sub-project entity with proper initialization
    5. Returns created sub-project with generated ID

    PATH PARAMETERS:
    - org_id: Organization UUID (multi-tenant isolation)
    - project_id: Parent project UUID

    REQUEST BODY:
    See SubProjectCreateRequest model for full details.

    RESPONSE:
    - 201: Created sub-project
    - 400: Validation error (invalid locations, dates, or capacity)
    - 404: Parent project not found
    - 409: Duplicate slug within organization
    - 500: Database or service error

    EXAMPLE:
        POST /api/v1/organizations/org-123/projects/proj-456/sub-projects
        {
            "parent_project_id": "proj-456",
            "organization_id": "org-123",
            "name": "Boston Locations Fall 2025",
            "slug": "boston-fall-2025",
            "location_country": "United States",
            "location_region": "Massachusetts",
            "location_city": "Boston",
            "start_date": "2025-09-01",
            "end_date": "2025-12-15",
            "max_participants": 30
        }
    """
    try:
        logger.info(f"Creating sub-project for org {org_id}, project {project_id}")

        # Validate organization and project IDs match request
        if request.organization_id != org_id:
            raise HTTPException(
                status_code=400,
                detail="organization_id in body must match organization in path"
            )

        if request.parent_project_id != project_id:
            raise HTTPException(
                status_code=400,
                detail="parent_project_id in body must match project in path"
            )

        # Convert request to dict for service
        data = request.dict()

        # Create sub-project
        sub_project = service.create_sub_project(data)

        # Convert entity to response
        return _sub_project_to_response(sub_project)

    except (InvalidLocationException, InvalidDateRangeException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateSubProjectException as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ProjectNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create sub-project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/organizations/{org_id}/projects/{project_id}/sub-projects",
    response_model=List[SubProjectResponse]
)
async def list_sub_projects(
    org_id: str,
    project_id: str,
    location_country: Optional[str] = Query(None, description="Filter by country"),
    location_region: Optional[str] = Query(None, description="Filter by region"),
    location_city: Optional[str] = Query(None, description="Filter by city (partial match)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date_from: Optional[date] = Query(None, description="Locations starting on or after this date"),
    start_date_to: Optional[date] = Query(None, description="Locations starting on or before this date"),
    service: SubProjectService = Depends(get_sub_project_service)
):
    """
    List all sub-projects for a parent project with optional filtering.

    BUSINESS WORKFLOW:
    1. Validates access to parent project
    2. Applies locations filters (country, region, city)
    3. Applies date range filters
    4. Applies status filter
    5. Returns sorted list of matching sub-projects

    FILTERING OPTIONS:
    - location_country: Exact match on country
    - location_region: Exact match on region
    - location_city: Partial match (case-insensitive) on city
    - status: Exact match on status
    - start_date_from: Locations starting on or after this date
    - start_date_to: Locations starting on or before this date

    SORTING:
    Results are sorted by start_date DESC, then created_at DESC.

    RESPONSE:
    - 200: List of sub-projects (may be empty)
    - 404: Parent project not found
    - 500: Database or service error

    EXAMPLE:
        GET /api/v1/organizations/org-123/projects/proj-456/sub-projects?location_country=United%20States&status=active
    """
    try:
        logger.info(f"Listing sub-projects for org {org_id}, project {project_id}")

        # Build filters
        filters = {}
        if location_country:
            filters['location_country'] = location_country
        if location_region:
            filters['location_region'] = location_region
        if location_city:
            filters['location_city'] = location_city
        if status:
            filters['status'] = status
        if start_date_from:
            filters['start_date_from'] = start_date_from
        if start_date_to:
            filters['start_date_to'] = start_date_to

        # Get sub-projects
        sub_projects = service.get_sub_projects_for_project(project_id, filters)

        # Convert to responses
        return [_sub_project_to_response(sp) for sp in sub_projects]

    except ProjectNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list sub-projects: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/organizations/{org_id}/projects/{project_id}/sub-projects/{sub_project_id}",
    response_model=SubProjectResponse
)
async def get_sub_project(
    org_id: str,
    project_id: str,
    sub_project_id: str,
    service: SubProjectService = Depends(get_sub_project_service)
):
    """
    Get a specific sub-project by ID.

    RESPONSE:
    - 200: Sub-project details
    - 404: Sub-project not found
    - 500: Database or service error
    """
    try:
        logger.info(f"Retrieving sub-project {sub_project_id}")

        sub_project = service.get_sub_project_by_id(sub_project_id)

        # Validate belongs to correct project and organization
        if sub_project.parent_project_id != UUID(project_id):
            raise HTTPException(status_code=404, detail="Sub-project not found in this project")

        if sub_project.organization_id != UUID(org_id):
            raise HTTPException(status_code=404, detail="Sub-project not found in this organization")

        return _sub_project_to_response(sub_project)

    except SubProjectNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to retrieve sub-project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put(
    "/organizations/{org_id}/projects/{project_id}/sub-projects/{sub_project_id}",
    response_model=SubProjectResponse
)
async def update_sub_project(
    org_id: str,
    project_id: str,
    sub_project_id: str,
    request: SubProjectUpdateRequest,
    service: SubProjectService = Depends(get_sub_project_service)
):
    """
    Update an existing sub-project.

    BUSINESS WORKFLOW:
    1. Validates sub-project exists
    2. Validates ownership (correct project and organization)
    3. Validates updates (date ranges, capacity constraints)
    4. Applies partial updates (only specified fields)
    5. Returns updated sub-project

    RESPONSE:
    - 200: Updated sub-project
    - 400: Validation error
    - 404: Sub-project not found
    - 422: Business rule violation
    - 500: Database or service error
    """
    try:
        logger.info(f"Updating sub-project {sub_project_id}")

        # Get existing sub-project to validate ownership
        existing = service.get_sub_project_by_id(sub_project_id)

        if existing.parent_project_id != UUID(project_id):
            raise HTTPException(status_code=404, detail="Sub-project not found in this project")

        if existing.organization_id != UUID(org_id):
            raise HTTPException(status_code=404, detail="Sub-project not found in this organization")

        # Convert request to dict, excluding None values
        update_data = {k: v for k, v in request.dict().items() if v is not None}

        # Update sub-project
        updated = service.update_sub_project(sub_project_id, update_data)

        return _sub_project_to_response(updated)

    except SubProjectNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (InvalidDateRangeException, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update sub-project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/organizations/{org_id}/projects/{project_id}/sub-projects/{sub_project_id}",
    status_code=204
)
async def delete_sub_project(
    org_id: str,
    project_id: str,
    sub_project_id: str,
    service: SubProjectService = Depends(get_sub_project_service)
):
    """
    Delete a sub-project.

    BUSINESS WORKFLOW:
    1. Validates sub-project exists
    2. Validates ownership
    3. Checks for active enrollments (future enhancement)
    4. Deletes sub-project (cascades to track assignments)

    RESPONSE:
    - 204: Successfully deleted (no content)
    - 404: Sub-project not found
    - 422: Cannot delete (has active enrollments)
    - 500: Database or service error
    """
    try:
        logger.info(f"Deleting sub-project {sub_project_id}")

        # Get existing sub-project to validate ownership
        existing = service.get_sub_project_by_id(sub_project_id)

        if existing.parent_project_id != UUID(project_id):
            raise HTTPException(status_code=404, detail="Sub-project not found in this project")

        if existing.organization_id != UUID(org_id):
            raise HTTPException(status_code=404, detail="Sub-project not found in this organization")

        # Delete sub-project
        service.delete_sub_project(sub_project_id)

        return None  # 204 No Content

    except SubProjectNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete sub-project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/organizations/{org_id}/projects/{project_id}/sub-projects/{sub_project_id}/tracks",
    status_code=201
)
async def assign_track(
    org_id: str,
    project_id: str,
    sub_project_id: str,
    request: TrackAssignmentRequest,
    service: SubProjectService = Depends(get_sub_project_service)
):
    """
    Assign a track to a sub-project with optional date overrides.

    BUSINESS WORKFLOW:
    1. Validates sub-project exists and ownership
    2. Validates track exists (future: call organization-management service)
    3. Checks if track already assigned to this sub-project
    4. Validates date range if dates provided
    5. Stores assignment in sub-project metadata

    RESPONSE:
    - 201: Track assignment created
    - 400: Validation error (invalid dates)
    - 404: Sub-project or track not found
    - 409: Track already assigned to this sub-project
    - 500: Database or service error
    """
    try:
        logger.info(f"Assigning track {request.track_id} to sub-project {sub_project_id}")

        # Get existing sub-project to validate ownership
        existing = service.get_sub_project_by_id(sub_project_id)

        if existing.parent_project_id != UUID(project_id):
            raise HTTPException(status_code=404, detail="Sub-project not found in this project")

        if existing.organization_id != UUID(org_id):
            raise HTTPException(status_code=404, detail="Sub-project not found in this organization")

        # Assign track
        assignment = service.assign_track_to_sub_project(
            sub_project_id=sub_project_id,
            track_id=request.track_id,
            start_date=request.start_date,
            end_date=request.end_date,
            primary_instructor_id=request.primary_instructor_id,
            sequence_order=request.sequence_order
        )

        return {"message": "Track assigned successfully", "assignment": assignment}

    except SubProjectNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidDateRangeException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateSubProjectException as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to assign track: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/organizations/{org_id}/projects/{project_id}/sub-projects/{sub_project_id}/enroll",
    status_code=201
)
async def enroll_student(
    org_id: str,
    project_id: str,
    sub_project_id: str,
    request: EnrollmentRequest,
    service: SubProjectService = Depends(get_sub_project_service)
):
    """
    Enroll a student in a sub-project with capacity validation.

    BUSINESS WORKFLOW:
    1. Validates sub-project exists and ownership
    2. Checks capacity availability
    3. Increments participant count
    4. Returns updated enrollment counts

    NOTE: This is a simplified version. Full implementation would
    coordinate with enrollment service to create actual enrollment record.

    RESPONSE:
    - 201: Student enrolled successfully
    - 404: Sub-project or student not found
    - 422: Sub-project at capacity
    - 500: Database or service error
    """
    try:
        logger.info(f"Enrolling student {request.student_id} in sub-project {sub_project_id}")

        # Get existing sub-project to validate ownership
        existing = service.get_sub_project_by_id(sub_project_id)

        if existing.parent_project_id != UUID(project_id):
            raise HTTPException(status_code=404, detail="Sub-project not found in this project")

        if existing.organization_id != UUID(org_id):
            raise HTTPException(status_code=404, detail="Sub-project not found in this organization")

        # Enroll student
        result = service.enroll_student(sub_project_id, request.student_id)

        return {
            "message": "Student enrolled successfully",
            "current_participants": result['current_participants'],
            "max_participants": result['max_participants']
        }

    except SubProjectNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SubProjectCapacityException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to enroll student: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _sub_project_to_response(sub_project: SubProject) -> SubProjectResponse:
    """
    Convert domain entity to API response DTO.

    This helper ensures consistent response format across all endpoints.
    """
    return SubProjectResponse(
        id=str(sub_project.id),
        parent_project_id=str(sub_project.parent_project_id),
        organization_id=str(sub_project.organization_id),
        name=sub_project.name,
        slug=sub_project.slug,
        description=sub_project.description,
        location_country=sub_project.location_country,
        location_region=sub_project.location_region,
        location_city=sub_project.location_city,
        location_address=sub_project.location_address,
        timezone=sub_project.timezone,
        start_date=sub_project.start_date,
        end_date=sub_project.end_date,
        duration_weeks=sub_project.duration_weeks,
        max_participants=sub_project.max_participants,
        current_participants=sub_project.current_participants,
        capacity_percentage=sub_project.calculate_capacity_percentage(),
        status=sub_project.status,
        created_at=sub_project.created_at,
        updated_at=sub_project.updated_at,
        created_by=str(sub_project.created_by) if sub_project.created_by else None,
        updated_by=str(sub_project.updated_by) if sub_project.updated_by else None,
        metadata=sub_project.metadata
    )
