#!/usr/bin/env python3
"""
Course Management Service - Refactored following SOLID principles
Single Responsibility: API layer only - business logic delegated to services
Open/Closed: Extensible through dependency injection
Liskov Substitution: Uses interface abstractions
Interface Segregation: Clean, focused interfaces
Dependency Inversion: Depends on abstractions, not concretions
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
import logging
import os
import sys
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
from contextlib import asynccontextmanager
from datetime import datetime

# Pydantic models for API (Data Transfer Objects)
from pydantic import BaseModel, Field

# Domain entities and services
from domain.entities.course import Course, DifficultyLevel, DurationUnit
from domain.entities.enrollment import EnrollmentRequest, BulkEnrollmentRequest
from domain.entities.feedback import CourseFeedback, StudentFeedback, FeedbackResponse
from domain.interfaces.course_service import ICourseService
from domain.interfaces.enrollment_service import IEnrollmentService
from domain.interfaces.feedback_service import IFeedbackService

# Infrastructure
from infrastructure.container import Container

# API Models (DTOs - following Single Responsibility)
class CourseCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    category: Optional[str] = None
    difficulty_level: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")
    estimated_duration: Optional[int] = Field(None, ge=1)
    duration_unit: str = Field(default="weeks", pattern="^(hours|days|weeks|months)$")
    price: float = Field(default=0.0, ge=0)
    tags: List[str] = Field(default_factory=list)

class CourseUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    category: Optional[str] = None
    difficulty_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    estimated_duration: Optional[int] = Field(None, ge=1)
    duration_unit: Optional[str] = Field(None, pattern="^(hours|days|weeks|months)$")
    price: Optional[float] = Field(None, ge=0)
    tags: Optional[List[str]] = None

class CourseResponse(BaseModel):
    id: str
    title: str
    description: str
    instructor_id: str
    category: Optional[str]
    difficulty_level: str
    estimated_duration: Optional[int]
    duration_unit: Optional[str]
    price: float
    is_published: bool
    thumbnail_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    tags: List[str]

class CourseFeedbackRequest(BaseModel):
    course_id: str
    overall_rating: int = Field(..., ge=1, le=5)
    content_quality: Optional[int] = Field(None, ge=1, le=5)
    instructor_effectiveness: Optional[int] = Field(None, ge=1, le=5)
    difficulty_appropriateness: Optional[int] = Field(None, ge=1, le=5)
    lab_quality: Optional[int] = Field(None, ge=1, le=5)
    positive_aspects: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    additional_comments: Optional[str] = None
    would_recommend: Optional[bool] = None
    is_anonymous: bool = False

class EnrollmentRequestDTO(BaseModel):
    student_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    course_id: str

class BulkEnrollmentRequestDTO(BaseModel):
    course_id: str
    student_emails: List[str] = Field(..., min_items=1)

# Global container
container: Optional[Container] = None
current_config: Optional[DictConfig] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event handler"""
    global container, current_config
    
    # Startup
    logging.info("Initializing Course Management Service...")
    container = Container(current_config)
    await container.initialize()
    logging.info("Course Management Service initialized successfully")
    
    yield
    
    # Shutdown
    logging.info("Shutting down Course Management Service...")
    if container:
        await container.cleanup()
    logging.info("Course Management Service shutdown complete")

