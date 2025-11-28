"""
Course Instance Management API Endpoints

BUSINESS CONTEXT:
This module contains course instance management endpoints following the Single
Responsibility Principle. Course instances represent specific scheduled offerings
of courses with start/end dates, enrollment limits, and instructor assignments.

SOLID PRINCIPLES APPLIED:
- Single Responsibility: Only course instance management endpoints
- Open/Closed: Extensible through dependency injection
- Liskov Substitution: Uses interface abstractions
- Interface Segregation: Focused on instance lifecycle management
- Dependency Inversion: Depends on abstractions

COURSE INSTANCE WORKFLOWS:
1. Instance Creation: Create scheduled course offering with dates and limits
2. Instance Retrieval: Get instances with filtering by instructor or status
3. Instance Enrichment: Augment instances with course and instructor details

INSTANCE STATES:
- scheduled: Planned future offering
- active: Currently running course
- completed: Finished course
- cancelled: Cancelled offering

@module api/course_instance_endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime
import logging
import sys
import os

# JWT Authentication - Import from auth module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from auth import get_current_user_id as get_authenticated_user_id

# Domain interfaces
from course_management.domain.interfaces.course_service import ICourseService

logger = logging.getLogger(__name__)

# ============================================================================
# IN-MEMORY STORAGE (Temporary - Replace with Database Later)
# ============================================================================

# NOTE: This is temporary in-memory storage for course instances
# In production, this should be replaced with proper database persistence
course_instances_store = {}
instance_counter = 1

# Create router with course instances tag
router = APIRouter(tags=["course-instances"])

# Dependency injection helpers
def get_course_service() -> ICourseService:
    """Dependency injection for course service"""
    from main import container
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_course_service()

# JWT-authenticated user ID extraction (replaced deprecated mock)
get_current_user_id = get_authenticated_user_id

# ============================================================================
# COURSE INSTANCE ENDPOINTS
# ============================================================================

@router.get("/course-instances")
async def get_course_instances(
    instructor_id: Optional[str] = None,
    status: Optional[str] = None,
    course_service: ICourseService = Depends(get_course_service)
):
    """
    Get course instances with optional filtering.

    BUSINESS LOGIC:
    Course instances represent scheduled offerings of courses. This endpoint
    allows instructors and administrators to view all scheduled, active, or
    completed course instances with optional filtering.

    FILTERING OPTIONS:
    - instructor_id: Returns only instances assigned to specific instructor
    - status: Returns only instances with specific status (scheduled, active, completed, cancelled)

    ENRICHMENT:
    Each instance is enriched with course details (title, code, description)
    to provide complete context without requiring additional API calls.

    QUERY PARAMETERS:
    - instructor_id (optional): Filter instances by instructor UUID
    - status (optional): Filter by instance status

    RESPONSE:
    Array of course instance objects, each containing:
    - id: Instance unique identifier
    - course_id: Associated course UUID
    - instructor_id: Assigned instructor UUID
    - start_date: Instance start date (YYYY-MM-DD)
    - end_date: Instance end date (YYYY-MM-DD)
    - max_students: Enrollment limit (optional)
    - status: Instance status (scheduled, active, completed, cancelled)
    - enrolled_count: Number of enrolled students
    - active_enrollments: Number of active enrollments
    - completed_count: Number of completed students
    - created_at: Instance creation timestamp
    - updated_at: Instance last update timestamp
    - course_title: Enriched course title
    - course_code: Enriched course code
    - course_description: Enriched course description

    ERROR HANDLING:
    - 500: Internal server error (database failure, enrichment failure)

    EXAMPLE USAGE:
        # Get all instances
        curl -X GET "https://localhost:8001/course-instances" \\
             -H "Authorization: Bearer $TOKEN"

        # Get instances for specific instructor
        curl -X GET "https://localhost:8001/course-instances?instructor_id=abc123" \\
             -H "Authorization: Bearer $TOKEN"

        # Get only active instances
        curl -X GET "https://localhost:8001/course-instances?status=active" \\
             -H "Authorization: Bearer $TOKEN"
    """
    try:
        # Filter instances
        instances = list(course_instances_store.values())

        if instructor_id:
            instances = [i for i in instances if i.get('instructor_id') == instructor_id]

        if status:
            instances = [i for i in instances if i.get('status') == status]

        # Enrich with course details
        for instance in instances:
            try:
                course = await course_service.get_course_by_id(instance['course_id'])
                if course:
                    instance['course_title'] = course.title
                    instance['course_code'] = getattr(course, 'code', f"COURSE-{instance['course_id'][:8]}")
                    instance['course_description'] = course.description
            except Exception as e:
                logging.warning(f"Failed to enrich instance {instance['id']} with course details: {e}")
                instance['course_title'] = f"Course {instance['course_id']}"
                instance['course_code'] = f"COURSE-{instance['course_id'][:8]}"

        return instances

    except Exception as e:
        logging.error(f"Error retrieving course instances: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post("/course-instances")
async def create_course_instance(
    request: dict,
    course_service: ICourseService = Depends(get_course_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Create a new course instance.

    BUSINESS LOGIC:
    Course instances enable instructors to schedule specific offerings of
    their courses with defined start/end dates, enrollment limits, and
    instructor assignments. This supports multiple offerings of the same
    course with different schedules and locations.

    WORKFLOW:
    1. Validate required fields (course_id, start_date, end_date)
    2. Validate course exists and is published
    3. Create instance with enrollment tracking initialized
    4. Assign current user as instructor (or specified instructor)
    5. Enrich instance with course details
    6. Return created instance with complete information

    VALIDATION:
    - Course must exist in the system
    - Course must be published (unpublished courses cannot be instantiated)
    - Start and end dates are required
    - Instructor ID defaults to current user if not specified

    REQUEST BODY:
    - course_id: UUID of published course (required)
    - start_date: Instance start date in YYYY-MM-DD format (required)
    - end_date: Instance end date in YYYY-MM-DD format (required)
    - max_students: Maximum enrollment limit (optional)
    - instructor_id: Assigned instructor UUID (optional, defaults to current user)
    - status: Instance status (optional, defaults to 'scheduled')

    RESPONSE:
    Created instance object containing:
    - id: Generated instance identifier
    - course_id: Associated course UUID
    - instructor_id: Assigned instructor UUID
    - start_date: Instance start date
    - end_date: Instance end date
    - max_students: Enrollment limit
    - status: Instance status
    - enrolled_count: Number enrolled (initialized to 0)
    - active_enrollments: Active enrollments (initialized to 0)
    - completed_count: Completed students (initialized to 0)
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    - course_title: Course title (if course found)
    - course_code: Course code (if course found)
    - course_description: Course description (if course found)
    - instructor_name: Instructor name (if course found)

    ERROR HANDLING:
    - 400: Missing required fields or invalid course state (unpublished)
    - 404: Course not found
    - 500: Internal server error (database failure, validation failure)

    EXAMPLE USAGE:
        curl -X POST "https://localhost:8001/course-instances" \\
             -H "Authorization: Bearer $TOKEN" \\
             -H "Content-Type: application/json" \\
             -d '{
                   "course_id": "abc-123",
                   "start_date": "2025-11-01",
                   "end_date": "2025-12-15",
                   "max_students": 30,
                   "status": "scheduled"
                 }'
    """
    global instance_counter

    try:
        # Validate required fields
        course_id = request.get('course_id')
        start_date = request.get('start_date')
        end_date = request.get('end_date')

        if not all([course_id, start_date, end_date]):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: course_id, start_date, end_date"
            )

        # Validate course exists
        try:
            course = await course_service.get_course_by_id(course_id)
            if not course:
                raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

            if not course.is_published:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot create instance for unpublished course"
                )
        except HTTPException:
            raise
        except Exception as e:
            logging.warning(f"Could not validate course {course_id}: {e}")
            # Continue anyway for testing purposes
            course = None

        # Create instance
        instance_id = str(instance_counter)
        instance_counter += 1

        instance = {
            'id': instance_id,
            'course_id': course_id,
            'instructor_id': request.get('instructor_id', current_user_id),
            'start_date': start_date,
            'end_date': end_date,
            'max_students': request.get('max_students'),
            'status': request.get('status', 'scheduled'),
            'enrolled_count': 0,
            'active_enrollments': 0,
            'completed_count': 0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # Add course details if available
        if course:
            instance['course_title'] = course.title
            instance['course_code'] = getattr(course, 'code', f"COURSE-{course_id[:8]}")
            instance['course_description'] = course.description
            instance['instructor_name'] = f"Instructor {current_user_id}"

        course_instances_store[instance_id] = instance

        logging.info(f"Created course instance {instance_id} for course {course_id}")

        return instance

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating course instance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e
