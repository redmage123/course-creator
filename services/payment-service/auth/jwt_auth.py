"""
JWT Authentication for Payment Service

Business Context:
Validates JWT tokens by delegating to the user-management service.
This follows the same pattern used by organization-management and other
services in the platform — the user-management service is the authoritative
source for token validation.

Technical Rationale:
- Tokens are validated by calling user-management's /users/me endpoint
- SSL verification is disabled for inter-service communication (self-signed certs)
- Returns a standardized user dict with role and organization information
"""

import logging
import os
from typing import Dict, Any

import httpx
from fastapi import HTTPException, status
from omegaconf import DictConfig


class JWTAuthenticator:
    """JWT authentication handler for the payment service."""

    def __init__(self, config: DictConfig):
        self._config = config
        self._logger = logging.getLogger(__name__)
        self._user_service_url = config.get('services', {}).get(
            'user_management_url', 'https://user-management:8000'
        )

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a JWT token by calling the user-management service.

        Returns a standardized user dict with user_id, email, role, and
        organization_id for use in authorization checks.
        """
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No token provided",
            )

        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(
                    f"{self._user_service_url}/users/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0,
                )

                if response.status_code == 401:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or expired token",
                    )
                elif response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Authentication service unavailable",
                    )

                user_data = response.json()
                return {
                    "sub": str(user_data["id"]),
                    "user_id": str(user_data["id"]),
                    "email": user_data["email"],
                    "username": user_data["username"],
                    "full_name": user_data.get("full_name"),
                    "role": user_data.get("role", "user"),
                    "roles": [user_data.get("role", "user")],
                    "organization": user_data.get("organization"),
                    "organization_id": user_data.get("organization_id"),
                }

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service timeout",
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
            )

    def require_organization_access(self, user: Dict[str, Any], organization_id: str) -> bool:
        """
        Check if a user has access to a specific organization.

        Site admins (username='admin') can access all organizations.
        Other users can only access their own organization.
        """
        if user.get("username") == "admin":
            return True
        user_org = user.get("organization_id") or user.get("organization")
        if str(user_org) == str(organization_id):
            return True
        return False