def create_app(config: DictConfig) -> FastAPI:
    """
    Application factory following SOLID principles
    Open/Closed: New routes can be added without modifying existing code
    """
    global current_config
    current_config = config
    
    app = FastAPI(
        title="Course Management Service",
        description="Microservice for managing courses, enrollments, and feedback",
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

app = create_app(current_config or {})

# Dependency injection helpers
def get_course_service() -> ICourseService:
    """Dependency injection for course service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_course_service()

def get_enrollment_service() -> IEnrollmentService:
    """Dependency injection for enrollment service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")  
    return container.get_enrollment_service()

def get_feedback_service() -> IFeedbackService:
    """Dependency injection for feedback service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_feedback_service()

def get_current_user_id() -> str:
    """
    Extract user ID from JWT token
    For now, return a mock user ID - in production, this would validate JWT
    """
    return "instructor_123"  # Mock implementation

# Course Management Endpoints
@app.post("/courses", response_model=CourseResponse)
async def create_course(
    request: CourseCreateRequest,
    course_service: ICourseService = Depends(get_course_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a new course"""
    try:
        # Convert DTO to domain entity
        course = Course(
            title=request.title,
            description=request.description,
            instructor_id=current_user_id,
            category=request.category,
            difficulty_level=DifficultyLevel(request.difficulty_level),
            estimated_duration=request.estimated_duration,
            duration_unit=DurationUnit(request.duration_unit),
            price=request.price,
            tags=request.tags
        )
        
        created_course = await course_service.create_course(course)
        return _course_to_response(created_course)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error creating course: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    course_service: ICourseService = Depends(get_course_service)
):
    """Get course by ID"""
    try:
        course = await course_service.get_course_by_id(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        return _course_to_response(course)
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error("Error getting course: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.get("/courses", response_model=List[CourseResponse])
async def get_instructor_courses(
    course_service: ICourseService = Depends(get_course_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Get all courses for the current instructor"""
    try:
        courses = await course_service.get_courses_by_instructor(current_user_id)
        return [_course_to_response(course) for course in courses]
        
    except Exception as e:
        logging.error("Error getting instructor courses: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.put("/courses/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: str,
    request: CourseUpdateRequest,
    course_service: ICourseService = Depends(get_course_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Update an existing course"""
    try:
        # Get existing course
        existing_course = await course_service.get_course_by_id(course_id)
        if not existing_course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Check ownership
        if existing_course.instructor_id != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this course")
        
        # Update fields
        existing_course.update_details(
            title=request.title,
            description=request.description,
            category=request.category,
            difficulty_level=DifficultyLevel(request.difficulty_level) if request.difficulty_level else None,
            price=request.price,
            estimated_duration=request.estimated_duration,
            duration_unit=DurationUnit(request.duration_unit) if request.duration_unit else None
        )
        
        if request.tags is not None:
            existing_course.tags = request.tags
        
        updated_course = await course_service.update_course(existing_course)
        return _course_to_response(updated_course)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error updating course: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.post("/courses/{course_id}/publish", response_model=CourseResponse)
async def publish_course(
    course_id: str,
    course_service: ICourseService = Depends(get_course_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Publish a course"""
    try:
        published_course = await course_service.publish_course(course_id, current_user_id)
        return _course_to_response(published_course)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error publishing course: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.post("/courses/{course_id}/unpublish", response_model=CourseResponse)
async def unpublish_course(
    course_id: str,
    course_service: ICourseService = Depends(get_course_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Unpublish a course"""
    try:
        unpublished_course = await course_service.unpublish_course(course_id, current_user_id)
        return _course_to_response(unpublished_course)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error unpublishing course: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.delete("/courses/{course_id}")
async def delete_course(
    course_id: str,
    course_service: ICourseService = Depends(get_course_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete a course"""
    try:
        success = await course_service.delete_course(course_id, current_user_id)
        if success:
            return {"message": "Course deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete course")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error deleting course: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

# Enrollment Endpoints
@app.post("/enrollments")
async def enroll_student(
    request: EnrollmentRequestDTO,
    enrollment_service: IEnrollmentService = Depends(get_enrollment_service)
):
    """Enroll a student in a course"""
    try:
        enrollment_request = EnrollmentRequest(
            student_email=request.student_email,
            course_id=request.course_id
        )
        
        enrollment = await enrollment_service.enroll_student(enrollment_request)
        return {"message": "Student enrolled successfully", "enrollment_id": enrollment.id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error enrolling student: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "course-management", "version": "2.0.0"}

# Helper functions
def _course_to_response(course: Course) -> CourseResponse:
    """Convert domain entity to API response DTO"""
    return CourseResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        instructor_id=course.instructor_id,
        category=course.category,
        difficulty_level=course.difficulty_level.value,
        estimated_duration=course.estimated_duration,
        duration_unit=course.duration_unit.value if course.duration_unit else None,
        price=course.price,
        is_published=course.is_published,
        thumbnail_url=course.thumbnail_url,
        created_at=course.created_at,
        updated_at=course.updated_at,
        tags=course.tags
    )

@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """Main entry point using Hydra configuration"""
    global current_config
    current_config = cfg
    
    # Setup centralized logging with syslog format
    service_name = os.environ.get('SERVICE_NAME', 'course-management')
    log_level = os.environ.get('LOG_LEVEL', getattr(cfg, 'logging', {}).get('level', 'INFO'))
    
    logger = setup_docker_logging(service_name, log_level)
    logger.info(f"Starting Course Management Service on port {cfg.server.port}")
    
    # Create app with configuration
    global app
    app = create_app(cfg)
    
    # Run server with reduced uvicorn logging to avoid duplicates
    uvicorn.run(
        app,
        host=cfg.server.host,
        port=cfg.server.port,
        log_level="warning",  # Reduce uvicorn log level since we have our own logging
        access_log=False      # Disable uvicorn access log since we log via middleware
    )

if __name__ == "__main__":
    main()