"""
Locations Management FastAPI endpoints
CRUD operations for training locations with geographic and scheduling constraints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime, date
import logging
import traceback

from organization_management.domain.entities.locations import Locations, LocationStatus
from app_dependencies import get_container, get_current_user, verify_permission
from organization_management.domain.entities.enhanced_role import Permission

router = APIRouter(prefix="/api/v1/locations", tags=["Locations"])
logger = logging.getLogger(__name__)


# Pydantic models for requests/responses

class CreateLocationRequest(BaseModel):
    """Request model for creating a new locations"""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    parent_project_id: UUID
    description: Optional[str] = Field(None, max_length=1000)
    location_country: str = Field(..., min_length=2, max_length=100)
    location_region: Optional[str] = Field(None, max_length=100)
    location_city: Optional[str] = Field(None, max_length=100)
    location_address: Optional[str] = None
    timezone: str = Field(default="UTC", max_length=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_participants: Optional[int] = Field(None, ge=1)
    metadata: Optional[Dict] = None


class UpdateLocationRequest(BaseModel):
    """Request model for updating an existing locations"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    location_country: Optional[str] = Field(None, min_length=2, max_length=100)
    location_region: Optional[str] = Field(None, max_length=100)
    location_city: Optional[str] = Field(None, max_length=100)
    location_address: Optional[str] = None
    timezone: Optional[str] = Field(None, max_length=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_participants: Optional[int] = Field(None, ge=1)
    status: Optional[str] = None
    metadata: Optional[Dict] = None


class LocationResponse(BaseModel):
    """Response model for locations data"""
    id: str
    organization_id: str
    parent_project_id: str
    name: str
    slug: str
    description: Optional[str]
    location_country: str
    location_region: Optional[str]
    location_city: Optional[str]
    location_address: Optional[str]
    timezone: str
    start_date: Optional[str]
    end_date: Optional[str]
    duration_weeks: Optional[int]
    max_participants: Optional[int]
    current_participants: int
    status: str
    created_at: str
    updated_at: str
    created_by: Optional[str]


def _build_location_response(locations: Locations) -> LocationResponse:
    """
    Build locations response from entity

    BUSINESS PURPOSE:
    Converts Locations domain entity to API response format.

    WHY THIS APPROACH:
    - Centralizes response building logic
    - Ensures consistent date formatting
    - Handles optional fields properly
    """
    return LocationResponse(
        id=str(locations.id),
        organization_id=str(locations.organization_id),
        parent_project_id=str(locations.parent_project_id),
        name=locations.name,
        slug=locations.slug,
        description=locations.description,
        location_country=locations.location_country,
        location_region=locations.location_region,
        location_city=locations.location_city,
        location_address=locations.location_address,
        timezone=locations.timezone,
        start_date=locations.start_date.isoformat() if locations.start_date else None,
        end_date=locations.end_date.isoformat() if locations.end_date else None,
        duration_weeks=locations.duration_weeks,
        max_participants=locations.max_participants,
        current_participants=locations.current_participants,
        status=locations.status.value,
        created_at=locations.created_at.isoformat(),
        updated_at=locations.updated_at.isoformat(),
        created_by=str(locations.created_by) if locations.created_by else None
    )


@router.post("/", response_model=LocationResponse)
async def create_location(
    request: CreateLocationRequest,
    current_user=Depends(get_current_user)
):
    """
    Create a new locations

    BUSINESS PURPOSE:
    Allows org admins to create new training locations for their projects.

    PERMISSIONS:
    - CREATE_LOCATIONS permission required
    """
    try:
        # Get organization ID from current user
        organization_id = current_user.get('organization_id') if isinstance(current_user, dict) else getattr(current_user, 'organization_id', None)

        # Verify permissions
        await verify_permission(current_user.get('id') if isinstance(current_user, dict) else current_user.id,
                              organization_id,
                              Permission.MANAGE_PROJECTS)

        # Get DAO
        container = get_container()
        dao = await container.get_organization_dao()

        # Create locations entity
        locations = Locations(
            organization_id=organization_id,
            parent_project_id=request.parent_project_id,
            name=request.name,
            slug=request.slug,
            description=request.description,
            location_country=request.location_country,
            location_region=request.location_region,
            location_city=request.location_city,
            location_address=request.location_address,
            timezone=request.timezone,
            start_date=request.start_date,
            end_date=request.end_date,
            max_participants=request.max_participants,
            metadata=request.metadata or {},
            created_by=current_user.get('id') if isinstance(current_user, dict) else current_user.id
        )

        # Validate before inserting
        if not locations.is_valid():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid locations data. Check required fields and constraints."
            )

        # Insert into database
        query = """
            INSERT INTO locations (
                id, organization_id, parent_project_id, name, slug, description,
                location_country, location_region, location_city, location_address,
                timezone, start_date, end_date, max_participants, current_participants,
                status, metadata, created_by, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
            )
            RETURNING *
        """

        row = await dao.db_pool.fetchrow(
            query,
            locations.id, locations.organization_id, locations.parent_project_id,
            locations.name, locations.slug, locations.description,
            locations.location_country, locations.location_region, locations.location_city,
            locations.location_address, locations.timezone, locations.start_date,
            locations.end_date, locations.max_participants, locations.current_participants,
            locations.status.value, locations.metadata, locations.created_by,
            locations.created_at, locations.updated_at
        )

        # Build response from returned row
        created_location = Locations(
            id=row['id'],
            organization_id=row['organization_id'],
            parent_project_id=row['parent_project_id'],
            name=row['name'],
            slug=row['slug'],
            description=row['description'],
            location_country=row['location_country'],
            location_region=row['location_region'],
            location_city=row['location_city'],
            location_address=row['location_address'],
            timezone=row['timezone'],
            start_date=row['start_date'],
            end_date=row['end_date'],
            duration_weeks=row['duration_weeks'],
            max_participants=row['max_participants'],
            current_participants=row['current_participants'],
            status=LocationStatus(row['status']),
            metadata=row['metadata'],
            created_by=row['created_by'],
            updated_by=row.get('updated_by'),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

        return _build_location_response(created_location)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    current_user=Depends(get_current_user)
):
    """
    Get locations by ID

    BUSINESS PURPOSE:
    Retrieves detailed information about a specific locations.
    """
    try:
        # Get DAO
        container = get_container()
        dao = await container.get_organization_dao()

        # Query locations
        query = "SELECT * FROM locations WHERE id = $1"
        row = await dao.db_pool.fetchrow(query, location_id)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Locations not found"
            )

        # Build locations entity
        locations = Locations(
            id=row['id'],
            organization_id=row['organization_id'],
            parent_project_id=row['parent_project_id'],
            name=row['name'],
            slug=row['slug'],
            description=row['description'],
            location_country=row['location_country'],
            location_region=row['location_region'],
            location_city=row['location_city'],
            location_address=row['location_address'],
            timezone=row['timezone'],
            start_date=row['start_date'],
            end_date=row['end_date'],
            duration_weeks=row['duration_weeks'],
            max_participants=row['max_participants'],
            current_participants=row['current_participants'],
            status=LocationStatus(row['status']),
            metadata=row['metadata'],
            created_by=row['created_by'],
            updated_by=row.get('updated_by'),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

        return _build_location_response(locations)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=List[LocationResponse])
