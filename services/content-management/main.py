#!/usr/bin/env python3

# Load environment variables from .cc_env file if present
import os
if os.path.exists('/app/shared/.cc_env'):
    with open('/app/shared/.cc_env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('"\'')
                os.environ[key] = value

"""
Content Management Service - Educational Content Processing and Management API

This service provides comprehensive content management capabilities for the Course Creator Platform,
following SOLID principles and Domain-Driven Design patterns.

## Core Responsibilities:

### File Processing Pipeline
- **Upload Management**: Handles multi-format file uploads (PDF, DOCX, PPTX, JSON) with security validation
- **Text Extraction**: Processes uploaded files to extract structured content and metadata
- **Content Analysis**: Analyzes document structure to identify learning objectives, topics, assessments
- **Format Conversion**: Converts between different educational content formats

### AI Integration & Content Generation
- **Syllabus Analysis**: Processes uploaded syllabi to extract course structure and learning outcomes
- **Content Enhancement**: Uses AI services to generate supplementary educational materials
- **Template Processing**: Applies AI-generated content to educational templates
- **Quality Assurance**: Validates generated content for educational standards and consistency

### Multi-Format Export Capabilities
- **PowerPoint Export**: Generates professional slide presentations from course content
- **PDF Generation**: Creates formatted PDF documents for assignments and handouts
- **Excel Export**: Produces spreadsheet-based content for data-driven exercises
- **JSON Export**: Provides structured data export for integration with other systems
- **ZIP Packaging**: Bundles complete course materials for distribution
- **SCORM Compliance**: Generates SCORM-compliant packages for LMS integration

### Pane-Based Content Management
- **Syllabus Pane**: Specialized handling of course syllabi with structure recognition
- **Slides Pane**: Template-based slide management with AI content generation
- **Labs Pane**: Custom lab environment configuration and management
- **Quizzes Pane**: Assessment creation with automatic answer key recognition

### Storage & Metadata Management
- **Secure Storage**: File storage with access controls and encryption
- **Metadata Tracking**: Comprehensive metadata management for content discovery
- **Version Control**: Content versioning for educational material evolution
- **Performance Optimization**: Efficient storage and retrieval for large educational datasets

## Architecture Principles:

### SOLID Design Patterns
- **Single Responsibility**: API layer only - business logic delegated to specialized services
- **Open/Closed**: Extensible through dependency injection and interface abstraction
- **Liskov Substitution**: Uses interface abstractions for seamless component replacement
- **Interface Segregation**: Clean, focused interfaces for different content management aspects
- **Dependency Inversion**: Depends on abstractions, not concrete implementations

### Educational Content Workflows
- **Upload Processing**: Drag-and-drop → validation → text extraction → AI analysis → storage
- **Content Generation**: AI prompts → content creation → template application → quality validation
- **Export Pipeline**: Content selection → format conversion → packaging → delivery
- **Search & Discovery**: Metadata indexing → tag-based search → content recommendations

### Performance Considerations
- **Async Processing**: Non-blocking file operations for handling large educational content
- **Memory Management**: Efficient processing of large documents and media files
- **Caching Strategy**: Intelligent caching for frequently accessed educational materials
- **Batch Operations**: Optimized bulk processing for course-wide content operations

### Security & Quality Assurance
- **File Validation**: Comprehensive validation for uploaded educational content
- **Content Sanitization**: Security scanning and content cleaning for safe processing
- **Access Control**: Role-based access to educational content and management functions
- **Audit Logging**: Complete audit trail for educational content lifecycle management

### Integration Patterns
- **AI Service Integration**: Seamless integration with course-generator service for content enhancement
- **Storage Service Communication**: Efficient file storage and retrieval operations
- **Analytics Integration**: Content usage tracking and educational effectiveness metrics
- **Lab Container Integration**: Dynamic lab environment configuration and deployment

This service is the central hub for all educational content processing, ensuring high-quality,
AI-enhanced educational materials that meet modern pedagogical standards.
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
import os
import sys
from datetime import datetime
from contextlib import asynccontextmanager
import hydra
from omegaconf import DictConfig
import uvicorn

# Add shared directory to path for organization middleware
sys.path.append('/app/shared')
try:
    from auth.organization_middleware import OrganizationAuthorizationMiddleware, get_organization_context
except ImportError:
    # Fallback if middleware not available
    OrganizationAuthorizationMiddleware = None
    get_organization_context = None

try:
    from logging_setup import setup_docker_logging
except ImportError:
    # Fallback if config module not available
    def setup_docker_logging(service_name: str, log_level: str = "INFO"):
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s %(hostname)s %(name)s[%(process)d]: %(levelname)s - %(message)s'
        )
        return logging.getLogger(service_name)

# Pydantic models for API (Data Transfer Objects)
from pydantic import BaseModel, Field

# Domain entities
from domain.entities.base_content import ContentType, ContentStatus
from domain.entities.syllabus import Syllabus
from domain.entities.slide import Slide
from domain.entities.quiz import Quiz
from domain.entities.exercise import Exercise
from domain.entities.lab_environment import LabEnvironment

# Domain interfaces
from domain.interfaces.content_service import (
    ISyllabusService, ISlideService, IQuizService, IExerciseService,
    ILabEnvironmentService, IContentSearchService, IContentValidationService,
    IContentAnalyticsService, IContentExportService
)

# Infrastructure
from infrastructure.container import ContentManagementContainer

# Custom exceptions
from exceptions import (
    ContentManagementException, FileProcessingException, ContentUploadException,
    ContentExportException, AIIntegrationException, ValidationException,
    ContentNotFoundException, DatabaseException, StorageException,
    ContentSearchException, TemplateException
)

# API Models (Data Transfer Objects) - Educational Content Management
#
# These models follow the Single Responsibility Principle, with each model
# focused on a specific aspect of educational content management.
# 
# Design Principles:
# - Clean separation between API layer and domain logic
# - Comprehensive validation for educational content integrity
# - Standardized structure for all educational content types
# - Support for educational metadata and content relationships
# - Integration with pane-based content management workflows
class SyllabusCreateRequest(BaseModel):
    """
    Data Transfer Object for creating new syllabus content.
    
    This model handles the upload and initial processing of syllabus documents,
    supporting the pane-based content management system's syllabus pane functionality.
    
    Educational Context:
    - Captures essential course information and structure
    - Supports AI-driven content analysis and enhancement
    - Validates educational standards compliance
    - Enables structured learning objective definition
    
    Business Logic:
    - Integrates with AI services for syllabus analysis
    - Supports multi-format syllabus processing (PDF, DOCX, etc.)
    - Validates academic content structure and completeness
    - Enables automatic course outline generation
    
    Performance Considerations:
    - Optimized validation for large syllabus documents
    - Efficient handling of complex course structures
    - Memory-efficient processing of educational metadata
    """
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    course_id: str = Field(..., min_length=1)
    course_info: Dict[str, Any] = Field(..., description="Course information including code, name, credits")
    learning_objectives: List[str] = Field(..., min_items=1, description="Learning objectives")
    modules: Optional[List[Dict[str, Any]]] = None
    assessment_methods: Optional[List[str]] = None
    grading_scheme: Optional[Dict[str, float]] = None
    policies: Optional[Dict[str, str]] = None
    schedule: Optional[Dict[str, Any]] = None
    textbooks: Optional[List[Dict[str, str]]] = None
    tags: Optional[List[str]] = None

class SyllabusUpdateRequest(BaseModel):
    """
    Data Transfer Object for updating existing syllabus content.
    
    Supports incremental updates to syllabus information while maintaining
    educational content integrity and version control.
    
    Educational Workflow:
    - Enables iterative course development and refinement
    - Supports collaborative editing of educational content
    - Maintains educational standards during content evolution
    - Preserves learning objective alignment and assessment mapping
    
    Business Logic:
    - Partial update support for efficient content modification
    - Validation ensures educational content consistency
    - Automatic timestamp and versioning management
    - Integration with content change tracking systems
    """
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    modules: Optional[List[Dict[str, Any]]] = None
    assessment_methods: Optional[List[str]] = None
    grading_scheme: Optional[Dict[str, float]] = None
    policies: Optional[Dict[str, str]] = None
    schedule: Optional[Dict[str, Any]] = None
    textbooks: Optional[List[Dict[str, str]]] = None
    tags: Optional[List[str]] = None

class ContentSearchRequest(BaseModel):
    """
    Data Transfer Object for content search and discovery operations.
    
    Enables sophisticated search across all educational content types,
    supporting instructors in finding and reusing educational materials.
    
    Search Capabilities:
    - Full-text search across uploaded documents and generated content
    - Tag-based filtering for content categorization
    - Content type filtering (syllabi, slides, exercises, quizzes)
    - Course-specific content discovery
    
    Educational Use Cases:
    - Finding existing materials for course development
    - Discovering reusable educational components
    - Content recommendation based on similarity
    - Cross-course content analysis and alignment
    
    Performance Optimization:
    - Efficient indexing for fast educational content retrieval
    - Optimized queries for large educational content databases
    - Caching strategy for frequently accessed educational materials
    """
    query: str = Field(..., min_length=2)
    content_types: Optional[List[str]] = None
    course_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None

class ContentResponse(BaseModel):
    """
    Standardized response model for all educational content types.
    
    Provides consistent data structure for educational content presentation
    across different panes and content management operations.
    
    Content Lifecycle Support:
    - Tracks content creation and modification timestamps
    - Maintains content status (draft, published, archived)
    - Provides consistent metadata structure
    - Supports content versioning and audit trails
    
    Integration Benefits:
    - Uniform API response structure across all content types
    - Simplified client-side content handling
    - Consistent metadata representation
    - Standardized content identification and linking
    
    Educational Context:
    - Enables content relationship mapping and dependency tracking
    - Supports educational content analytics and usage monitoring
    - Facilitates content quality assessment and improvement
    """
    id: str
    title: str
    description: Optional[str] = None
    course_id: str
    created_by: str
    tags: List[str] = []
    status: str
    content_type: str
    created_at: datetime
    updated_at: datetime

# Global container
container: Optional[ContentManagementContainer] = None
current_config: Optional[DictConfig] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI application lifecycle manager for content management service.
    
    Manages the complete lifecycle of the content management service,
    ensuring proper initialization and cleanup of educational content
    processing resources.
    
    Startup Operations:
    - Initialize dependency injection container with educational content services
    - Establish connections to storage systems for educational materials
    - Configure AI service integrations for content enhancement
    - Set up file processing pipelines for multi-format support
    - Initialize caching systems for educational content optimization
    
    Shutdown Operations:
    - Gracefully close file processing operations
    - Clean up temporary educational content and processing files
    - Flush pending content operations and export jobs
    - Close AI service connections and storage handles
    
    Resource Management:
    - Ensures proper cleanup of large educational file processing operations
    - Manages memory usage for content analysis and generation tasks
    - Coordinates with storage systems for data integrity
    
    Educational Context:
    - Maintains educational content processing pipeline availability
    - Ensures consistent service quality for educational workloads
    - Supports high-availability requirements for academic environments
    """
    """FastAPI lifespan event handler"""
    global container, current_config
    
    # Startup
    logging.info("Initializing Content Management Service...")
    container = ContentManagementContainer(current_config or {})
    await container.initialize()
    logging.info("Content Management Service initialized successfully")
    
    yield
    
    # Shutdown
    logging.info("Shutting down Content Management Service...")
    if container:
        await container.cleanup()
    logging.info("Content Management Service shutdown complete")

def create_app(config: DictConfig = None) -> FastAPI:
    """
    Application factory for creating the Content Management Service FastAPI instance.
    
    Creates a fully configured FastAPI application with comprehensive content
    management capabilities, following SOLID principles and educational best practices.
    
    Configuration Support:
    - Hydra-based configuration management for educational environments
    - Environment-specific settings for development, staging, and production
    - Educational content processing parameter configuration
    - AI service integration settings and fallback configurations
    
    Middleware Configuration:
    - CORS support for cross-origin educational content access
    - Request/response logging for educational content audit trails
    - Security middleware for safe educational content processing
    - Performance monitoring for educational workload optimization
    
    Exception Handling:
    - Comprehensive exception mapping for educational content operations
    - Detailed error reporting for content processing failures
    - Educational context preservation in error responses
    - Graceful degradation for AI service unavailability
    
    Educational Features:
    - Multi-format file processing for diverse educational content
    - AI-enhanced content generation and validation
    - Pane-based content management for different educational content types
    - Export capabilities for various educational delivery formats
    
    Args:
        config: Hydra configuration object with service settings
        
    Returns:
        Configured FastAPI application instance ready for educational content management
        
    Architecture Benefits:
    - Follows Open/Closed principle for extensible content management
    - Supports dependency injection for testable educational services
    - Enables configuration-driven educational content processing
    - Provides consistent API structure for educational content operations
    """
    """
    Application factory following SOLID principles
    Open/Closed: New routes can be added without modifying existing code
    """
    global current_config
    current_config = config or {}
    
    app = FastAPI(
        title="Content Management Service",
        description="Content creation, management, and processing service",
        version="2.0.0",
        lifespan=lifespan
    )
    
    # Organization security middleware (must be first for security)
    if OrganizationAuthorizationMiddleware:
        app.add_middleware(
            OrganizationAuthorizationMiddleware,
            config=config
        )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Exception type to HTTP status code mapping (Open/Closed Principle)
    EXCEPTION_STATUS_MAPPING = {
        ValidationException: 400,
        ContentNotFoundException: 404,
        FileProcessingException: 422,
        ContentUploadException: 422,
        ContentExportException: 422,
        ContentSearchException: 422,
        TemplateException: 422,
        AIIntegrationException: 500,
        DatabaseException: 500,
        StorageException: 500,
    }
    
    # Custom exception handler
    @app.exception_handler(ContentManagementException)
    async def content_management_exception_handler(request, exc: ContentManagementException):
        """Handle custom content management exceptions."""
        # Use mapping to determine status code (extensible design)
        status_code = next(
            (code for exc_type, code in EXCEPTION_STATUS_MAPPING.items() if isinstance(exc, exc_type)),
            500  # Default status code
        )
            
        response_data = exc.to_dict()
        response_data["path"] = str(request.url)
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "content-management",
            "version": "2.0.0",
            "timestamp": datetime.utcnow()
        }
    
    return app

