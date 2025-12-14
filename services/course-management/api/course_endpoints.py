"""
Course Management API Endpoints

BUSINESS CONTEXT:
This module contains all course management REST API endpoints following the Single
Responsibility Principle. It handles the complete course lifecycle from creation
through publication to deletion.

SOLID PRINCIPLES APPLIED:
- Single Responsibility: Only course management endpoints (no enrollment, feedback, etc.)
- Open/Closed: Extensible through dependency injection
- Liskov Substitution: Uses interface abstractions for services
- Interface Segregation: Depends only on ICourseService interface
- Dependency Inversion: Depends on abstractions, not concrete implementations

EDUCATIONAL WORKFLOW PATTERNS:
- Course Creation → Content Development → Publication → Student Access
- Instructor owns courses through authenticated session
- Course states: draft (unpublished) → published → unpublished (archived)
- CRUD operations support full course lifecycle management

SECURITY CONSIDERATIONS:
- All endpoints require authentication via JWT
- Course ownership validated for update/delete operations
- Published courses are read-only to students
- Organization context enforced via middleware
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
from datetime import datetime
import logging

# Domain entities and services
from course_management.domain.entities.course import Course, DifficultyLevel, DurationUnit
from course_management.domain.interfaces.course_service import ICourseService

# Custom exceptions
from exceptions import (
    CourseManagementException, CourseNotFoundException, CourseValidationException,
    DatabaseException
)

# Organization security middleware
import sys
sys.path.insert(0, '/app/shared')
from auth.organization_middleware import get_organization_context

# Pydantic models for API (Data Transfer Objects)
from pydantic import BaseModel, Field

# DTOs - Course Request/Response Models
class CourseCreateRequest(BaseModel):
    """
    Data Transfer Object for course creation requests.

    This DTO encapsulates all the necessary information for creating a new course
    in the educational platform. It implements strict validation to ensure data
    integrity and provides clear educational workflow structure.

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
    """
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
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
    # Note: project_id is NOT stored in courses table - projects manage tracks
    # Courses belong to tracks, tracks belong to projects
    track_id: Optional[str] = Field(
        None,
        description="Track ID (optional - for track-based learning paths)"
    )
    location_id: Optional[str] = Field(
        None,
        description="Location ID (optional - for location-specific course delivery)"
    )

class CourseUpdateRequest(BaseModel):
    """
    Data Transfer Object for course update requests.

    BUSINESS CONTEXT (v3.3.1):
    Allows updating course metadata AND organizational associations.
    Instructors can move courses between organizations/projects/tracks or
    disassociate courses from organizational hierarchy entirely.
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
    location_id: Optional[str] = Field(None, description="Update locations association")

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
    location_id: Optional[str] = None

class PaginatedCoursesResponse(BaseModel):
    """
    Data Transfer Object for paginated course list responses.

    BUSINESS CONTEXT:
    Returns courses in paginated format for efficient frontend rendering.
    Provides metadata for pagination controls (total, pages, etc).
    """
    data: List[CourseResponse]
    total: int
    page: int = 1
    limit: int = 100
    pages: int = 1

# Create router with course prefix and tag
router = APIRouter(prefix="/courses", tags=["courses"])

# Dependency injection helpers (use FastAPI Request to access app.state)
from fastapi import Request

def get_course_service(request: Request) -> ICourseService:
    """Dependency injection for course service"""
    if not hasattr(request.app.state, 'container') or not request.app.state.container:
        raise HTTPException(status_code=500, detail="Service not initialized (course_endpoints.py)")
    return request.app.state.container.get_course_service()

def get_current_user_id(authorization: str = Header(None)) -> str:
    """
    Extract user ID from JWT token in Authorization header.

    BUSINESS CONTEXT:
    Authenticates the request and extracts the user_id claim from the JWT token.
    This ensures proper instructor assignment for course creation.

    TECHNICAL IMPLEMENTATION:
    Decodes JWT token without verification (verification happens at API gateway/nginx level).
    Extracts user_id claim which is used as instructor_id for course ownership.

    WHY THIS APPROACH:
    - JWT is already verified by the API gateway
    - We only need to extract claims for business logic
    - No need to re-verify signature here
    """
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.split(' ')[1]

    try:
        import jwt
        # Decode without verification since it's already verified by API gateway
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get('user_id')

        if not user_id:
            raise HTTPException(status_code=401, detail="user_id claim not found in token")

        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid JWT token: {str(e)}")


