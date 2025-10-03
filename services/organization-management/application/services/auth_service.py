"""
Authentication Service - Business Logic for Authentication
Single Responsibility: Handle authentication business logic
Open/Closed: Extensible through dependency injection
Dependency Inversion: Depends on authentication abstractions
"""
from typing import Dict, Any
from uuid import UUID
import logging

from auth.jwt_auth import JWTAuthenticator


class AuthService:
    """
    Service class for authentication business operations
    """

    def __init__(self, jwt_authenticator: JWTAuthenticator):
        self._jwt_authenticator = jwt_authenticator
        self._logger = logging.getLogger(__name__)

    async def authenticate_user(self, token: str) -> Dict[str, Any]:
        """
        Authenticate user with JWT token

        Args:
            token: JWT token string

        Returns:
            User information dictionary
        """
        try:
            return await self._jwt_authenticator.validate_token(token)
        except Exception as e:
            self._logger.error(f"Authentication failed: {str(e)}")
            raise

    def require_org_admin(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Require organization admin role

        Business Context:
        Organization admins and site admins can manage organization resources.
        Site admin (username='admin') has ALL permissions across ALL organizations.

        Args:
            user: User information

        Returns:
            User information if authorized

        Raises:
            HTTPException: If user doesn't have required role
        """
        from fastapi import HTTPException, status

        # Site admin (special user) has all permissions
        if user.get('username') == 'admin':
            return user

        required_roles = ["admin", "org_admin", "organization_admin"]
        user_roles = user.get('roles', [])

        if not any(role in required_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}"
            )

        return user

    def require_project_manager(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Require project manager role or higher

        Business Context:
        Project managers, org admins, and site admin can manage projects.

        Args:
            user: User information

        Returns:
            User information if authorized
        """
        from fastapi import HTTPException, status

        # Site admin (special user) has all permissions
        if user.get('username') == 'admin':
            return user

        required_roles = ["admin", "org_admin", "organization_admin", "project_manager"]
        user_roles = user.get('roles', [])

        if not any(role in required_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}"
            )

        return user

    def check_organization_access(self, user: Dict[str, Any], organization_id: UUID) -> bool:
        """
        Check if user has access to organization

        Business Context:
        - Site admin (username='admin') has access to ALL organizations
        - Organization admins have access ONLY to their specific organization
        - This enforces organization isolation for security

        Args:
            user: User information
            organization_id: Organization ID

        Returns:
            True if user has access

        Raises:
            HTTPException: If user doesn't have access to the organization
        """
        from fastapi import HTTPException, status

        # Site admin has access to all organizations
        if user.get('username') == 'admin':
            return True

        has_access = self._jwt_authenticator.require_organization_access(user, str(organization_id))

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to access this organization"
            )

        return True
