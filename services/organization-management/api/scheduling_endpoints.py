"""
Instructor Scheduling API Endpoints

BUSINESS CONTEXT:
This module handles time-based scheduling of instructors to courses. It provides
calendar integration, conflict detection, and weekly schedule management for
organizational course delivery.

FEATURES:
- Create time-slot based schedules (day, time, locations, room)
- Automatic conflict detection (same instructor, overlapping times)
- Recurring schedule support (weekly, biweekly, monthly)
- Room and virtual meeting link management
- Weekly schedule views for instructors
- Organization-wide scheduling dashboard

AUTHORIZATION:
- Requires org_admin or project_manager role for schedule creation/modification
- Instructors can view their own schedules
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime, date, time
from uuid import UUID
from pydantic import BaseModel, Field

from auth.jwt_auth import JWTAuthenticator
from app_dependencies import get_current_user, get_container
from api.rbac_endpoints import Permission, verify_permission

# Create router
router = APIRouter(prefix="/api/v1/schedules", tags=["instructor-schedules"])

# ==============================================================================
# REQUEST/RESPONSE MODELS
# ==============================================================================

class ScheduleCreateRequest(BaseModel):
    """Request to create a new instructor schedule"""
    instructor_id: UUID
    course_id: UUID
    location_id: Optional[UUID] = None
    schedule_name: Optional[str] = Field(None, max_length=255)

    # Time details
    day_of_week: int = Field(..., ge=0, le=6, description="0=Sunday, 6=Saturday")
    start_time: time
    end_time: time

    # Locations details
    room_number: Optional[str] = Field(None, max_length=50)
    building: Optional[str] = Field(None, max_length=100)
    virtual_meeting_link: Optional[str] = None
    meeting_platform: Optional[str] = Field(None, pattern="^(zoom|teams|google_meet|webex|in_person|hybrid)$")

    # Recurrence
    is_recurring: bool = True
    recurrence_pattern: str = Field(default="weekly", pattern="^(weekly|biweekly|monthly|one_time)$")

    # Date range
    effective_from: date
    effective_until: Optional[date] = None

    # Capacity
    max_students: Optional[int] = Field(None, ge=1)
    expected_attendance: Optional[int] = Field(None, ge=1)

    # Notes
    notes: Optional[str] = None
    preparation_notes: Optional[str] = None

class ScheduleUpdateRequest(BaseModel):
    """Request to update an existing schedule"""
    schedule_name: Optional[str] = None
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    room_number: Optional[str] = None
    building: Optional[str] = None
    virtual_meeting_link: Optional[str] = None
    meeting_platform: Optional[str] = None
    effective_from: Optional[date] = None
    effective_until: Optional[date] = None
    status: Optional[str] = Field(None, pattern="^(active|cancelled|completed|suspended)$")
    max_students: Optional[int] = None
    expected_attendance: Optional[int] = None
    notes: Optional[str] = None
    preparation_notes: Optional[str] = None

class ScheduleResponse(BaseModel):
    """Response model for instructor schedule"""
    schedule_id: UUID
    schedule_name: Optional[str]
    instructor_id: UUID
    instructor_name: str
    course_id: UUID
    course_title: str
    day_of_week: int
    day_name: str
    start_time: time
    end_time: time
    time_slot: str
    duration_hours: float
    room_number: Optional[str]
    building: Optional[str]
    meeting_platform: Optional[str]
    virtual_meeting_link: Optional[str]
    is_recurring: bool
    recurrence_pattern: str
    effective_from: date
    effective_until: Optional[date]
    status: str
    max_students: Optional[int]
    expected_attendance: Optional[int]
    # Locations context
    location_id: Optional[UUID]
    location_name: Optional[str]
    location_city: Optional[str]
    timezone: Optional[str]
    # Track context
    track_id: Optional[UUID]
    track_name: Optional[str]
    # Organization context
    organization_id: UUID
    organization_name: str
    created_at: datetime

class ConflictResponse(BaseModel):
    """Response model for schedule conflicts"""
    conflict_schedule_id: UUID
    conflict_course_title: str
    conflict_day_of_week: int
    conflict_start_time: time
    conflict_end_time: time
    conflict_location: Optional[str]
    conflict_room: Optional[str]

class WeeklyScheduleResponse(BaseModel):
    """Response model for weekly schedule summary"""
    instructor_id: UUID
    instructor_name: str
    day_of_week: int
    day_name: str
    sessions_count: int
    total_hours_per_day: float
    daily_schedule: str  # Comma-separated list of sessions

# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@router.post("", response_model=ScheduleResponse)
async def create_schedule(
    request: ScheduleCreateRequest,
    current_user=Depends(get_current_user)
):
    """
    Create a new instructor schedule with conflict detection.

    BUSINESS USE CASE:
    - Schedule instructor teaching sessions
    - Plan semester/term schedules
    - Coordinate room and resource allocation

    CONFLICT DETECTION:
    - Automatically checks for time conflicts
    - Returns detailed conflict information if detected
    - Prevents double-booking instructors

    AUTHORIZATION:
    - Requires MANAGE_SCHEDULES permission
    """
    container = get_container()
    dao = await container.get_organization_dao()

    # Get course to determine organization
    course_query = "SELECT organization_id FROM courses WHERE id = $1"
    course_row = await dao.db_pool.fetchrow(course_query, request.course_id)

    if not course_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    organization_id = course_row['organization_id']
    if not organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Course must be associated with an organization")

    # Verify permission
    await verify_permission(current_user.id, organization_id, Permission.MANAGE_INSTRUCTORS)

    # Check for conflicts
    conflict_query = """
        SELECT * FROM check_schedule_conflict($1, $2, $3, $4, $5, $6, NULL)
    """
    conflicts = await dao.db_pool.fetch(
        conflict_query,
        request.instructor_id,
        request.day_of_week,
        request.start_time,
        request.end_time,
        request.effective_from,
        request.effective_until
    )

    if conflicts:
        conflict_details = [
            ConflictResponse(
                conflict_schedule_id=c['conflict_schedule_id'],
                conflict_course_title=c['conflict_course_title'],
                conflict_day_of_week=c['conflict_day_of_week'],
                conflict_start_time=c['conflict_start_time'],
                conflict_end_time=c['conflict_end_time'],
                conflict_location=c['conflict_location'],
                conflict_room=c['conflict_room']
            )
            for c in conflicts
        ]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Schedule conflict detected",
                "conflicts": [c.dict() for c in conflict_details]
            }
        )

    # Create schedule
    insert_query = """
        INSERT INTO instructor_schedules (
            instructor_id, course_id, organization_id, location_id, schedule_name,
            day_of_week, start_time, end_time,
            room_number, building, virtual_meeting_link, meeting_platform,
            is_recurring, recurrence_pattern,
            effective_from, effective_until,
            status, max_students, expected_attendance,
            notes, preparation_notes, created_by
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, 'active', $17, $18, $19, $20, $21)
        RETURNING id
    """
    schedule_id = await dao.db_pool.fetchval(
        insert_query,
        request.instructor_id, request.course_id, organization_id, request.location_id,
        request.schedule_name, request.day_of_week, request.start_time, request.end_time,
        request.room_number, request.building, request.virtual_meeting_link, request.meeting_platform,
        request.is_recurring, request.recurrence_pattern,
        request.effective_from, request.effective_until,
        request.max_students, request.expected_attendance,
        request.notes, request.preparation_notes, current_user.id
    )

    # Return created schedule
    return await get_schedule(schedule_id, current_user)

@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: UUID,
    current_user=Depends(get_current_user)
):
    """
    Get schedule by ID.

    AUTHORIZATION:
    - Org admins and instructors can view schedules
    """
    container = get_container()
    dao = await container.get_organization_dao()

    query = "SELECT * FROM instructor_schedules_view WHERE schedule_id = $1"
    row = await dao.db_pool.fetchrow(query, schedule_id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    # Verify permission
    organization_id = row['organization_id']
    await verify_permission(current_user.id, organization_id, Permission.VIEW_SCHEDULES)

    return ScheduleResponse(**dict(row))

@router.get("/instructor/{instructor_id}", response_model=List[ScheduleResponse])
async def get_instructor_schedules(
    instructor_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user=Depends(get_current_user)
):
    """
    Get all schedules for an instructor.

    BUSINESS USE CASE:
    - View instructor's teaching calendar
    - Print weekly schedule
    - Identify availability gaps

    QUERY PARAMETERS:
    - start_date: Filter schedules starting from this date
    - end_date: Filter schedules ending before this date
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
    await verify_permission(current_user.id, organization_id, Permission.VIEW_SCHEDULES)

    # Use database function for date filtering
    if start_date and end_date:
        query = "SELECT * FROM get_instructor_schedule($1, $2, $3)"
        rows = await dao.db_pool.fetch(query, instructor_id, start_date, end_date)
    else:
        # Get all active schedules
        query = "SELECT * FROM instructor_schedules_view WHERE instructor_id = $1 AND status = 'active' ORDER BY day_of_week, start_time"
        rows = await dao.db_pool.fetch(query, instructor_id)

    return [ScheduleResponse(**dict(row)) for row in rows]

