"""
Syllabus Models

Pydantic models for syllabus data validation and serialization.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class CourseLevel(str, Enum):
    """Course difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


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
    """Request model for syllabus generation."""
    course_id: Optional[str] = Field(None, description="Course identifier")
    title: str = Field(..., description="Course title")
    description: str = Field(..., description="Course description")
    level: CourseLevel = Field(default=CourseLevel.BEGINNER, description="Course difficulty level")
    duration: Optional[int] = Field(None, description="Total course duration in hours")
    objectives: List[str] = Field(default_factory=list, description="Course learning objectives")
    prerequisites: List[str] = Field(default_factory=list, description="Course prerequisites")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    additional_requirements: Optional[str] = Field(None, description="Additional requirements or notes")
    
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