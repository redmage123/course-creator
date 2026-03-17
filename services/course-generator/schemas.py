"""
Course Generator Service Pydantic Schemas

This module defines Pydantic data validation schemas for the AI-powered course generation
service, handling course template creation, asynchronous content generation jobs, and
LLM prompt management for course content synthesis.

Business Context:
-----------------
The course generator service uses large language models (LLMs) to automatically create
educational content from templates, reducing instructor workload and enabling rapid
course development. Key workflows:

1. Instructor creates course template (title, objectives, difficulty, audience)
2. System starts async generation job (may take several minutes)
3. LLM generates course content using stored prompt templates
4. Generated content (modules, lessons, quizzes) returned as structured JSON
5. Instructor reviews, edits, and publishes generated course

Technical Implementation:
------------------------
- Async job pattern for long-running LLM operations (avoid HTTP timeouts)
- Prompt template system for consistent content generation
- Progress tracking for user feedback during generation
- Structured content output (JSON) for downstream processing

Schema Purposes:
- CourseTemplate: Input specification for what course to generate
- GenerationJob: Async job tracking with status and progress
- ContentPrompt: LLM prompt templates with parameterization
- List responses: Paginated results for template/job browsing

Dependencies:
- Pydantic: Data validation and serialization
- UUID: Unique identifiers for templates and jobs
- datetime: Timestamp tracking for audit and TTL
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, constr

# Base Models
class BaseSchema(BaseModel):
    """
    Base schema providing common fields for all generated entities.

    Attributes:
        id: Unique identifier (UUID v4)
        created_at: UTC timestamp when entity was created
        updated_at: UTC timestamp when entity was last modified

    Configuration:
        orm_mode: Enables Pydantic to read data from SQLAlchemy ORM models
                  (read attributes instead of treating as dict)

    Business Context:
        All entities need timestamps for audit trails, sorting by recency,
        and identifying stale generation jobs that can be cleaned up.
    """
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Course Template Schemas
class CourseTemplateBase(BaseModel):
    """
    Base schema for course generation templates (instructor input specification).

    Attributes:
        title: Course name (1-255 characters, required)
        description: High-level course overview (optional)
        target_audience: Intended learners (e.g., "beginner programmers", optional)
        learning_objectives: List of specific skills/knowledge to teach (optional)
        difficulty_level: Difficulty rating (e.g., "beginner", "intermediate", optional)
        estimated_duration: Expected course length in hours (optional)

    Business Context:
        Templates capture instructor intent for course generation. LLM uses these
        parameters to generate appropriate content. More detailed templates produce
        better results. Optional fields allow quick generation with sensible defaults.

    LLM Usage:
        - Title guides topic selection
        - Target audience adjusts tone and prerequisite assumptions
        - Learning objectives become module/lesson structure
        - Difficulty level controls content complexity
        - Duration determines content depth
    """
    title: constr(min_length=1, max_length=255)
    description: Optional[str] = None
    target_audience: Optional[str] = None
    learning_objectives: Optional[List[str]] = Field(default_factory=list)
    difficulty_level: Optional[str] = None
    estimated_duration: Optional[int] = None

class CourseTemplateCreate(CourseTemplateBase):
    """Schema for creating course templates via POST /templates."""
    pass

class CourseTemplateUpdate(CourseTemplateBase):
    """Schema for updating templates via PATCH /templates/{id}. All fields optional."""
    title: Optional[constr(min_length=1, max_length=255)] = None

class CourseTemplateResponse(CourseTemplateBase, BaseSchema):
    """Schema for template responses via GET /templates and GET /templates/{id}."""
    pass

# Generation Job Schemas
class GenerationJobBase(BaseModel):
    """
    Base schema for asynchronous course content generation jobs.

    Attributes:
        course_template_id: UUID of template to generate content from
        status: Job status (pending/running/completed/failed)
        error_message: Error details if job failed (null if successful)
        completion_percentage: Progress indicator (0.0-100.0) for UI display
        generated_content: LLM output as JSON (null until completed)

    Business Context:
        LLM generation takes 30-180 seconds depending on content complexity.
        Async job pattern prevents HTTP timeouts and enables progress tracking.
        Users can navigate away and check back later.

    Status Lifecycle:
        1. pending: Job created, waiting for worker to pick up
        2. running: Worker actively calling LLM API
        3. completed: Content successfully generated (see generated_content)
        4. failed: Error occurred (see error_message for details)

    Generated Content Structure:
        {
            "modules": [
                {
                    "title": "Module 1",
                    "lessons": [
                        {"title": "Lesson 1", "content": "...", "duration_minutes": 30}
                    ]
                }
            ],
            "quizzes": [...],
            "exercises": [...]
        }
    """
    course_template_id: UUID
    status: str = Field(default="pending")
    error_message: Optional[str] = None
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    generated_content: Optional[dict] = None

class GenerationJobCreate(GenerationJobBase):
    """Schema for creating generation jobs via POST /jobs."""
    pass

class GenerationJobUpdate(BaseModel):
    """
    Schema for updating job status via PATCH /jobs/{id}.

    Used internally by workers to report progress and completion.
    """
    status: Optional[str] = None
    error_message: Optional[str] = None
    completion_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    generated_content: Optional[dict] = None

class GenerationJobResponse(GenerationJobBase, BaseSchema):
    """Schema for job responses via GET /jobs and GET /jobs/{id}."""
    pass

# Content Prompt Schemas
class ContentPromptBase(BaseModel):
    """
    Base schema for LLM prompt templates used in content generation.

    Attributes:
        prompt_type: Prompt category (e.g., "lesson", "quiz", "exercise")
        template: LLM prompt with placeholders (e.g., "Generate a lesson about {topic}")
        parameters: JSON object defining required placeholders (e.g., {"topic": "string"})
        description: Human-readable explanation of prompt purpose (optional)
        is_active: Whether this prompt should be used (allows A/B testing)

    Business Context:
        Prompt engineering significantly impacts LLM output quality. This system allows:
        - Version control of prompts (update without code changes)
        - A/B testing (activate best-performing prompts)
        - Parameterization (reuse prompts with different inputs)
        - Prompt library management (multiple prompts per content type)

    Example Prompt Template:
        {
            "prompt_type": "lesson",
            "template": "Create a detailed lesson about {topic} for {audience}.
                        Include {example_count} practical examples. Difficulty: {difficulty}.",
            "parameters": {
                "topic": "string",
                "audience": "string",
                "example_count": "integer",
                "difficulty": "string"
            }
        }
    """
    prompt_type: str
    template: str
    parameters: Optional[dict] = None
    description: Optional[str] = None
    is_active: bool = True

class ContentPromptCreate(ContentPromptBase):
    """Schema for creating prompts via POST /prompts."""
    pass

class ContentPromptUpdate(BaseModel):
    """Schema for updating prompts via PATCH /prompts/{id}. Supports partial updates."""
    prompt_type: Optional[str] = None
    template: Optional[str] = None
    parameters: Optional[dict] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ContentPromptResponse(ContentPromptBase, BaseSchema):
    """Schema for prompt responses via GET /prompts."""
    pass

# List Response Schemas
class CourseTemplateListResponse(BaseModel):
    """Paginated response for template listings via GET /templates."""
    items: List[CourseTemplateResponse]
    total: int

class GenerationJobListResponse(BaseModel):
    """Paginated response for job listings via GET /jobs."""
    items: List[GenerationJobResponse]
    total: int

class ContentPromptListResponse(BaseModel):
    """Paginated response for prompt listings via GET /prompts."""
    items: List[ContentPromptResponse]
    total: int

# Error Response Schema
class ErrorResponse(BaseModel):
    """
    Standard error response schema for API error handling.

    Attributes:
        detail: Human-readable error message

    Business Context:
        Consistent error format enables client-side error handling and display.
    """
    detail: str