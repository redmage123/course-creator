"""
Route handlers following SOLID principles.
Single Responsibility: Define API endpoints and delegate to services.
"""
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

# Pydantic models for API (Data Transfer Objects)
from pydantic import BaseModel, EmailStr, Field

# Domain entities and services
from domain.entities.user import User, UserRole, UserStatus
from domain.entities.session import Session
from domain.interfaces.user_service import IUserService, IAuthenticationService
from domain.interfaces.session_service import ISessionService

# Custom exceptions
from exceptions import (
    UserManagementException, AuthenticationException, AuthorizationException,
    UserNotFoundException, UserValidationException, DatabaseException,
    SessionException, JWTException, EmailServiceException
)

# API Models (DTOs - following Single Responsibility)
class UserCreateRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = Field(default="student", pattern="^(student|instructor|admin)$")
    organization: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: str = "en"

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    bio: Optional[str] = None
    profile_picture_url: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

class PasswordResetRequest(BaseModel):
    email: EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Response Models
class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    status: str
    organization: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: str
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: UserResponse

class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    session_type: str
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_accessed: datetime
    ip_address: Optional[str] = None
    device_info: Dict[str, Any] = {}
    is_valid: bool
    remaining_time: Optional[float] = None

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Dependency injection helpers
def get_user_service() -> IUserService:
    """Dependency injection for user service"""
    from fastapi import Request
    # This will be set during app creation
    if not hasattr(get_user_service, '_container'):
        raise HTTPException(status_code=500, detail="Service not initialized")
    return get_user_service._container.get_user_service()

def get_auth_service() -> IAuthenticationService:
    """Dependency injection for authentication service"""
    if not hasattr(get_auth_service, '_container'):
        raise HTTPException(status_code=500, detail="Service not initialized")
    return get_auth_service._container.get_authentication_service()

def get_session_service() -> ISessionService:
    """Dependency injection for session service"""
    if not hasattr(get_session_service, '_container'):
        raise HTTPException(status_code=500, detail="Service not initialized")
    return get_session_service._container.get_session_service()

