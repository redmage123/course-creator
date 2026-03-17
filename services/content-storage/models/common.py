"""
Common Models

Base models and common data structures for content storage.
"""

from pydantic import BaseModel as PydanticBaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class BaseModel(PydanticBaseModel):
    """Base model with common configuration."""
    
    model_config = {
        "use_enum_values": True,
        "populate_by_name": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """Success response model."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class TimestampMixin:
    """Mixin for models with timestamps."""
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)