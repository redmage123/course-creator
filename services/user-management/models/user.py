"""
User Models

Pydantic models for user data validation and serialization.
"""

from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation model."""
    password: str
    username: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseModel):
    """User update model."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class User(UserBase):
    """Complete user model."""
    id: str
    username: str
    is_active: bool
    is_verified: bool = False
    role: UserRole = UserRole.STUDENT
    roles: List[str] = []  # For backward compatibility
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    @validator('roles', pre=True, always=True)
    def set_roles(cls, v, values):
        """Set roles list from role field for backward compatibility."""
        if 'role' in values:
            return [values['role']]
        return v or []


class AdminUserCreate(UserCreate):
    """Admin user creation model with role specification."""
    role: UserRole = UserRole.STUDENT


class UserProfile(BaseModel):
    """User profile model for public display."""
    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    role: UserRole
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: Optional[datetime] = None


class UserStats(BaseModel):
    """User statistics model."""
    total_users: int
    active_users: int
    users_by_role: dict