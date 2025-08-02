"""
Session Repository Interface - Authentication Session Data Access Layer

This module defines the abstract interface for session data access operations
within the User Management Service. It follows the Repository pattern to
abstract session storage and provide clean separation between domain logic
and infrastructure concerns.

Architectural Benefits:
    Interface Segregation: Focused specifically on session data operations
    Dependency Inversion: Authentication logic depends on this abstraction
    Testability: Enables easy mocking for authentication tests
    Security Focus: Designed for secure session management patterns
    Clean Architecture: Separates authentication logic from storage details

Session Management Capabilities:
    - Complete session lifecycle management (create, read, update, delete)
    - Token-based session retrieval for authentication
    - User session management (multiple sessions per user)
    - Security operations (revocation, cleanup)
    - Status-based session filtering
    - Performance optimizations (recent sessions, active counts)

Security Features:
    - Token-based session lookup for stateless authentication
    - Bulk revocation for security incidents
    - Automatic cleanup of expired sessions
    - Session status management for access control
    - User session limit enforcement support

Integration Points:
    - Authentication middleware uses token lookup methods
    - Session management services use lifecycle methods
    - Security services use revocation and cleanup methods
    - Analytics services use session activity methods

Author: Course Creator Platform Team
Version: 2.3.0
Last Updated: 2025-08-02
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from domain.entities.session import Session, SessionStatus

class ISessionRepository(ABC):
    """
    Abstract base class defining the contract for session data access operations.
    
    This interface defines all methods required for session management within
    the User Management Service. It serves as the boundary between authentication
    logic and session storage infrastructure.
    
    Design Principles:
        - All operations are async for high-performance authentication
        - Token-based operations for stateless authentication patterns
        - Security-focused methods for session lifecycle management
        - Bulk operations for administrative and security purposes
        - Performance-optimized queries for frequent authentication checks
    
    Critical Security Methods:
        - get_by_token: Core authentication method called on every request
        - revoke_by_user_id: Emergency session termination
        - cleanup_expired: Automated security maintenance
        - get_active_by_user_id: Session management and limits
    
    Thread Safety:
        Implementations must be thread-safe for concurrent authentication
        and session management operations in high-traffic environments.
    """
    
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
        """
        Retrieve session by authentication token.
        
        This is the most critical method for authentication, called on every
        authenticated request to validate session tokens.
        
        Args:
            token (str): Session token from authentication header
        
        Returns:
            Optional[Session]: Session if valid token found, None otherwise
        
        Performance Note:
            This method must be highly optimized as it's called frequently
        """
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
        """
        Revoke all sessions for a specific user.
        
        Used for security incidents, password changes, or when user
        access needs to be immediately terminated.
        
        Args:
            user_id (str): User whose sessions should be revoked
        
        Returns:
            int: Number of sessions revoked
        """
        pass
    
    @abstractmethod
    async def revoke_by_token(self, token: str) -> bool:
        """Revoke session by token"""
        pass
    
    @abstractmethod
    async def cleanup_expired(self) -> int:
        """
        Remove expired sessions from storage.
        
        Automated cleanup process to maintain database performance
        and remove sessions that are no longer valid.
        
        Returns:
            int: Number of expired sessions removed
        
        Note:
            Should be called periodically by cleanup services
        """
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