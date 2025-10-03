"""
FastAPI Dependencies for Organization Management Service
Single Responsibility: Dependency injection for FastAPI endpoints
"""
from typing import Dict, Any, List
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from infrastructure.container import get_container
from application.services.organization_service import OrganizationService
from application.services.auth_service import AuthService
from application.services.membership_service import MembershipService
from application.services.meeting_room_service import MeetingRoomService
from domain.entities.enhanced_role import Permission

security = HTTPBearer()

def get_config():
    """Get current Hydra configuration"""
    from main import current_config
    return current_config


async def get_organization_service() -> OrganizationService:
    """Get organization service for FastAPI dependency injection"""
    container = get_container()
    return await container.get_organization_service()


def get_auth_service() -> AuthService:
    """Get authentication service for FastAPI dependency injection"""
    container = get_container()
    return container.get_auth_service()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    return await auth_service.authenticate_user(credentials.credentials)


async def require_org_admin(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """Require organization admin role"""
    return auth_service.require_org_admin(current_user)


async def require_project_manager(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """Require project manager role or higher"""
    return auth_service.require_project_manager(current_user)


async def require_instructor_or_admin(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    Require instructor role or higher (instructor, project_manager, org_admin)

    Business Context:
    Site admin (username='admin') bypasses role checks and has all permissions.
    """
    # Site admin has all permissions
    if current_user.get('username') == 'admin':
        return current_user

    user_roles = current_user.get('roles', [])
    allowed_roles = ['instructor', 'project_manager', 'org_admin', 'organization_admin', 'admin']

    if not any(role in allowed_roles for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor, project manager, or administrator access required"
        )

    return current_user


async def get_membership_service() -> MembershipService:
    """Get membership service for FastAPI dependency injection"""
    container = get_container()
    return await container.get_membership_service()


async def get_meeting_room_service() -> MeetingRoomService:
    """Get meeting room service for FastAPI dependency injection"""
    container = get_container()
    return await container.get_meeting_room_service()


async def verify_permission(user_id: UUID, organization_id: UUID, permission: Permission) -> bool:
    """Verify user has specific permission in organization"""
    try:
        membership_service = await get_membership_service()
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


async def verify_organization_access(
    organization_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> bool:
    """
    Verify user has access to the specified organization

    Business Context:
    - Site admin (username='admin') has access to ALL organizations
    - Organization admins can ONLY access their own organization
    - This enforces proper organization isolation for security

    Args:
        organization_id: Organization ID to check access for
        current_user: Current authenticated user
        auth_service: Authentication service

    Returns:
        True if user has access

    Raises:
        HTTPException: If user doesn't have access to the organization
    """
    return auth_service.check_organization_access(current_user, organization_id)


async def verify_site_admin_permission(current_user: Dict[str, Any]) -> bool:
    """
    Verify user is site admin using configuration-driven role definitions

    Business Context:
    Site admin verification uses Hydra configuration to avoid hard-coded role strings.
    This enables flexible role management and easier configuration updates.
    """
    try:
        config = get_config()
        user_role = current_user.get('role')
        username = current_user.get('username')

        # Get allowed roles from configuration
        allowed_roles: List[str] = [
            config.roles.admin,
            config.roles.organization_admin
        ]

        # Get site admin username from configuration
        site_admin_username = config.special_users.site_admin_username

        # Allow configured roles or configured site admin username
        if user_role not in allowed_roles and username != site_admin_username:
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