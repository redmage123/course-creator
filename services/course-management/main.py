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
Course Management Service - Core Educational Platform Component

This module serves as the main entry point for the Course Management Service, which is a 
critical microservice in the educational platform responsible for managing the complete 
course lifecycle, student enrollments, and bi-directional feedback systems.

ARCHITECTURAL PRINCIPLES:
The service follows SOLID principles throughout its design:
- Single Responsibility: API layer only - business logic delegated to services
- Open/Closed: Extensible through dependency injection and configurable mappings
- Liskov Substitution: Uses interface abstractions for all service dependencies
- Interface Segregation: Clean, focused interfaces for each domain area
- Dependency Inversion: Depends on abstractions, not concrete implementations

CORE RESPONSIBILITIES:
1. Course Lifecycle Management: Complete CRUD operations for course creation, publication, and management
2. Student Enrollment: Managing student enrollment processes and access control
3. Bi-Directional Feedback System: Handling both student→course and instructor→student feedback flows
4. Quiz Management Integration: Supporting quiz publication and analytics integration
5. Email Notification: Hydra-configured email notifications for course events
6. Data Integrity: Ensuring referential integrity across course-related operations

EDUCATIONAL WORKFLOW PATTERNS:
- Course Creation → Content Development → Publication → Enrollment → Delivery → Feedback
- Instructor manages courses through structured lifecycle states
- Students access published courses through controlled enrollment processes
- Feedback flows bi-directionally to improve educational outcomes
- Analytics integration provides insights into course effectiveness

INTEGRATION PATTERNS:
- Analytics Service: Course performance data and student progress metrics
- User Management Service: Authentication and authorization
- Content Management Service: Course content and materials
- Lab Container Service: Hands-on learning environments
- Organization Management Service: RBAC and multi-tenant support

PERFORMANCE CONSIDERATIONS:
- Async operations for database interactions to handle educational scale
- Dependency injection container for efficient service lifecycle management
- Connection pooling and caching for high-throughput enrollment operations
- Optimized queries for instructor dashboards and student course listings

DATABASE RELATIONSHIPS:
- Courses have one-to-many relationships with enrollments and feedback
- Enrollments link students to courses with access control metadata
- Feedback entities support both course evaluation and student assessment
- Quiz publications are course-instance specific for precise analytics
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
from course_management.domain.entities.course import Course, DifficultyLevel, DurationUnit
from course_management.domain.entities.enrollment import EnrollmentRequest, BulkEnrollmentRequest
from course_management.domain.entities.feedback import CourseFeedback, StudentFeedback, FeedbackResponse
from course_management.domain.interfaces.course_service import ICourseService
from course_management.domain.interfaces.enrollment_service import IEnrollmentService
from course_management.domain.interfaces.feedback_service import IFeedbackService

# Infrastructure
from course_management.infrastructure.container import Container

# Organization security middleware
sys.path.insert(0, '/app/shared')
from auth.organization_middleware import OrganizationAuthorizationMiddleware, get_organization_context, require_organization_role
from cache.organization_redis_cache import OrganizationCacheManager

# Custom exceptions
from exceptions import (
    CourseManagementException, CourseNotFoundException, CourseValidationException,
    EnrollmentException, FeedbackException, ProgressException, DatabaseException,
    AuthorizationException, ValidationException, EmailServiceException,
    QuizManagementException
)

