"""
User model for database operations
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class UserBase(BaseModel):
    """Base User model"""
    id: UUID
    email: String
    username: String
    full_name: String
    hashed_password: String
    is_active: Boolean = True
    is_verified: Boolean = False
    role: String = student
    avatar_url: String
    bio: Text
    created_at: DateTime
    updated_at: DateTime
    last_login: DateTime

class UserCreate(UserBase):
    """Create User model"""
    pass

class UserUpdate(BaseModel):
    """Update User model"""
    email: Optional[String] = None
    username: Optional[String] = None
    full_name: Optional[String] = None
    hashed_password: Optional[String] = None
    is_active: Optional[Boolean] = None
    is_verified: Optional[Boolean] = None
    role: Optional[String] = None
    avatar_url: Optional[String] = None
    bio: Optional[Text] = None
    created_at: Optional[DateTime] = None
    updated_at: Optional[DateTime] = None
    last_login: Optional[DateTime] = None

class User(UserBase):
    """Full User model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
