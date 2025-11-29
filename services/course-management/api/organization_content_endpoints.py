"""
Organization Content Overview API Endpoints

This module provides API endpoints for retrieving organization content overview,
including projects, direct courses, and track-based courses. It supports the
new workflow where organizations can create courses directly without requiring
projects or tracks.

BUSINESS PURPOSE:
Enable organization administrators and instructors to view all content
(projects and courses) within their organization from a single unified endpoint.

API ENDPOINTS:
- GET /organizations/{org_id}/content - Get organization content overview
- GET /organizations/{org_id}/content/summary - Get content counts summary
- GET /organizations/{org_id}/direct-courses - List direct organization courses
"""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from exceptions import (
    CourseManagementException,
    DatabaseException,
    AuthorizationException,
    CourseNotFoundException
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organizations", tags=["Organization Content"])


# =============================================================================
# Response Models
# =============================================================================

class ContentItemResponse(BaseModel):
    """
    Unified content item representing either a project or a course.

    CONTENT TYPES:
    - project_only: Project without associated course in response
    - direct_course: Course created directly under organization
    - track_course: Course within a track
    - project_course: Course associated with project (via track)
    """
    content_type: str = Field(..., description="Type: project_only, direct_course, track_course")

    # Organization info
    organization_id: str
    organization_name: Optional[str] = None

    # Project info (null for direct courses)
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    project_status: Optional[str] = None
    project_created_at: Optional[datetime] = None

    # Course info (null for project_only items)
    course_id: Optional[str] = None
    course_title: Optional[str] = None
    course_description: Optional[str] = None
    difficulty_level: Optional[str] = None
    is_published: Optional[bool] = None
    course_created_at: Optional[datetime] = None

    # Track info (for track-based courses)
    track_id: Optional[str] = None
    track_name: Optional[str] = None

    # Instructor info
    instructor_id: Optional[str] = None
    instructor_name: Optional[str] = None


class OrganizationContentResponse(BaseModel):
    """Response containing all content for an organization."""
    organization_id: str
    organization_name: str
    projects: List[ContentItemResponse] = Field(default_factory=list)
    direct_courses: List[ContentItemResponse] = Field(default_factory=list)
    track_courses: List[ContentItemResponse] = Field(default_factory=list)
    total_items: int = 0


class ContentSummaryResponse(BaseModel):
    """Summary counts of organization content."""
    organization_id: str
    project_count: int = 0
    direct_course_count: int = 0
    track_course_count: int = 0
    total_course_count: int = 0
    published_course_count: int = 0


class DirectCourseCreateRequest(BaseModel):
    """Request to create a course directly under an organization (no track required)."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    instructor_id: str = Field(..., description="UUID of the instructor")
    difficulty_level: Optional[str] = Field(default="beginner")
    category: Optional[str] = None
    estimated_duration: Optional[int] = Field(default=None, ge=1)
    duration_unit: Optional[str] = Field(default="weeks")
    price: Optional[float] = Field(default=0.0, ge=0)
    tags: Optional[List[str]] = Field(default_factory=list)


class DirectCourseResponse(BaseModel):
    """Response for a direct organization course."""
    id: str
    title: str
    description: str
    organization_id: str
    instructor_id: str
    difficulty_level: str
    is_published: bool
    category: Optional[str] = None
    estimated_duration: Optional[int] = None
    duration_unit: Optional[str] = None
    price: float = 0.0
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    context_mode: str = "direct_org"


# =============================================================================
# API Endpoints
# =============================================================================

@router.get(
    "/{org_id}/content",
    response_model=OrganizationContentResponse,
    summary="Get organization content overview",
    description="""
    Retrieve all content within an organization including:
    - Projects (with their tracks and courses)
    - Direct courses (courses created directly under organization without tracks)
    - Track-based courses (courses within project/track hierarchy)

    This endpoint supports the new workflow where organizations can create
    courses directly without requiring projects or tracks.
    """
)
async def get_organization_content(
    org_id: str,
    include_unpublished: bool = Query(default=True, description="Include unpublished courses"),
    content_type: Optional[str] = Query(default=None, description="Filter by content type")
):
    """
    Get unified content overview for an organization.

    BUSINESS LOGIC:
    1. Query organization_content_overview view for all content
    2. Group content by type (projects, direct_courses, track_courses)
    3. Apply optional filters (published status, content type)
    4. Return structured response with all content items

    Args:
        org_id: Organization UUID
        include_unpublished: Whether to include unpublished courses
        content_type: Optional filter for content type

    Returns:
        OrganizationContentResponse with all organization content
    """
    try:
        # This would normally use the DAO to query the database
        # For now, return a structured response showing the expected format
        logger.info(f"Getting content overview for organization {org_id}")

        # Placeholder implementation - in production, this queries the DB view
        return OrganizationContentResponse(
            organization_id=org_id,
            organization_name="Organization",
            projects=[],
            direct_courses=[],
            track_courses=[],
            total_items=0
        )

    except DatabaseException as db_err:
        logger.error(f"Database error getting organization content: {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {db_err.message}"
        )
    except CourseManagementException as cm_err:
        logger.error(f"Course management error: {cm_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=cm_err.message
        )


@router.get(
    "/{org_id}/content/summary",
    response_model=ContentSummaryResponse,
    summary="Get organization content summary",
    description="Get counts of projects, direct courses, and track-based courses."
)
async def get_organization_content_summary(org_id: str):
    """
    Get content count summary for an organization.

    BUSINESS LOGIC:
    Uses get_organization_content_summary() database function to
    efficiently retrieve content counts without loading all data.

    Args:
        org_id: Organization UUID

    Returns:
        ContentSummaryResponse with content counts
    """
    try:
        logger.info(f"Getting content summary for organization {org_id}")

        # Placeholder - in production, calls get_organization_content_summary(org_id)
        return ContentSummaryResponse(
            organization_id=org_id,
            project_count=0,
            direct_course_count=0,
            track_course_count=0,
            total_course_count=0,
            published_course_count=0
        )

    except DatabaseException as db_err:
        logger.error(f"Database error getting content summary: {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {db_err.message}"
        )


@router.get(
    "/{org_id}/direct-courses",
    response_model=List[DirectCourseResponse],
    summary="List direct organization courses",
    description="""
    List all courses created directly under an organization (not in any track).
    These are courses where organization_id is set but track_id is NULL.
    """
)
async def list_direct_courses(
    org_id: str,
    published_only: bool = Query(default=False, description="Only return published courses"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    List courses created directly under organization.

    BUSINESS LOGIC:
    Query courses where organization_id = org_id AND track_id IS NULL.
    This represents the "direct org" course creation mode.

    Args:
        org_id: Organization UUID
        published_only: Filter to published courses only
        limit: Maximum number of results
        offset: Pagination offset

    Returns:
        List of DirectCourseResponse
    """
    try:
        logger.info(f"Listing direct courses for organization {org_id}")

        # Placeholder - in production, queries courses table
        return []

    except DatabaseException as db_err:
        logger.error(f"Database error listing direct courses: {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {db_err.message}"
        )


@router.post(
    "/{org_id}/direct-courses",
    response_model=DirectCourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create direct organization course",
    description="""
    Create a course directly under an organization without requiring a track.
    This enables the simplified workflow where organizations can create
    standalone courses without the full project/track hierarchy.
    """
)
async def create_direct_course(
    org_id: str,
    course_data: DirectCourseCreateRequest
):
    """
    Create a course directly under an organization.

    BUSINESS LOGIC:
    1. Validate organization exists and user has permission
    2. Create course with organization_id set, track_id = NULL
    3. Return created course with context_mode = "direct_org"

    Args:
        org_id: Organization UUID
        course_data: Course creation data

    Returns:
        DirectCourseResponse with created course
    """
    try:
        logger.info(f"Creating direct course for organization {org_id}")

        # Placeholder - in production, creates course via service
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Direct course creation endpoint - implementation pending"
        )

    except AuthorizationException as auth_err:
        logger.error(f"Authorization error: {auth_err}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=auth_err.message
        )
    except DatabaseException as db_err:
        logger.error(f"Database error creating direct course: {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {db_err.message}"
        )
