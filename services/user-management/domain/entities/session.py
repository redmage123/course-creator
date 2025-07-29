"""
Session Domain Entity
Single Responsibility: Encapsulates session business logic and validation
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum
import uuid

class SessionStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"

@dataclass
class Session:
    """
    User session domain entity with business logic and validation
    """
    user_id: str
    token: str
    session_type: str = "web"  # web, mobile, api
    status: SessionStatus = SessionStatus.ACTIVE
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set default expiration if not provided"""
        self.validate()
        
        if not self.expires_at:
            # Default session duration based on type
            if self.session_type == "api":
                duration = timedelta(days=365)  # API tokens last longer
            elif self.session_type == "mobile":
                duration = timedelta(days=30)   # Mobile sessions last longer
            else:
                duration = timedelta(days=7)    # Web sessions
            
            self.expires_at = self.created_at + duration
    
    def validate(self) -> None:
        """Validate session data"""
        if not self.user_id:
            raise ValueError("User ID is required")
        
        if not self.token:
            raise ValueError("Token is required")
        
        if len(self.token) < 10:
            raise ValueError("Token must be at least 10 characters")
        
        if self.session_type not in ["web", "mobile", "api"]:
            raise ValueError("Invalid session type")
    
    def is_valid(self) -> bool:
        """Check if session is valid (active and not expired)"""
        if self.status != SessionStatus.ACTIVE:
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        return True
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return True
        return False
    
    def extend_session(self, duration: timedelta = None) -> None:
        """Extend session expiration"""
        if not self.is_valid():
            raise ValueError("Cannot extend invalid session")
        
        if duration is None:
            # Default extension based on session type
            if self.session_type == "api":
                duration = timedelta(days=365)
            elif self.session_type == "mobile":
                duration = timedelta(days=30)
            else:
                duration = timedelta(days=7)
        
        self.expires_at = datetime.utcnow() + duration
        self.last_accessed = datetime.utcnow()
    
    def revoke(self) -> None:
        """Revoke the session"""
        self.status = SessionStatus.REVOKED
        self.last_accessed = datetime.utcnow()
    
    def mark_expired(self) -> None:
        """Mark session as expired"""
        self.status = SessionStatus.EXPIRED
        self.last_accessed = datetime.utcnow()
    
    def update_access(self, ip_address: str = None, user_agent: str = None) -> None:
        """Update session access information"""
        self.last_accessed = datetime.utcnow()
        
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
        
        remaining = self.expires_at - datetime.utcnow()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)
    
    def is_long_lived(self) -> bool:
        """Check if this is a long-lived session (API or mobile)"""
        return self.session_type in ["api", "mobile"]
    
    def should_refresh(self, threshold_hours: int = 1) -> bool:
        """Check if session should be refreshed"""
        if not self.expires_at:
            return False
        
        threshold = timedelta(hours=threshold_hours)
        time_until_expiry = self.expires_at - datetime.utcnow()
        
        return time_until_expiry < threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
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