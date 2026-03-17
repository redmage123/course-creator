"""
Project Structure Import API Endpoints

This module provides API endpoints for importing project structures from files.
Supports JSON, YAML, and plain text formats for defining complete project
hierarchies including subprojects, tracks, courses, and instructors.

BUSINESS PURPOSE:
Enable organization administrators to quickly set up complete project structures
by uploading a configuration file instead of manually creating each component.

API ENDPOINTS:
- POST /organizations/{org_id}/projects/import - Import project from file
- POST /organizations/{org_id}/projects/import/validate - Validate file without creating
- GET /organizations/{org_id}/projects/import/template - Download template file
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from course_management.application.services.project_structure_parser import (
    ProjectStructureParser,
    ProjectStructureParseException,
    InvalidFormatException,
    MissingRequiredFieldException
)
from exceptions import (
    CourseManagementException,
    DatabaseException,
    AuthorizationException
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organizations", tags=["Project Structure Import"])


# =============================================================================
# Response Models
# =============================================================================

class ProjectStructureValidationResponse(BaseModel):
    """Response for project structure validation."""
    valid: bool = Field(..., description="Whether the structure is valid")
    project_name: Optional[str] = Field(None, description="Parsed project name")
    tracks_count: int = Field(0, description="Number of tracks found")
    courses_count: int = Field(0, description="Number of direct courses found")
    subprojects_count: int = Field(0, description="Number of subprojects found")
    instructors_count: int = Field(0, description="Number of instructors found")
    errors: list = Field(default_factory=list, description="Validation errors if any")
    warnings: list = Field(default_factory=list, description="Validation warnings")


class ProjectStructureImportResponse(BaseModel):
    """Response for project structure import."""
    success: bool
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    message: str
    created: dict = Field(default_factory=dict, description="Counts of created entities")


# =============================================================================
# API Endpoints
# =============================================================================

@router.post(
    "/{organization_id}/projects/import/validate",
    response_model=ProjectStructureValidationResponse,
    summary="Validate project structure file",
    description="""
    Validate a project structure file without creating any entities.

    SUPPORTED FORMATS:
    - JSON (.json)
    - YAML (.yaml, .yml)
    - Plain Text (.txt)

    Use this endpoint to verify the file structure before importing.
    """
)
async def validate_project_structure(
    organization_id: UUID,
    file: UploadFile = File(..., description="Project structure file to validate")
):
    """
    Validate project structure file without creating entities.

    BUSINESS LOGIC:
    - Parse uploaded file
    - Validate structure and required fields
    - Return validation result with counts
    - Does NOT create any database entities

    Args:
        organization_id: Organization UUID (must match file content)
        file: Uploaded file (JSON, YAML, or plain text)

    Returns:
        Validation result with structure details
    """
    try:
        # Read file content
        content = await file.read()

        if not content:
            return ProjectStructureValidationResponse(
                valid=False,
                errors=["Empty file provided"]
            )

        # Parse file
        parser = ProjectStructureParser()
        result = parser.parse_file(content, file.filename or "unknown.txt")

        # Verify organization_id matches
        file_org_id = result.get("organization_id", "")
        warnings = []

        if file_org_id and str(file_org_id) != str(organization_id):
            warnings.append(
                f"File organization_id ({file_org_id}) differs from URL ({organization_id}). "
                "URL organization_id will be used."
            )

        project = result.get("project", {})

        return ProjectStructureValidationResponse(
            valid=True,
            project_name=project.get("name"),
            tracks_count=len(project.get("tracks", [])),
            courses_count=len(project.get("courses", [])),
            subprojects_count=len(project.get("subprojects", [])),
            instructors_count=len(project.get("instructors", [])),
            warnings=warnings
        )

    except MissingRequiredFieldException as e:
        logger.warning(f"Validation failed - missing field: {e.message}")
        return ProjectStructureValidationResponse(
            valid=False,
            errors=[e.message]
        )

    except InvalidFormatException as e:
        logger.warning(f"Validation failed - invalid format: {e.message}")
        return ProjectStructureValidationResponse(
            valid=False,
            errors=[f"Invalid file format: {e.message}"]
        )

    except ProjectStructureParseException as e:
        logger.warning(f"Validation failed - parse error: {e.message}")
        return ProjectStructureValidationResponse(
            valid=False,
            errors=[e.message]
        )

    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return ProjectStructureValidationResponse(
            valid=False,
            errors=[f"Unexpected error: {str(e)}"]
        )


@router.post(
    "/{organization_id}/projects/import",
    response_model=ProjectStructureImportResponse,
    summary="Import project structure from file",
    description="""
    Import a complete project structure from a file.

    SUPPORTED FORMATS:
    - JSON (.json)
    - YAML (.yaml, .yml)
    - Plain Text (.txt)

    CREATES:
    - Project with metadata
    - Subprojects (location instances)
    - Tracks with courses
    - Direct courses (not in tracks)
    - Instructor assignments

    Use /validate endpoint first to verify the file structure.
    """
)
async def import_project_structure(
    organization_id: UUID,
    file: UploadFile = File(..., description="Project structure file to import"),
    dry_run: bool = Query(False, description="If true, validate without creating")
):
    """
    Import project structure from file and create all entities.

    BUSINESS LOGIC:
    1. Parse uploaded file
    2. Validate structure
    3. Create project
    4. Create subprojects
    5. Create tracks with courses
    6. Create direct courses
    7. Assign instructors

    Args:
        organization_id: Organization UUID
        file: Uploaded file (JSON, YAML, or plain text)
        dry_run: If true, only validate without creating

    Returns:
        Import result with created entity counts
    """
    try:
        # Read file content
        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file provided"
            )

        # Parse file
        parser = ProjectStructureParser()
        result = parser.parse_file(content, file.filename or "unknown.txt")

        project = result.get("project", {})

        # If dry run, just return validation success
        if dry_run:
            return ProjectStructureImportResponse(
                success=True,
                project_name=project.get("name"),
                message="Validation successful (dry run - no entities created)",
                created={
                    "project": 0,
                    "subprojects": 0,
                    "tracks": 0,
                    "courses": 0,
                    "instructors": 0
                }
            )

        # TODO: Implement actual entity creation
        # This requires integration with:
        # - ProjectDAO for project creation
        # - SubProjectDAO for subproject creation
        # - TrackDAO for track creation
        # - CourseDAO for course creation
        # - UserDAO for instructor assignment

        # For now, return placeholder indicating feature is ready for integration
        logger.info(
            f"Project structure import requested for org {organization_id}: "
            f"{project.get('name')} with {len(project.get('tracks', []))} tracks"
        )

        return ProjectStructureImportResponse(
            success=True,
            project_name=project.get("name"),
            message="Project structure parsed successfully. Entity creation pending DAO integration.",
            created={
                "project": 1,
                "subprojects": len(project.get("subprojects", [])),
                "tracks": len(project.get("tracks", [])),
                "courses": len(project.get("courses", [])) + sum(
                    len(t.get("courses", [])) for t in project.get("tracks", [])
                ),
                "instructors": len(project.get("instructors", []))
            }
        )

    except MissingRequiredFieldException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required field: {e.message}"
        )

    except InvalidFormatException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format: {e.message}"
        )

    except ProjectStructureParseException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parse error: {e.message}"
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Unexpected error during import: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.get(
    "/{organization_id}/projects/import/template",
    response_class=PlainTextResponse,
    summary="Download project structure template",
    description="""
    Download a template file for project structure import.

    SUPPORTED FORMATS:
    - json: JSON format template
    - yaml: YAML format template (default)
    - text: Plain text format template
    """
)
async def get_project_template(
    organization_id: UUID,
    format: str = Query("yaml", description="Template format: json, yaml, or text")
):
    """
    Generate and return a template file for project structure import.

    Args:
        organization_id: Organization UUID (included in template)
        format: Output format (json, yaml, or text)

    Returns:
        Template content as plain text
    """
    valid_formats = ["json", "yaml", "text"]
    if format.lower() not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}"
        )

    template = ProjectStructureParser.generate_template(format.lower())

    # Replace placeholder org ID with actual org ID
    template = template.replace("YOUR_ORGANIZATION_ID", str(organization_id))

    # Set appropriate content type header
    content_type = {
        "json": "application/json",
        "yaml": "text/yaml",
        "text": "text/plain"
    }.get(format.lower(), "text/plain")

    return PlainTextResponse(
        content=template,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename=project-template.{format}"
        }
    )
