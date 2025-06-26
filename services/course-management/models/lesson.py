"""
Lesson model for database operations
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class LessonBase(BaseModel):
    """Base Lesson model"""
    id: UUID
    course_id: UUID
    title: String
    content: Text
    order_index: Integer
    duration_minutes: Integer
    lesson_type: String
    created_at: DateTime
    updated_at: DateTime

class LessonCreate(LessonBase):
    """Create Lesson model"""
    pass

class LessonUpdate(BaseModel):
    """Update Lesson model"""
    course_id: Optional[UUID] = None
    title: Optional[String] = None
    content: Optional[Text] = None
    order_index: Optional[Integer] = None
    duration_minutes: Optional[Integer] = None
    lesson_type: Optional[String] = None
    created_at: Optional[DateTime] = None
    updated_at: Optional[DateTime] = None

class Lesson(LessonBase):
    """Full Lesson model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
