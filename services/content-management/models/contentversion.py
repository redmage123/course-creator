"""
ContentVersion model for database operations
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class ContentVersionBase(BaseModel):
    """Base ContentVersion model"""
    id: UUID
    content_id: UUID
    version_number: Integer
    file_path: String
    change_notes: Text
    created_at: DateTime

class ContentVersionCreate(ContentVersionBase):
    """Create ContentVersion model"""
    pass

class ContentVersionUpdate(BaseModel):
    """Update ContentVersion model"""
    content_id: Optional[UUID] = None
    version_number: Optional[Integer] = None
    file_path: Optional[String] = None
    change_notes: Optional[Text] = None
    created_at: Optional[DateTime] = None

class ContentVersion(ContentVersionBase):
    """Full ContentVersion model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