app = create_app()

# Dependency injection helpers
def get_syllabus_service() -> ISyllabusService:
    """
    Dependency injection provider for syllabus management service.
    
    Provides access to comprehensive syllabus processing capabilities,
    supporting the syllabus pane in the content management system.
    
    Educational Capabilities:
    - Syllabus document parsing and structure analysis
    - Learning objective extraction and validation
    - Course timeline and assessment mapping
    - Integration with AI services for syllabus enhancement
    
    Business Logic:
    - Validates educational standards compliance
    - Supports multiple syllabus formats and structures
    - Enables syllabus template application and customization
    - Facilitates syllabus comparison and alignment analysis
    
    Returns:
        ISyllabusService: Syllabus management service instance
        
    Raises:
        HTTPException: If service container is not initialized
        
    Integration Benefits:
    - Seamless integration with course generation workflows
    - Support for educational content lifecycle management
    - Enables syllabus-driven course development automation
    """
    """Dependency injection for syllabus service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_syllabus_service()

def get_slide_service() -> ISlideService:
    """Dependency injection for slide service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_slide_service()

def get_quiz_service() -> IQuizService:
    """Dependency injection for quiz service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_quiz_service()

def get_exercise_service() -> IExerciseService:
    """Dependency injection for exercise service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_exercise_service()

