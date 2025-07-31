"""
Site Admin FastAPI endpoints
Provides site-wide administrative capabilities including organization deletion
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict
from uuid import UUID
from pydantic import BaseModel

from application.services.organization_service import OrganizationService
from application.services.membership_service import MembershipService
from application.services.meeting_room_service import MeetingRoomService
from domain.entities.enhanced_role import RoleType, Permission
from app_dependencies import get_container, get_current_user, verify_site_admin_permission
from datetime import datetime

router = APIRouter(prefix="/api/v1/site-admin", tags=["Site Admin"])


class OrganizationDeletionRequest(BaseModel):
    organization_id: UUID
    confirmation_name: str  # Must match organization name for safety


class SiteStatsResponse(BaseModel):
    total_organizations: int
    total_users: int
    total_projects: int
    total_tracks: int
    total_meeting_rooms: int
    organizations_by_status: Dict[str, int]
    users_by_role: Dict[str, int]


async def get_organization_service() -> OrganizationService:
    """Get organization service from container"""
    return await get_container().get_organization_service()


async def get_membership_service() -> MembershipService:
    """Get membership service from container"""
    return await get_container().get_membership_service()


async def get_meeting_room_service() -> MeetingRoomService:
    """Get meeting room service from container"""
    return await get_container().get_meeting_room_service()


@router.get("/stats", response_model=SiteStatsResponse)
async def get_site_statistics(
    current_user=Depends(get_current_user),
    organization_service: OrganizationService = Depends(get_organization_service),
    membership_service: MembershipService = Depends(get_membership_service),
    meeting_room_service: MeetingRoomService = Depends(get_meeting_room_service)
):
    """Get comprehensive site statistics (Site Admin only)"""
    try:
        # Verify site admin permissions
        await verify_site_admin_permission(current_user)

        # Get organizations
        organizations = await organization_service.get_all_organizations()

        # Count organizations by status
        orgs_by_status = {}
        total_projects = 0
        total_tracks = 0

        for org in organizations:
            status_key = "active" if org.is_active() else "inactive"
            orgs_by_status[status_key] = orgs_by_status.get(status_key, 0) + 1

            # Count projects and tracks for each org
            projects = await organization_service.get_organization_projects(org.id)
            total_projects += len(projects)

            for project in projects:
                # Would need track service to count tracks per project
                # For now, assume we can get this data
                pass

        # Get all memberships for user role counting
        all_memberships = []
        for org in organizations:
            memberships = await membership_service.get_organization_members(org.id)
            all_memberships.extend(memberships)

        # Count users by role
        users_by_role = {}
        unique_users = set()

        for membership in all_memberships:
            role_type = membership["role_type"]
            users_by_role[role_type] = users_by_role.get(role_type, 0) + 1
            unique_users.add(membership["user_id"])

        # Count meeting rooms
        total_meeting_rooms = 0
        for org in organizations:
            rooms = await meeting_room_service.get_organization_rooms(org.id)
            total_meeting_rooms += len(rooms)

        return SiteStatsResponse(
            total_organizations=len(organizations),
            total_users=len(unique_users),
            total_projects=total_projects,
            total_tracks=total_tracks,  # Would need proper counting
            total_meeting_rooms=total_meeting_rooms,
            organizations_by_status=orgs_by_status,
            users_by_role=users_by_role
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/organizations", response_model=List[dict])
async def list_all_organizations(
    current_user=Depends(get_current_user),
    organization_service: OrganizationService = Depends(get_organization_service),
    membership_service: MembershipService = Depends(get_membership_service)
):
    """List all organizations with member counts (Site Admin only)"""
    try:
        # Verify site admin permissions
        await verify_site_admin_permission(current_user)

        organizations = await organization_service.get_all_organizations()

        result = []
        for org in organizations:
            # Get member counts
            members = await membership_service.get_organization_members(org.id)
            member_counts = {}
            for member in members:
                role = member["role_type"]
                member_counts[role] = member_counts.get(role, 0) + 1

            # Get project count
            projects = await organization_service.get_organization_projects(org.id)

            result.append({
                "id": str(org.id),
                "name": org.name,
                "slug": org.slug,
                "description": org.description,
                "created_at": org.created_at.isoformat(),
                "is_active": org.is_active(),
                "member_counts": member_counts,
                "total_members": len(members),
                "project_count": len(projects)
            })

        return result

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/organizations/{organization_id}")
async def delete_organization(
    organization_id: UUID,
    request: OrganizationDeletionRequest,
    current_user=Depends(get_current_user),
    organization_service: OrganizationService = Depends(get_organization_service),
    membership_service: MembershipService = Depends(get_membership_service),
    meeting_room_service: MeetingRoomService = Depends(get_meeting_room_service)
):
    """Delete organization and all associated data (Site Admin only)"""
    try:
        # Verify site admin permissions
        await verify_site_admin_permission(current_user)

        # Verify organization ID matches request
        if organization_id != request.organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization ID mismatch"
            )

        # Get organization for name verification
        organization = await organization_service.get_organization(organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        # Verify confirmation name matches
        if request.confirmation_name != organization.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization name confirmation does not match"
            )

        # Get all members before deletion for logging
        members = await membership_service.get_organization_members(organization_id)

        # Delete all meeting rooms first
        meeting_rooms = await meeting_room_service.get_organization_rooms(organization_id)
        for room in meeting_rooms:
            await meeting_room_service.delete_meeting_room(room.id)

        # Delete all memberships (this will cascade to track assignments)
        for member in members:
            await membership_service.remove_organization_member(
                UUID(member["membership_id"]),
                current_user.id
            )

        # Delete the organization (this will cascade to projects and tracks)
        success = await organization_service.delete_organization(organization_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete organization"
            )

        # Log the deletion
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Site admin {current_user.id} deleted organization {organization_id} "
            f"({organization.name}) with {len(members)} members and {len(meeting_rooms)} meeting rooms"
        )

        return {
            "message": "Organization deleted successfully",
            "organization_id": str(organization_id),
            "organization_name": organization.name,
            "deleted_members": len(members),
            "deleted_meeting_rooms": len(meeting_rooms)
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/organizations/{organization_id}/deactivate")
async def deactivate_organization(
    organization_id: UUID,
    current_user=Depends(get_current_user),
    organization_service: OrganizationService = Depends(get_organization_service)
):
    """Deactivate organization (soft delete - Site Admin only)"""
    try:
        # Verify site admin permissions
        await verify_site_admin_permission(current_user)

        success = await organization_service.deactivate_organization(organization_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        return {"message": "Organization deactivated successfully"}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/organizations/{organization_id}/reactivate")
async def reactivate_organization(
    organization_id: UUID,
    current_user=Depends(get_current_user),
    organization_service: OrganizationService = Depends(get_organization_service)
):
    """Reactivate organization (Site Admin only)"""
    try:
        # Verify site admin permissions
        await verify_site_admin_permission(current_user)

        # Get organization
        organization = await organization_service.get_organization(organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        # Reactivate
        organization.activate()
        updated_org = await organization_service.update_organization(organization)

        return {
            "message": "Organization reactivated successfully",
            "organization": {
                "id": str(updated_org.id),
                "name": updated_org.name,
                "is_active": updated_org.is_active()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/users/{user_id}/memberships")
async def get_user_all_memberships(
    user_id: UUID,
    current_user=Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service)
):
    """Get all memberships across all organizations for a user (Site Admin only)"""
    try:
        # Verify site admin permissions
        await verify_site_admin_permission(current_user)

        # This would require getting user memberships across all organizations
        # For now, return placeholder
        return {
            "user_id": str(user_id),
            "memberships": [],
            "message": "User membership lookup not yet implemented"
        }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/platform/health")
async def get_platform_health(
    current_user=Depends(get_current_user),
    meeting_room_service: MeetingRoomService = Depends(get_meeting_room_service)
):
    """Get platform integration health status (Site Admin only)"""
    try:
        # Verify site admin permissions
        await verify_site_admin_permission(current_user)

        from domain.entities.meeting_room import MeetingPlatform

        health_status = {
            "teams_integration": meeting_room_service.validate_platform_configuration(MeetingPlatform.TEAMS),
            "zoom_integration": meeting_room_service.validate_platform_configuration(MeetingPlatform.ZOOM),
            "database": True,  # Would need proper health check
            "timestamp": datetime.utcnow().isoformat()
        }

        return health_status

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
