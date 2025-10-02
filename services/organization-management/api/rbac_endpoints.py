"""
FastAPI endpoints for Enhanced RBAC operations
Organization membership, track assignments, and role management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr

from application.services.membership_service import MembershipService
from application.services.meeting_room_service import MeetingRoomService
from domain.entities.enhanced_role import RoleType, Permission
from domain.entities.meeting_room import MeetingPlatform, RoomType
from app_dependencies import get_container, get_current_user, verify_permission, get_membership_service, get_meeting_room_service

router = APIRouter(prefix="/api/v1/rbac", tags=["RBAC"])


def get_user_id(user: Dict[str, Any]) -> UUID:
    """Extract user ID from user dict or object"""
    if isinstance(user, dict):
        user_id = user.get('id') or user.get('user_id')
        return UUID(user_id) if isinstance(user_id, str) else user_id
    return user.id


# Pydantic models for requests/responses


class AddMemberRequest(BaseModel):
    user_email: EmailStr
    role_type: str = "instructor"  # instructor, organization_admin
    project_ids: Optional[List[UUID]] = None


class AssignStudentRequest(BaseModel):
    user_email: EmailStr
    track_id: UUID


class AssignInstructorRequest(BaseModel):
    instructor_id: UUID
    track_id: UUID


class CreateMeetingRoomRequest(BaseModel):
    name: str
    platform: str  # "teams" or "zoom"
    room_type: str  # "track_room", "instructor_room", "project_room"
    project_id: Optional[UUID] = None
    track_id: Optional[UUID] = None
    instructor_id: Optional[UUID] = None
    settings: Optional[dict] = None


class MemberResponse(BaseModel):
    membership_id: str
    user_id: str
    email: str
    name: str
    role_type: str
    permissions: List[str]
    project_ids: List[str]
    track_ids: List[str]
    status: str
    invited_at: str
    accepted_at: Optional[str]


class AssignmentResponse(BaseModel):
    assignment_id: str
    user_id: str
    email: str
    name: str
    assigned_at: str
    status: str


class MeetingRoomResponse(BaseModel):
    id: str
    name: str
    display_name: str
    platform: str
    room_type: str
    join_url: Optional[str]
    host_url: Optional[str]
    meeting_id: Optional[str]
    status: str
    created_at: str

# Remove duplicate functions since they're now in app_dependencies

# Organization membership endpoints


@router.post("/organizations/{organization_id}/members", response_model=MemberResponse)
async def add_organization_member(
    organization_id: UUID,
    request: AddMemberRequest,
    current_user=Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service)
):
    """Add member (admin or instructor) to organization"""
    try:
        # Verify permissions
        user_id = get_user_id(current_user)
        await verify_permission(
            user_id,
            organization_id,
            Permission.ADD_ORGANIZATION_ADMINS if request.role_type == "organization_admin" else Permission.ADD_INSTRUCTORS_TO_ORG
        )

        if request.role_type == "organization_admin":
            membership = await membership_service.add_organization_admin(
                organization_id, request.user_email, user_id
            )
        elif request.role_type == "instructor":
            membership = await membership_service.add_instructor_to_organization(
                organization_id, request.user_email, user_id, request.project_ids
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role type: {request.role_type}"
            )

        # Convert to response format
        members = await membership_service.get_organization_members(organization_id)
        member_data = next((m for m in members if m["membership_id"] == str(membership.id)), None)

        if not member_data:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve created member")

        return MemberResponse(**member_data)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/organizations/{organization_id}/members", response_model=List[MemberResponse])
async def get_organization_members(
    organization_id: UUID,
    role_type: Optional[str] = None,
    current_user=Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service)
):
    """Get organization members"""
    try:
        # Verify permissions
        await verify_permission(get_user_id(current_user), organization_id, Permission.MANAGE_ORGANIZATION)

        role_filter = None
        if role_type:
            role_filter = RoleType(role_type)

        members = await membership_service.get_organization_members(organization_id, role_filter)
        return [MemberResponse(**member) for member in members]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/organizations/{organization_id}/members/{membership_id}")
async def remove_organization_member(
    organization_id: UUID,
    membership_id: UUID,
    current_user=Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service)
):
    """Remove member from organization"""
    try:
        # Verify permissions
        await verify_permission(get_user_id(current_user), organization_id, Permission.REMOVE_ORGANIZATION_ADMINS)

        success = await membership_service.remove_organization_member(membership_id, get_user_id(current_user))

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        return {"message": "Member removed successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Student assignment endpoints


@router.post("/projects/{project_id}/students", response_model=dict)
async def assign_student_to_project(
    project_id: UUID,
    request: AssignStudentRequest,
    current_user=Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service)
):
    """Assign student to project and track"""
    try:
        # Get organization ID from project (would need project service)
        # For now, assume we can get it from the current user's context
        organization_id = current_user.organization_id  # This would need proper implementation

        # Verify permissions
        await verify_permission(get_user_id(current_user), organization_id, Permission.ADD_STUDENTS_TO_PROJECT)

        membership, assignment = await membership_service.add_student_to_project(
            project_id, organization_id, request.user_email, request.track_id, get_user_id(current_user)
        )

        return {
            "message": "Student assigned successfully",
            "membership_id": str(membership.id),
            "assignment_id": str(assignment.id)
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Track assignment endpoints


@router.post("/tracks/{track_id}/instructors")
async def assign_instructor_to_track(
    track_id: UUID,
    request: AssignInstructorRequest,
    current_user=Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service)
):
    """Assign instructor to teach track"""
    try:
        # Verify permissions (would need to get organization from track)
        # await verify_permission(get_user_id(current_user), organization_id, Permission.ASSIGN_INSTRUCTORS_TO_TRACKS)

        assignment = await membership_service.assign_instructor_to_track(
            request.instructor_id, track_id, get_user_id(current_user)
        )

        return {
            "message": "Instructor assigned successfully",
            "assignment_id": str(assignment.id)
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/tracks/{track_id}/instructors", response_model=List[AssignmentResponse])
async def get_track_instructors(
    track_id: UUID,
    current_user=Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service)
):
    """Get instructors assigned to track"""
    try:
        instructors = await membership_service.get_track_instructors(track_id)
        return [AssignmentResponse(**instructor) for instructor in instructors]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/tracks/{track_id}/students", response_model=List[AssignmentResponse])
async def get_track_students(
    track_id: UUID,
    current_user=Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service)
):
    """Get students assigned to track"""
    try:
        students = await membership_service.get_track_students(track_id)
        return [AssignmentResponse(**student) for student in students]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Meeting room endpoints


@router.post("/organizations/{organization_id}/meeting-rooms", response_model=MeetingRoomResponse)
async def create_meeting_room(
    organization_id: UUID,
    request: CreateMeetingRoomRequest,
    current_user=Depends(get_current_user),
    meeting_room_service: MeetingRoomService = Depends(get_meeting_room_service)
):
    """Create meeting room"""
    try:
        # Verify permissions
        user_id = get_user_id(current_user)
        platform_permission = Permission.CREATE_TEAMS_ROOMS if request.platform == "teams" else Permission.CREATE_ZOOM_ROOMS
        await verify_permission(user_id, organization_id, platform_permission)

        # Validate and convert enums
        try:
            platform = MeetingPlatform(request.platform)
            room_type = RoomType(request.room_type)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid enum value: {e}")

        room = await meeting_room_service.create_meeting_room(
            organization_id=organization_id,
            name=request.name,
            platform=platform,
            room_type=room_type,
            created_by=user_id,
            project_id=request.project_id,
            track_id=request.track_id,
            instructor_id=request.instructor_id,
            settings=request.settings
        )

        return MeetingRoomResponse(
            id=str(room.id),
            name=room.name,
            display_name=room.get_display_name(),
            platform=room.platform.value,
            room_type=room.room_type.value,
            join_url=room.join_url,
            host_url=room.host_url,
            meeting_id=room.meeting_id,
            status=room.status,
            created_at=room.created_at.isoformat()
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/organizations/{organization_id}/meeting-rooms", response_model=List[MeetingRoomResponse])
async def get_organization_meeting_rooms(
    organization_id: UUID,
    platform: Optional[str] = None,
    room_type: Optional[str] = None,
    current_user=Depends(get_current_user),
    meeting_room_service: MeetingRoomService = Depends(get_meeting_room_service)
):
    """Get organization meeting rooms"""
    try:
        # Verify permissions
        await verify_permission(get_user_id(current_user), organization_id, Permission.MANAGE_MEETING_ROOMS)

        platform_filter = None
        room_type_filter = None

        if platform:
            platform_filter = MeetingPlatform(platform)
        if room_type:
            room_type_filter = RoomType(room_type)

        rooms = await meeting_room_service.get_organization_rooms(
            organization_id, platform_filter, room_type_filter
        )

        return [
            MeetingRoomResponse(
                id=str(room.id),
                name=room.name,
                display_name=room.get_display_name(),
                platform=room.platform.value,
                room_type=room.room_type.value,
                join_url=room.join_url,
                host_url=room.host_url,
                meeting_id=room.meeting_id,
                status=room.status,
                created_at=room.created_at.isoformat()
            )
            for room in rooms
        ]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/meeting-rooms/{room_id}")
async def delete_meeting_room(
    room_id: UUID,
    current_user=Depends(get_current_user),
    meeting_room_service: MeetingRoomService = Depends(get_meeting_room_service)
):
    """Delete meeting room"""
    try:
        # Would need to verify permissions based on room's organization
        success = await meeting_room_service.delete_meeting_room(room_id)

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

        return {"message": "Meeting room deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/meeting-rooms/{room_id}/invite")
async def send_room_invitations(
    room_id: UUID,
    invitee_emails: List[EmailStr],
    current_user=Depends(get_current_user),
    meeting_room_service: MeetingRoomService = Depends(get_meeting_room_service)
):
    """Send meeting room invitations"""
    try:
        success = await meeting_room_service.send_room_invitation(room_id, invitee_emails)

        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to send invitations")

        return {"message": f"Invitations sent to {len(invitee_emails)} users"}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Quick room creation endpoints


@router.post("/tracks/{track_id}/meeting-room", response_model=MeetingRoomResponse)
async def create_track_room(
    track_id: UUID,
    platform: str,
    name: Optional[str] = None,
    current_user=Depends(get_current_user),
    meeting_room_service: MeetingRoomService = Depends(get_meeting_room_service)
):
    """Create meeting room for track"""
    try:
        # Would need to get organization_id from track
        organization_id = current_user.organization_id  # Placeholder

        platform_enum = MeetingPlatform(platform)

        room = await meeting_room_service.create_track_room(
            track_id, organization_id, platform_enum, get_user_id(current_user), name
        )

        return MeetingRoomResponse(
            id=str(room.id),
            name=room.name,
            display_name=room.get_display_name(),
            platform=room.platform.value,
            room_type=room.room_type.value,
            join_url=room.join_url,
            host_url=room.host_url,
            meeting_id=room.meeting_id,
            status=room.status,
            created_at=room.created_at.isoformat()
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/instructors/{instructor_id}/meeting-room", response_model=MeetingRoomResponse)
async def create_instructor_room(
    instructor_id: UUID,
    platform: str,
    name: Optional[str] = None,
    current_user=Depends(get_current_user),
    meeting_room_service: MeetingRoomService = Depends(get_meeting_room_service)
):
    """Create personal meeting room for instructor"""
    try:
        organization_id = current_user.organization_id  # Placeholder

        platform_enum = MeetingPlatform(platform)

        room = await meeting_room_service.create_instructor_room(
            instructor_id, organization_id, platform_enum, get_user_id(current_user), name
        )

        return MeetingRoomResponse(
            id=str(room.id),
            name=room.name,
            display_name=room.get_display_name(),
            platform=room.platform.value,
            room_type=room.room_type.value,
            join_url=room.join_url,
            host_url=room.host_url,
            meeting_id=room.meeting_id,
            status=room.status,
            created_at=room.created_at.isoformat()
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