# API Models (DTOs - following Single Responsibility)
class CourseCreateRequest(BaseModel):
    """
    Data Transfer Object for course creation requests.

    This DTO encapsulates all the necessary information for creating a new course
    in the educational platform. It implements strict validation to ensure data
    integrity and provides clear educational workflow structure.

    EDUCATIONAL WORKFLOW:
    1. Instructor provides course metadata and structure
    2. System validates educational standards (duration, difficulty)
    3. Course is created in draft state pending content development
    4. Analytics tracking begins for course development metrics

    VALIDATION STRATEGY:
    - Title length ensures readable course catalogs and SEO optimization
    - Description length supports comprehensive course summaries
    - Difficulty levels align with educational taxonomy standards
    - Duration estimates help with course scheduling and student planning
    - Price validation supports both free and premium course models

    BUSINESS RULES:
    - All courses start as unpublished drafts for content development
    - Tags enable categorization and discovery in course catalogs
    - Duration units support flexible course planning (micro-courses to full programs)
    - Category classification improves course recommendation algorithms

    COURSE CREATION MODES (v3.3.1):
    The platform supports two flexible course creation patterns to accommodate different user types:

    MODE 1 - STANDALONE COURSE CREATION (Single Instructors):
    - Individual instructors can create courses WITHOUT organizational hierarchy
    - organization_id, project_id, track_id are all null/optional
    - Course is directly accessible to the instructor for content development
    - Use Case: Independent instructors, freelance educators, simple course creation
    - Example: A Python instructor creates "Python for Beginners" without any org context

    MODE 2 - ORGANIZATIONAL COURSE CREATION (Corporate Training):
    - Corporate/enterprise users create courses WITHIN organizational structures
    - Courses can belong to: Organization → Project → Track hierarchy
    - Organizational fields are optional to provide maximum flexibility
    - Courses can be added to tracks later via track_classes junction table
    - Use Case: Corporate training programs, university courses, structured learning paths
    - Example: TechCorp creates "Python for Data Science" in their "Data Analytics" track

    HYBRID APPROACH:
    - Courses can start as standalone and be added to org hierarchy later
    - Instructors can create courses at any level (standalone, org-level, project-level, track-level)
    - Track association uses junction table for many-to-many relationships
    """
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    category: Optional[str] = None
    difficulty_level: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")
    estimated_duration: Optional[int] = Field(None, ge=1)
    duration_unit: str = Field(default="weeks", pattern="^(hours|days|weeks|months)$")
    price: float = Field(default=0.0, ge=0)
    tags: List[str] = Field(default_factory=list)

    # Optional organizational context (new in v3.3.1)
    organization_id: Optional[str] = Field(
        None,
        description="Organization ID (optional - for corporate training programs)"
    )
    project_id: Optional[str] = Field(
        None,
        description="Project ID (optional - for project-based courses)"
    )
    track_id: Optional[str] = Field(
        None,
        description="Track ID (optional - for track-based learning paths)"
    )