async def list_locations(
    organization_id: Optional[UUID] = None,
    parent_project_id: Optional[UUID] = None,
    location_status: Optional[str] = None,
    country: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """
    List locations with optional filters

    BUSINESS PURPOSE:
    Allows org admins to view all locations in their organization with filtering.

    QUERY PATTERNS:
    - With parent_project_id: Returns locations for specific project
    - With organization_id: Returns all locations in organization
    - With status filter: Filters by locations status
    - With country filter: Filters by country
    """
    logger.info("=== list_locations endpoint called ===")
    logger.info(f"Parameters: org_id={organization_id}, project_id={parent_project_id}, status={location_status}, country={country}")
    logger.info(f"Current user: {current_user}")
    try:
        # Default to current user's organization if not specified
        if not organization_id:
            organization_id = current_user.get('organization_id') if isinstance(current_user, dict) else getattr(current_user, 'organization_id', None)

        # If organization_id is still None, this is an error
        if organization_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization ID is required. User must belong to an organization."
            )

        # Get DAO
        container = get_container()
        dao = await container.get_organization_dao()

        # Build query with filters
        query = "SELECT * FROM locations WHERE organization_id = $1"
        params = [str(organization_id)]

        if parent_project_id:
            query += f" AND parent_project_id = ${len(params) + 1}"
            params.append(str(parent_project_id))

        if location_status:
            query += f" AND status = ${len(params) + 1}"
            params.append(location_status)

        if country:
            query += f" AND location_country ILIKE ${len(params) + 1}"
            params.append(f"%{country}%")

        query += " ORDER BY created_at DESC"

        # Execute query
        rows = await dao.db_pool.fetch(query, *params)

        # Build locations entities
        locations = []
        for row in rows:
            locations = Locations(
                id=row['id'],
                organization_id=row['organization_id'],
                parent_project_id=row['parent_project_id'],
                name=row['name'],
                slug=row['slug'],
                description=row['description'],
                location_country=row['location_country'],
                location_region=row['location_region'],
                location_city=row['location_city'],
                location_address=row['location_address'],
                timezone=row['timezone'],
                start_date=row['start_date'],
                end_date=row['end_date'],
                duration_weeks=row['duration_weeks'],
                max_participants=row['max_participants'],
                current_participants=row['current_participants'],
                status=LocationStatus(row['status']),
                metadata=row['metadata'],
                created_by=row['created_by'],
                updated_by=row.get('updated_by'),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            locations.append(locations)

        # Build responses
        return [_build_location_response(loc) for loc in locations]

    except HTTPException:
        # Re-raise HTTP exceptions as-is (don't convert to 500)
        raise
    except Exception as e:
        logger.error(f"Error in list_locations: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: UUID,
    request: UpdateLocationRequest,
    current_user=Depends(get_current_user)
):
    """
    Update locations

    BUSINESS PURPOSE:
    Allows org admins to update locations details.
    """
    try:
        # Get DAO
        container = get_container()
        dao = await container.get_organization_dao()

        # Get existing locations
        query = "SELECT * FROM locations WHERE id = $1"
        row = await dao.db_pool.fetchrow(query, location_id)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Locations not found"
            )

        # Verify permissions
        await verify_permission(
            current_user.get('id') if isinstance(current_user, dict) else current_user.id,
            row['organization_id'],
            Permission.MANAGE_PROJECTS
        )

        # Build update fields
        update_fields = []
        params = []
        param_count = 1

        if request.name is not None:
            update_fields.append(f"name = ${param_count}")
            params.append(request.name)
            param_count += 1

        if request.description is not None:
            update_fields.append(f"description = ${param_count}")
            params.append(request.description)
            param_count += 1

        if request.location_country is not None:
            update_fields.append(f"location_country = ${param_count}")
            params.append(request.location_country)
            param_count += 1

        if request.location_region is not None:
            update_fields.append(f"location_region = ${param_count}")
            params.append(request.location_region)
            param_count += 1

        if request.location_city is not None:
            update_fields.append(f"location_city = ${param_count}")
            params.append(request.location_city)
            param_count += 1

        if request.location_address is not None:
            update_fields.append(f"location_address = ${param_count}")
            params.append(request.location_address)
            param_count += 1

        if request.timezone is not None:
            update_fields.append(f"timezone = ${param_count}")
            params.append(request.timezone)
            param_count += 1

        if request.start_date is not None:
            update_fields.append(f"start_date = ${param_count}")
            params.append(request.start_date)
            param_count += 1

        if request.end_date is not None:
            update_fields.append(f"end_date = ${param_count}")
            params.append(request.end_date)
            param_count += 1

        if request.max_participants is not None:
            update_fields.append(f"max_participants = ${param_count}")
            params.append(request.max_participants)
            param_count += 1

        if request.status is not None:
            # Validate status
            try:
                LocationStatus(request.status)
                update_fields.append(f"status = ${param_count}")
                params.append(request.status)
                param_count += 1
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {request.status}"
                )

        if request.metadata is not None:
            update_fields.append(f"metadata = ${param_count}")
            params.append(request.metadata)
            param_count += 1

        # Always update updated_at and updated_by
        update_fields.append(f"updated_at = ${param_count}")
        params.append(datetime.utcnow())
        param_count += 1

        update_fields.append(f"updated_by = ${param_count}")
        params.append(current_user.get('id') if isinstance(current_user, dict) else current_user.id)
        param_count += 1

        # Add location_id as last parameter
        params.append(location_id)

        # Execute update
        update_query = f"""
            UPDATE locations
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING *
        """

        updated_row = await dao.db_pool.fetchrow(update_query, *params)

        # Build response
        updated_location = Locations(
            id=updated_row['id'],
            organization_id=updated_row['organization_id'],
            parent_project_id=updated_row['parent_project_id'],
            name=updated_row['name'],
            slug=updated_row['slug'],
            description=updated_row['description'],
            location_country=updated_row['location_country'],
            location_region=updated_row['location_region'],
            location_city=updated_row['location_city'],
            location_address=updated_row['location_address'],
            timezone=updated_row['timezone'],
            start_date=updated_row['start_date'],
            end_date=updated_row['end_date'],
            duration_weeks=updated_row['duration_weeks'],
            max_participants=updated_row['max_participants'],
            current_participants=updated_row['current_participants'],
            status=LocationStatus(updated_row['status']),
            metadata=updated_row['metadata'],
            created_by=updated_row['created_by'],
            updated_by=updated_row['updated_by'],
            created_at=updated_row['created_at'],
            updated_at=updated_row['updated_at']
        )

        return _build_location_response(updated_location)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{location_id}")
async def delete_location(
    location_id: UUID,
    current_user=Depends(get_current_user)
):
    """
    Delete locations

    BUSINESS PURPOSE:
    Allows org admins to delete locations. Cascades to tracks associated with locations.

    BUSINESS RULE:
    Deletion cascades to tracks (enforced by database FK constraint).
    """
    try:
        # Get DAO
        container = get_container()
        dao = await container.get_organization_dao()

        # Get existing locations
        query = "SELECT * FROM locations WHERE id = $1"
        row = await dao.db_pool.fetchrow(query, location_id)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Locations not found"
            )

        # Verify permissions
        await verify_permission(
            current_user.get('id') if isinstance(current_user, dict) else current_user.id,
            row['organization_id'],
            Permission.MANAGE_PROJECTS
        )

        # Delete locations
        delete_query = "DELETE FROM locations WHERE id = $1"
        await dao.db_pool.execute(delete_query, location_id)

        return {"message": "Locations deleted successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
