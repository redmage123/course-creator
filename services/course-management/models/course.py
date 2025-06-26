"""
Course model for database operations
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class CourseBase(BaseModel):
    """Base Course model"""
    id: UUID
    title: String
    description: Text
    instructor_id: UUID
    category: String
    difficulty_level: String
    is_published: Boolean = False
    created_at: DateTime
    updated_at: DateTime

class CourseCreate(CourseBase):
    """Create Course model"""
    pass

class CourseUpdate(BaseModel):
    """Update Course model"""
    title: Optional[String] = None
    description: Optional[Text] = None
    instructor_id: Optional[UUID] = None
    category: Optional[String] = None
    difficulty_level: Optional[String] = None
    is_published: Optional[Boolean] = None
    created_at: Optional[DateTime] = None
    updated_at: Optional[DateTime] = None

class Course(CourseBase):
    """Full Course model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
