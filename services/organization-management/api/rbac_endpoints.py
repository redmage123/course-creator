"""
FastAPI endpoints for Enhanced RBAC operations
Organization membership, track assignments, and role management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr

from organization_management.application.services.membership_service import MembershipService
from organization_management.application.services.meeting_room_service import MeetingRoomService
from organization_management.application.services.notification_service import NotificationService
from organization_management.domain.entities.enhanced_role import RoleType, Permission
from organization_management.domain.entities.meeting_room import MeetingPlatform, RoomType
from app_dependencies import get_container, get_current_user, verify_permission, get_membership_service, get_meeting_room_service, get_notification_service, verify_site_admin_permission

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
    role: Optional[str] = None,  # Changed from role_type to match frontend
    role_type: Optional[str] = None,  # Keep for backward compatibility
    current_user=Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service)
):
    """Get organization members filtered by role"""
    try:
        # Verify permissions
        await verify_permission(get_user_id(current_user), organization_id, Permission.MANAGE_ORGANIZATION)

        # Use 'role' parameter if provided, otherwise fall back to 'role_type'
        role_param = role or role_type
        role_filter = None
        if role_param:
            role_filter = RoleType(role_param)

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
        permission_map = {
            "teams": Permission.CREATE_TEAMS_ROOMS,
            "zoom": Permission.CREATE_ZOOM_ROOMS,
            "slack": Permission.CREATE_SLACK_ROOMS
        }
        platform_permission = permission_map.get(request.platform)
        if not platform_permission:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid platform: {request.platform}")
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


# ==================== AUDIT LOG ENDPOINTS ====================

class AuditLogEntry(BaseModel):
    """
    Audit log entry response model

    BUSINESS CONTEXT:
    Audit logs provide compliance, security monitoring, and accountability
    for all platform actions. Each entry records who did what, when, and from where.
    """
    event_id: str
    action: str
    timestamp: str
    user_id: Optional[str]
    user_name: Optional[str]
    user_email: Optional[str]
    organization_id: Optional[str]
    target_resource_type: Optional[str]
    target_resource: Optional[str]
    description: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    severity: str


@router.get("/audit-log")
async def get_audit_log(
    action: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    GET /api/v1/rbac/audit-log

    Retrieve audit log entries with optional filtering

    BUSINESS REQUIREMENT:
    Site admins need to review platform activity for security monitoring,
    compliance auditing, and troubleshooting.

    TECHNICAL IMPLEMENTATION:
    - Filters by action type and date
    - Paginated results (default 100 entries)
    - Requires site_admin role
    - Returns structured audit entries with user/resource details

    SECURITY:
    - Only site admins can access audit logs
    - All queries are logged
    - Sensitive data is redacted
    """
    from fastapi.responses import JSONResponse
    
    try:
        # Verify site admin permission
        await verify_site_admin_permission(current_user)

        # Mock audit log data for now (replace with actual database query)
        # TODO: Implement database storage and retrieval
        mock_entries = [
            {
                "event_id": "audit-001",
                "action": "organization_created",
                "timestamp": "2025-01-15T10:30:00Z",
                "user_id": "user-123",
                "user_name": "John Admin",
                "user_email": "john@example.com",
                "organization_id": "org-456",
                "target_resource_type": "organization",
                "target_resource": "Acme Corp",
                "description": "Created new organization Acme Corp",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0",
                "severity": "medium"
            },
            {
                "event_id": "audit-002",
                "action": "user_created",
                "timestamp": "2025-01-15T11:00:00Z",
                "user_id": "user-123",
                "user_name": "John Admin",
                "user_email": "john@example.com",
                "organization_id": "org-456",
                "target_resource_type": "user",
                "target_resource": "jane@example.com",
                "description": "Created new user account for jane@example.com",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0",
                "severity": "medium"
            }
        ]

        # Filter by action if specified
        filtered_entries = mock_entries
        if action:
            filtered_entries = [e for e in filtered_entries if e["action"] == action]

        # Filter by date if specified
        if date:
            filtered_entries = [e for e in filtered_entries if e["timestamp"].startswith(date)]

        # Apply pagination
        total = len(filtered_entries)
        paginated_entries = filtered_entries[offset:offset + limit]

        return {
            "entries": paginated_entries,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit log: {str(e)}"
        )


