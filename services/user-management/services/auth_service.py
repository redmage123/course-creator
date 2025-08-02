"""
Authentication Service

Business logic for authentication operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Request

from repositories.user_repository import UserRepository
from repositories.session_repository import SessionRepository
from repositories.role_repository import RoleRepository
from models.user import User
from models.auth import LoginResponse, ValidateResponse
from models.session import UserSession
from auth.jwt_manager import JWTManager
from auth.session_manager import SessionManager
from auth.password_manager import PasswordManager


class AuthService:
    """
    Service for authentication operations.
    
    Handles business logic for authentication, session management, and authorization.
    """
    
    def __init__(self, user_repository: UserRepository, session_repository: SessionRepository,
                 role_repository: RoleRepository, jwt_manager: JWTManager, 
                 session_manager: SessionManager, password_manager: PasswordManager):
        """
        Initialize authentication service.
        
        Args:
            user_repository: User repository
            session_repository: Session repository
            role_repository: Role repository
            jwt_manager: JWT manager
            session_manager: Session manager
            password_manager: Password manager
        """
        self.user_repository = user_repository
        self.session_repository = session_repository
        self.role_repository = role_repository
        self.jwt_manager = jwt_manager
        self.session_manager = session_manager
        self.password_manager = password_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def login(self, username: str, password: str, request: Request = None) -> Optional[LoginResponse]:
        """
        Authenticate user and create session.
        
        Args:
            username: Username or email
            password: Password
            request: HTTP request for session info
            
        Returns:
            Login response with token and user info, or None if login fails
        """
        try:
            # Find user by email (username is typically email)
            user = await self.user_repository.get_user_by_email(username)
            if not user:
                # Try by username if email lookup fails
                user = await self.user_repository.get_user_by_username(username)
            
            if not user:
                self.logger.warning(f"Login attempt for non-existent user: {username}")
                return None
            
            # Verify password
            if not self.password_manager.verify_password(password, user.hashed_password):
                self.logger.warning(f"Invalid password for user: {username}")
                return None
            
            # Check if user is active
            if not user.is_active:
                self.logger.warning(f"Login attempt for inactive user: {username}")
                return None
            
            # Create JWT token
            access_token = self.jwt_manager.create_token(user.id, user.role)
            expires_at = datetime.utcnow() + timedelta(minutes=self.jwt_manager.token_expiry)
            
            # Create session
            ip_address = request.client.host if request else None
            user_agent = request.headers.get("User-Agent") if request else None
            
            session = await self.session_manager.create_session(
                user.id, access_token, ip_address, user_agent
            )
            
            # Update last login
            await self.user_repository.update_last_login(user.id)
            
            self.logger.info(f"User logged in successfully: {user.email}")
            
            return LoginResponse(
                access_token=access_token,
                token_type="bearer",
                user={
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role
                },
                expires_at=expires_at,
                session_id=session.id if session else ""
            )
            
        except Exception as e:
            self.logger.error(f"Error during login for {username}: {e}")
            return None
    
    async def logout(self, token: str, user_id: str) -> bool:
        """
        Logout user and invalidate session.
        
        Args:
            token: JWT token
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = await self.session_manager.invalidate_session(token, user_id)
            
            if success:
                self.logger.info(f"User logged out successfully: {user_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error during logout for user {user_id}: {e}")
            return False
    
    async def validate_session(self, token: str) -> Optional[ValidateResponse]:
        """
        Validate session and return session info.
        
        Args:
            token: JWT token
            
        Returns:
            Validation response or None if invalid
        """
        try:
            # Decode token
            token_payload = self.jwt_manager.decode_token(token)
            if not token_payload:
                return None
            
            user_id = token_payload.sub
            
            # Validate session
            session = await self.session_manager.validate_session(token, user_id)
            if not session:
                return None
            
            # Get user
            user = await self.user_repository.get_user_by_id(user_id)
            if not user:
                return None
            
            return ValidateResponse(
                valid=True,
                user_id=user.id,
                email=user.email,
                expires_at=session.expires_at,
                message="Session is valid"
            )
            
        except Exception as e:
            self.logger.error(f"Error validating session: {e}")
            return None
    
    async def refresh_token(self, token: str) -> Optional[str]:
        """
        Refresh JWT token.
        
        Args:
            token: Current JWT token
            
        Returns:
            New JWT token or None if refresh fails
        """
        try:
            return self.jwt_manager.refresh_token(token)
            
        except Exception as e:
            self.logger.error(f"Error refreshing token: {e}")
            return None
    
    async def get_user_sessions(self, user_id: str) -> list:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active sessions
        """
        try:
            sessions = await self.session_manager.get_user_sessions(user_id)
            
            session_list = []
            for session in sessions:
                session_info = {
                    "id": session.id,
                    "ip_address": session.ip_address,
                    "user_agent": session.user_agent,
                    "created_at": session.created_at,
                    "last_accessed_at": session.last_accessed_at,
                    "expires_at": session.expires_at
                }
                session_list.append(session_info)
            
            return session_list
            
        except Exception as e:
            self.logger.error(f"Error getting sessions for user {user_id}: {e}")
            return []
    
    async def revoke_session(self, session_id: str, user_id: str) -> bool:
        """
        Revoke a specific session.
        
        Args:
            session_id: Session ID
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return await self.session_manager.revoke_session(session_id, user_id)
            
        except Exception as e:
            self.logger.error(f"Error revoking session {session_id}: {e}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            return await self.session_manager.cleanup_expired_sessions()
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    async def check_permission(self, role: str, permission: str) -> bool:
        """
        Check if a role has a specific permission.
        
        Args:
            role: User role
            permission: Permission to check
            
        Returns:
            True if role has permission, False otherwise
        """
        try:
            return await self.role_repository.check_permission(role, permission)
            
        except Exception as e:
            self.logger.error(f"Error checking permission {permission} for role {role}: {e}")
            return False
    
    async def get_role_permissions(self, role: str) -> list:
        """
        Get permissions for a role.
        
        Args:
            role: Role name
            
        Returns:
            List of permissions
        """
        try:
            return await self.role_repository.get_role_permissions(role)
            
        except Exception as e:
            self.logger.error(f"Error getting permissions for role {role}: {e}")
            return []
    
    async def validate_role(self, role: str) -> bool:
        """
        Validate if a role exists.
        
        Args:
            role: Role name
            
        Returns:
            True if role exists, False otherwise
        """
        try:
            return await self.role_repository.validate_role(role)
            
        except Exception as e:
            self.logger.error(f"Error validating role {role}: {e}")
            return False
    
    async def get_session_stats(self) -> dict:
        """
        Get session statistics.
        
        Returns:
            Session statistics
        """
        try:
            return await self.session_manager.get_session_stats()
            
        except Exception as e:
            self.logger.error(f"Error getting session stats: {e}")
            return {}
    
    async def reset_user_password(self, email: str, new_password: str) -> bool:
        """
        Reset user password and invalidate all sessions.
        
        Args:
            email: User email
            new_password: New password
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user
            user = await self.user_repository.get_user_by_email(email)
            if not user:
                return False
            
            # Hash new password
            hashed_password = self.password_manager.hash_password(new_password)
            
            # Update password
            success = await self.user_repository.update_password(user.id, hashed_password)
            
            if success:
                # Invalidate all sessions for this user
                await self.session_manager.invalidate_all_sessions(user.id)
                self.logger.info(f"Password reset and sessions invalidated for user: {email}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error resetting password for user {email}: {e}")
            return False