@router.get("/instructor/{instructor_id}/weekly", response_model=List[WeeklyScheduleResponse])
async def get_instructor_weekly_schedule(
    instructor_id: UUID,
    current_user=Depends(get_current_user)
):
    """
    Get weekly schedule summary for an instructor.

    BUSINESS USE CASE:
    - Quick overview of weekly teaching load
    - Dashboard widget display
    - Printable weekly schedule
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
    await verify_permission(current_user.id, organization_id, Permission.VIEW_SCHEDULES)

    query = "SELECT * FROM instructor_weekly_schedule WHERE instructor_id = $1 ORDER BY day_of_week"
    rows = await dao.db_pool.fetch(query, instructor_id)

    return [WeeklyScheduleResponse(**dict(row)) for row in rows]

@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: UUID,
    request: ScheduleUpdateRequest,
    current_user=Depends(get_current_user)
):
    """
    Update an existing schedule.

    BUSINESS USE CASE:
    - Change room assignments
    - Adjust time slots
    - Update meeting links
    - Modify date ranges

    CONFLICT DETECTION:
    - Automatically checks for conflicts when changing day/time
    """
    container = get_container()
    dao = await container.get_organization_dao()

    # Get existing schedule
    existing = await dao.db_pool.fetchrow(
        "SELECT * FROM instructor_schedules WHERE id = $1",
        schedule_id
    )

    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    organization_id = existing['organization_id']

    # Verify permission
    await verify_permission(current_user.id, organization_id, Permission.MANAGE_INSTRUCTORS)

    # Check for conflicts if time or day changed
    if (request.day_of_week is not None or request.start_time is not None or
        request.end_time is not None or request.effective_from is not None or
        request.effective_until is not None):

        day = request.day_of_week if request.day_of_week is not None else existing['day_of_week']
        start = request.start_time if request.start_time is not None else existing['start_time']
        end = request.end_time if request.end_time is not None else existing['end_time']
        eff_from = request.effective_from if request.effective_from is not None else existing['effective_from']
        eff_until = request.effective_until if request.effective_until is not None else existing['effective_until']

        conflicts = await dao.db_pool.fetch(
            "SELECT * FROM check_schedule_conflict($1, $2, $3, $4, $5, $6, $7)",
            existing['instructor_id'], day, start, end, eff_from, eff_until, schedule_id
        )

        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "Schedule conflict detected", "conflicts": [dict(c) for c in conflicts]}
            )

    # Build update query dynamically
    update_fields = []
    params = [schedule_id]
    param_count = 2

    field_mapping = {
        'schedule_name': request.schedule_name,
        'day_of_week': request.day_of_week,
        'start_time': request.start_time,
        'end_time': request.end_time,
        'room_number': request.room_number,
        'building': request.building,
        'virtual_meeting_link': request.virtual_meeting_link,
        'meeting_platform': request.meeting_platform,
        'effective_from': request.effective_from,
        'effective_until': request.effective_until,
        'status': request.status,
        'max_students': request.max_students,
        'expected_attendance': request.expected_attendance,
        'notes': request.notes,
        'preparation_notes': request.preparation_notes
    }

    for field, value in field_mapping.items():
        if value is not None:
            update_fields.append(f"{field} = ${param_count}")
            params.append(value)
            param_count += 1

    # Always update updated_by and updated_at
    update_fields.append(f"updated_by = ${param_count}")
    params.append(current_user.id)

    if not update_fields:
        # No changes requested
        return await get_schedule(schedule_id, current_user)

    update_query = f"""
        UPDATE instructor_schedules
        SET {', '.join(update_fields)}
        WHERE id = $1
    """
    await dao.db_pool.execute(update_query, *params)

    return await get_schedule(schedule_id, current_user)

@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: UUID,
    current_user=Depends(get_current_user)
):
    """
    Delete a schedule.

    BUSINESS USE CASE:
    - Remove incorrect schedule entry
    - Cancel course session
    - Clean up old schedules

    AUTHORIZATION:
    - Requires MANAGE_INSTRUCTORS permission
    """
    container = get_container()
    dao = await container.get_organization_dao()

    # Get schedule to verify organization
    existing = await dao.db_pool.fetchrow(
        "SELECT organization_id FROM instructor_schedules WHERE id = $1",
        schedule_id
    )

    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    # Verify permission
    await verify_permission(current_user.id, existing['organization_id'], Permission.MANAGE_INSTRUCTORS)

    # Delete schedule
    result = await dao.db_pool.execute(
        "DELETE FROM instructor_schedules WHERE id = $1",
        schedule_id
    )

    if result == "DELETE 0":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    return {"message": "Schedule deleted successfully"}

@router.post("/check-conflicts", response_model=List[ConflictResponse])
async def check_schedule_conflicts(
    request: ScheduleCreateRequest,
    current_user=Depends(get_current_user)
):
    """
    Check for schedule conflicts without creating a schedule.

    BUSINESS USE CASE:
    - Pre-validation before creating schedule
    - UI real-time conflict checking
    - Planning assistance

    RETURNS:
    - Empty list if no conflicts
    - List of conflicting schedules if conflicts exist
    """
    container = get_container()
    dao = await container.get_organization_dao()

    conflicts = await dao.db_pool.fetch(
        "SELECT * FROM check_schedule_conflict($1, $2, $3, $4, $5, $6, NULL)",
        request.instructor_id,
        request.day_of_week,
        request.start_time,
        request.end_time,
        request.effective_from,
        request.effective_until
    )

    return [ConflictResponse(**dict(c)) for c in conflicts]