def get_lab_environment_service() -> ILabEnvironmentService:
    """Dependency injection for lab environment service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_lab_environment_service()

def get_content_search_service() -> IContentSearchService:
    """Dependency injection for content search service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_content_search_service()

def get_content_validation_service() -> IContentValidationService:
    """Dependency injection for content validation service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_content_validation_service()

def get_content_analytics_service() -> IContentAnalyticsService:
    """Dependency injection for content analytics service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_content_analytics_service()

def get_content_export_service() -> IContentExportService:
    """Dependency injection for content export service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_content_export_service()

async def get_current_user() -> str:
    """
    Authentication dependency for educational content access control.
    
    Provides user identification for educational content operations,
    ensuring proper access control and audit trails for educational materials.
    
    Educational Context:
    - Supports role-based access to educational content (instructors, students, admins)
    - Enables content ownership tracking for academic integrity
    - Facilitates collaboration controls for course development
    - Supports institutional content sharing and access policies
    
    Security Considerations:
    - Validates JWT tokens for secure educational content access
    - Maintains session security for sensitive educational materials
    - Supports fine-grained permissions for different content types
    - Enables audit logging for educational content access patterns
    
    Returns:
        str: Current authenticated user identifier
        
    Future Implementation:
    - Will integrate with comprehensive JWT token validation
    - Will support role-based educational content access control
    - Will enable institutional authentication integration
    
    Note:
        Currently simplified for development - will be enhanced with
        full authentication and authorization for production educational environments.
    """
    """Get current user (simplified for now)"""
    # In a real implementation, this would validate JWT token
    return "current_user_id"

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "content-management",
        "version": "2.0.0",
        "timestamp": datetime.utcnow()
    }

# Syllabus Endpoints
@app.post("/api/v1/syllabi", response_model=ContentResponse)
async def create_syllabus(
    request: SyllabusCreateRequest,
    current_user: str = Depends(get_current_user),
    syllabus_service: ISyllabusService = Depends(get_syllabus_service)
):
    """Create a new syllabus"""
    try:
        syllabus = await syllabus_service.create_syllabus(
            request.dict(), current_user
        )
        return _content_to_response(syllabus)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error creating syllabus: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.get("/api/v1/syllabi/{syllabus_id}", response_model=ContentResponse)
async def get_syllabus(
    syllabus_id: str,
    syllabus_service: ISyllabusService = Depends(get_syllabus_service)
):
    """Get syllabus by ID"""
    try:
        syllabus = await syllabus_service.get_syllabus(syllabus_id)
        if not syllabus:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        return _content_to_response(syllabus)
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error("Error getting syllabus: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.put("/api/v1/syllabi/{syllabus_id}", response_model=ContentResponse)
async def update_syllabus(
    syllabus_id: str,
    request: SyllabusUpdateRequest,
    current_user: str = Depends(get_current_user),
    syllabus_service: ISyllabusService = Depends(get_syllabus_service)
):
    """Update syllabus"""
    try:
        syllabus = await syllabus_service.update_syllabus(
            syllabus_id, request.dict(exclude_unset=True), current_user
        )
        if not syllabus:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        return _content_to_response(syllabus)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error updating syllabus: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.delete("/api/v1/syllabi/{syllabus_id}")
async def delete_syllabus(
    syllabus_id: str,
    current_user: str = Depends(get_current_user),
    syllabus_service: ISyllabusService = Depends(get_syllabus_service)
):
    """Delete syllabus"""
    try:
        success = await syllabus_service.delete_syllabus(syllabus_id, current_user)
        if not success:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        return {"message": "Syllabus deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error deleting syllabus: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.post("/api/v1/syllabi/{syllabus_id}/publish", response_model=ContentResponse)
async def publish_syllabus(
    syllabus_id: str,
    current_user: str = Depends(get_current_user),
    syllabus_service: ISyllabusService = Depends(get_syllabus_service)
):
    """Publish syllabus"""
    try:
        syllabus = await syllabus_service.publish_syllabus(syllabus_id, current_user)
        if not syllabus:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        return _content_to_response(syllabus)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error publishing syllabus: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.post("/api/v1/syllabi/{syllabus_id}/archive", response_model=ContentResponse)
async def archive_syllabus(
    syllabus_id: str,
    current_user: str = Depends(get_current_user),
    syllabus_service: ISyllabusService = Depends(get_syllabus_service)
):
    """Archive syllabus"""
    try:
        syllabus = await syllabus_service.archive_syllabus(syllabus_id, current_user)
        if not syllabus:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        return _content_to_response(syllabus)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error archiving syllabus: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.get("/api/v1/courses/{course_id}/syllabi", response_model=List[ContentResponse])
async def get_course_syllabi(
    course_id: str,
    include_drafts: bool = False,
    syllabus_service: ISyllabusService = Depends(get_syllabus_service)
):
    """Get all syllabi for a course"""
    try:
        syllabi = await syllabus_service.get_course_syllabi(course_id, include_drafts)
        return [_content_to_response(syllabus) for syllabus in syllabi]
        
    except Exception as e:
        logging.error("Error getting course syllabi: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

# Content Search Endpoints
@app.post("/api/v1/content/search")
async def search_content(
    request: ContentSearchRequest,
    search_service: IContentSearchService = Depends(get_content_search_service)
):
    """Search content across all types"""
    try:
        # Convert string content types to enum
        content_types = None
        if request.content_types:
            content_types = [ContentType(ct) for ct in request.content_types]
        
        results = await search_service.search_content(
            query=request.query,
            content_types=content_types,
            course_id=request.course_id,
            filters=request.filters
        )
        
        return results
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error searching content: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.get("/api/v1/content/search/tags")
async def search_by_tags(
    tags: str,  # Comma-separated tags
    content_types: Optional[str] = None,  # Comma-separated content types
    course_id: Optional[str] = None,
    search_service: IContentSearchService = Depends(get_content_search_service)
):
    """Search content by tags"""
    try:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Convert string content types to enum
        content_type_list = None
        if content_types:
            content_type_list = [ContentType(ct.strip()) for ct in content_types.split(",") if ct.strip()]
        
        results = await search_service.search_by_tags(
            tags=tag_list,
            content_types=content_type_list,
            course_id=course_id
        )
        
        return results
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error searching by tags: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.get("/api/v1/content/recommendations/{content_id}")
async def get_content_recommendations(
    content_id: str,
    limit: int = 5,
    search_service: IContentSearchService = Depends(get_content_search_service)
):
    """Get content recommendations"""
    try:
        recommendations = await search_service.get_content_recommendations(content_id, limit)
        return {"recommendations": recommendations}
        
    except Exception as e:
        logging.error("Error getting recommendations: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

# Content Analytics Endpoints
@app.get("/api/v1/analytics/content/statistics")
async def get_content_statistics(
    course_id: Optional[str] = None,
    analytics_service: IContentAnalyticsService = Depends(get_content_analytics_service)
):
    """Get content statistics"""
    try:
        stats = await analytics_service.get_content_statistics(course_id)
        return stats
        
    except Exception as e:
        logging.error("Error getting content statistics: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.get("/api/v1/analytics/content/{content_id}/metrics")
async def get_content_metrics(
    content_id: str,
    days: int = 30,
    analytics_service: IContentAnalyticsService = Depends(get_content_analytics_service)
):
    """Get content usage metrics"""
    try:
        metrics = await analytics_service.get_content_usage_metrics(content_id, days)
        return metrics
        
    except Exception as e:
        logging.error("Error getting content metrics: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

# Content Validation Endpoints
@app.post("/api/v1/content/{content_id}/validate")
async def validate_content(
    content_id: str,
    validation_service: IContentValidationService = Depends(get_content_validation_service)
):
    """Validate content"""
    try:
        # This is a simplified implementation
        # In a real system, you'd need to load the content first
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "validation_score": 100
        }
        return validation_result
        
    except Exception as e:
        logging.error("Error validating content: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

# Content Export Endpoints
@app.post("/api/v1/content/{content_id}/export")
async def export_content(
    content_id: str,
    export_format: str,
    export_service: IContentExportService = Depends(get_content_export_service)
):
    """Export content"""
    try:
        export_result = await export_service.export_content(content_id, export_format)
        return export_result
        
    except Exception as e:
        logging.error("Error exporting content: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.post("/api/v1/courses/{course_id}/export")
async def export_course_content(
    course_id: str,
    export_format: str,
    content_types: Optional[str] = None,
    export_service: IContentExportService = Depends(get_content_export_service)
):
    """Export all content for a course"""
    try:
        # Convert string content types to enum
        content_type_list = None
        if content_types:
            content_type_list = [ContentType(ct.strip()) for ct in content_types.split(",") if ct.strip()]
        
        export_result = await export_service.export_course_content(
            course_id, export_format, content_type_list
        )
        return export_result
        
    except Exception as e:
        logging.error("Error exporting course content: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

# Helper functions (following Single Responsibility)
def _content_to_response(content) -> ContentResponse:
    """
    Convert domain entity to standardized API response format.
    
    Transforms internal content domain objects into consistent API responses,
    following the Single Responsibility Principle for clean data transformation.
    
    Educational Content Transformation:
    - Standardizes content representation across all educational content types
    - Preserves educational metadata and content relationships
    - Ensures consistent timestamp and status representation
    - Maintains content ownership and access control information
    
    Business Logic:
    - Abstracts internal domain structure from API consumers
    - Provides stable API contract for educational content access
    - Enables versioning and backward compatibility for educational clients
    - Supports content caching and optimization strategies
    
    Args:
        content: Domain entity instance (Syllabus, Slide, Quiz, Exercise, LabEnvironment)
        
    Returns:
        ContentResponse: Standardized response model for educational content
        
    Architecture Benefits:
    - Follows Dependency Inversion Principle with domain abstraction
    - Enables consistent educational content presentation
    - Supports API evolution without breaking educational client applications
    - Facilitates educational content analytics and monitoring
    """
    """Convert domain entity to API response DTO"""
    return ContentResponse(
        id=content.id,
        title=content.title,
        description=content.description,
        course_id=content.course_id,
        created_by=content.created_by,
        tags=content.tags,
        status=content.status.value,
        content_type=content.get_content_type().value,
        created_at=content.created_at,
        updated_at=content.updated_at
    )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "error_code": f"HTTP_{exc.status_code}"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logging.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )

@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """
    Main entry point for the Content Management Service.
    
    Initializes and runs the educational content management service with
    comprehensive configuration management and centralized logging.
    
    Service Initialization:
    - Configures centralized syslog format logging for educational content operations
    - Initializes Hydra configuration management for educational environments
    - Sets up service networking and port configuration
    - Establishes educational content processing pipeline
    
    Educational Content Service Features:
    - Multi-format file processing for educational materials (PDF, DOCX, PPTX, JSON)
    - AI-enhanced content generation and validation
    - Pane-based content management for different educational content types
    - Comprehensive export capabilities for educational content delivery
    - Integration with course generation and analytics services
    
    Configuration Management:
    - Environment-specific settings for educational institutions
    - Educational content processing parameters and limits
    - AI service integration configuration and fallback options
    - Storage and caching configuration for educational workloads
    
    Performance Optimization:
    - Async processing for large educational content operations
    - Memory management for educational document processing
    - Optimized logging to reduce overhead while maintaining audit trails
    - Efficient resource utilization for educational content workflows
    
    Operational Features:
    - Health check endpoints for educational service monitoring
    - Graceful shutdown handling for educational content integrity
    - Error handling and recovery for educational content processing
    - Integration with platform-wide educational service ecosystem
    
    Args:
        cfg: Hydra configuration object containing educational service settings
        
    Educational Context:
    - Supports high-availability requirements for academic environments
    - Enables scalable educational content processing for institutional use
    - Provides consistent educational content management across course lifecycles
    - Facilitates educational content compliance and quality assurance
    """
    """Main entry point using Hydra configuration"""
    global current_config
    current_config = cfg
    
    # Setup centralized logging with syslog format
    service_name = os.environ.get('SERVICE_NAME', 'content-management')
    log_level = os.environ.get('LOG_LEVEL', cfg.get('logging', {}).get('level', 'INFO'))
    
    logger = setup_docker_logging(service_name, log_level)
    port = cfg.get('server', {}).get('port', 8005)
    host = cfg.get('server', {}).get('host', '0.0.0.0')
    
    logger.info(f"Starting Content Management Service on {host}:{port}")
    
    # Create app with configuration
    global app
    app = create_app(cfg)
    
    # Run server with HTTPS/SSL configuration and reduced uvicorn logging to avoid duplicates
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="warning",  # Reduce uvicorn log level since we have our own logging
        access_log=False,     # Disable uvicorn access log since we log via middleware
        ssl_keyfile="/app/ssl/nginx-selfsigned.key",
        ssl_certfile="/app/ssl/nginx-selfsigned.crt"
    )

if __name__ == "__main__":
    main()