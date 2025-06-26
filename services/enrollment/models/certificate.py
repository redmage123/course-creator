"""
Certificate model for database operations
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class CertificateBase(BaseModel):
    """Base Certificate model"""
    id: UUID
    enrollment_id: UUID
    student_id: UUID
    course_id: UUID
    certificate_url: String
    issued_at: DateTime
    verification_code: String
    is_verified: Boolean = True
    created_at: DateTime

class CertificateCreate(CertificateBase):
    """Create Certificate model"""
    pass

class CertificateUpdate(BaseModel):
    """Update Certificate model"""
    enrollment_id: Optional[UUID] = None
    student_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    certificate_url: Optional[String] = None
    issued_at: Optional[DateTime] = None
    verification_code: Optional[String] = None
    is_verified: Optional[Boolean] = None
    created_at: Optional[DateTime] = None

class Certificate(CertificateBase):
    """Full Certificate model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
