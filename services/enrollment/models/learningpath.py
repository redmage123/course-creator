"""
LearningPath model for database operations
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class LearningPathBase(BaseModel):
    """Base LearningPath model"""
    id: UUID
    student_id: UUID
    name: String
    description: Text
    target_completion_date: DateTime
    is_active: Boolean = True
    created_at: DateTime
    updated_at: DateTime

class LearningPathCreate(LearningPathBase):
    """Create LearningPath model"""
    pass

class LearningPathUpdate(BaseModel):
    """Update LearningPath model"""
    student_id: Optional[UUID] = None
    name: Optional[String] = None
    description: Optional[Text] = None
    target_completion_date: Optional[DateTime] = None
    is_active: Optional[Boolean] = None
    created_at: Optional[DateTime] = None
    updated_at: Optional[DateTime] = None

class LearningPath(LearningPathBase):
    """Full LearningPath model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