class CourseUpdateRequest(BaseModel):
    """
    Data Transfer Object for course update requests.

    BUSINESS CONTEXT (v3.3.1):
    Allows updating course metadata AND organizational associations.
    Instructors can move courses between organizations/projects/tracks or
    disassociate courses from organizational hierarchy entirely.

    FLEXIBLE UPDATE PATTERNS:
    - Update only course metadata (title, description, etc.)
    - Update only organizational associations
    - Update both metadata and organizational context
    - Remove organizational associations (set to null)
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    category: Optional[str] = None
    difficulty_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    estimated_duration: Optional[int] = Field(None, ge=1)
    duration_unit: Optional[str] = Field(None, pattern="^(hours|days|weeks|months)$")
    price: Optional[float] = Field(None, ge=0)
    tags: Optional[List[str]] = None

    # Optional organizational context updates (new in v3.3.1)
    organization_id: Optional[str] = Field(None, description="Update organization association")
    project_id: Optional[str] = Field(None, description="Update project association")
    track_id: Optional[str] = Field(None, description="Update track association")

class CourseResponse(BaseModel):
    """
    Data Transfer Object for course API responses.

    BUSINESS CONTEXT (v3.3.1):
    Returns complete course information including optional organizational context.
    Clients can use organizational fields to determine if course belongs to
    organizational hierarchy or is standalone.
    """
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

    # Optional organizational context (new in v3.3.1)
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    track_id: Optional[str] = None

# NOTE: CourseFeedbackRequest DTO has been moved to api/feedback_endpoints.py (SOLID refactoring)

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
    """
    FastAPI lifespan event handler for Course Management Service.

    This context manager handles the complete lifecycle of the course management service,
    ensuring proper initialization and cleanup of all educational platform components.

    STARTUP SEQUENCE:
    1. Initialize dependency injection container with Hydra configuration
    2. Establish database connections with connection pooling for educational scale
    3. Configure email service for course notifications and enrollment confirmations
    4. Initialize analytics integration for course performance tracking
    5. Set up background task queues for bulk enrollment operations
    6. Verify integration with other platform services (user management, content storage)

    EDUCATIONAL PLATFORM INTEGRATION:
    - Database connections support high-concurrency course operations
    - Email service enables automated enrollment confirmations and course updates
    - Analytics integration provides real-time insights into course performance
    - Service mesh connectivity ensures reliable inter-service communication

    SHUTDOWN SEQUENCE:
    1. Gracefully drain in-flight requests to preserve data integrity
    2. Close database connections to prevent connection leaks
    3. Flush email queues to ensure no notifications are lost
    4. Save any pending analytics data to maintain course metrics continuity
    5. Clean up background tasks and temporary resources

    ERROR HANDLING:
    - Startup failures are logged with detailed error information
    - Service health checks validate successful initialization
    - Graceful degradation for non-critical component failures
    - Automatic retry mechanisms for transient initialization issues
    """
    # Startup - container stored in app.state for access by route handlers
    logging.info("Initializing Course Management Service...")
    if not current_config:
        logging.warning("No configuration provided, using default config")
    app.state.container = Container(current_config or {})
    await app.state.container.initialize()

    # Initialize Video DAO with database pool
    try:
        from data_access.course_video_dao import CourseVideoDAO
        from api import video_endpoints
        video_endpoints.video_dao = CourseVideoDAO(app.state.container._connection_pool)
        logging.info("Video DAO initialized successfully")
    except Exception as e:
        logging.warning(f"Failed to initialize Video DAO: {e}")

    logging.info("Course Management Service initialized successfully")

    yield

    # Shutdown
    logging.info("Shutting down Course Management Service...")
    if hasattr(app.state, 'container') and app.state.container:
        await app.state.container.cleanup()
    logging.info("Course Management Service shutdown complete")

def create_app(config: DictConfig) -> FastAPI:
    """
    Application factory for Course Management Service following SOLID principles.
    
    This factory creates a fully configured FastAPI application with all necessary
    middleware, exception handlers, and educational workflow endpoints. The design
    follows the Open/Closed principle allowing extension without modification.
    
    ARCHITECTURAL PATTERNS:
    - Factory Pattern: Centralized application configuration and setup
    - Dependency Injection: Service dependencies injected via FastAPI's DI system
    - Exception Mapping: Configurable exception-to-HTTP status code mapping
    - Middleware Chain: CORS, authentication, logging, and error handling
    
    EDUCATIONAL WORKFLOW SUPPORT:
    - Course lifecycle management endpoints (create, publish, manage)
    - Student enrollment and access control endpoints
    - Bi-directional feedback collection and analysis endpoints
    - Quiz management and publication control endpoints
    - Analytics integration for course performance tracking
    
    CROSS-CUTTING CONCERNS:
    - CORS middleware enables frontend integration across domains
    - Centralized exception handling provides consistent error responses
    - Request/response logging for audit trails and debugging
    - Health check endpoint for service monitoring and load balancing
    
    EXTENSIBILITY DESIGN:
    - New endpoints can be added without modifying existing code
    - Exception mapping is configurable and extensible
    - Middleware stack can be extended through configuration
    - Service dependencies are injected, enabling easy testing and mocking
    
    SECURITY CONSIDERATIONS:
    - CORS configuration allows controlled cross-origin access
    - Exception handlers prevent sensitive information leakage
    - Request validation ensures data integrity
    - Authentication middleware integration for protected endpoints
    """
    global current_config
    current_config = config
    
    app = FastAPI(
        title="Course Management Service",
        description="Microservice for managing courses, enrollments, and feedback",
        version="2.0.0",
        lifespan=lifespan
    )
    
    # Organization security middleware (must be added before CORS)
    app.add_middleware(
        OrganizationAuthorizationMiddleware,
        config=config
    )
    
    # CORS middleware - Security: Use environment-configured origins
    # Never use wildcard (*) in production - enables CSRF attacks
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://localhost:3000,https://localhost:3001').split(',')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Exception type to HTTP status code mapping (Open/Closed Principle)
    EXCEPTION_STATUS_MAPPING = {
        ValidationException: 400,
        CourseValidationException: 400,
        AuthorizationException: 403,
        CourseNotFoundException: 404,
        EnrollmentException: 422,
        FeedbackException: 422,
        ProgressException: 422,
        QuizManagementException: 422,
        EmailServiceException: 500,
        DatabaseException: 500,
    }
    
    # Custom exception handler
    @app.exception_handler(CourseManagementException)
    async def course_management_exception_handler(request, exc: CourseManagementException):
        """Handle custom course management exceptions."""
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
        return {"status": "healthy", "service": "course-management", "version": "2.0.0"}

    # Include course API router (SOLID refactoring - extracted from main.py)
    from api.course_endpoints import router as course_router
    app.include_router(course_router)

    # Include enrollment API router (SOLID refactoring - extracted from main.py)
    from api.enrollment_endpoints import router as enrollment_router
    app.include_router(enrollment_router)

    # Include feedback API router (SOLID refactoring - extracted from main.py)
    from api.feedback_endpoints import router as feedback_router
    app.include_router(feedback_router)

    # Include project import API router (SOLID refactoring - extracted from main.py)
    from api.project_import_endpoints import router as project_import_router
    app.include_router(project_import_router)

    # Include course instance API router (SOLID refactoring - extracted from main.py)
    from api.course_instance_endpoints import router as course_instance_router
    app.include_router(course_instance_router)

    # Include sub-project API router (v3.4.0)
    from api.sub_project_endpoints import router as sub_project_router
    app.include_router(sub_project_router)

    # Include video API router (re-enabled after fixing deprecated code)
    from api.video_endpoints import router as video_router
    app.include_router(video_router, tags=["videos"])

    return app

# App will be created in main() after config is loaded
app = None

# Dependency injection helpers
def get_course_service() -> ICourseService:
    """Dependency injection for course service"""
    if not app or not hasattr(app.state, 'container') or not app.state.container:
        raise HTTPException(status_code=500, detail="Service not initialized (main.py)")
    return app.state.container.get_course_service()

def get_enrollment_service() -> IEnrollmentService:
    """Dependency injection for enrollment service"""
    if not app or not hasattr(app.state, 'container') or not app.state.container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return app.state.container.get_enrollment_service()

def get_feedback_service() -> IFeedbackService:
    """Dependency injection for course service"""
    if not app or not hasattr(app.state, 'container') or not app.state.container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return app.state.container.get_feedback_service()

def get_db_pool():
    """Get database connection pool"""
    if not app or not hasattr(app.state, 'container') or not app.state.container:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return app.state.container._connection_pool

# JWT-authenticated user ID extraction (replaced deprecated mock)
# Import from auth module for proper JWT-based authentication
from auth import get_current_user_id

# Video DAO initialization is handled during app startup via video_endpoints module
# The video_dao is set when the app starts and the database pool is available

# NOTE: Course Management Endpoints have been extracted to api/course_endpoints.py (SOLID refactoring)
# NOTE: Enrollment Endpoints have been extracted to api/enrollment_endpoints.py (SOLID refactoring)
# NOTE: Feedback Endpoints have been extracted to api/feedback_endpoints.py (SOLID refactoring)
# NOTE: Project Import Endpoints have been extracted to api/project_import_endpoints.py (SOLID refactoring)
# NOTE: Course Instance Endpoints have been extracted to api/course_instance_endpoints.py (SOLID refactoring)


# Helper functions
def _course_to_response(course: Course) -> CourseResponse:
    """
    Convert domain entity to API response DTO.

    BUSINESS CONTEXT (v3.3.1):
    Maps domain Course entity to API response, including optional organizational
    fields. Clients can determine if course is standalone or organizational
    based on presence of organization_id, project_id, track_id.
    """
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
        tags=course.tags,
        # Optional organizational context (new in v3.3.1)
        organization_id=getattr(course, 'organization_id', None),
        project_id=getattr(course, 'project_id', None),
        track_id=getattr(course, 'track_id', None)
    )

@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """Main entry point using Hydra configuration"""
    global current_config, app

    # Set config BEFORE creating app
    current_config = cfg

    # Setup centralized logging with syslog format
    service_name = os.environ.get('SERVICE_NAME', 'course-management')
    log_level = os.environ.get('LOG_LEVEL', getattr(cfg, 'logging', {}).get('level', 'INFO'))

    logger = setup_docker_logging(service_name, log_level)
    logger.info(f"Starting Course Management Service on port {cfg.server.port}")

    # Create app with loaded configuration
    app = create_app(cfg)

    # Run server with HTTPS/SSL configuration and reduced uvicorn logging to avoid duplicates
    uvicorn.run(
        app,
        host=cfg.server.host,
        port=cfg.server.port,
        log_level="warning",  # Reduce uvicorn log level since we have our own logging
        access_log=False,     # Disable uvicorn access log since we log via middleware
        ssl_keyfile="/app/ssl/nginx-selfsigned.key",
        ssl_certfile="/app/ssl/nginx-selfsigned.crt"
    )

if __name__ == "__main__":
    main()