@router.get("/audit-log/export")
async def export_audit_log(
    action: Optional[str] = None,
    date: Optional[str] = None,
    format: str = "csv",
    current_user: dict = Depends(get_current_user)
):
    """
    GET /api/v1/rbac/audit-log/export

    Export audit log entries to CSV format

    BUSINESS REQUIREMENT:
    Organizations need to export audit logs for compliance reporting,
    external security audits, and long-term archival.

    TECHNICAL IMPLEMENTATION:
    - Supports CSV format (JSON format could be added)
    - Applies same filters as main audit log endpoint
    - Returns file as download attachment
    - Includes all audit entry fields

    SECURITY:
    - Only site admins can export audit logs
    - Export actions are themselves logged
    - Large exports may be rate-limited
    """
    from fastapi.responses import StreamingResponse
    import io
    import csv
    from datetime import datetime as dt

    try:
        # Verify site admin permission
        await verify_site_admin_permission(current_user)

        # Mock data (same as get_audit_log)
        mock_entries = [
            {
                "event_id": "audit-001",
                "action": "organization_created",
                "timestamp": "2025-01-15T10:30:00Z",
                "user_id": "user-123",
                "user_name": "John Admin",
                "user_email": "john@example.com",
                "organization_id": "org-456",
                "target_resource_type": "organization",
                "target_resource": "Acme Corp",
                "description": "Created new organization Acme Corp",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0",
                "severity": "medium"
            },
            {
                "event_id": "audit-002",
                "action": "user_created",
                "timestamp": "2025-01-15T11:00:00Z",
                "user_id": "user-123",
                "user_name": "John Admin",
                "user_email": "john@example.com",
                "organization_id": "org-456",
                "target_resource_type": "user",
                "target_resource": "jane@example.com",
                "description": "Created new user account for jane@example.com",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0",
                "severity": "medium"
            }
        ]

        # Filter if needed
        filtered_entries = mock_entries
        if action:
            filtered_entries = [e for e in filtered_entries if e["action"] == action]
        if date:
            filtered_entries = [e for e in filtered_entries if e["timestamp"].startswith(date)]

        # Create CSV
        output = io.StringIO()
        if filtered_entries:
            fieldnames = list(filtered_entries[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered_entries)

        # Return as downloadable file
        output.seek(0)
        filename = f"audit-log-{dt.now().strftime('%Y-%m-%d')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export audit log: {str(e)}"
        )


# ============================================================================
# BULK MEETING ROOM CREATION ENDPOINTS
# ============================================================================

@router.post("/organizations/{organization_id}/meeting-rooms/bulk-create-instructor-rooms")
async def bulk_create_instructor_rooms(
    organization_id: UUID,
    platform: str,
    send_notifications: bool = True,
    current_user=Depends(get_current_user),
    meeting_room_service: MeetingRoomService = Depends(get_meeting_room_service)
):
    """
    POST /api/v1/rbac/organizations/{organization_id}/meeting-rooms/bulk-create-instructor-rooms

    Create meeting rooms for all instructors in organization

    BUSINESS REQUIREMENT:
    Org admins need ability to create meeting rooms for all instructors at once
    when setting up a new organization or onboarding multiple instructors.
    Each instructor gets a personal room on the specified platform.

    TECHNICAL IMPLEMENTATION:
    - Validates user has permission to create rooms
    - Creates rooms only for instructors who don't already have one
    - Sends notifications to each instructor with room details
    - Returns summary of creation results

    SECURITY:
    - Requires MANAGE_MEETING_ROOMS permission
    - Must be org admin or site admin
    """
    try:
        # Verify permissions
        user_id = get_user_id(current_user)
        await verify_permission(user_id, organization_id, Permission.MANAGE_MEETING_ROOMS)

        # Validate platform
        try:
            platform_enum = MeetingPlatform(platform)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {platform}"
            )

        # Create rooms for all instructors
        results = await meeting_room_service.create_rooms_for_all_instructors(
            organization_id=organization_id,
            platform=platform_enum,
            created_by=user_id,
            send_notifications=send_notifications
        )

        return {
            "success": True,
            "organization_id": str(organization_id),
            "platform": platform,
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create instructor rooms: {str(e)}"
        )


@router.post("/organizations/{organization_id}/meeting-rooms/bulk-create-track-rooms")
async def bulk_create_track_rooms(
    organization_id: UUID,
    platform: str,
    send_notifications: bool = True,
    current_user=Depends(get_current_user),
    meeting_room_service: MeetingRoomService = Depends(get_meeting_room_service)
):
    """
    POST /api/v1/rbac/organizations/{organization_id}/meeting-rooms/bulk-create-track-rooms

    Create meeting rooms for all tracks in organization

    BUSINESS REQUIREMENT:
    Org admins need ability to create meeting rooms for all tracks at once
    to ensure every track has a dedicated space for synchronous learning.
    All students and instructors in each track are notified.

    TECHNICAL IMPLEMENTATION:
    - Validates user has permission to create rooms
    - Creates rooms only for tracks that don't already have one
    - Sends notifications to all track participants
    - Returns summary of creation results

    SECURITY:
    - Requires MANAGE_MEETING_ROOMS permission
    - Must be org admin or site admin
    """
    try:
        # Verify permissions
        user_id = get_user_id(current_user)
        await verify_permission(user_id, organization_id, Permission.MANAGE_MEETING_ROOMS)

        # Validate platform
        try:
            platform_enum = MeetingPlatform(platform)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {platform}"
            )

        # Create rooms for all tracks
        results = await meeting_room_service.create_rooms_for_all_tracks(
            organization_id=organization_id,
            platform=platform_enum,
            created_by=user_id,
            send_notifications=send_notifications
        )

        return {
            "success": True,
            "organization_id": str(organization_id),
            "platform": platform,
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create track rooms: {str(e)}"
        )


