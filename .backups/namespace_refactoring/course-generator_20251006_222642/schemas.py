from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, constr

# Base Models
class BaseSchema(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Course Template Schemas
class CourseTemplateBase(BaseModel):
    title: constr(min_length=1, max_length=255)
    description: Optional[str] = None
    target_audience: Optional[str] = None
    learning_objectives: Optional[List[str]] = Field(default_factory=list)
    difficulty_level: Optional[str] = None
    estimated_duration: Optional[int] = None

class CourseTemplateCreate(CourseTemplateBase):
    pass

class CourseTemplateUpdate(CourseTemplateBase):
    title: Optional[constr(min_length=1, max_length=255)] = None

class CourseTemplateResponse(CourseTemplateBase, BaseSchema):
    pass

# Generation Job Schemas
class GenerationJobBase(BaseModel):
    course_template_id: UUID
    status: str = Field(default="pending")
    error_message: Optional[str] = None
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    generated_content: Optional[dict] = None

class GenerationJobCreate(GenerationJobBase):
    pass

class GenerationJobUpdate(BaseModel):
    status: Optional[str] = None
    error_message: Optional[str] = None
    completion_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    generated_content: Optional[dict] = None

class GenerationJobResponse(GenerationJobBase, BaseSchema):
    pass

# Content Prompt Schemas
class ContentPromptBase(BaseModel):
    prompt_type: str
    template: str
    parameters: Optional[dict] = None
    description: Optional[str] = None
    is_active: bool = True

class ContentPromptCreate(ContentPromptBase):
    pass

class ContentPromptUpdate(BaseModel):
    prompt_type: Optional[str] = None
    template: Optional[str] = None
    parameters: Optional[dict] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ContentPromptResponse(ContentPromptBase, BaseSchema):
    pass

# List Response Schemas
class CourseTemplateListResponse(BaseModel):
    items: List[CourseTemplateResponse]
    total: int

class GenerationJobListResponse(BaseModel):
    items: List[GenerationJobResponse]
    total: int

class ContentPromptListResponse(BaseModel):
    items: List[ContentPromptResponse]
    total: int

# Error Response Schema
class ErrorResponse(BaseModel):
    detail: str