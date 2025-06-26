"""
Enrollment model for database operations
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class EnrollmentBase(BaseModel):
    """Base Enrollment model"""
    id: UUID
    student_id: UUID
    course_id: UUID
    enrollment_date: DateTime
    status: String = active
    progress_percentage: Float = 0.0
    last_accessed: DateTime
    completed_at: DateTime
    certificate_issued: Boolean = False
    created_at: DateTime
    updated_at: DateTime

class EnrollmentCreate(EnrollmentBase):
    """Create Enrollment model"""
    pass

class EnrollmentUpdate(BaseModel):
    """Update Enrollment model"""
    student_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    enrollment_date: Optional[DateTime] = None
    status: Optional[String] = None
    progress_percentage: Optional[Float] = None
    last_accessed: Optional[DateTime] = None
    completed_at: Optional[DateTime] = None
    certificate_issued: Optional[Boolean] = None
    created_at: Optional[DateTime] = None
    updated_at: Optional[DateTime] = None

class Enrollment(EnrollmentBase):
    """Full Enrollment model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
