"""
Session Service Interface
Interface Segregation: Focused interface for session business operations
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..entities.session import Session, SessionStatus

class ISessionService(ABC):
    """Interface for session business operations"""
    
    @abstractmethod
    async def create_session(self, user_id: str, session_type: str = "web", 
                           ip_address: str = None, user_agent: str = None) -> Session:
        """Create a new session"""
        pass
    
    @abstractmethod
    async def get_session_by_token(self, token: str) -> Optional[Session]:
        """Get session by token"""
        pass
    
    @abstractmethod
    async def validate_session(self, token: str) -> Optional[Session]:
        """Validate session and return if active"""
        pass
    
    @abstractmethod
    async def extend_session(self, token: str, duration: timedelta = None) -> Session:
        """Extend session expiration"""
        pass
    
    @abstractmethod
    async def revoke_session(self, token: str) -> bool:
        """Revoke a specific session"""
        pass
    
    @abstractmethod
    async def revoke_all_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user"""
        pass
    
    @abstractmethod
    async def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[Session]:
        """Get sessions for a user"""
        pass
    
    @abstractmethod
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        pass
    
    @abstractmethod
    async def get_session_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        pass
    
    @abstractmethod
    async def update_session_access(self, token: str, ip_address: str = None, 
                                  user_agent: str = None) -> bool:
        """Update session access information"""
        pass

class ITokenService(ABC):
    """Interface for token operations"""
    
    @abstractmethod
    async def generate_access_token(self, user_id: str, session_id: str) -> str:
        """Generate access token"""
        pass
    
    @abstractmethod
    async def generate_refresh_token(self, user_id: str, session_id: str) -> str:
        """Generate refresh token"""
        pass
    
    @abstractmethod
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode token"""
        pass
    
    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token using refresh token"""
        pass
    
    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """Revoke token"""
        pass