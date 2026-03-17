"""
Session Domain Entity - User Authentication Session Management

This module defines the Session domain entity for managing user authentication
sessions within the Course Creator Platform. It handles session lifecycle,
validation, and security features for different types of user sessions.

Session Management Strategy:
    - Stateful Sessions: Sessions are stored and managed server-side
    - Multi-Device Support: Different session types for web, mobile, and API
    - Security Features: IP tracking, user agent validation, automatic expiration
    - Flexible Expiration: Different durations based on session type and security needs
    - Audit Trail: Comprehensive tracking of session activity and lifecycle

Session Types and Business Logic:
    - Web Sessions: Short-lived (7 days) for browser-based interactions
    - Mobile Sessions: Medium-lived (30 days) for mobile app persistence  
    - API Sessions: Long-lived (365 days) for service-to-service communication

Security Considerations:
    - Token-based authentication with secure random tokens
    - IP address tracking for suspicious activity detection
    - User agent monitoring for device consistency validation
    - Automatic expiration prevents indefinite access
    - Revocation support for security incident response
    - Session extension with validation for active users

Domain Model Features:
    - Rich Domain Model: Contains business logic for session operations
    - Value Objects: SessionStatus enum for type-safe status management
    - Invariants: Validation rules ensure session integrity
    - Behavioral Methods: Session lifecycle operations and queries
    - Metadata Support: Extensible attributes for session context

Integration Points:
    - Authentication Service: Session creation and validation
    - Authorization Middleware: Session verification for protected endpoints  
    - User Service: User identification and profile access
    - Analytics Service: Session activity tracking and user behavior
    - Security Service: Suspicious activity detection and response

Author: Course Creator Platform Team
Version: 2.3.0
Last Updated: 2025-08-02
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from enum import Enum
import uuid

class SessionStatus(Enum):
    """
    Session Status Enumeration - Defines Session Lifecycle States
    
    This enumeration manages the lifecycle of user sessions, controlling
    session validity and access permissions throughout the session lifetime.
    
    Status Definitions:
        ACTIVE: Session is valid and can be used for authentication
            - User can access protected resources
            - Session is within expiration time
            - No security violations detected
        
        EXPIRED: Session has exceeded its time-to-live
            - Automatically set when expiration time is reached
            - User must re-authenticate to continue
            - Session cannot be reactivated
        
        REVOKED: Session was manually invalidated
            - Used for security incidents or logout operations
            - Immediately terminates session access
            - Cannot be reversed or reactivated
    
    Security Implications:
        - Only ACTIVE sessions are valid for authentication
        - Status transitions are logged for audit purposes
        - REVOKED status supports emergency access termination
        - Status checks are critical for authorization decisions
    """
    ACTIVE = "active"      # Session is valid and usable
    EXPIRED = "expired"    # Session has exceeded time limit
    REVOKED = "revoked"    # Session was manually invalidated

@dataclass
class Session:
    """
    Session Domain Entity - Authentication Session with Security Features
    
    This class represents a user authentication session within the Course Creator
    Platform, managing session lifecycle, security validation, and access control.
    
    Domain Model Characteristics:
        - Entity Pattern: Has unique identity and tracks session lifecycle
        - Rich Domain Model: Contains business logic for session operations
        - Security First: Built-in security features and validation
        - Multi-Device Support: Different behaviors for different session types
        - Audit Trail: Comprehensive tracking of session activity
    
    Session Security Features:
        - Token-based authentication with validation
        - Automatic expiration based on session type
        - IP address and user agent tracking
        - Revocation support for security incidents
        - Session extension with activity validation
        - Device information tracking for security analysis
    
    Session Types and Durations:
        - Web Sessions: 7 days (browser-based interactions)
        - Mobile Sessions: 30 days (mobile app persistence)
        - API Sessions: 365 days (service integrations)
    
    Business Rules:
        1. All sessions must have valid user ID and token
        2. Tokens must be sufficiently complex (minimum 10 characters)
        3. Session types must be from allowed set (web, mobile, api)
        4. Expired sessions cannot be extended or used
        5. Revoked sessions cannot be reactivated
        6. Session activity updates access timestamp
    
    Usage Examples:
        # Create new session
        session = Session(
            user_id="user123",
            token="secure_random_token",
            session_type="web"
        )
        
        # Validate session
        if session.is_valid():
            # Allow access
        
        # Extend active session
        if session.should_refresh():
            session.extend_session()
        
        # Revoke for security
        session.revoke()
    """
    user_id: str
    token: str
    session_type: str = "web"  # web, mobile, api
    status: SessionStatus = SessionStatus.ACTIVE
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """
        Post-initialization setup for session entity.
        
        Validates session data and sets appropriate expiration time based on
        session type if not explicitly provided. This ensures all sessions
        have proper security boundaries.
        
        Session Duration Logic:
            - API Sessions: 365 days (long-lived for service integrations)
            - Mobile Sessions: 30 days (balance between UX and security)
            - Web Sessions: 7 days (shorter for browser security)
        
        Security Rationale:
            - Different session types have different security profiles
            - Shorter durations for less secure environments (browsers)
            - Longer durations for controlled environments (mobile apps, APIs)
            - Automatic expiration prevents indefinite access
        
        Raises:
            ValueError: If validation fails during initialization
        """
        self.validate()
        
        """
        Set default expiration based on session type security profile.
        Each session type has different security requirements and usage patterns.
        """
        if not self.expires_at:
            if self.session_type == "api":
                duration = timedelta(days=365)  # API tokens for service integration
            elif self.session_type == "mobile":
                duration = timedelta(days=30)   # Mobile app session persistence
            else:
                duration = timedelta(days=7)    # Web browser sessions
            
            self.expires_at = self.created_at + duration
    
    def validate(self) -> None:
        """
        Comprehensive validation of session data for security and integrity.
        
        Validates all critical session attributes to ensure the session
        can be safely used for authentication and authorization decisions.
        
        Validation Rules:
            - User ID: Required for session-user association
            - Token: Required, minimum 10 characters for security
            - Session Type: Must be valid type (web, mobile, api)
        
        Security Considerations:
            - Token length requirement prevents weak tokens
            - Session type validation ensures proper handling
            - User ID validation ensures session ownership
        
        Raises:
            ValueError: Specific error message for validation failures
        """
        if not self.user_id:
            raise ValueError("User ID is required")
        
        if not self.token:
            raise ValueError("Token is required")
        
        if len(self.token) < 10:
            raise ValueError("Token must be at least 10 characters")
        
        if self.session_type not in ["web", "mobile", "api"]:
            raise ValueError("Invalid session type")
    
    def is_valid(self) -> bool:
        """
        Check if session is valid for authentication and authorization.
        
        This is the primary method for determining if a session can be used
        for accessing protected resources. Used extensively throughout the
        authentication and authorization pipeline.
        
        Validation Criteria:
            1. Session status must be ACTIVE (not expired or revoked)
            2. Session must not be past its expiration time
        
        Returns:
            bool: True if session is valid for use, False otherwise
        
        Usage:
            if session.is_valid():
                # Allow access to protected resource
            else:
                # Require re-authentication
        
        Integration Points:
            - Authentication middleware checks this for every request
            - Authorization decorators use this for endpoint protection
            - Session cleanup services use this to identify expired sessions
        """
        if self.status != SessionStatus.ACTIVE:
            return False
        
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        
        return True
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return True
        return False
    
    def extend_session(self, duration: timedelta = None) -> None:
        """
        Extend session expiration time for active users.
        
        Allows extension of valid sessions to maintain user access without
        requiring re-authentication. Only valid (active, non-expired) sessions
        can be extended for security.
        
        Security Features:
            - Only valid sessions can be extended
            - Updates last accessed time for audit trail
            - Uses session-type-appropriate durations
            - Prevents extension of compromised sessions
        
        Args:
            duration (timedelta, optional): Custom extension duration.
                                          If None, uses default for session type.
        
        Raises:
            ValueError: If session is invalid and cannot be extended
        
        Usage:
            # Extend with default duration
            session.extend_session()
            
            # Extend with custom duration
            session.extend_session(timedelta(hours=2))
        
        Business Logic:
            - Web sessions: 7 days (frequent re-auth for security)
            - Mobile sessions: 30 days (balance UX and security)
            - API sessions: 365 days (service continuity)
        """
        if not self.is_valid():
            raise ValueError("Cannot extend invalid session")
        
        if duration is None:
            # Default extension based on session type security profile
            if self.session_type == "api":
                duration = timedelta(days=365)
            elif self.session_type == "mobile":
                duration = timedelta(days=30)
            else:
                duration = timedelta(days=7)
        
        self.expires_at = datetime.now(timezone.utc) + duration
        self.last_accessed = datetime.now(timezone.utc)
    
    def revoke(self) -> None:
        """Revoke the session"""
        self.status = SessionStatus.REVOKED
        self.last_accessed = datetime.now(timezone.utc)
    
    def mark_expired(self) -> None:
        """Mark session as expired"""
        self.status = SessionStatus.EXPIRED
        self.last_accessed = datetime.now(timezone.utc)
    
    def update_access(self, ip_address: str = None, user_agent: str = None) -> None:
        """Update session access information"""
        self.last_accessed = datetime.now(timezone.utc)
        
        if ip_address:
            self.ip_address = ip_address
        
        if user_agent:
            self.user_agent = user_agent
    
    def add_device_info(self, info: Dict[str, Any]) -> None:
        """Add device information"""
        self.device_info.update(info)
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to session"""
        self.metadata[key] = value
    
    def get_remaining_time(self) -> Optional[timedelta]:
        """Get remaining time before expiration"""
        if not self.expires_at:
            return None
        
        remaining = self.expires_at - datetime.now(timezone.utc)
        return remaining if remaining.total_seconds() > 0 else timedelta(0)
    
    def is_long_lived(self) -> bool:
        """Check if this is a long-lived session (API or mobile)"""
        return self.session_type in ["api", "mobile"]
    
    def should_refresh(self, threshold_hours: int = 1) -> bool:
        """Check if session should be refreshed"""
        if not self.expires_at:
            return False
        
        threshold = timedelta(hours=threshold_hours)
        time_until_expiry = self.expires_at - datetime.now(timezone.utc)
        
        return time_until_expiry < threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert session entity to dictionary for API responses and logging.
        
        Provides comprehensive session information in a serializable format
        suitable for JSON APIs, logging, and inter-service communication.
        
        Included Information:
            - All session attributes and metadata
            - Computed properties (is_valid, remaining_time)
            - Security information (IP, user agent)
            - Timestamps in ISO format for consistency
        
        Returns:
            Dict[str, Any]: Complete session representation with computed fields
        
        Security Considerations:
            - Includes full token (caller should filter for security)
            - Contains IP and user agent for security analysis
            - Device info may contain sensitive information
            - Consider field filtering for different contexts
        
        Usage:
            # For API responses (filter sensitive fields)
            response_data = {k: v for k, v in session.to_dict().items() 
                           if k not in ['token']}
            
            # For logging (include all fields)
            logger.info("Session activity", extra=session.to_dict())
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'session_type': self.session_type,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_accessed': self.last_accessed.isoformat(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'device_info': self.device_info,
            'metadata': self.metadata,
            'is_valid': self.is_valid(),
            'remaining_time': self.get_remaining_time().total_seconds() if self.get_remaining_time() else None
        }