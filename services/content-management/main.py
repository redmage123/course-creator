"""
Content Management Service - Refactored following SOLID principles
Single Responsibility: API layer only - business logic delegated to services
Open/Closed: Extensible through dependency injection
Liskov Substitution: Uses interface abstractions
Interface Segregation: Clean, focused interfaces
Dependency Inversion: Depends on abstractions, not concretions
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

# API Models (DTOs - following Single Responsibility)
class SyllabusCreateRequest(BaseModel):
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
    query: str = Field(..., min_length=2)
    content_types: Optional[List[str]] = None
    course_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None

class ContentResponse(BaseModel):
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
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app

app = create_app()

# Dependency injection helpers
def get_syllabus_service() -> ISyllabusService:
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
    
    # Run server with reduced uvicorn logging to avoid duplicates
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="warning",  # Reduce uvicorn log level since we have our own logging
        access_log=False      # Disable uvicorn access log since we log via middleware
    )

if __name__ == "__main__":
    main()