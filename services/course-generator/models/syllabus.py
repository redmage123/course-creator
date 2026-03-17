"""
Syllabus Models

Pydantic models for syllabus data validation and serialization.

Enhanced in v3.3.2 to support URL-based course generation from external
third-party software documentation. Instructors can now provide documentation
URLs that will be fetched, parsed, and used as context for AI-powered
course generation.
"""

from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import re


class CourseLevel(str, Enum):
    """Course difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ContentSourceType(str, Enum):
    """
    Types of external content sources for URL-based generation.

    Business Context:
    Different documentation types may benefit from different processing
    strategies and prompt engineering approaches.
    """
    DOCUMENTATION = "documentation"  # Technical documentation
    TUTORIAL = "tutorial"  # Tutorial/how-to content
    API_REFERENCE = "api_reference"  # API documentation
    KNOWLEDGE_BASE = "knowledge_base"  # Help/support content
    BLOG = "blog"  # Blog posts
    WIKI = "wiki"  # Wiki pages
    GENERAL = "general"  # General web content


class ExternalSourceConfig(BaseModel):
    """
    Configuration for an external content source URL.

    Business Context:
    Allows instructors to provide URLs to third-party documentation
    with optional metadata about the source type and priority.
    """
    url: str = Field(..., description="URL to fetch content from")
    source_type: ContentSourceType = Field(
        default=ContentSourceType.GENERAL,
        description="Type of content source"
    )
    priority: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Priority for content (1-10, higher = more important)"
    )
    description: Optional[str] = Field(
        None,
        description="Optional description of what this URL contains"
    )

    @validator('url')
    def validate_url(cls, v):
        """Validate URL format."""
        if not v or not v.strip():
            raise ValueError('URL cannot be empty')

        v = v.strip()

        # Basic URL validation
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')

        # Check for reasonable URL length
        if len(v) > 2048:
            raise ValueError('URL exceeds maximum length of 2048 characters')

        return v


class ModuleTopic(BaseModel):
    """Individual topic within a module."""
    title: str = Field(..., description="Topic title")
    description: str = Field(..., description="Topic description")
    duration: Optional[int] = Field(None, description="Duration in minutes")
    objectives: List[str] = Field(default_factory=list, description="Topic learning objectives")


class SyllabusModule(BaseModel):
    """Course module definition."""
    module_number: int = Field(..., description="Module number")
    title: str = Field(..., description="Module title")
    description: str = Field(..., description="Module description")
    duration: Optional[int] = Field(None, description="Module duration in minutes")
    objectives: List[str] = Field(default_factory=list, description="Module learning objectives")
    topics: List[ModuleTopic] = Field(default_factory=list, description="Module topics")
    
    @validator('module_number')
    def validate_module_number(cls, v):
        if v < 1:
            raise ValueError('Module number must be positive')
        return v


class SyllabusRequest(BaseModel):
    """
    Request model for syllabus generation.

    Enhanced in v3.3.2 to support URL-based course generation from external
    documentation URLs. When source_url or source_urls is provided, the system
    will fetch the content and use it as context for AI-powered course generation.

    URL-Based Generation:
    - Provide source_url for single documentation URL
    - Provide source_urls for multiple documentation URLs
    - External sources for advanced configuration with source types
    - Set use_rag_enhancement=True (default) to store in RAG for better generation
    """
    course_id: Optional[str] = Field(None, description="Course identifier")
    title: str = Field(..., description="Course title")
    description: str = Field(..., description="Course description")
    level: CourseLevel = Field(default=CourseLevel.BEGINNER, description="Course difficulty level")
    duration: Optional[int] = Field(None, description="Total course duration in hours")
    objectives: List[str] = Field(default_factory=list, description="Course learning objectives")
    prerequisites: List[str] = Field(default_factory=list, description="Course prerequisites")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    additional_requirements: Optional[str] = Field(None, description="Additional requirements or notes")

    # URL-based generation fields (v3.3.2)
    source_url: Optional[str] = Field(
        None,
        description="Primary URL to fetch documentation from for course generation"
    )
    source_urls: List[str] = Field(
        default_factory=list,
        description="Additional URLs to fetch documentation from"
    )
    external_sources: List[ExternalSourceConfig] = Field(
        default_factory=list,
        description="Advanced: External sources with type and priority configuration"
    )

    # URL processing options
    use_rag_enhancement: bool = Field(
        default=True,
        description="Store fetched content in RAG for enhanced generation"
    )
    include_code_examples: bool = Field(
        default=True,
        description="Include code examples from documentation in course content"
    )
    max_content_chunks: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of content chunks to process from URLs"
    )

    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    @validator('description')
    def validate_description(cls, v):
        if not v or not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()

    @validator('source_url')
    def validate_source_url(cls, v):
        """Validate primary source URL if provided."""
        if v is None:
            return v

        v = v.strip()
        if not v:
            return None

        if not v.startswith(('http://', 'https://')):
            raise ValueError('source_url must start with http:// or https://')

        if len(v) > 2048:
            raise ValueError('source_url exceeds maximum length of 2048 characters')

        return v

    @validator('source_urls', each_item=True)
    def validate_source_urls_items(cls, v):
        """Validate each URL in source_urls list."""
        if not v or not v.strip():
            raise ValueError('URL in source_urls cannot be empty')

        v = v.strip()

        if not v.startswith(('http://', 'https://')):
            raise ValueError(f'URL must start with http:// or https://: {v[:50]}...')

        if len(v) > 2048:
            raise ValueError(f'URL exceeds maximum length: {v[:50]}...')

        return v

    @root_validator(skip_on_failure=True)
    def validate_url_count(cls, values):
        """Validate total number of URLs doesn't exceed limit."""
        source_url = values.get('source_url')
        source_urls = values.get('source_urls', [])
        external_sources = values.get('external_sources', [])

        total_urls = (1 if source_url else 0) + len(source_urls) + len(external_sources)

        if total_urls > 10:
            raise ValueError(
                f'Too many source URLs ({total_urls}). Maximum is 10 URLs per request.'
            )

        return values

    @property
    def has_external_sources(self) -> bool:
        """Check if request includes external URL sources."""
        return bool(
            self.source_url or
            self.source_urls or
            self.external_sources
        )

    @property
    def all_source_urls(self) -> List[str]:
        """Get all source URLs from all fields."""
        urls = []

        if self.source_url:
            urls.append(self.source_url)

        urls.extend(self.source_urls)

        for source in self.external_sources:
            if source.url not in urls:
                urls.append(source.url)

        return urls


