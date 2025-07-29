"""
User domain entity following SOLID principles.
Single Responsibility: Represents a user with business logic.
"""
from datetime import datetime
from typing import Optional
from enum import Enum

from ...database.interfaces import BaseEntity

class UserRole(Enum):
    """User role enumeration."""
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"

class User(BaseEntity):
    """User domain entity."""
    
    def __init__(
        self,
        email: str,
        username: str,
        full_name: str,
        hashed_password: str,
        role: UserRole = UserRole.STUDENT,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        organization: Optional[str] = None,
        is_active: bool = True,
        is_verified: bool = False,
        avatar_url: Optional[str] = None,
        bio: Optional[str] = None,
        last_login: Optional[datetime] = None
    ):
        super().__init__()
        self.email = email
        self.username = username
        self.full_name = full_name
        self.hashed_password = hashed_password
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.organization = organization
        self.is_active = is_active
        self.is_verified = is_verified
        self.avatar_url = avatar_url
        self.bio = bio
        self.last_login = last_login
    
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN
    
    def is_instructor(self) -> bool:
        """Check if user is an instructor."""
        return self.role == UserRole.INSTRUCTOR
    
    def is_student(self) -> bool:
        """Check if user is a student."""
        return self.role == UserRole.STUDENT
    
    def can_create_courses(self) -> bool:
        """Check if user can create courses."""
        return self.role in [UserRole.ADMIN, UserRole.INSTRUCTOR]
    
    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.role == UserRole.ADMIN
    
    def activate(self) -> None:
        """Activate the user account."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def verify_email(self) -> None:
        """Mark email as verified."""
        self.is_verified = True
        self.updated_at = datetime.utcnow()
    
    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_profile(
        self,
        full_name: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        organization: Optional[str] = None,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> None:
        """Update user profile information."""
        if full_name is not None:
            self.full_name = full_name
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if organization is not None:
            self.organization = organization
        if bio is not None:
            self.bio = bio
        if avatar_url is not None:
            self.avatar_url = avatar_url
        
        self.updated_at = datetime.utcnow()
    
    def change_role(self, new_role: UserRole) -> None:
        """Change user role (admin only operation)."""
        self.role = new_role
        self.updated_at = datetime.utcnow()
    
    def __str__(self) -> str:
        """String representation of user."""
        return f"User({self.username}, {self.email}, {self.role.value})"
    
    def __repr__(self) -> str:
        """Developer representation of user."""
        return (f"User(id={self.id}, username='{self.username}', "
                f"email='{self.email}', role={self.role.value})")
    
    def to_dict(self) -> dict:
        """Convert user to dictionary (for API responses)."""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'organization': self.organization,
            'role': self.role.value,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }