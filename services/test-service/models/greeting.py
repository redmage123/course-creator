"""
Greeting model for Simple greeting model
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

class GreetingBase(BaseModel):
    """Base Greeting model"""
    message: str
    language: str = 'en'

class GreetingCreate(GreetingBase):
    """Create Greeting model"""
    pass

class GreetingUpdate(BaseModel):
    """Update Greeting model"""
    message: Optional[str] = None
    language: Optional[str] = None

class Greeting(GreetingBase):
    """Full Greeting model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True
