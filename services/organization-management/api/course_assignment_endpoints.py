"""
Course-Instructor Assignment API Endpoints

BUSINESS CONTEXT:
This module handles assigning instructors to specific courses (course-level assignments),
which is different from track-level or locations-level assignments. This enables granular
control over which instructor teaches which course.

FEATURES:
- Assign multiple instructors to a course (primary, assistant, guest lecturer, etc.)
- View all instructors assigned to a course
- View all courses assigned to an instructor
- Atomic update operations (replace all assignments)
- Workload tracking and analytics

AUTHORIZATION:
- Requires org_admin or project_manager role
- Operations are organization-scoped for multi-tenant isolation
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field

from auth.jwt_auth import JWTAuthenticator
from app_dependencies import get_current_user, get_container
from api.rbac_endpoints import Permission, verify_permission

# Create router
router = APIRouter(prefix="/api/v1/courses", tags=["course-assignments"])

# ==============================================================================
# REQUEST/RESPONSE MODELS
# ==============================================================================

class CourseInstructorAssignmentRequest(BaseModel):
    """Request to assign an instructor to a course"""
    instructor_id: UUID
    assigned_role: str = Field(default="primary", pattern="^(primary|assistant|substitute|guest_lecturer|co_instructor)$")
    responsibilities: Optional[str] = None
    teaching_hours_per_week: Optional[float] = Field(None, ge=0, le=168)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class UpdateCourseInstructorsRequest(BaseModel):
    """Request to update all instructors for a course (atomic replacement)"""
    instructor_assignments: List[CourseInstructorAssignmentRequest]

class CourseInstructorResponse(BaseModel):
    """Response model for course-instructor assignment"""
    assignment_id: UUID
    course_id: UUID
    course_title: str
    instructor_id: UUID
    instructor_name: str
    instructor_email: str
    assigned_role: str
    status: str
    responsibilities: Optional[str]
    teaching_hours_per_week: Optional[float]
    start_date: Optional[date]
    end_date: Optional[date]
    assigned_at: datetime
    # Optional course context
    track_id: Optional[UUID]
    track_name: Optional[str]
    location_id: Optional[UUID]
    location_name: Optional[str]
    organization_id: UUID
    organization_name: str

class InstructorCourseListResponse(BaseModel):
    """Response listing an instructor's course assignments"""
    instructor_id: UUID
    instructor_name: str
    total_courses: int
    total_teaching_hours: Optional[float]
    course_assignments: List[CourseInstructorResponse]

# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@router.get("/{course_id}/instructors", response_model=List[CourseInstructorResponse])
async def get_course_instructors(
    course_id: UUID,
    include_inactive: bool = False,
    current_user=Depends(get_current_user)
):
    """
    Get all instructors assigned to a course.

    BUSINESS USE CASE:
    - View teaching team for a course
    - Display instructor information on course pages
    - Administrative course management

    QUERY PARAMETERS:
    - include_inactive: Include inactive assignments (default: false)
    """
    container = get_container()
    dao = await container.get_organization_dao()

    # Get course to determine organization and verify permissions
    course_query = "SELECT organization_id FROM courses WHERE id = $1"
    course_row = await dao.db_pool.fetchrow(course_query, course_id)

    if not course_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    organization_id = course_row['organization_id']
    if not organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Course is not associated with an organization")

    # Verify permission
    await verify_permission(current_user.id, organization_id, Permission.VIEW_COURSES)

    # Get course instructor assignments
    status_filter = "" if include_inactive else "AND cia.status = 'active'"
    query = f"""
        SELECT * FROM course_instructor_assignments_view
        WHERE course_id = $1 {status_filter}
        ORDER BY
            CASE assigned_role
                WHEN 'primary' THEN 1
                WHEN 'co_instructor' THEN 2
                WHEN 'assistant' THEN 3
                WHEN 'substitute' THEN 4
                WHEN 'guest_lecturer' THEN 5
                ELSE 6
            END,
            assigned_at
    """

    rows = await dao.db_pool.fetch(query, course_id)

    return [
        CourseInstructorResponse(
            assignment_id=row['assignment_id'],
            course_id=row['course_id'],
            course_title=row['course_title'],
            instructor_id=row['instructor_id'],
            instructor_name=row['instructor_name'],
            instructor_email=row['instructor_email'],
            assigned_role=row['assigned_role'],
            status=row['assignment_status'],
            responsibilities=row['responsibilities'],
            teaching_hours_per_week=row['teaching_hours_per_week'],
            start_date=row['start_date'],
            end_date=row['end_date'],
            assigned_at=row['assigned_at'],
            track_id=row['track_id'],
            track_name=row['track_name'],
            location_id=row['location_id'],
            location_name=row['location_name'],
            organization_id=row['organization_id'],
            organization_name=row['organization_name']
        )
        for row in rows
    ]

