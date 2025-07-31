"""
Track Management FastAPI endpoints
CRUD operations for learning tracks with enrollment automation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

from application.services.track_service import TrackService
from domain.entities.track import Track, TrackStatus, DifficultyLevel
from app_dependencies import get_container, get_current_user, verify_permission
from domain.entities.enhanced_role import Permission

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
        organization_id = current_user.organization_id
        await verify_permission(current_user.id, organization_id, Permission.CREATE_TRACKS)

        # Validate difficulty level
        try:
            difficulty = DifficultyLevel(request.difficulty_level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid difficulty level: {request.difficulty_level}"
            )

        track = await track_service.create_track(
            name=request.name,
            description=request.description,
            project_id=request.project_id,
            organization_id=organization_id,
            created_by=current_user.id,
            target_audience=request.target_audience,
            prerequisites=request.prerequisites,
            learning_objectives=request.learning_objectives,
            duration_weeks=request.duration_weeks,
            difficulty_level=difficulty,
            max_students=request.max_students
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
            difficulty_level=track.difficulty_level.value,
            max_students=track.max_students,
            status=track.status.value,
            enrollment_count=0,  # New track has no enrollments
            instructor_count=0,  # New track has no instructors
            created_at=track.created_at.isoformat(),
            updated_at=track.updated_at.isoformat()
        )

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


def _parse_status_filter(status: Optional[str]) -> Optional[TrackStatus]:
    """Parse and validate status filter"""
    if not status:
        return None
    try:
        return TrackStatus(status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status}"
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
    """Build track response with enrollment and instructor counts"""
    enrollment_count = await track_service.get_track_enrollment_count(track.id)
    instructor_count = await track_service.get_track_instructor_count(track.id)

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
    status: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    current_user=Depends(get_current_user),
    track_service: TrackService = Depends(get_track_service)
):
    """List tracks with optional filters"""
    try:
        # Default to current user's organization if not specified
        if not organization_id:
            organization_id = current_user.organization_id

        # Parse filters
        status_filter = _parse_status_filter(status)
        difficulty_filter = _parse_difficulty_filter(difficulty_level)

        tracks = await track_service.list_tracks(
            organization_id=organization_id,
            project_id=project_id,
            status=status_filter,
            difficulty_level=difficulty_filter
        )

        # Build track responses with counts
        result = []
        for track in tracks:
            track_response = await _build_track_response(track, track_service)
            result.append(track_response)

        return result

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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
    status: Optional[str] = None,
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

        enrollments = await track_service.get_track_enrollments(track_id, status)

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
