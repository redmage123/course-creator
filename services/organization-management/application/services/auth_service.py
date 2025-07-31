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

        Args:
            user: User information

        Returns:
            User information if authorized

        Raises:
            HTTPException: If user doesn't have required role
        """
        required_roles = ["super_admin", "org_admin"]
        return self._jwt_authenticator.require_role(required_roles)(user)

    def require_project_manager(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Require project manager role or higher

        Args:
            user: User information

        Returns:
            User information if authorized
        """
        required_roles = ["super_admin", "org_admin", "project_manager"]
        return self._jwt_authenticator.require_role(required_roles)(user)

    def check_organization_access(self, user: Dict[str, Any], organization_id: UUID) -> bool:
        """
        Check if user has access to organization

        Args:
            user: User information
            organization_id: Organization ID

        Returns:
            True if user has access
        """
        return self._jwt_authenticator.require_organization_access(user, str(organization_id))
