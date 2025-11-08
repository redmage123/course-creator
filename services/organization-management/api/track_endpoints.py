"""
Track Management FastAPI endpoints
CRUD operations for learning tracks with enrollment automation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

from organization_management.application.services.track_service import TrackService
from organization_management.domain.entities.track import Track, TrackStatus, DifficultyLevel
from app_dependencies import get_container, get_current_user, verify_permission
from organization_management.domain.entities.enhanced_role import Permission

router = APIRouter(prefix="/api/v1/tracks", tags=["Tracks"])

# Pydantic models for requests/responses


class CreateTrackRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    project_id: UUID
    target_audience: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    learning_objectives: List[str] = Field(default_factory=list)
    duration_weeks: Optional[int] = Field(None, ge=1, le=52)
    difficulty_level: str = Field(default="beginner")
    max_students: Optional[int] = Field(None, ge=1, le=1000)


class UpdateTrackRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    target_audience: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None
    duration_weeks: Optional[int] = Field(None, ge=1, le=52)
    difficulty_level: Optional[str] = None
    max_students: Optional[int] = Field(None, ge=1, le=1000)
    status: Optional[str] = None


class TrackResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    project_id: str
    organization_id: str
    target_audience: List[str]
    prerequisites: List[str]
    learning_objectives: List[str]
    duration_weeks: Optional[int]
    difficulty_level: str
    max_students: Optional[int]
    status: str
    enrollment_count: int
    instructor_count: int
    created_at: str
    updated_at: str


class TrackEnrollmentRequest(BaseModel):
    student_emails: List[str] = Field(..., min_items=1)
    auto_approve: bool = True


class EnrollmentResponse(BaseModel):
    track_id: str
    successful_enrollments: List[str]
    failed_enrollments: List[Dict[str, str]]
    total_enrolled: int


class LocationResponse(BaseModel):
    """
    Response model for locations data

    BUSINESS CONTEXT:
    Locations represent geographic instances of projects where tracks can be offered.
    Used when assigning instructors to specific locations within a track.
    """
    id: str
    name: str
    parent_project_id: str
    organization_id: str
    location_country: str
    location_region: Optional[str]
    location_city: Optional[str]
    timezone: str
    start_date: Optional[str]
    end_date: Optional[str]
    max_participants: Optional[int]
    current_participants: int
    status: str


async def get_track_service() -> TrackService:
    """Get track service from container"""
    return await get_container().get_track_service()


@router.post("/", response_model=TrackResponse)
async def create_track(
    request: CreateTrackRequest,
    current_user=Depends(get_current_user),
    track_service: TrackService = Depends(get_track_service)
):
    """Create a new learning track"""
    try:
        # Verify permissions - need to get organization ID from project
        # For now, assume we can get it from the current user's context
        organization_id_str = current_user.get('organization_id')
        if not organization_id_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must be associated with an organization to create tracks"
            )

        # Convert string IDs from JWT to UUID objects for permission check
        user_id_str = current_user.get('user_id') or current_user.get('sub')
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID missing from JWT token"
            )

        try:
            user_id_uuid = UUID(user_id_str)
            organization_id_uuid = UUID(organization_id_str)
        except (ValueError, TypeError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UUID format - user_id: {user_id_str}, org_id: {organization_id_str}, error: {str(e)}"
            )

        await verify_permission(user_id_uuid, organization_id_uuid, Permission.CREATE_TRACKS)

        # Use string version for track creation (service expects string)
        organization_id = organization_id_str

        # Validate difficulty level
        try:
            difficulty = DifficultyLevel(request.difficulty_level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid difficulty level: {request.difficulty_level}"
            )

        # Generate slug from track name
        slug = request.name.lower().replace(' ', '-').replace('_', '-')

        track = await track_service.create_track(
            project_id=request.project_id,
            name=request.name,
            slug=slug,
            description=request.description,
            created_by=UUID(user_id_str),
            target_audience=request.target_audience,
            prerequisites=request.prerequisites,
            learning_objectives=request.learning_objectives,
            duration_weeks=request.duration_weeks,
            difficulty_level=request.difficulty_level,  # Service expects string
            max_enrolled=request.max_students
        )

        return TrackResponse(
            id=str(track.id),
            name=track.name,
            description=track.description,
            project_id=str(track.project_id),
            organization_id=str(track.organization_id),
            target_audience=track.target_audience,
            prerequisites=track.prerequisites,
            learning_objectives=track.learning_objectives,
            duration_weeks=track.duration_weeks,
            difficulty_level=track.difficulty_level.value if hasattr(track.difficulty_level, 'value') else track.difficulty_level,
            max_students=track.max_enrolled,
            status=track.status.value if hasattr(track.status, 'value') else track.status,
            enrollment_count=0,  # New track has no enrollments
            instructor_count=0,  # New track has no instructors
            created_at=track.created_at.isoformat(),
            updated_at=track.updated_at.isoformat()
        )

    except HTTPException:
        # Re-raise HTTP exceptions (including 403 from verify_permission) without modification
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{track_id}", response_model=TrackResponse)
async def get_track(
    track_id: UUID,
    current_user=Depends(get_current_user),
    track_service: TrackService = Depends(get_track_service)
):
    """Get track by ID"""
    try:
        track = await track_service.get_track(track_id)

        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found"
            )

        # Get enrollment and instructor counts
        enrollment_count = await track_service.get_track_enrollment_count(track_id)
        instructor_count = await track_service.get_track_instructor_count(track_id)

        return TrackResponse(
            id=str(track.id),
            name=track.name,
            description=track.description,
            project_id=str(track.project_id),
            organization_id=str(track.organization_id),
            target_audience=track.target_audience,
            prerequisites=track.prerequisites,
            learning_objectives=track.learning_objectives,
            duration_weeks=track.duration_weeks,
            difficulty_level=track.difficulty_level.value,
            max_students=track.max_students,
            status=track.status.value,
            enrollment_count=enrollment_count,
            instructor_count=instructor_count,
            created_at=track.created_at.isoformat(),
            updated_at=track.updated_at.isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def _parse_status_filter(status_value: Optional[str]) -> Optional[TrackStatus]:
    """Parse and validate status filter"""
    if not status_value:
        return None
    try:
        return TrackStatus(status_value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status_value}"
        )


def _parse_difficulty_filter(difficulty_level: Optional[str]) -> Optional[DifficultyLevel]:
    """Parse and validate difficulty level filter"""
    if not difficulty_level:
        return None
    try:
        return DifficultyLevel(difficulty_level)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid difficulty level: {difficulty_level}"
        )


async def _build_track_response(track, track_service: TrackService) -> TrackResponse:
    """
    Build track response with enrollment and instructor counts

    BUSINESS CONTEXT:
    Track responses include real-time enrollment and instructor counts for analytics.
    For newly created tracks or when count methods are not yet implemented,
    these counts default to 0 to ensure API responses remain stable.

    TECHNICAL IMPLEMENTATION:
    Uses graceful degradation pattern - attempts to fetch real-time counts,
    but falls back to 0 if methods don't exist or database queries fail.
    This ensures the tracks list endpoint remains functional even if
    enrollment/instructor counting features are incomplete.

    WHY THIS APPROACH:
    - Prevents API failures when new tracks have no enrollments/instructors
    - Allows incremental development (can add count methods later)
    - Maintains backward compatibility if count methods are removed
    - Logs failures for debugging without breaking the API response
    """
    import logging
    logger = logging.getLogger(__name__)

    # Get enrollment count with graceful degradation
    enrollment_count = 0
    if hasattr(track_service, 'get_track_enrollment_count'):
        try:
            enrollment_count = await track_service.get_track_enrollment_count(track.id)
        except AttributeError as e:
            logger.warning(f"Enrollment count method exists but failed for track {track.id}: {e}")
            enrollment_count = 0
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid data type when getting enrollment count for track {track.id}: {e}")
            enrollment_count = 0
        except Exception as e:
            logger.error(f"Unexpected error getting enrollment count for track {track.id}: {e}")
            enrollment_count = 0

    # Get instructor count with graceful degradation
    instructor_count = 0
    if hasattr(track_service, 'get_track_instructor_count'):
        try:
            instructor_count = await track_service.get_track_instructor_count(track.id)
        except AttributeError as e:
            logger.warning(f"Instructor count method exists but failed for track {track.id}: {e}")
            instructor_count = 0
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid data type when getting instructor count for track {track.id}: {e}")
            instructor_count = 0
        except Exception as e:
            logger.error(f"Unexpected error getting instructor count for track {track.id}: {e}")
            instructor_count = 0

    return TrackResponse(
        id=str(track.id),
        name=track.name,
        description=track.description,
        project_id=str(track.project_id),
        organization_id=str(track.organization_id),
        target_audience=track.target_audience,
        prerequisites=track.prerequisites,
        learning_objectives=track.learning_objectives,
        duration_weeks=track.duration_weeks,
        difficulty_level=track.difficulty_level.value,
        max_students=track.max_students,
        status=track.status.value,
        enrollment_count=enrollment_count,
        instructor_count=instructor_count,
        created_at=track.created_at.isoformat(),
        updated_at=track.updated_at.isoformat()
    )


@router.get("/", response_model=List[TrackResponse])
async def list_tracks(
    project_id: Optional[UUID] = None,
    organization_id: Optional[UUID] = None,
    track_status: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    current_user=Depends(get_current_user),
    track_service: TrackService = Depends(get_track_service)
):
    """
    List tracks with optional filters

    BUSINESS CONTEXT:
    Organization admins need to view all tracks across all projects in their organization.
    This endpoint supports both project-specific and organization-wide track listing.

    QUERY PATTERNS:
    - With project_id: Returns tracks for specific project only
    - Without project_id: Returns all tracks in user's organization
    - With status filter: Filters by track status (draft, active, archived)
    - With difficulty filter: Filters by difficulty level (beginner, intermediate, advanced)
    """
    try:
        # Default to current user's organization if not specified
        if not organization_id:
            # current_user is a dict, not an object
            organization_id = current_user.get('organization_id') if isinstance(current_user, dict) else getattr(current_user, 'organization_id', None)

        # Parse filters
        status_filter = _parse_status_filter(track_status)
        difficulty_filter = _parse_difficulty_filter(difficulty_level)

        # Get tracks - if project_id is provided, use that; otherwise get all organization tracks
        if project_id:
            tracks = await track_service.get_tracks_by_project(project_id, status_filter)
        elif organization_id:
            # Get all tracks for the organization using direct SQL query
            # TODO: Move this to track_service.get_tracks_by_organization() method
            container = get_container()
            dao = await container.get_organization_dao()

            # Build SQL query with filters
            query = "SELECT * FROM course_creator.tracks WHERE organization_id = $1"
            params = [str(organization_id)]

            if track_status:
                query += " AND status = $2"
                params.append(track_status)
            if difficulty_level:
                query += f" AND difficulty_level = ${len(params) + 1}"
                params.append(difficulty_level)

            query += " ORDER BY created_at DESC"

            # Execute query
            rows = await dao.db_pool.fetch(query, *params)

            # Convert rows to Track entities
            from organization_management.domain.entities.track import Track, TrackType
            tracks = []
            for row in rows:
                # Parse track_type enum
                try:
                    track_type_enum = TrackType(row.get('track_type', 'sequential'))
                except ValueError:
                    track_type_enum = TrackType.SEQUENTIAL

                track = Track(
                    id=row['id'],
                    organization_id=row['organization_id'],
                    name=row['name'],
                    slug=row.get('slug', ''),
                    project_id=row.get('project_id'),
                    location_id=row.get('location_id'),
                    description=row.get('description'),
                    track_type=track_type_enum,
                    target_audience=row.get('target_audience', []),
                    prerequisites=row.get('prerequisites', []),
                    duration_weeks=row.get('duration_weeks'),
                    max_enrolled=row.get('max_students'),
                    learning_objectives=row.get('learning_objectives', []),
                    skills_taught=row.get('skills_taught', []),
                    difficulty_level=row.get('difficulty_level', 'beginner'),
                    display_order=row.get('display_order', 0),
                    auto_enroll_enabled=row.get('auto_enroll_enabled', True),
                    status=row.get('status', 'draft'),
                    settings=row.get('settings', {}),
                    created_at=row.get('created_at'),
                    updated_at=row.get('updated_at'),
                    created_by=row.get('created_by')
                )
                tracks.append(track)
        else:
            # No organization or project specified
            tracks = []

        # Build track responses with counts
        result = []
        for track in tracks:
            track_response = await _build_track_response(track, track_service)
            result.append(track_response)

        return result

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{track_id}/locations", response_model=List[LocationResponse])
async def get_track_locations(
    track_id: UUID,
    current_user=Depends(get_current_user),
    track_service: TrackService = Depends(get_track_service)
):
    """
    Get all locations associated with a track's parent project

    BUSINESS CONTEXT:
    When assigning instructors to tracks, org admins need to see which locations
    are available for that track. This endpoint returns all locations under the
    track's parent project, enabling locations-specific instructor assignments.

    WORKFLOW:
    1. Track belongs to a project
    2. Project has multiple locations (geographic instances)
    3. Instructors can be assigned to specific locations within the track
    4. This endpoint provides the list of available locations for assignment
    """
    try:
        # Get track to find its parent project
        track = await track_service.get_track(track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found"
            )

        # Verify user has permission to view track details
        await verify_permission(current_user.id, track.organization_id, Permission.VIEW_TRACKS)

        # Get locations for the track's parent project
        container = get_container()
        dao = await container.get_organization_dao()

        # Query locations table for this project
        query = """
            SELECT
                id, name, parent_project_id, organization_id,
                location_country, location_region, location_city,
                timezone, start_date, end_date,
                max_participants, current_participants, status
            FROM locations
            WHERE parent_project_id = $1
            AND status IN ('draft', 'active')
            ORDER BY name
        """

        rows = await dao.db_pool.fetch(query, track.project_id)

        # Build response
        locations = []
        for row in rows:
            locations.append(LocationResponse(
                id=str(row['id']),
                name=row['name'],
                parent_project_id=str(row['parent_project_id']),
                organization_id=str(row['organization_id']),
                location_country=row['location_country'],
                location_region=row.get('location_region'),
                location_city=row.get('location_city'),
                timezone=row['timezone'],
                start_date=row['start_date'].isoformat() if row.get('start_date') else None,
                end_date=row['end_date'].isoformat() if row.get('end_date') else None,
                max_participants=row.get('max_participants'),
                current_participants=row.get('current_participants', 0),
                status=row['status']
            ))

        return locations

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch track locations: {str(e)}"
        )


def _build_update_data(request: UpdateTrackRequest) -> dict:
    """Build update data dictionary from request"""
    update_data = {}

    # Simple field updates
    field_mappings = [
        ('name', 'name'),
        ('description', 'description'),
        ('target_audience', 'target_audience'),
        ('prerequisites', 'prerequisites'),
        ('learning_objectives', 'learning_objectives'),
        ('duration_weeks', 'duration_weeks'),
        ('max_students', 'max_students')
    ]

    for request_field, update_field in field_mappings:
        value = getattr(request, request_field)
        if value is not None:
            update_data[update_field] = value

    # Enum field updates with validation
    if request.difficulty_level is not None:
        try:
            update_data['difficulty_level'] = DifficultyLevel(request.difficulty_level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid difficulty level: {request.difficulty_level}"
            )

    if request.status is not None:
        try:
            update_data['status'] = TrackStatus(request.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {request.status}"
            )

    return update_data


@router.put("/{track_id}", response_model=TrackResponse)
async def update_track(
    track_id: UUID,
    request: UpdateTrackRequest,
    current_user=Depends(get_current_user),
    track_service: TrackService = Depends(get_track_service)
):
    """Update track"""
    try:
        # Get existing track
        track = await track_service.get_track(track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found"
            )

        # Verify permissions
        await verify_permission(current_user.id, track.organization_id, Permission.MANAGE_TRACKS)

        # Build update data
        update_data = _build_update_data(request)

        # Update track
        updated_track = await track_service.update_track(track_id, **update_data)

        # Build response with counts
        return await _build_track_response(updated_track, track_service)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{track_id}")
async def delete_track(
    track_id: UUID,
    current_user=Depends(get_current_user),
    track_service: TrackService = Depends(get_track_service)
):
    """Delete track"""
    try:
        # Get existing track
        track = await track_service.get_track(track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found"
            )

        # Verify permissions
        await verify_permission(current_user.id, track.organization_id, Permission.MANAGE_TRACKS)

        success = await track_service.delete_track(track_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete track with active enrollments"
            )

        return {"message": "Track deleted successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{track_id}/publish")
async def publish_track(
    track_id: UUID,
    current_user=Depends(get_current_user),
    track_service: TrackService = Depends(get_track_service)
):
    """Publish track (make it available for enrollment)"""
    try:
        # Get existing track
        track = await track_service.get_track(track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found"
            )

        # Verify permissions
        await verify_permission(current_user.id, track.organization_id, Permission.PUBLISH_TRACKS)

        published_track = await track_service.publish_track(track_id)

        return {
            "message": "Track published successfully",
            "track_id": str(track_id),
            "status": published_track.status.value
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{track_id}/unpublish")
async def unpublish_track(
    track_id: UUID,
    current_user=Depends(get_current_user),
    track_service: TrackService = Depends(get_track_service)
):
    """Unpublish track (make it unavailable for enrollment)"""
    try:
        # Get existing track
        track = await track_service.get_track(track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found"
            )

        # Verify permissions
        await verify_permission(current_user.id, track.organization_id, Permission.MANAGE_TRACKS)

        unpublished_track = await track_service.unpublish_track(track_id)

        return {
            "message": "Track unpublished successfully",
            "track_id": str(track_id),
            "status": unpublished_track.status.value
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{track_id}/enroll", response_model=EnrollmentResponse)
async def bulk_enroll_students(
    track_id: UUID,
    request: TrackEnrollmentRequest,
    current_user=Depends(get_current_user),
    track_service: TrackService = Depends(get_track_service)
):
    """Bulk enroll students in track"""
    try:
        # Get existing track
        track = await track_service.get_track(track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found"
            )

        # Verify permissions
        await verify_permission(current_user.id, track.organization_id, Permission.ADD_STUDENTS_TO_PROJECT)

        result = await track_service.bulk_enroll_students(
            track_id, request.student_emails, current_user.id, request.auto_approve
        )

        return EnrollmentResponse(
            track_id=str(track_id),
            successful_enrollments=result['successful'],
            failed_enrollments=[
                {"email": email, "reason": reason}
                for email, reason in result['failed'].items()
            ],
            total_enrolled=len(result['successful'])
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{track_id}/enrollments")
async def get_track_enrollments(
    track_id: UUID,
    enrollment_status: Optional[str] = None,
    current_user=Depends(get_current_user),
    track_service: TrackService = Depends(get_track_service)
):
    """Get track enrollments"""
    try:
        # Get existing track
        track = await track_service.get_track(track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found"
            )

        # Verify permissions
        await verify_permission(current_user.id, track.organization_id, Permission.MANAGE_TRACKS)

        enrollments = await track_service.get_track_enrollments(track_id, enrollment_status)

        return {
            "track_id": str(track_id),
            "enrollments": enrollments,
            "total_count": len(enrollments)
        }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{track_id}/analytics")
async def get_track_analytics(
    track_id: UUID,
    current_user=Depends(get_current_user),
    track_service: TrackService = Depends(get_track_service)
):
    """Get track analytics and progress metrics"""
    try:
        # Get existing track
        track = await track_service.get_track(track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found"
            )

        # Verify permissions
        await verify_permission(current_user.id, track.organization_id, Permission.VIEW_ANALYTICS)

        analytics = await track_service.get_track_analytics(track_id)

        return {
            "track_id": str(track_id),
            "track_name": track.name,
            "analytics": analytics,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{track_id}/duplicate")
async def duplicate_track(
    track_id: UUID,
    new_name: Optional[str] = None,
    current_user=Depends(get_current_user),
    track_service: TrackService = Depends(get_track_service)
):
    """Duplicate an existing track"""
    try:
        # Get existing track
        track = await track_service.get_track(track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found"
            )

        # Verify permissions
        await verify_permission(current_user.id, track.organization_id, Permission.CREATE_TRACKS)

        duplicated_track = await track_service.duplicate_track(
            track_id, current_user.id, new_name
        )

        return {
            "message": "Track duplicated successfully",
            "original_track_id": str(track_id),
            "new_track_id": str(duplicated_track.id),
            "new_track_name": duplicated_track.name
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