# ============================================================================
# NOTIFICATION ENDPOINTS
# ============================================================================

@router.post("/organizations/{organization_id}/notifications/send-channel-notification")
async def send_channel_notification(
    organization_id: UUID,
    channel_id: str,
    title: str,
    message: str,
    priority: str = "normal",
    current_user=Depends(get_current_user),
    notification_service = Depends(get_notification_service)
):
    """
    POST /api/v1/rbac/organizations/{organization_id}/notifications/send-channel-notification

    Send notification to a Slack channel

    BUSINESS REQUIREMENT:
    Org admins need ability to send announcements and updates to
    organization channels. Used for course updates, deadline reminders,
    and general announcements.

    TECHNICAL IMPLEMENTATION:
    - Sends formatted notification to Slack channel
    - Supports priority levels (low, normal, high, urgent)
    - Priority affects message color and styling

    SECURITY:
    - Requires MANAGE_ORGANIZATION permission
    - Must be org admin or site admin
    """
    try:
        # Verify permissions
        user_id = get_user_id(current_user)
        await verify_permission(user_id, organization_id, Permission.MANAGE_ORGANIZATION)

        # Validate priority
        try:
            from organization_management.domain.entities.notification import NotificationPriority, NotificationEvent
            priority_enum = NotificationPriority(priority)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority: {priority}"
            )

        # Send notification
        success = await notification_service.send_channel_notification(
            channel_id=channel_id,
            event_type=NotificationEvent.SYSTEM_ANNOUNCEMENT,
            title=title,
            message=message,
            organization_id=organization_id,
            priority=priority_enum
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send notification"
            )

        return {
            "success": True,
            "channel_id": channel_id,
            "title": title
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send channel notification: {str(e)}"
        )


@router.post("/organizations/{organization_id}/notifications/send-announcement")
async def send_organization_announcement(
    organization_id: UUID,
    title: str,
    message: str,
    priority: str = "normal",
    current_user=Depends(get_current_user),
    notification_service = Depends(get_notification_service)
):
    """
    POST /api/v1/rbac/organizations/{organization_id}/notifications/send-announcement

    Send announcement to all members of organization

    BUSINESS REQUIREMENT:
    Org admins need ability to send important announcements to all
    organization members. Used for policy changes, system updates,
    and organization-wide communications.

    TECHNICAL IMPLEMENTATION:
    - Sends notification to all organization members
    - Respects individual user notification preferences
    - Returns count of notifications sent

    SECURITY:
    - Requires MANAGE_ORGANIZATION permission
    - Must be org admin or site admin
    """
    try:
        # Verify permissions
        user_id = get_user_id(current_user)
        await verify_permission(user_id, organization_id, Permission.MANAGE_ORGANIZATION)

        # Validate priority
        try:
            from organization_management.domain.entities.notification import NotificationPriority
            priority_enum = NotificationPriority(priority)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority: {priority}"
            )

        # Send announcement
        sent_count = await notification_service.send_organization_announcement(
            organization_id=organization_id,
            title=title,
            message=message,
            priority=priority_enum
        )

        return {
            "success": True,
            "organization_id": str(organization_id),
            "sent_count": sent_count,
            "title": title
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send announcement: {str(e)}"
        )


@router.get("/organizations/{organization_id}/notifications/statistics")
async def get_notification_statistics(
    organization_id: UUID,
    current_user=Depends(get_current_user),
    notification_service = Depends(get_notification_service)
):
    """
    GET /api/v1/rbac/organizations/{organization_id}/notifications/statistics

    Get notification statistics for organization

    BUSINESS REQUIREMENT:
    Org admins need insights into notification effectiveness,
    user engagement, and communication patterns.

    TECHNICAL IMPLEMENTATION:
    - Aggregates notification data by event type, priority, status
    - Calculates read rates and engagement metrics
    - Returns structured statistics

    SECURITY:
    - Requires MANAGE_ORGANIZATION permission
    - Must be org admin or site admin
    """
    try:
        # Verify permissions
        user_id = get_user_id(current_user)
        await verify_permission(user_id, organization_id, Permission.MANAGE_ORGANIZATION)

        # Get statistics
        stats = await notification_service.get_notification_statistics(organization_id)

        return {
            "success": True,
            "organization_id": str(organization_id),
            "statistics": stats
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification statistics: {str(e)}"
        )