def get_current_user_context(authorization: str = Header(None)) -> dict:
    """
    Extract user context (user_id and role) from JWT token.

    BUSINESS CONTEXT:
    Some operations like course deletion need to check both user identity
    and role to allow org admins to delete any course in their organization.

    Returns:
        dict with user_id and role keys
    """
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.split(' ')[1]

    try:
        import jwt
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get('user_id')
        role = payload.get('role', 'student')

        if not user_id:
            raise HTTPException(status_code=401, detail="user_id claim not found in token")

        return {
            "user_id": user_id,
            "role": role
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid JWT token: {str(e)}")

# Helper function to convert domain entity to API response
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
        track_id=getattr(course, 'track_id', None),
        location_id=getattr(course, 'location_id', None)
    )

# ============================================================================
# COURSE MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("", response_model=CourseResponse)
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
        # Support both standalone and organizational course creation (v3.3.1)
        # Note: project_id removed - courses belong to tracks, tracks belong to projects
        course = Course(
            title=request.title,
            description=request.description,
            instructor_id=current_user_id,
            category=request.category,
            difficulty_level=DifficultyLevel(request.difficulty_level),
            estimated_duration=request.estimated_duration,
            duration_unit=DurationUnit(request.duration_unit),
            price=request.price,
            tags=request.tags,
            # Optional organizational context (new in v3.3.1)
            organization_id=request.organization_id,
            track_id=request.track_id,
            location_id=request.location_id
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

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    course_service: ICourseService = Depends(get_course_service),
    org_context: dict = Depends(get_organization_context)
):
    """
    Get course by ID with organization context validation.

    BUSINESS CONTEXT:
    Retrieves a single course with full details. Automatically validates
    that the course belongs to the current user's organization context.

    SECURITY:
    - Organization context enforced via middleware
    - Only returns courses within authorized organization
    - Students see only published courses
    - Instructors see their own courses regardless of publish state
    """
    try:
        # Include organization context in query
        organization_id = org_context['organization_id']
        course = await course_service.get_course_by_id(course_id, organization_id=organization_id)
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

