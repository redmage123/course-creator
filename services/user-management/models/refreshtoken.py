"""
RefreshToken model for database operations
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class RefreshTokenBase(BaseModel):
    """Base RefreshToken model"""
    id: UUID
    user_id: UUID
    token: String
    expires_at: DateTime
    created_at: DateTime

class RefreshTokenCreate(RefreshTokenBase):
    """Create RefreshToken model"""
    pass

class RefreshTokenUpdate(BaseModel):
    """Update RefreshToken model"""
    user_id: Optional[UUID] = None
    token: Optional[String] = None
    expires_at: Optional[DateTime] = None
    created_at: Optional[DateTime] = None

class RefreshToken(RefreshTokenBase):
    """Full RefreshToken model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