class SyllabusFeedback(BaseModel):
    """Feedback model for syllabus refinement."""
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    focus_areas: List[str] = Field(default_factory=list, description="Areas to focus on")
    adjustments: Dict[str, Any] = Field(default_factory=dict, description="Specific adjustments")
    additional_modules: List[str] = Field(default_factory=list, description="Additional modules to include")
    remove_modules: List[str] = Field(default_factory=list, description="Modules to remove")
    reorder_modules: List[int] = Field(default_factory=list, description="New module order")
    duration_adjustment: Optional[int] = Field(None, description="Duration adjustment in hours")
    difficulty_adjustment: Optional[CourseLevel] = Field(None, description="Difficulty level adjustment")


class SyllabusData(BaseModel):
    """Complete syllabus data model."""
    title: str = Field(..., description="Course title")
    description: str = Field(..., description="Course description")
    level: CourseLevel = Field(..., description="Course difficulty level")
    duration: Optional[int] = Field(None, description="Total course duration in hours")
    objectives: List[str] = Field(default_factory=list, description="Course learning objectives")
    prerequisites: List[str] = Field(default_factory=list, description="Course prerequisites")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    modules: List[SyllabusModule] = Field(default_factory=list, description="Course modules")
    
    # Metadata fields
    generated_at: Optional[str] = Field(None, description="Generation timestamp")
    generation_method: Optional[str] = Field(None, description="Generation method (ai/fallback)")
    refined_at: Optional[str] = Field(None, description="Last refinement timestamp")
    refinement_method: Optional[str] = Field(None, description="Refinement method (ai/fallback)")
    saved_at: Optional[str] = Field(None, description="Save timestamp")
    created_at: Optional[datetime] = Field(None, description="Database creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Database update timestamp")
    
    @validator('modules')
    def validate_modules(cls, v):
        if not v:
            raise ValueError('At least one module is required')
        
        # Check for duplicate module numbers
        module_numbers = [module.module_number for module in v]
        if len(module_numbers) != len(set(module_numbers)):
            raise ValueError('Module numbers must be unique')
        
        return v


class SyllabusResponse(BaseModel):
    """Response model for syllabus operations."""
    success: bool = Field(..., description="Operation success status")
    syllabus: Optional[SyllabusData] = Field(None, description="Syllabus data")
    message: Optional[str] = Field(None, description="Response message")
    course_id: Optional[str] = Field(None, description="Course identifier")


class SyllabusListResponse(BaseModel):
    """Response model for syllabus listing."""
    success: bool = Field(..., description="Operation success status")
    syllabi: List[SyllabusData] = Field(default_factory=list, description="List of syllabi")
    count: int = Field(..., description="Number of syllabi returned")
    limit: int = Field(..., description="Query limit")
    offset: int = Field(..., description="Query offset")
    search: Optional[str] = Field(None, description="Search term used")


class SyllabusValidationResult(BaseModel):
    """Validation results for syllabus data."""
    valid: bool = Field(..., description="Overall validation status")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


class SyllabusValidationResponse(BaseModel):
    """Response model for syllabus validation."""
    success: bool = Field(..., description="Operation success status")
    validation: SyllabusValidationResult = Field(..., description="Validation results")
    course_id: str = Field(..., description="Course identifier")


class SyllabusOperationResponse(BaseModel):
    """Generic response model for syllabus operations."""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Operation message")
    course_id: str = Field(..., description="Course identifier")