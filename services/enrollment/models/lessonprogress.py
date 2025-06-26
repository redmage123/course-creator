"""
LessonProgress model for database operations
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class LessonProgressBase(BaseModel):
    """Base LessonProgress model"""
    id: UUID
    enrollment_id: UUID
    lesson_id: UUID
    status: String = not_started
    progress_percentage: Float = 0.0
    time_spent_minutes: Integer = 0
    started_at: DateTime
    completed_at: DateTime
    last_position: Integer = 0
    created_at: DateTime
    updated_at: DateTime

class LessonProgressCreate(LessonProgressBase):
    """Create LessonProgress model"""
    pass

class LessonProgressUpdate(BaseModel):
    """Update LessonProgress model"""
    enrollment_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    status: Optional[String] = None
    progress_percentage: Optional[Float] = None
    time_spent_minutes: Optional[Integer] = None
    started_at: Optional[DateTime] = None
    completed_at: Optional[DateTime] = None
    last_position: Optional[Integer] = None
    created_at: Optional[DateTime] = None
    updated_at: Optional[DateTime] = None

class LessonProgress(LessonProgressBase):
    """Full LessonProgress model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
