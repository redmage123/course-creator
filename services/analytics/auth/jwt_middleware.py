"""
JWT Authentication Middleware for Course Management Service

BUSINESS CONTEXT:
Provides centralized JWT token validation for all protected course management endpoints.
Ensures only authenticated users can access, modify, or delete course content.

SOLID PRINCIPLES:
- Single Responsibility: Handles only JWT validation and user extraction
- Dependency Inversion: Depends on ITokenService interface
- Interface Segregation: Focused authentication contract

SECURITY REQUIREMENTS:
- Validates JWT token signature and expiration
- Extracts user ID and role from authenticated tokens
- Rejects invalid, expired, or missing tokens with 401 Unauthorized
- Supports Authorization: Bearer <token> header format

TECHNICAL IMPLEMENTATION:
- FastAPI dependency injection pattern
- Integrates with existing user-management JWT infrastructure
- Provides get_current_user() dependency for protected endpoints
"""

from fastapi import HTTPException, status, Depends, Header
from typing import Optional, Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)


# User Management Service Configuration
USER_MANAGEMENT_SERVICE_URL = "https://user-management:8000"


async def get_authorization_header(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract and validate Authorization header.

    SECURITY VALIDATION:
    - Checks Authorization header is present
    - Validates Bearer token format
    - Extracts token for further validation

    Args:
        authorization: Authorization header value

    Returns:
        str: JWT token

    Raises:
        HTTPException: 401 if header missing or malformed
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate Bearer format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return parts[1]


async def validate_jwt_token(token: str) -> Dict[str, Any]:
    """
    Validate JWT token with user-management service.

    DISTRIBUTED ARCHITECTURE:
    - Calls user-management service for token validation
    - Centralizes authentication logic in one service
    - Enables consistent token validation across all microservices

    SECURITY IMPLEMENTATION:
    - Validates token signature
    - Checks token expiration
    - Extracts user payload (user_id, role, permissions)

    Args:
        token: JWT token string

    Returns:
        Dict containing user information (user_id, role, etc.)

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    try:
        # Call user-management service to validate token
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{USER_MANAGEMENT_SERVICE_URL}/auth/validate",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )

            if response.status_code == 200:
                user_data = response.json()
                return user_data

            elif response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired JWT token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            else:
                # Unexpected error from auth service
                logger.error(f"Auth service returned unexpected status {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service unavailable",
                )

    except HTTPException:
        # Re-raise HTTPException to preserve status codes
        raise

    except httpx.TimeoutException:
        logger.error("Timeout calling authentication service")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service timeout",
        )

    except httpx.RequestError as e:
        logger.error(f"Error calling authentication service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )

    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error during JWT validation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal authentication error",
        )


async def get_current_user(
    token: str = Depends(get_authorization_header)
) -> Dict[str, Any]:
    """
    FastAPI dependency for extracting current authenticated user.

    DEPENDENCY INJECTION PATTERN:
    - Use with FastAPI Depends() for automatic authentication
    - Provides user information to endpoint handlers
    - Handles all authentication errors centrally

    USAGE EXAMPLE:
    ```python
    @router.get("/my-protected-endpoint")
    async def protected_route(current_user: Dict = Depends(get_current_user)):
        user_id = current_user["user_id"]
        role = current_user["role"]
        # ... endpoint logic
    ```

    Args:
        token: JWT token extracted from Authorization header

    Returns:
        Dict containing:
        - user_id: Unique user identifier
        - role: User role (instructor, student, org_admin, etc.)
        - username: User's username
        - email: User's email (optional)

    Raises:
        HTTPException: 401 if authentication fails
    """
    user_data = await validate_jwt_token(token)
    return user_data


async def get_current_user_id(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """
    Extract user ID from authenticated user.

    CONVENIENCE DEPENDENCY:
    - Simplifies endpoints that only need user_id
    - Maintains authentication requirements
    - Reduces boilerplate code

    Args:
        current_user: Authenticated user data from get_current_user

    Returns:
        str: User ID

    Raises:
        HTTPException: 401 if authentication fails
    """
    return current_user.get("user_id") or current_user.get("id")


async def get_current_user_role(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """
    Extract user role from authenticated user.

    RBAC INTEGRATION:
    - Enables role-based access control in endpoints
    - Supports authorization checks
    - Provides role for business logic

    Args:
        current_user: Authenticated user data from get_current_user

    Returns:
        str: User role (instructor, student, org_admin, site_admin, guest)

    Raises:
        HTTPException: 401 if authentication fails
    """
    return current_user.get("role", "guest")


def require_role(*required_roles: str):
    """
    Dependency factory for role-based access control.

    RBAC AUTHORIZATION:
    - Enforces role requirements on endpoints
    - Supports multiple allowed roles
    - Provides clear authorization errors

    USAGE EXAMPLE:
    ```python
    @router.post("/admin-only")
    async def admin_endpoint(
        current_user: Dict = Depends(get_current_user),
        _: None = Depends(require_role("site_admin", "org_admin"))
    ):
        # Only site_admin or org_admin can access
    ```

    Args:
        required_roles: One or more roles required for access

    Returns:
        Dependency function that validates user role

    Raises:
        HTTPException: 403 if user lacks required role
    """
    async def role_checker(current_user: Dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(required_roles)}",
            )
        return None

    return role_checker
