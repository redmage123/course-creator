"""
Instructor Assignment Management API Endpoints

BUSINESS CONTEXT:
Organization admins need to assign instructors to tracks and locations within their organization.
This enables:
- Track-level assignments: Instructor teaches all content in a track
- Locations-level assignments: Instructor teaches at specific geographic locations
- Flexible workload distribution across multiple instructors
- Clear instructor-to-content mapping for students

WORKFLOW:
1. Org admin views instructors in their organization
2. Selects an instructor to assign
3. Chooses which tracks the instructor will teach
4. Optionally selects specific locations within those tracks
5. Saves assignments
6. Instructor gains access to assigned track content and students
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

from app_dependencies import get_container, get_current_user, verify_permission
from organization_management.domain.entities.enhanced_role import Permission

router = APIRouter(prefix="/api/v1/instructors", tags=["Instructor Assignments"])


# ============================================================================
# Pydantic Models
# ============================================================================


class InstructorAssignmentsResponse(BaseModel):
    """
    Response model for instructor assignment data

    BUSINESS CONTEXT:
    Returns current assignments for an instructor, showing which tracks
    and locations they are assigned to. Used to pre-populate assignment modal.
    """
    instructor_id: str
    track_ids: List[str] = Field(default_factory=list)
    location_ids: List[str] = Field(default_factory=list)
    organization_id: str


class UpdateInstructorAssignmentsRequest(BaseModel):
    """
    Request model to update instructor assignments

    BUSINESS CONTEXT:
    Organization admin sends updated list of track and locations IDs.
    System will replace all existing assignments with this new set.
    Empty arrays mean remove all assignments of that type.
    """
    track_ids: List[UUID] = Field(default_factory=list)
    location_ids: List[UUID] = Field(default_factory=list)


class AssignmentDetail(BaseModel):
    """Individual assignment detail for response"""
    assignment_type: str  # 'track' or 'locations'
    entity_id: str
    entity_name: str
    status: str
    assigned_role: str
    assigned_at: str


class InstructorAssignmentsDetailResponse(BaseModel):
    """Detailed assignments with entity names"""
    instructor_id: str
    assignments: List[AssignmentDetail]
    total_tracks: int
    total_locations: int


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/{instructor_id}/assignments", response_model=InstructorAssignmentsResponse)
async def get_instructor_assignments(
    instructor_id: UUID,
    current_user=Depends(get_current_user)
):
    """
    Get current assignments for an instructor

    BUSINESS CONTEXT:
    When org admin opens the assignment modal, this endpoint returns the instructor's
    current track and locations assignments so they can be pre-selected in the UI.

    RETURNS:
    - List of track IDs instructor is assigned to
    - List of locations IDs instructor is assigned to
    - Organization ID for context

    PERMISSIONS:
    - Org admin can view assignments within their organization
    - Site admin can view any assignments
    """
    try:
        container = get_container()
        dao = await container.get_organization_dao()

        # Get instructor to find their organization
        instructor_query = "SELECT organization_id FROM course_creator.organization_memberships WHERE user_id = $1 LIMIT 1"
        instructor_row = await dao.db_pool.fetchrow(instructor_query, instructor_id)

        if not instructor_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instructor not found or not member of any organization"
            )

        organization_id = instructor_row['organization_id']

        # Verify permission - must be admin of same organization
        await verify_permission(current_user.id, organization_id, Permission.MANAGE_INSTRUCTORS)

        # Get track assignments
        track_query = """
            SELECT track_id
            FROM instructor_track_assignments
            WHERE instructor_id = $1
            AND organization_id = $2
            AND status = 'active'
        """
        track_rows = await dao.db_pool.fetch(track_query, instructor_id, organization_id)
        track_ids = [str(row['track_id']) for row in track_rows]

        # Get locations assignments
        location_query = """
            SELECT location_id
            FROM instructor_location_assignments
            WHERE instructor_id = $1
            AND organization_id = $2
            AND status = 'active'
        """
        location_rows = await dao.db_pool.fetch(location_query, instructor_id, organization_id)
        location_ids = [str(row['location_id']) for row in location_rows]

        return InstructorAssignmentsResponse(
            instructor_id=str(instructor_id),
            track_ids=track_ids,
            location_ids=location_ids,
            organization_id=str(organization_id)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch instructor assignments: {str(e)}"
        )


@router.put("/{instructor_id}/assignments", response_model=InstructorAssignmentsResponse)
async def update_instructor_assignments(
    instructor_id: UUID,
    request: UpdateInstructorAssignmentsRequest,
    current_user=Depends(get_current_user)
):
    """
    Update instructor assignments (replace all existing assignments)

    BUSINESS CONTEXT:
    Organization admin has modified the instructor's track and locations assignments
    in the UI. This endpoint replaces ALL existing assignments with the new set.

    LOGIC:
    1. Verify instructor exists and get their organization
    2. Verify current user has permission to manage instructors in that org
    3. Delete all existing active assignments for this instructor
    4. Insert new assignments from request
    5. Return updated assignment list

    ATOMIC OPERATION:
    All changes happen in a single database transaction. If any step fails,
    all changes are rolled back.

    PERMISSIONS:
    - Org admin can manage assignments within their organization
    - Site admin can manage any assignments
    """
    try:
        container = get_container()
        dao = await container.get_organization_dao()

        # Get instructor's organization
        instructor_query = "SELECT organization_id FROM course_creator.organization_memberships WHERE user_id = $1 LIMIT 1"
        instructor_row = await dao.db_pool.fetchrow(instructor_query, instructor_id)

        if not instructor_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instructor not found or not member of any organization"
            )

        organization_id = instructor_row['organization_id']

        # Verify permission
        await verify_permission(current_user.id, organization_id, Permission.MANAGE_INSTRUCTORS)

        # Start transaction
        async with dao.db_pool.acquire() as conn:
            async with conn.transaction():
                # Delete existing track assignments
                await conn.execute(
                    """
                    DELETE FROM instructor_track_assignments
                    WHERE instructor_id = $1 AND organization_id = $2
                    """,
                    instructor_id,
                    organization_id
                )

                # Delete existing locations assignments
                await conn.execute(
                    """
                    DELETE FROM instructor_location_assignments
                    WHERE instructor_id = $1 AND organization_id = $2
                    """,
                    instructor_id,
                    organization_id
                )

                # Insert new track assignments
                for track_id in request.track_ids:
                    await conn.execute(
                        """
                        INSERT INTO instructor_track_assignments
                        (instructor_id, track_id, organization_id, status, assigned_role, assigned_by)
                        VALUES ($1, $2, $3, 'active', 'primary', $4)
                        """,
                        instructor_id,
                        track_id,
                        organization_id,
                        current_user.id
                    )

                # Insert new locations assignments
                for location_id in request.location_ids:
                    await conn.execute(
                        """
                        INSERT INTO instructor_location_assignments
                        (instructor_id, location_id, organization_id, status, assigned_role, assigned_by)
                        VALUES ($1, $2, $3, 'active', 'primary', $4)
                        """,
                        instructor_id,
                        location_id,
                        organization_id,
                        current_user.id
                    )

        # Return updated assignments
        return InstructorAssignmentsResponse(
            instructor_id=str(instructor_id),
            track_ids=[str(track_id) for track_id in request.track_ids],
            location_ids=[str(location_id) for location_id in request.location_ids],
            organization_id=str(organization_id)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update instructor assignments: {str(e)}"
        )


@router.get("/{instructor_id}/assignments/detailed", response_model=InstructorAssignmentsDetailResponse)
async def get_instructor_assignments_detailed(
    instructor_id: UUID,
    current_user=Depends(get_current_user)
):
    """
    Get detailed instructor assignments with entity names

    BUSINESS CONTEXT:
    Used for displaying instructor workload and assignment details in admin dashboards.
    Includes entity names (track names, locations names) for user-friendly display.

    RETURNS:
    - Detailed list of all assignments with entity names
    - Counts of total tracks and locations assigned
    """
    try:
        container = get_container()
        dao = await container.get_organization_dao()

        # Get instructor's organization
        instructor_query = "SELECT organization_id FROM course_creator.organization_memberships WHERE user_id = $1 LIMIT 1"
        instructor_row = await dao.db_pool.fetchrow(instructor_query, instructor_id)

        if not instructor_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instructor not found"
            )

        organization_id = instructor_row['organization_id']

        # Verify permission
        await verify_permission(current_user.id, organization_id, Permission.VIEW_INSTRUCTORS)

        # Get track assignments with details
        track_query = """
            SELECT
                ita.id,
                ita.track_id,
                t.name as track_name,
                ita.status,
                ita.assigned_role,
                ita.assigned_at
            FROM instructor_track_assignments ita
            JOIN course_creator.tracks t ON ita.track_id = t.id
            WHERE ita.instructor_id = $1
            AND ita.organization_id = $2
            AND ita.status = 'active'
        """
        track_rows = await dao.db_pool.fetch(track_query, instructor_id, organization_id)

        # Get locations assignments with details
        location_query = """
            SELECT
                ila.id,
                ila.location_id,
                l.name as location_name,
                ila.status,
                ila.assigned_role,
                ila.assigned_at
            FROM instructor_location_assignments ila
            JOIN locations l ON ila.location_id = l.id
            WHERE ila.instructor_id = $1
            AND ila.organization_id = $2
            AND ila.status = 'active'
        """
        location_rows = await dao.db_pool.fetch(location_query, instructor_id, organization_id)

        # Build assignments list
        assignments = []

        for row in track_rows:
            assignments.append(AssignmentDetail(
                assignment_type='track',
                entity_id=str(row['track_id']),
                entity_name=row['track_name'],
                status=row['status'],
                assigned_role=row['assigned_role'],
                assigned_at=row['assigned_at'].isoformat()
            ))

        for row in location_rows:
            assignments.append(AssignmentDetail(
                assignment_type='locations',
                entity_id=str(row['location_id']),
                entity_name=row['location_name'],
                status=row['status'],
                assigned_role=row['assigned_role'],
                assigned_at=row['assigned_at'].isoformat()
            ))

        return InstructorAssignmentsDetailResponse(
            instructor_id=str(instructor_id),
            assignments=assignments,
            total_tracks=len(track_rows),
            total_locations=len(location_rows)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch detailed assignments: {str(e)}"
        )
