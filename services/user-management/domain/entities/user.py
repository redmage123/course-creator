"""
User Domain Entity
Single Responsibility: Encapsulates user business logic and validation
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
import re

class UserRole(Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor" 
    ADMIN = "admin"

class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

@dataclass
class User:
    """
    User domain entity with business logic and validation
    """
    email: str
    username: str
    full_name: str
    role: UserRole = UserRole.STUDENT
    status: UserStatus = UserStatus.ACTIVE
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: str = "en"
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate user data after initialization"""
        self.validate()
        
        # Auto-generate full_name if not provided
        if not self.full_name and self.first_name and self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}"
    
    def validate(self) -> None:
        """Validate user data"""
        if not self.email:
            raise ValueError("Email is required")
        
        if not self._is_valid_email(self.email):
            raise ValueError("Invalid email format")
        
        if not self.username:
            raise ValueError("Username is required")
        
        if not self._is_valid_username(self.username):
            raise ValueError("Username must be 3-30 characters, alphanumeric and underscores only")
        
        if not self.full_name:
            raise ValueError("Full name is required")
        
        if len(self.full_name) < 2:
            raise ValueError("Full name must be at least 2 characters")
        
        if self.phone and not self._is_valid_phone(self.phone):
            raise ValueError("Invalid phone number format")
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_username(self, username: str) -> bool:
        """Validate username format"""
        pattern = r'^[a-zA-Z0-9_]{3,30}$'
        return re.match(pattern, username) is not None
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        pattern = r'^\+?[1-9]\d{1,14}$'
        return re.match(pattern, phone) is not None
    
    def update_profile(self, **kwargs) -> None:
        """Update user profile information"""
        allowed_fields = {
            'full_name', 'first_name', 'last_name', 'organization', 
            'phone', 'timezone', 'language', 'bio', 'profile_picture_url'
        }
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(self, field):
                setattr(self, field, value)
        
        self.updated_at = datetime.utcnow()
        self.validate()
    
    def change_role(self, new_role: UserRole) -> None:
        """Change user role with validation"""
        if not isinstance(new_role, UserRole):
            raise ValueError("Invalid role type")
        
        self.role = new_role
        self.updated_at = datetime.utcnow()
    
    def change_status(self, new_status: UserStatus) -> None:
        """Change user status"""
        if not isinstance(new_status, UserStatus):
            raise ValueError("Invalid status type")
        
        self.status = new_status
        self.updated_at = datetime.utcnow()
    
    def record_login(self) -> None:
        """Record user login"""
        self.last_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def is_active(self) -> bool:
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE
    
    def is_instructor(self) -> bool:
        """Check if user has instructor privileges"""
        return self.role in [UserRole.INSTRUCTOR, UserRole.ADMIN]
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
    
    def can_create_courses(self) -> bool:
        """Check if user can create courses"""
        return self.is_instructor() and self.is_active()
    
    def can_manage_users(self) -> bool:
        """Check if user can manage other users"""
        return self.is_admin() and self.is_active()
    
    def get_display_name(self) -> str:
        """Get user display name"""
        return self.full_name or self.username
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to user"""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
    
    def remove_metadata(self, key: str) -> None:
        """Remove metadata from user"""
        if key in self.metadata:
            del self.metadata[key]
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role.value,
            'status': self.status.value,
            'organization': self.organization,
            'phone': self.phone,
            'timezone': self.timezone,
            'language': self.language,
            'profile_picture_url': self.profile_picture_url,
            'bio': self.bio,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }