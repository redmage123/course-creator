"""
Session Manager

Manages user sessions and authentication state.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from omegaconf import DictConfig

from ..repositories.session_repository import SessionRepository
from ..models.session import SessionCreate, UserSession
from .jwt_manager import JWTManager
from .password_manager import PasswordManager


class SessionManager:
    """
    Session management utility.
    
    Handles session creation, validation, and cleanup.
    """
    
    def __init__(self, config: DictConfig, session_repository: SessionRepository,
                 jwt_manager: JWTManager, password_manager: PasswordManager):
        """
        Initialize session manager.
        
        Args:
            config: Configuration containing session settings
            session_repository: Session repository
            jwt_manager: JWT manager
            password_manager: Password manager
        """
        self.config = config
        self.session_repository = session_repository
        self.jwt_manager = jwt_manager
        self.password_manager = password_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def create_session(self, user_id: str, token: str, 
                           ip_address: str = None, user_agent: str = None) -> Optional[UserSession]:
        """
        Create a new user session.
        
        Args:
            user_id: User ID
            token: JWT token
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Created session or None if creation fails
        """
        try:
            # Clean up old sessions for this user
            await self.cleanup_old_sessions(user_id, max_sessions=3)
            
            # Create session data
            session_data = SessionCreate(
                user_id=user_id,
                token=token,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Hash token for storage
            token_hash = self.password_manager.hash_password(token)
            
            # Calculate expiration time
            expires_at = datetime.utcnow() + timedelta(minutes=self.config.jwt.token_expiry)
            
            # Create session
            session = await self.session_repository.create_session(
                session_data, token_hash, expires_at
            )
            
            if session:
                self.logger.info(f"Created session for user {user_id}")
                return session
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating session: {e}")
            return None
    
    async def validate_session(self, token: str, user_id: str) -> Optional[UserSession]:
        """
        Validate a user session.
        
        Args:
            token: JWT token
            user_id: User ID
            
        Returns:
            Valid session or None if invalid
        """
        try:
            # Calculate inactivity timeout
            inactivity_timeout = timedelta(minutes=self.config.jwt.token_expiry)
            
            # Get active sessions for user
            active_sessions = await self.session_repository.get_active_sessions_by_user(
                user_id, inactivity_timeout
            )
            
            # Check if token matches any active session
            for session in active_sessions:
                if self.password_manager.verify_password(token, session.token_hash):
                    # Update last accessed time
                    new_expires_at = datetime.utcnow() + inactivity_timeout
                    await self.session_repository.update_session_access(
                        session.id, new_expires_at
                    )
                    
                    self.logger.debug(f"Session validated for user {user_id}")
                    return session
            
            self.logger.warning(f"Session validation failed for user {user_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error validating session: {e}")
            return None
    
    async def invalidate_session(self, token: str, user_id: str) -> bool:
        """
        Invalidate a specific session.
        
        Args:
            token: JWT token
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Hash token for lookup
            token_hash = self.password_manager.hash_password(token)
            
            # Delete session
            success = await self.session_repository.delete_session_by_token(token_hash, user_id)
            
            if success:
                self.logger.info(f"Session invalidated for user {user_id}")
            else:
                self.logger.warning(f"Failed to invalidate session for user {user_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error invalidating session: {e}")
            return False
    
    async def invalidate_all_sessions(self, user_id: str) -> int:
        """
        Invalidate all sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions invalidated
        """
        try:
            count = await self.session_repository.delete_all_user_sessions(user_id)
            self.logger.info(f"Invalidated {count} sessions for user {user_id}")
            return count
            
        except Exception as e:
            self.logger.error(f"Error invalidating all sessions for user {user_id}: {e}")
            return 0
    
    async def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active sessions
        """
        try:
            inactivity_timeout = timedelta(minutes=self.config.jwt.token_expiry)
            
            sessions = await self.session_repository.get_active_sessions_by_user(
                user_id, inactivity_timeout
            )
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"Error getting user sessions: {e}")
            return []
    
    async def revoke_session(self, session_id: str, user_id: str) -> bool:
        """
        Revoke a specific session.
        
        Args:
            session_id: Session ID
            user_id: User ID (for security check)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get session to verify ownership
            session = await self.session_repository.get_session_by_id(session_id)
            
            if not session or session.user_id != user_id:
                self.logger.warning(f"Session {session_id} not found or not owned by user {user_id}")
                return False
            
            # Delete session
            success = await self.session_repository.delete_session(session_id)
            
            if success:
                self.logger.info(f"Session {session_id} revoked for user {user_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error revoking session {session_id}: {e}")
            return False
    
    async def cleanup_old_sessions(self, user_id: str, max_sessions: int = 3) -> int:
        """
        Clean up old sessions for a user.
        
        Args:
            user_id: User ID
            max_sessions: Maximum number of sessions to keep
            
        Returns:
            Number of sessions cleaned up
        """
        try:
            count = await self.session_repository.cleanup_old_sessions(user_id, max_sessions)
            
            if count > 0:
                self.logger.info(f"Cleaned up {count} old sessions for user {user_id}")
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old sessions: {e}")
            return 0
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up all expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            inactivity_timeout = timedelta(minutes=self.config.jwt.token_expiry)
            count = await self.session_repository.cleanup_expired_sessions(inactivity_timeout)
            
            if count > 0:
                self.logger.info(f"Cleaned up {count} expired sessions")
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    async def get_session_stats(self) -> dict:
        """
        Get session statistics.
        
        Returns:
            Session statistics
        """
        try:
            inactivity_timeout = timedelta(minutes=self.config.jwt.token_expiry)
            active_sessions = await self.session_repository.count_active_sessions(inactivity_timeout)
            
            return {
                "active_sessions": active_sessions,
                "inactivity_timeout_minutes": self.config.jwt.token_expiry
            }
            
        except Exception as e:
            self.logger.error(f"Error getting session stats: {e}")
            return {
                "active_sessions": 0,
                "inactivity_timeout_minutes": self.config.jwt.token_expiry
            }