"""
Authentication and Authorization Dependencies
Provides FastAPI dependency functions for RBAC system
"""
from fastapi import HTTPException, status
from typing import Dict, Any
from uuid import UUID

from domain.entities.enhanced_role import Permission, RoleType
from app.dependencies import get_container


async def verify_permission(user_id: UUID, organization_id: UUID, permission: Permission) -> bool:
    """Verify user has specific permission in organization"""
    try:
        membership_service = await get_container().get_membership_service()
        has_permission = await membership_service.check_user_permission(
            user_id, organization_id, permission
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {permission.value}"
            )

        return True

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Permission check failed: {str(e)}"
        )


async def verify_site_admin_permission(current_user: Dict[str, Any]) -> bool:
    """Verify user is site admin"""
    try:
        # Check if user has site admin role
        user_role = current_user.get('role')
        if user_role != 'admin':  # Assuming 'admin' is the site admin role
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Site administrator access required"
            )

        return True

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Site admin permission check failed: {str(e)}"
        )


async def verify_organization_admin(user_id: UUID, organization_id: UUID) -> bool:
    """Verify user is organization admin"""
    return await verify_permission(user_id, organization_id, Permission.MANAGE_ORGANIZATION)


async def verify_can_add_admins(user_id: UUID, organization_id: UUID) -> bool:
    """Verify user can add organization admins"""
    return await verify_permission(user_id, organization_id, Permission.ADD_ORGANIZATION_ADMINS)


async def verify_can_add_instructors(user_id: UUID, organization_id: UUID) -> bool:
    """Verify user can add instructors to organization"""
    return await verify_permission(user_id, organization_id, Permission.ADD_INSTRUCTORS_TO_ORG)


async def verify_can_manage_students(user_id: UUID, organization_id: UUID) -> bool:
    """Verify user can manage students"""
    return await verify_permission(user_id, organization_id, Permission.ADD_STUDENTS_TO_PROJECT)


async def verify_can_manage_tracks(user_id: UUID, organization_id: UUID) -> bool:
    """Verify user can manage tracks"""
    return await verify_permission(user_id, organization_id, Permission.CREATE_TRACKS)


async def verify_can_create_meeting_rooms(user_id: UUID, organization_id: UUID, platform: str) -> bool:
    """Verify user can create meeting rooms for platform"""
    if platform.lower() == "teams":
        permission = Permission.CREATE_TEAMS_ROOMS
    elif platform.lower() == "zoom":
        permission = Permission.CREATE_ZOOM_ROOMS
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported platform: {platform}"
        )

    return await verify_permission(user_id, organization_id, permission)


async def get_user_role_in_organization(user_id: UUID, organization_id: UUID) -> Dict[str, Any]:
    """Get user's role and permissions in organization"""
    try:
        membership_service = await get_container().get_membership_service()

        # Get user membership
        membership_repo = await get_container().get_membership_repository()
        membership = await membership_repo.get_user_membership(user_id, organization_id)

        if not membership or not membership.is_active():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a member of this organization"
            )

        return {
            "role_type": membership.role.role_type.value,
            "permissions": [p.value for p in membership.role.permissions],
            "project_ids": [str(pid) for pid in membership.role.project_ids],
            "track_ids": [str(tid) for tid in membership.role.track_ids],
            "membership_id": str(membership.id)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user role: {str(e)}"
        )


def require_permissions(*permissions: Permission):
    """Decorator to require specific permissions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be implemented as a FastAPI dependency
            # For now, it's a placeholder
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(*roles: RoleType):
    """Decorator to require specific roles"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be implemented as a FastAPI dependency
            # For now, it's a placeholder
            return await func(*args, **kwargs)
        return wrapper
    return decorator