"""
LessonContent model for database operations
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class LessonContentBase(BaseModel):
    """Base LessonContent model"""
    id: UUID
    lesson_id: UUID
    content_id: UUID
    order_index: Integer = 0
    is_primary: Boolean = False
    created_at: DateTime

class LessonContentCreate(LessonContentBase):
    """Create LessonContent model"""
    pass

class LessonContentUpdate(BaseModel):
    """Update LessonContent model"""
    lesson_id: Optional[UUID] = None
    content_id: Optional[UUID] = None
    order_index: Optional[Integer] = None
    is_primary: Optional[Boolean] = None
    created_at: Optional[DateTime] = None

class LessonContent(LessonContentBase):
    """Full LessonContent model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
