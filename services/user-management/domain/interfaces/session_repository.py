"""
Session Repository Interface
Interface Segregation: Focused interface for session data access
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from ..entities.session import Session, SessionStatus

class ISessionRepository(ABC):
    """Interface for session data access operations"""
    
    @abstractmethod
    async def create(self, session: Session) -> Session:
        """Create a new session"""
        pass
    
    @abstractmethod
    async def get_by_id(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        pass
    
    @abstractmethod
    async def get_by_token(self, token: str) -> Optional[Session]:
        """Get session by token"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> List[Session]:
        """Get all sessions for a user"""
        pass
    
    @abstractmethod
    async def get_active_by_user_id(self, user_id: str) -> List[Session]:
        """Get active sessions for a user"""
        pass
    
    @abstractmethod
    async def update(self, session: Session) -> Session:
        """Update session"""
        pass
    
    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Delete session"""
        pass
    
    @abstractmethod
    async def revoke_by_user_id(self, user_id: str) -> int:
        """Revoke all sessions for a user"""
        pass
    
    @abstractmethod
    async def revoke_by_token(self, token: str) -> bool:
        """Revoke session by token"""
        pass
    
    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Clean up expired sessions"""
        pass
    
    @abstractmethod
    async def get_by_status(self, status: SessionStatus) -> List[Session]:
        """Get sessions by status"""
        pass
    
    @abstractmethod
    async def count_active_by_user(self, user_id: str) -> int:
        """Count active sessions for a user"""
        pass
    
    @abstractmethod
    async def get_recent_sessions(self, user_id: str, limit: int = 10) -> List[Session]:
        """Get recent sessions for a user"""
        pass
    
    @abstractmethod
    async def extend_session(self, token: str, expires_at: datetime) -> bool:
        """Extend session expiration"""
        pass