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
    Service class for authentication business operations in the organization management service.

    BUSINESS PURPOSE:
    Provides centralized authentication and authorization logic for organization-level operations.
    Enforces role-based access control (RBAC) and organization isolation for multi-tenant security.

    RESPONSIBILITIES:
    - JWT token validation for authenticated requests
    - Role-based permission enforcement (org admin, project manager, site admin)
    - Organization-level access control and isolation
    - Multi-tenant security boundary enforcement

    MULTI-TENANT SECURITY:
    This service implements critical security boundaries:
    - Site admin (username='admin') has global access to ALL organizations
    - Organization admins have access ONLY to their specific organization
    - Organization isolation prevents cross-tenant data access
    - Enforces principle of least privilege through role hierarchies

    DESIGN PATTERNS:
    - Single Responsibility: Handles only authentication/authorization logic
    - Dependency Inversion: Depends on JWTAuthenticator abstraction
    - Open/Closed: Extensible through dependency injection

    Args:
        jwt_authenticator: JWT token validation service for user authentication
    """

    def __init__(self, jwt_authenticator: JWTAuthenticator):
        """
        Initialize authentication service with JWT authenticator.

        Args:
            jwt_authenticator: Service for validating JWT tokens and extracting user information
        """
        self._jwt_authenticator = jwt_authenticator
        self._logger = logging.getLogger(__name__)

    async def authenticate_user(self, token: str) -> Dict[str, Any]:
        """
        Authenticate user with JWT token and extract user information.

        WHAT: Validates JWT token and extracts user identity and roles
        WHY: All organization management operations require authenticated users

        BUSINESS CONTEXT:
        This is the entry point for all authenticated requests. The JWT token contains:
        - User ID and username for identity
        - User roles for authorization (student, instructor, org_admin, site_admin)
        - Organization membership for multi-tenant isolation

        TECHNICAL IMPLEMENTATION:
        Delegates to JWTAuthenticator for cryptographic validation and claims extraction.
        Token validation includes signature verification, expiration check, and issuer validation.

        Args:
            token: JWT token string from Authorization header (Bearer <token>)

        Returns:
            Dict containing user information:
                - id: User UUID
                - username: User login name
                - email: User email address
                - roles: List of role names (e.g., ['org_admin', 'instructor'])
                - organization_id: UUID of user's primary organization

        Raises:
            Exception: If token is invalid, expired, or malformed
        """
        try:
            return await self._jwt_authenticator.validate_token(token)
        except Exception as e:
            self._logger.error(f"Authentication failed: {str(e)}")
            raise

    def require_org_admin(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Require organization admin role for operation authorization.

        WHAT: Validates user has organization admin privileges
        WHY: Organization-level operations (manage members, settings, projects) require admin role

        BUSINESS CONTEXT:
        Organization admins and site admins can manage organization resources.
        Site admin (username='admin') has ALL permissions across ALL organizations.

        ROLE HIERARCHY:
        - site_admin (username='admin'): Global access to all organizations
        - org_admin/organization_admin/admin: Access to specific organization only
        - Instructors, students: No organization management access

        Args:
            user: User information dict from JWT token

        Returns:
            User information if authorized

        Raises:
            HTTPException 403: If user doesn't have required admin role
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
        Require project manager role or higher for project operations.

        WHAT: Validates user has project management privileges
        WHY: Project creation, track management, and content operations require elevated permissions

        BUSINESS CONTEXT:
        Project managers, org admins, and site admin can manage projects.
        This enables delegation of project management without full org admin access.

        ROLE HIERARCHY (highest to lowest):
        - site_admin: All permissions globally
        - org_admin/organization_admin: All permissions in their organization
        - project_manager: Can create/manage projects and tracks
        - instructor: Can only manage assigned courses
        - student: Read-only access to enrolled content

        Args:
            user: User information dict from JWT token

        Returns:
            User information if authorized

        Raises:
            HTTPException 403: If user lacks project management privileges
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
