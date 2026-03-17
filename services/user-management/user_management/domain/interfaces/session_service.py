"""
Session Service Interface - Authentication Session Business Logic

This module defines the abstract interfaces for session-related business operations
within the User Management Service. It provides clean separation between session
management logic and token handling operations.

Architectural Benefits:
    Interface Segregation: Separate concerns for session and token management
    Security Focus: Designed for secure authentication and session handling
    Business Logic Encapsulation: Hides complex session rules behind simple interfaces
    Testability: Enables comprehensive testing of authentication flows
    Performance Optimization: Interfaces designed for high-frequency auth operations

Service Separation:
    ISessionService: Session lifecycle and management operations
    ITokenService: JWT token generation, validation, and refresh operations
    
This separation allows for different implementation strategies and better
maintainability of authentication-related code.

Security Considerations:
    - Session validation is critical for every authenticated request
    - Token services handle sensitive cryptographic operations
    - Session cleanup prevents resource exhaustion attacks
    - Revocation operations support security incident response

Author: Course Creator Platform Team
Version: 2.3.0
Last Updated: 2025-08-02
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from user_management.domain.entities.session import Session, SessionStatus

class ISessionService(ABC):
    """
    Abstract interface for session lifecycle and management operations.
    
    This interface defines the contract for session-related business logic,
    including session creation, validation, extension, and revocation.
    
    Core Responsibilities:
        - Session creation with security context
        - Session validation for authentication
        - Session lifecycle management (extend, revoke)
        - Security operations (cleanup, bulk revocation)
        - Session activity tracking and monitoring
    
    Performance Considerations:
        - validate_session is called on every authenticated request
        - Session lookup operations must be highly optimized
        - Cleanup operations should run efficiently in background
    """
    
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
    """
    Abstract interface for JWT token generation and management operations.
    
    This interface defines the contract for token-related operations,
    including JWT generation, validation, refresh, and revocation.
    
    Token Management Responsibilities:
        - Access token generation with user claims
        - Refresh token generation for session persistence
        - Token validation and payload extraction
        - Token refresh flows for seamless authentication
        - Token revocation for security incidents
    
    Security Features:
        - Cryptographically secure token generation
        - Token expiration and validation
        - Secure refresh token flows
        - Token revocation and blacklisting
    """
    
    @abstractmethod
    async def generate_access_token(
        self,
        user_id: str,
        session_id: str,
        role: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> str:
        """Generate access token with optional role and organization_id claims"""
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