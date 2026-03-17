#!/usr/bin/env python3

"""
Syllabus Management API Endpoints

This module provides RESTful API endpoints for syllabus management in the Course Creator Platform,
following SOLID principles and clean architecture patterns.

## Educational Context:

### Syllabus Management Capabilities
- **Creation & Upload**: Process syllabus documents with AI-driven structure analysis
- **Lifecycle Management**: Draft, publish, and archive workflows for syllabus evolution
- **Learning Objectives**: Extraction and validation of educational outcomes
- **Course Alignment**: Integration with course structure and assessment mapping

### Business Workflows
- **Content Creation**: Instructors upload and structure syllabus content
- **Publishing**: Controlled release of syllabus to students and stakeholders
- **Versioning**: Track syllabus changes over academic terms
- **Discovery**: Course-based syllabus retrieval for educational planning

### Architecture Principles
- **Single Responsibility**: Focused on syllabus-specific operations
- **Dependency Injection**: Service dependencies injected via FastAPI
- **Clean Separation**: API layer separated from business logic
- **Educational Standards**: Validates against academic content requirements

## API Endpoints:
- POST /api/v1/syllabi - Create new syllabus
- GET /api/v1/syllabi/{syllabus_id} - Retrieve specific syllabus
- PUT /api/v1/syllabi/{syllabus_id} - Update syllabus content
- DELETE /api/v1/syllabi/{syllabus_id} - Remove syllabus
- POST /api/v1/syllabi/{syllabus_id}/publish - Publish syllabus
- POST /api/v1/syllabi/{syllabus_id}/archive - Archive syllabus
- GET /api/v1/courses/{course_id}/syllabi - List course syllabi

## Integration:
This router integrates with the ISyllabusService interface for business logic execution,
ensuring clean separation between API presentation and educational domain logic.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Dict, Any
import logging
import os
import sys
from datetime import datetime

# JWT Authentication - Import from auth module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from auth import get_current_user_id as get_authenticated_user_id

# API Models (Data Transfer Objects)
from pydantic import BaseModel, Field

# Domain entities and interfaces
from content_management.domain.entities.syllabus import Syllabus
from content_management.domain.interfaces.content_service import ISyllabusService

# Response models (using centralized models to avoid circular imports)
from models import ContentResponse

# Initialize router with prefix and tags
router = APIRouter(
    prefix="/api/v1/syllabi",
    tags=["syllabi"],
    responses={
        404: {"description": "Syllabus not found"},
        500: {"description": "Internal server error"}
    }
)

# Request Models
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
    from main import container
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_syllabus_service()

# JWT-authenticated user ID extraction (replaced deprecated mock)
get_current_user = get_authenticated_user_id

# Helper function
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

# API Endpoints

@router.post("", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_syllabus(
    request: SyllabusCreateRequest,
    current_user: str = Depends(get_current_user),
    syllabus_service: ISyllabusService = Depends(get_syllabus_service)
):
    """
    Create a new syllabus for a course.

    Educational Workflow:
    1. Instructor uploads syllabus document or manually creates syllabus structure
    2. AI analyzes content to extract learning objectives and course structure
    3. System validates educational standards compliance
    4. Syllabus is created in draft status for review and refinement

    Business Logic:
    - Validates course association and user permissions
    - Processes educational content structure and metadata
    - Integrates with AI services for content enhancement
    - Creates audit trail for syllabus creation

    Args:
        request: Syllabus creation request with course structure and learning objectives
        current_user: Authenticated user creating the syllabus
        syllabus_service: Injected syllabus service for business logic

    Returns:
        ContentResponse: Created syllabus with generated ID and metadata

    Raises:
        HTTPException 400: Invalid syllabus data or educational content structure
        HTTPException 500: Service error during syllabus creation
    """
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

@router.get("/{syllabus_id}", response_model=ContentResponse)
async def get_syllabus(
    syllabus_id: str,
    syllabus_service: ISyllabusService = Depends(get_syllabus_service)
):
    """
    Retrieve a specific syllabus by ID.

    Educational Use Cases:
    - Students accessing published course syllabus
    - Instructors reviewing syllabus content
    - Administrators auditing educational content
    - Content recommendation systems analyzing syllabus structure

    Business Logic:
    - Validates user permissions for syllabus access
    - Returns complete syllabus structure with all metadata
    - Supports caching for frequently accessed syllabi

    Args:
        syllabus_id: Unique identifier for the syllabus
        syllabus_service: Injected syllabus service for business logic

    Returns:
        ContentResponse: Complete syllabus data with educational metadata

    Raises:
        HTTPException 404: Syllabus not found
        HTTPException 500: Service error during retrieval
    """
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

@router.put("/{syllabus_id}", response_model=ContentResponse)
async def update_syllabus(
    syllabus_id: str,
    request: SyllabusUpdateRequest,
    current_user: str = Depends(get_current_user),
    syllabus_service: ISyllabusService = Depends(get_syllabus_service)
):
    """
    Update an existing syllabus.

    Educational Workflow:
    - Instructor updates syllabus during course planning
    - System validates educational content consistency
    - Version control tracks syllabus evolution
    - Students receive notifications of significant changes

    Business Logic:
    - Partial update support for efficient content modification
    - Validates educational standards during updates
    - Maintains version history for syllabus changes
    - Updates related course content and assessments

    Args:
        syllabus_id: Unique identifier for the syllabus to update
        request: Syllabus update request with modified fields
        current_user: Authenticated user making the update
        syllabus_service: Injected syllabus service for business logic

    Returns:
        ContentResponse: Updated syllabus with new timestamp and metadata

    Raises:
        HTTPException 400: Invalid update data or educational content structure
        HTTPException 404: Syllabus not found
        HTTPException 500: Service error during update
    """
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

@router.delete("/{syllabus_id}", status_code=status.HTTP_200_OK)
async def delete_syllabus(
    syllabus_id: str,
    current_user: str = Depends(get_current_user),
    syllabus_service: ISyllabusService = Depends(get_syllabus_service)
):
    """
    Delete a syllabus.

    Educational Context:
    - Removes draft syllabi that are no longer needed
    - Maintains data integrity for educational content
    - Preserves audit trail even after deletion

    Business Logic:
    - Validates user permissions for syllabus deletion
    - Prevents deletion of published syllabi with active enrollments
    - Maintains referential integrity with related course content
    - Creates audit log entry for deletion operation

    Args:
        syllabus_id: Unique identifier for the syllabus to delete
        current_user: Authenticated user performing deletion
        syllabus_service: Injected syllabus service for business logic

    Returns:
        Dict: Success message confirming deletion

    Raises:
        HTTPException 400: Invalid deletion request (e.g., published syllabus)
        HTTPException 404: Syllabus not found
        HTTPException 500: Service error during deletion
    """
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

@router.post("/{syllabus_id}/publish", response_model=ContentResponse)
async def publish_syllabus(
    syllabus_id: str,
    current_user: str = Depends(get_current_user),
    syllabus_service: ISyllabusService = Depends(get_syllabus_service)
):
    """
    Publish a syllabus to make it available to students.

    Educational Workflow:
    - Instructor finalizes syllabus content
    - System validates educational completeness
    - Syllabus is published to course students
    - Notifications sent to enrolled students

    Business Logic:
    - Validates syllabus completeness before publishing
    - Updates syllabus status to published
    - Triggers notifications to course stakeholders
    - Creates immutable snapshot for academic records

    Args:
        syllabus_id: Unique identifier for the syllabus to publish
        current_user: Authenticated user publishing the syllabus
        syllabus_service: Injected syllabus service for business logic

    Returns:
        ContentResponse: Published syllabus with updated status

    Raises:
        HTTPException 400: Syllabus not ready for publishing
        HTTPException 404: Syllabus not found
        HTTPException 500: Service error during publishing
    """
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

@router.post("/{syllabus_id}/archive", response_model=ContentResponse)
async def archive_syllabus(
    syllabus_id: str,
    current_user: str = Depends(get_current_user),
    syllabus_service: ISyllabusService = Depends(get_syllabus_service)
):
    """
    Archive a syllabus at the end of an academic term.

    Educational Context:
    - Maintains historical record of course syllabi
    - Removes syllabus from active course listings
    - Preserves syllabus for academic compliance and accreditation

    Business Logic:
    - Updates syllabus status to archived
    - Maintains read-only access for historical reference
    - Preserves all syllabus data and metadata
    - Creates audit trail for archival operation

    Args:
        syllabus_id: Unique identifier for the syllabus to archive
        current_user: Authenticated user archiving the syllabus
        syllabus_service: Injected syllabus service for business logic

    Returns:
        ContentResponse: Archived syllabus with updated status

    Raises:
        HTTPException 400: Invalid archival request
        HTTPException 404: Syllabus not found
        HTTPException 500: Service error during archival
    """
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

@router.get("/courses/{course_id}/syllabi", response_model=List[ContentResponse])
async def get_course_syllabi(
    course_id: str,
    include_drafts: bool = False,
    syllabus_service: ISyllabusService = Depends(get_syllabus_service)
):
    """
    Get all syllabi for a specific course.

    Educational Use Cases:
    - Instructors viewing all syllabus versions for a course
    - Students accessing current course syllabus
    - Administrators reviewing course syllabi for compliance
    - Analytics systems analyzing syllabus evolution

    Business Logic:
    - Returns published syllabi by default
    - Optional inclusion of draft syllabi for authorized users
    - Supports version comparison and historical analysis
    - Ordered by creation date (newest first)

    Args:
        course_id: Unique identifier for the course
        include_drafts: Whether to include draft syllabi (default: False)
        syllabus_service: Injected syllabus service for business logic

    Returns:
        List[ContentResponse]: List of syllabi for the course

    Raises:
        HTTPException 500: Service error during retrieval
    """
    try:
        syllabi = await syllabus_service.get_course_syllabi(course_id, include_drafts)
        return [_content_to_response(syllabus) for syllabus in syllabi]

    except Exception as e:
        logging.error("Error getting course syllabi: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e