@router.put("/{course_id}/instructors", response_model=List[CourseInstructorResponse])
async def update_course_instructors(
    course_id: UUID,
    request: UpdateCourseInstructorsRequest,
    current_user=Depends(get_current_user)
):
    """
    Update all instructor assignments for a course (atomic replacement).

    BUSINESS USE CASE:
    - Assign teaching team to a course
    - Update instructor roles for a semester
    - Replace instructors when team changes

    TRANSACTION GUARANTEE:
    - All existing assignments are removed
    - All new assignments are created
    - Operation is atomic (all or nothing)

    AUTHORIZATION:
    - Requires MANAGE_INSTRUCTORS permission
    """
    container = get_container()
    dao = await container.get_organization_dao()

    # Get course to determine organization
    course_query = "SELECT organization_id FROM courses WHERE id = $1"
    course_row = await dao.db_pool.fetchrow(course_query, course_id)

    if not course_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    organization_id = course_row['organization_id']
    if not organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Course is not associated with an organization")

    # Verify permission
    await verify_permission(current_user.id, organization_id, Permission.MANAGE_INSTRUCTORS)

    # Validate all instructors exist and belong to organization
    for assignment in request.instructor_assignments:
        instructor_query = """
            SELECT 1 FROM course_creator.organization_memberships
            WHERE user_id = $1 AND organization_id = $2
        """
        instructor_exists = await dao.db_pool.fetchrow(instructor_query, assignment.instructor_id, organization_id)
        if not instructor_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Instructor {assignment.instructor_id} not found in organization"
            )

    # Atomic transaction
    async with dao.db_pool.acquire() as conn:
        async with conn.transaction():
            # Delete existing assignments
            await conn.execute(
                "DELETE FROM course_instructor_assignments WHERE course_id = $1 AND organization_id = $2",
                course_id, organization_id
            )

            # Insert new assignments
            for assignment in request.instructor_assignments:
                await conn.execute(
                    """INSERT INTO course_instructor_assignments
                    (course_id, instructor_id, organization_id, assigned_role, status,
                     responsibilities, teaching_hours_per_week, start_date, end_date, assigned_by)
                    VALUES ($1, $2, $3, $4, 'active', $5, $6, $7, $8, $9)""",
                    course_id, assignment.instructor_id, organization_id, assignment.assigned_role,
                    assignment.responsibilities, assignment.teaching_hours_per_week,
                    assignment.start_date, assignment.end_date, current_user.id
                )

    # Return updated assignments
    return await get_course_instructors(course_id, False, current_user)

@router.get("/instructor/{instructor_id}/assignments", response_model=InstructorCourseListResponse)
async def get_instructor_course_assignments(
    instructor_id: UUID,
    current_user=Depends(get_current_user)
):
    """
    Get all course assignments for an instructor.

    BUSINESS USE CASE:
    - View instructor's teaching schedule
    - Workload management
    - Calendar integration

    RETURNS:
    - List of all courses instructor is assigned to
    - Total teaching hours per week
    - Assignment details and responsibilities
    """
    container = get_container()
    dao = await container.get_organization_dao()

    # Get instructor's organization
    instructor_query = "SELECT organization_id FROM course_creator.organization_memberships WHERE user_id = $1 LIMIT 1"
    instructor_row = await dao.db_pool.fetchrow(instructor_query, instructor_id)

    if not instructor_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instructor not found")

    organization_id = instructor_row['organization_id']

    # Verify permission
    await verify_permission(current_user.id, organization_id, Permission.VIEW_INSTRUCTORS)

    # Get instructor details
    instructor_details = await dao.db_pool.fetchrow(
        "SELECT full_name FROM course_creator.users WHERE id = $1",
        instructor_id
    )

    # Get course assignments
    query = """
        SELECT * FROM course_instructor_assignments_view
        WHERE instructor_id = $1 AND assignment_status = 'active'
        ORDER BY course_title
    """
    rows = await dao.db_pool.fetch(query, instructor_id)

    assignments = [
        CourseInstructorResponse(
            assignment_id=row['assignment_id'],
            course_id=row['course_id'],
            course_title=row['course_title'],
            instructor_id=row['instructor_id'],
            instructor_name=row['instructor_name'],
            instructor_email=row['instructor_email'],
            assigned_role=row['assigned_role'],
            status=row['assignment_status'],
            responsibilities=row['responsibilities'],
            teaching_hours_per_week=row['teaching_hours_per_week'],
            start_date=row['start_date'],
            end_date=row['end_date'],
            assigned_at=row['assigned_at'],
            track_id=row['track_id'],
            track_name=row['track_name'],
            location_id=row['location_id'],
            location_name=row['location_name'],
            organization_id=row['organization_id'],
            organization_name=row['organization_name']
        )
        for row in rows
    ]

    total_hours = sum(a.teaching_hours_per_week or 0 for a in assignments)

    return InstructorCourseListResponse(
        instructor_id=instructor_id,
        instructor_name=instructor_details['full_name'],
        total_courses=len(assignments),
        total_teaching_hours=total_hours if total_hours > 0 else None,
        course_assignments=assignments
    )

@router.delete("/{course_id}/instructors/{instructor_id}")
async def remove_instructor_from_course(
    course_id: UUID,
    instructor_id: UUID,
    current_user=Depends(get_current_user)
):
    """
    Remove an instructor from a course.

    BUSINESS USE CASE:
    - Remove instructor due to schedule conflict
    - End temporary assignment
    - Administrative reassignment

    AUTHORIZATION:
    - Requires MANAGE_INSTRUCTORS permission
    """
    container = get_container()
    dao = await container.get_organization_dao()

    # Get course to determine organization
    course_query = "SELECT organization_id FROM courses WHERE id = $1"
    course_row = await dao.db_pool.fetchrow(course_query, course_id)

    if not course_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    organization_id = course_row['organization_id']
    if not organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Course is not associated with an organization")

    # Verify permission
    await verify_permission(current_user.id, organization_id, Permission.MANAGE_INSTRUCTORS)

    # Delete assignment
    result = await dao.db_pool.execute(
        """DELETE FROM course_instructor_assignments
        WHERE course_id = $1 AND instructor_id = $2 AND organization_id = $3""",
        course_id, instructor_id, organization_id
    )

    if result == "DELETE 0":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    return {"message": "Instructor removed from course successfully"}
