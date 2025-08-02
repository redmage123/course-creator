"""
Authentication Dependencies

FastAPI dependencies for authentication and authorization.
"""

import logging
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

from models.user import User
from services.user_service import UserService
from services.auth_service import AuthService


logger = logging.getLogger(__name__)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(),
    auth_service: AuthService = Depends(),
    request: Request = None
) -> User:
    """
    Get current authenticated user.
    
    Args:
        token: JWT token
        user_service: User service instance
        auth_service: Auth service instance
        request: HTTP request (optional)
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token to get user ID
        token_payload = auth_service.jwt_manager.decode_token(token)
        if not token_payload:
            raise credentials_exception
        
        user_id = token_payload.sub
        if not user_id:
            raise credentials_exception
            
        # Validate session
        session = await auth_service.session_manager.validate_session(token, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise credentials_exception
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}")
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current user
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require admin privileges.
    
    Args:
        current_user: Current user
        
    Returns:
        Current user (if admin)
        
    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def require_instructor_or_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require instructor or admin privileges.
    
    Args:
        current_user: Current user
        
    Returns:
        Current user (if instructor or admin)
        
    Raises:
        HTTPException: If user is not instructor or admin
    """
    if current_user.role not in ["instructor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor or Admin privileges required"
        )
    return current_user


async def require_role(required_role: str):
    """
    Require specific role.
    
    Args:
        required_role: Required role
        
    Returns:
        Dependency function
    """
    async def role_dependency(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{required_role.title()} privileges required"
            )
        return current_user
    
    return role_dependency


async def require_permission(permission: str):
    """
    Require specific permission.
    
    Args:
        permission: Required permission
        
    Returns:
        Dependency function
    """
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user),
        auth_service: AuthService = Depends()
    ) -> User:
        has_permission = await auth_service.check_permission(
            current_user.role, permission
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        
        return current_user
    
    return permission_dependency


async def optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    user_service: UserService = Depends(),
    auth_service: AuthService = Depends()
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise None.
    
    Args:
        token: JWT token (optional)
        user_service: User service instance
        auth_service: Auth service instance
        
    Returns:
        Current user or None
    """
    if not token:
        return None
    
    try:
        return await get_current_user(token, user_service, auth_service)
    except HTTPException:
        return None
    except Exception as e:
        logger.error(f"Error in optional_user: {e}")
        return None