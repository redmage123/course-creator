"""
Common Models

Base models and common data structures.
"""

from pydantic import BaseModel as PydanticBaseModel
from typing import Generic, TypeVar, List, Optional
from datetime import datetime

T = TypeVar('T')


class BaseModel(PydanticBaseModel):
    """Base model with common configuration."""
    
    class Config:
        orm_mode = True
        use_enum_values = True
        allow_population_by_field_name = True


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""
    items: List[T]
    total: int
    page: int = 1
    per_page: int = 100
    pages: int


class TimestampMixin(BaseModel):
    """Mixin for models with timestamps."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    details: Optional[dict] = None


class SuccessResponse(BaseModel):
    """Success response model."""
    success: bool = True
    message: str
    data: Optional[dict] = None