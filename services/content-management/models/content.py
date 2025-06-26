"""
Content model for database operations
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class ContentBase(BaseModel):
    """Base Content model"""
    id: UUID
    title: String
    description: Text
    content_type: String
    file_path: String
    file_size: BigInteger
    mime_type: String
    duration: Integer
    thumbnail_url: String
    processing_status: String = pending
    upload_by: UUID
    created_at: DateTime
    updated_at: DateTime

class ContentCreate(ContentBase):
    """Create Content model"""
    pass

class ContentUpdate(BaseModel):
    """Update Content model"""
    title: Optional[String] = None
    description: Optional[Text] = None
    content_type: Optional[String] = None
    file_path: Optional[String] = None
    file_size: Optional[BigInteger] = None
    mime_type: Optional[String] = None
    duration: Optional[Integer] = None
    thumbnail_url: Optional[String] = None
    processing_status: Optional[String] = None
    upload_by: Optional[UUID] = None
    created_at: Optional[DateTime] = None
    updated_at: Optional[DateTime] = None

class Content(ContentBase):
    """Full Content model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
