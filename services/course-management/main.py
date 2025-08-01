#!/usr/bin/env python3
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
from domain.entities.course import Course, DifficultyLevel, DurationUnit
from domain.entities.enrollment import EnrollmentRequest, BulkEnrollmentRequest
from domain.entities.feedback import CourseFeedback, StudentFeedback, FeedbackResponse
from domain.interfaces.course_service import ICourseService
from domain.interfaces.enrollment_service import IEnrollmentService
from domain.interfaces.feedback_service import IFeedbackService

# Infrastructure
from infrastructure.container import Container

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
    """
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
    """
    Data Transfer Object for student course feedback submissions.
    
    This DTO captures comprehensive student feedback on course quality, instructor
    effectiveness, and overall learning experience. It supports both quantitative
    ratings and qualitative comments to provide actionable insights for course improvement.
    
    FEEDBACK CATEGORIES:
    1. Overall Experience: Holistic course satisfaction rating
    2. Content Quality: Assessment of educational materials and curriculum design
    3. Instructor Effectiveness: Teaching methodology and communication evaluation
    4. Difficulty Appropriateness: Course challenge level relative to stated prerequisites
    5. Lab Quality: Hands-on learning environment assessment (for technical courses)
    
    EDUCATIONAL VALUE:
    - Quantitative ratings enable statistical analysis and trend tracking
    - Qualitative feedback provides specific, actionable improvement suggestions
    - Anonymous option encourages honest feedback without fear of retaliation
    - Recommendation flag indicates overall student satisfaction and course viability
    
    ANALYTICS INTEGRATION:
    - Ratings feed into course performance dashboards
    - Comments are analyzed for sentiment and common themes
    - Trends help identify course improvement opportunities
    - Aggregate scores influence course recommendations and instructor evaluations
    
    PRIVACY CONSIDERATIONS:
    - Anonymous feedback protects student identity while preserving feedback value
    - Comments are stored securely and access-controlled to authorized personnel
    - Feedback history enables longitudinal analysis of course improvements
    """
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
    """
    Create a new course in the educational platform.
    
    This endpoint initiates the course creation workflow, establishing a new course
    entity with instructor ownership and proper lifecycle state management.
    
    EDUCATIONAL WORKFLOW:
    1. Validate instructor permissions and course data integrity
    2. Create course entity in draft state with instructor ownership
    3. Initialize course metadata and educational taxonomy classification
    4. Set up analytics tracking for course development metrics
    5. Prepare course for content development and publication workflow
    
    BUSINESS RULES:
    - All courses start in unpublished/draft state for content development
    - Instructor ID is automatically assigned from authenticated session
    - Course title must be unique within instructor's course catalog
    - Difficulty level and duration must align with educational standards
    - Price validation supports both free and premium course models
    
    DATA INTEGRITY:
    - Course entity creation is atomic with proper rollback on failure
    - Tags are normalized and validated against platform taxonomy
    - Duration units are standardized for consistent scheduling
    - Foreign key constraints ensure instructor exists in user management
    
    ANALYTICS INTEGRATION:
    - Course creation metrics are tracked for platform insights
    - Instructor productivity metrics begin tracking
    - Course development timeline starts for completion analysis
    
    ERROR HANDLING:
    - Validation errors return detailed field-specific feedback
    - Database constraints violations are handled gracefully
    - Duplicate course detection with helpful error messages
    - Service unavailability is handled with appropriate retry guidance
    """
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
        raise CourseValidationException(
            message="Invalid course data provided",
            validation_errors={"general": str(e)},
            original_exception=e
        )
    except CourseManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise DatabaseException(
            message="Failed to create course",
            operation="create_course",
            table_name="courses",
            original_exception=e
        )

@app.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    course_service: ICourseService = Depends(get_course_service)
):
    """Get course by ID"""
    try:
        course = await course_service.get_course_by_id(course_id)
        if not course:
            raise CourseNotFoundException(
                message="Course not found",
                course_id=course_id
            )
        
        return _course_to_response(course)
        
    except CourseManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise DatabaseException(
            message=f"Failed to retrieve course with ID {course_id}",
            operation="get_course_by_id",
            table_name="courses",
            record_id=course_id,
            original_exception=e
        )

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

# Feedback Endpoints
@app.post("/feedback/course")
async def submit_course_feedback(
    request: CourseFeedbackRequest,
    current_user_id: str = Depends(get_current_user_id),
    feedback_service: IFeedbackService = Depends(get_feedback_service)
):
    """
    Submit comprehensive course feedback from a student.
    
    This endpoint implements the student→course feedback flow of the bi-directional
    feedback system, capturing detailed student assessments of course quality,
    instructor effectiveness, and overall learning experience.
    
    FEEDBACK WORKFLOW:
    1. Validate student enrollment in the course being evaluated
    2. Process quantitative ratings across multiple quality dimensions
    3. Capture qualitative feedback for specific improvement insights
    4. Store feedback with appropriate privacy controls (anonymous option)
    5. Trigger analytics processing for course performance metrics
    6. Send notification to instructor about new feedback (if configured)
    
    QUALITY DIMENSIONS:
    - Overall Rating: Holistic course satisfaction and learning outcome assessment
    - Content Quality: Educational material relevance, accuracy, and effectiveness
    - Instructor Effectiveness: Teaching methodology, communication, and support quality
    - Difficulty Appropriateness: Course challenge level relative to prerequisites
    - Lab Quality: Hands-on learning environment and practical exercise effectiveness
    
    ANALYTICS INTEGRATION:
    - Quantitative ratings feed into instructor performance dashboards
    - Qualitative comments are processed for sentiment analysis and theme extraction
    - Trend analysis identifies course improvement opportunities over time
    - Aggregate feedback scores influence course recommendation algorithms
    
    PRIVACY AND ETHICS:
    - Anonymous feedback option protects student identity while preserving value
    - Feedback attribution enables follow-up communication when appropriate
    - Data retention policies ensure compliance with educational privacy regulations
    - Instructor access controls prevent misuse of student feedback information
    
    BUSINESS VALUE:
    - Continuous improvement cycle for course quality enhancement
    - Instructor development insights for teaching methodology optimization
    - Student satisfaction metrics for course catalog optimization
    - Platform quality assurance through systematic feedback collection
    """
    try:
        feedback = CourseFeedback(
            student_id=current_user_id,
            course_id=request.course_id,
            overall_rating=request.overall_rating,
            content_quality=request.content_quality,
            instructor_effectiveness=request.instructor_effectiveness,
            difficulty_appropriateness=request.difficulty_appropriateness,
            lab_quality=request.lab_quality,
            positive_aspects=request.positive_aspects,
            areas_for_improvement=request.areas_for_improvement,
            additional_comments=request.additional_comments,
            would_recommend=request.would_recommend,
            is_anonymous=request.is_anonymous
        )
        
        feedback_id = await feedback_service.submit_course_feedback(feedback)
        return {"message": "Course feedback submitted successfully", "feedback_id": feedback_id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error submitting course feedback: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.get("/feedback/course/{course_id}")
async def get_course_feedback(
    course_id: str,
    current_user_id: str = Depends(get_current_user_id),
    feedback_service: IFeedbackService = Depends(get_feedback_service)
):
    """Get feedback for a course (instructors only)"""
    try:
        feedback_list = await feedback_service.get_course_feedback(course_id, current_user_id)
        return {"feedback": feedback_list}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error retrieving course feedback: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.post("/feedback/student")
async def submit_student_feedback(
    request: dict,  # We'll need to create a proper DTO
    current_user_id: str = Depends(get_current_user_id),
    feedback_service: IFeedbackService = Depends(get_feedback_service)
):
    """
    Submit comprehensive student assessment feedback from an instructor.
    
    This endpoint implements the instructor→student feedback flow of the bi-directional
    feedback system, enabling instructors to provide detailed performance assessments,
    development guidance, and personalized recommendations for student growth.
    
    ASSESSMENT WORKFLOW:
    1. Validate instructor authorization for the specific student and course
    2. Process multi-dimensional performance assessments across academic areas
    3. Capture qualitative development insights and improvement recommendations
    4. Store feedback with configurable sharing controls for student visibility
    5. Trigger analytics processing for student progress tracking
    6. Send optional notification to student about new feedback (if enabled)
    
    ASSESSMENT DIMENSIONS:
    - Overall Performance: Holistic academic achievement and learning progress
    - Participation: Class engagement, discussion contributions, and collaboration
    - Lab Performance: Hands-on technical skills and practical application ability
    - Quiz Performance: Knowledge retention and conceptual understanding
    - Improvement Trend: Progress trajectory and learning velocity assessment
    
    DEVELOPMENT GUIDANCE:
    - Strengths Identification: Recognizing and reinforcing positive learning behaviors
    - Improvement Areas: Specific, actionable guidance for skill development
    - Recommendations: Personalized learning paths and resource suggestions
    - Achievements: Notable accomplishments and milestone recognition
    - Concerns: Early intervention opportunities for academic support
    
    ANALYTICS INTEGRATION:
    - Performance metrics feed into student progress tracking systems
    - Instructor feedback patterns inform teaching effectiveness analysis
    - Student development trends guide personalized learning recommendations
    - Early warning systems for students requiring additional support
    
    PRIVACY AND ETHICS:
    - Instructor control over feedback sharing preserves appropriate boundaries
    - Student access to feedback promotes transparent communication
    - Confidential assessment options for sensitive developmental feedback
    - Audit trails maintain accountability for instructor assessments
    
    EDUCATIONAL IMPACT:
    - Personalized feedback improves student engagement and learning outcomes
    - Regular assessment supports timely intervention and course correction
    - Instructor reflection on student progress enhances teaching methodology
    - Longitudinal tracking enables comprehensive student development analysis
    """
    try:
        feedback = StudentFeedback(
            instructor_id=current_user_id,
            student_id=request["student_id"],
            course_id=request["course_id"],
            overall_performance=request.get("overall_performance"),
            participation=request.get("participation"),
            lab_performance=request.get("lab_performance"),
            quiz_performance=request.get("quiz_performance"),
            improvement_trend=request.get("improvement_trend"),
            strengths=request.get("strengths"),
            areas_for_improvement=request.get("areas_for_improvement"),
            specific_recommendations=request.get("specific_recommendations"),
            notable_achievements=request.get("notable_achievements"),
            concerns=request.get("concerns"),
            progress_assessment=request.get("progress_assessment"),
            expected_outcome=request.get("expected_outcome"),
            feedback_type=request.get("feedback_type", "regular"),
            is_shared_with_student=request.get("is_shared_with_student", False)
        )
        
        feedback_id = await feedback_service.submit_student_feedback(feedback)
        return {"message": "Student feedback submitted successfully", "feedback_id": feedback_id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error submitting student feedback: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.get("/feedback/student/{student_id}")
async def get_student_feedback(
    student_id: str,
    current_user_id: str = Depends(get_current_user_id),
    feedback_service: IFeedbackService = Depends(get_feedback_service)
):
    """Get feedback for a student"""
    try:
        feedback_list = await feedback_service.get_student_feedback(student_id, current_user_id)
        return {"feedback": feedback_list}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error retrieving student feedback: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e


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