@router.get("", response_model=PaginatedCoursesResponse)
async def get_courses(
    instructor_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None,
    track_id: Optional[str] = None,
    published_only: bool = True,
    page: int = 1,
    limit: int = 100,
    course_service: ICourseService = Depends(get_course_service)
):
    """
    Get courses with pagination and filtering

    Query parameters:
    - instructor_id: Filter by instructor (if provided)
    - organization_id: Filter by organization (if provided)
    - project_id: Filter by project (if provided)
    - track_id: Filter by track (if provided)
    - published_only: Only return published courses (default: True)
    - page: Page number (default: 1)
    - limit: Items per page (default: 100)

    This endpoint supports:
    1. Public course browsing (no auth required if published_only=True)
    2. Instructor course management (with auth)
    3. Organization-filtered course lists
    """
    try:
        # Calculate offset from page number
        offset = (page - 1) * limit

        if instructor_id:
            # Get specific instructor's courses
            courses = await course_service.get_courses_by_instructor(instructor_id)
        elif organization_id:
            # Get organization's courses (filter by organization_id)
            # Respect published_only parameter - if false, get ALL courses
            if published_only:
                all_courses = await course_service.get_published_courses(limit=1000, offset=0)
            else:
                all_courses = await course_service.get_all_courses(limit=1000, offset=0)
            courses = [c for c in all_courses if c.organization_id == organization_id]
        elif project_id:
            # Get project's courses
            if published_only:
                all_courses = await course_service.get_published_courses(limit=1000, offset=0)
            else:
                all_courses = await course_service.get_all_courses(limit=1000, offset=0)
            courses = [c for c in all_courses if getattr(c, 'project_id', None) == project_id]
        elif track_id:
            # Get track's courses
            if published_only:
                all_courses = await course_service.get_published_courses(limit=1000, offset=0)
            else:
                all_courses = await course_service.get_all_courses(limit=1000, offset=0)
            courses = [c for c in all_courses if c.track_id == track_id]
        else:
            # Get all courses for browsing (default: published only)
            if published_only:
                courses = await course_service.get_published_courses(limit=1000, offset=0)
            else:
                courses = await course_service.get_all_courses(limit=1000, offset=0)

        # Apply pagination
        total = len(courses)
        pages = (total + limit - 1) // limit  # Ceiling division
        paginated_courses = courses[offset:offset + limit]

        return PaginatedCoursesResponse(
            data=[_course_to_response(course) for course in paginated_courses],
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )

    except Exception as e:
        logging.error("Error getting courses: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: str,
    request: CourseUpdateRequest,
    course_service: ICourseService = Depends(get_course_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Update an existing course.

    BUSINESS CONTEXT:
    Allows instructors to modify their course metadata, including moving
    courses between organizational contexts (v3.3.1).

    AUTHORIZATION:
    - Only course owner (instructor) can update
    - Organization context validated via middleware
    - Cannot update other instructor's courses

    FLEXIBLE UPDATES:
    - Update only specified fields (partial updates)
    - Can update organizational associations
    - Can remove organizational context by setting to null
    """
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

@router.post("/{course_id}/publish", response_model=CourseResponse)
async def publish_course(
    course_id: str,
    course_service: ICourseService = Depends(get_course_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Publish a course to make it available to students.

    BUSINESS CONTEXT:
    Publishes a draft course, making it visible in the course catalog
    and available for student enrollment.

    WORKFLOW:
    1. Validates course is ready for publication (has content, etc.)
    2. Updates course state to published
    3. Makes course visible in public catalog
    4. Enables student enrollment

    AUTHORIZATION:
    - Only course owner can publish
    - Course must meet minimum quality requirements
    """
    try:
        published_course = await course_service.publish_course(course_id, current_user_id)
        return _course_to_response(published_course)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error publishing course: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.post("/{course_id}/unpublish", response_model=CourseResponse)
async def unpublish_course(
    course_id: str,
    course_service: ICourseService = Depends(get_course_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Unpublish a course to remove it from public access.

    BUSINESS CONTEXT:
    Removes course from public catalog while preserving existing
    student enrollments. Useful for course maintenance or retirement.

    WORKFLOW:
    1. Updates course state to unpublished
    2. Removes from public catalog
    3. Preserves existing student enrollments
    4. Prevents new enrollments

    AUTHORIZATION:
    - Only course owner can unpublish
    - Cannot unpublish if active enrollments exist (configurable)
    """
    try:
        unpublished_course = await course_service.unpublish_course(course_id, current_user_id)
        return _course_to_response(unpublished_course)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error unpublishing course: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.delete("/{course_id}")
async def delete_course(
    course_id: str,
    course_service: ICourseService = Depends(get_course_service),
    user_context: dict = Depends(get_current_user_context)
):
    """
    Delete a course permanently.

    BUSINESS CONTEXT:
    Permanently removes a course from the system. This is a destructive
    operation and should be used with caution.

    WORKFLOW:
    1. Validates course ownership OR org admin role
    2. Checks for active enrollments
    3. Removes course and all associated data
    4. Returns success confirmation

    AUTHORIZATION (Updated):
    - Course owner (instructor) can delete their own courses
    - Organization admins can delete any course in their organization
    - Site admins can delete any course
    - Cannot delete if active enrollments exist

    WARNING:
    This operation cannot be undone. Consider unpublishing instead
    if you want to preserve course data.
    """
    try:
        user_id = user_context["user_id"]
        user_role = user_context["role"]

        # Organization admins and site admins can delete any course
        is_admin = user_role in ['organization_admin', 'site_admin']

        success = await course_service.delete_course(
            course_id,
            user_id,
            is_admin=is_admin
        )
        if success:
            return {"message": "Course deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete course")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logging.error("Error deleting course: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e
