"""
JWT Authentication for Organization Management Service
Single Responsibility: JWT token validation and user extraction
Dependency Inversion: Uses configuration abstractions
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import jwt
import httpx
from fastapi import HTTPException, status
from omegaconf import DictConfig


class JWTAuthenticator:
    """
    JWT authentication handler for organization management service
    """

    def __init__(self, config: DictConfig):
        self._config = config
        self._logger = logging.getLogger(__name__)
        self._secret_key = config.get('jwt', {}).get('secret_key', 'your-secret-key-change-in-production')
        self._algorithm = config.get('jwt', {}).get('algorithm', 'HS256')
        self._user_service_url = config.get('services', {}).get('user_management_url', 'http://user-management:8000')

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token and extract user information

        Args:
            token: JWT token string

        Returns:
            User information dictionary

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Decode JWT token
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])

            # Extract user information
            user_id = payload.get('sub')
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user ID"
                )

            # Get additional user information from user service
            user_info = await self._get_user_info(user_id)

            return user_info

        except jwt.ExpiredSignatureError:
            self._logger.warning("Token expired for user")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError as e:
            self._logger.warning("Invalid token: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            self._logger.error("Error validating token: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )

    async def _get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from user management service

        Args:
            user_id: User ID

        Returns:
            User information dictionary
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self._user_service_url}/api/v1/users/{user_id}")

                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        "id": user_data["id"],
                        "email": user_data["email"],
                        "role": user_data.get("role", "student"),
                        "organization_id": user_data.get("organization_id"),
                        "full_name": user_data.get("full_name"),
                        "is_active": user_data.get("is_active", True)
                    }
                elif response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found"
                    )
                else:
                    self._logger.error("Error getting user info: HTTP %d", response.status_code)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="User service error"
                    )

        except httpx.RequestError as e:
            self._logger.error("Error connecting to user service: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User service unavailable"
            )

    def require_role(self, required_roles: list) -> callable:
        """
        Create a dependency that requires specific roles

        Args:
            required_roles: List of required roles

        Returns:
            FastAPI dependency function
        """
        def role_checker(user: Dict[str, Any]) -> Dict[str, Any]:
            user_role = user.get("role")
            if user_role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required roles: {required_roles}"
                )
            return user

        return role_checker

    def require_organization_access(self, user: Dict[str, Any], organization_id: str) -> bool:
        """
        Check if user has access to specific organization

        Args:
            user: User information
            organization_id: Organization ID to check access for

        Returns:
            True if user has access, False otherwise
        """
        user_role = user.get("role")
        user_org_id = user.get("organization_id")

        # Super admins have access to all organizations
        if user_role == "super_admin":
            return True

        # Organization admins and users have access to their own organization
        if user_org_id == organization_id:
            return True

        return False