def set_container(container):
    """Set the container for dependency injection"""
    get_user_service._container = container
    get_auth_service._container = container
    get_session_service._container = container

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session_service: ISessionService = Depends(get_session_service),
    user_service: IUserService = Depends(get_user_service)
) -> User:
    """Get current authenticated user"""
    session = await session_service.validate_session(token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await user_service.get_user_by_id(session.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

def setup_auth_routes(app: FastAPI) -> None:
    """Setup authentication routes"""
    
    @app.post("/auth/register", response_model=UserResponse)
    async def register(
        request: UserCreateRequest,
        user_service: IUserService = Depends(get_user_service)
    ):
        """Register a new user"""
        try:
            user_data = request.dict(exclude={'password'})
            user = await user_service.create_user(user_data, request.password)
            return _user_to_response(user)
            
        except ValueError as e:
            raise UserValidationException(
                message="Invalid user data provided",
                validation_errors={"general": str(e)},
                original_exception=e
            )
        except UserManagementException:
            # Re-raise custom exceptions
            raise
        except Exception as e:
            raise UserManagementException(
                message="Failed to register user",
                error_code="USER_REGISTRATION_ERROR",
                details={"email": request.email, "username": request.username},
                original_exception=e
            )

    @app.post("/auth/login", response_model=TokenResponse)
    async def login(
        request: LoginRequest,
        auth_service: IAuthenticationService = Depends(get_auth_service),
        session_service: ISessionService = Depends(get_session_service)
    ):
        """Authenticate user and create session"""
        try:
            user = await auth_service.authenticate_user(request.email, request.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Create session
            session = await session_service.create_session(user.id, "web")
            
            return TokenResponse(
                access_token=session.token,
                user=_user_to_response(user)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logging.error("Error during login: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post("/auth/logout")
    async def logout(
        token: str = Depends(oauth2_scheme),
        session_service: ISessionService = Depends(get_session_service)
    ):
        """Logout user and revoke session"""
        try:
            await session_service.revoke_session(token)
            return {"message": "Successfully logged out"}
            
        except Exception as e:
            logging.error("Error during logout: %s", e)
            # Don't return error - logout should always succeed
            return {"message": "Logged out"}

    @app.post("/auth/password/change")
    async def change_password(
        request: PasswordChangeRequest,
        current_user: User = Depends(get_current_user),
        auth_service: IAuthenticationService = Depends(get_auth_service)
    ):
        """Change user password"""
        try:
            success = await auth_service.change_password(
                current_user.id,
                request.old_password,
                request.new_password
            )
            
            if not success:
                raise HTTPException(status_code=400, detail="Invalid old password")
            
            return {"message": "Password changed successfully"}
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logging.error("Error changing password: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post("/auth/password/reset")
    async def reset_password(
        request: PasswordResetRequest,
        auth_service: IAuthenticationService = Depends(get_auth_service)
    ):
        """Reset user password"""
        try:
            temp_password = await auth_service.reset_password(request.email)
            
            # In production, send email instead of returning password
            return {
                "message": "Password reset successfully",
                "temporary_password": temp_password  # Remove in production
            }
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logging.error("Error resetting password: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

def setup_user_routes(app: FastAPI) -> None:
    """Setup user management routes"""
    
    @app.get("/users/me", response_model=UserResponse)
    async def get_current_user_profile(current_user: User = Depends(get_current_user)):
        """Get current user profile"""
        return _user_to_response(current_user)

    @app.put("/users/me", response_model=UserResponse)
    async def update_profile(
        request: UserUpdateRequest,
        current_user: User = Depends(get_current_user),
        user_service: IUserService = Depends(get_user_service)
    ):
        """Update current user profile"""
        try:
            profile_data = request.dict(exclude_unset=True)
            updated_user = await user_service.update_user_profile(current_user.id, profile_data)
            return _user_to_response(updated_user)
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logging.error("Error updating profile: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.get("/users/search")
    async def search_users(
        q: str,
        limit: int = 50,
        current_user: User = Depends(get_current_user),
        user_service: IUserService = Depends(get_user_service)
    ):
        """Search users (requires authentication)"""
        try:
            users = await user_service.search_users(q, limit)
            return [_user_to_response(user) for user in users]
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logging.error("Error searching users: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

def setup_session_routes(app: FastAPI) -> None:
    """Setup session management routes"""
    
    @app.get("/sessions/me", response_model=List[SessionResponse])
    async def get_my_sessions(
        current_user: User = Depends(get_current_user),
        session_service: ISessionService = Depends(get_session_service)
    ):
        """Get current user's sessions"""
        try:
            sessions = await session_service.get_user_sessions(current_user.id)
            return [_session_to_response(session) for session in sessions]
            
        except Exception as e:
            logging.error("Error getting sessions: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.delete("/sessions/all")
    async def revoke_all_sessions(
        current_user: User = Depends(get_current_user),
        session_service: ISessionService = Depends(get_session_service)
    ):
        """Revoke all user sessions"""
        try:
            count = await session_service.revoke_all_user_sessions(current_user.id)
            return {"message": f"Revoked {count} sessions"}
            
        except Exception as e:
            logging.error("Error revoking sessions: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

def setup_admin_routes(app: FastAPI) -> None:
    """Setup admin routes"""
    
    @app.get("/admin/users", response_model=List[UserResponse])
    async def get_all_users(
        current_user: User = Depends(get_current_user),
        user_service: IUserService = Depends(get_user_service)
    ):
        """Get all users (admin only)"""
        if not current_user.is_admin():
            raise HTTPException(status_code=403, detail="Admin access required")
        
        try:
            users = await user_service.get_users_by_role(UserRole.STUDENT)
            users.extend(await user_service.get_users_by_role(UserRole.INSTRUCTOR))
            users.extend(await user_service.get_users_by_role(UserRole.ADMIN))
            
            return [_user_to_response(user) for user in users]
            
        except Exception as e:
            logging.error("Error getting users: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.get("/admin/statistics")
    async def get_user_statistics(
        current_user: User = Depends(get_current_user),
        user_service: IUserService = Depends(get_user_service)
    ):
        """Get user statistics (admin only)"""
        if not current_user.is_admin():
            raise HTTPException(status_code=403, detail="Admin access required")
        
        try:
            stats = await user_service.get_user_statistics()
            return stats
            
        except Exception as e:
            logging.error("Error getting statistics: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

# Helper functions (following Single Responsibility)
def _user_to_response(user: User) -> UserResponse:
    """Convert domain entity to API response DTO"""
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        status=user.status.value,
        organization=user.organization,
        phone=user.phone,
        timezone=user.timezone,
        language=user.language,
        profile_picture_url=user.profile_picture_url,
        bio=user.bio,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

def _session_to_response(session: Session) -> SessionResponse:
    """Convert domain entity to API response DTO"""
    return SessionResponse(
        session_id=session.id,
        user_id=session.user_id,
        session_type=session.session_type,
        status=session.status.value,
        created_at=session.created_at,
        expires_at=session.expires_at,
        last_accessed=session.last_accessed,
        ip_address=session.ip_address,
        device_info=session.device_info,
        is_valid=session.is_valid(),
        remaining_time=session.get_remaining_time().total_seconds() if session.get_remaining_time() else None
    )