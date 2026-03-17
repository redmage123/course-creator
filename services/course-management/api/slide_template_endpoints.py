"""
Slide Template API Endpoints

This module provides API endpoints for managing organization-level slide templates.
Templates allow organizations to define consistent branding for course presentations.

BUSINESS PURPOSE:
Enable organization administrators to create, manage, and apply custom slide
templates for consistent branding across all course presentations.

API ENDPOINTS:
- GET /organizations/{org_id}/templates - List organization templates
- POST /organizations/{org_id}/templates - Create new template
- GET /templates/{template_id} - Get template details
- PUT /templates/{template_id} - Update template
- DELETE /templates/{template_id} - Delete template
- POST /templates/{template_id}/set-default - Set as default template
- POST /templates/{template_id}/upload-logo - Upload template logo
"""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from pydantic import BaseModel, Field

from exceptions import (
    SlideTemplateException,
    SlideTemplateNotFoundException,
    SlideTemplateValidationException,
    DatabaseException,
    AuthorizationException
)
from course_management.domain.entities.slide_template import SlideTemplate, TemplateTheme

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Slide Templates"])


# =============================================================================
# Request/Response Models
# =============================================================================

class TemplateConfigModel(BaseModel):
    """Template configuration schema."""
    theme: str = Field(default="default", description="Theme: default, dark, light, corporate, custom")
    primaryColor: str = Field(default="#1976d2", description="Primary brand color (hex)")
    secondaryColor: str = Field(default="#dc004e", description="Secondary brand color (hex)")
    fontFamily: str = Field(default="Roboto, sans-serif", description="CSS font-family")
    headerStyle: Dict[str, Any] = Field(default_factory=dict, description="Header CSS properties")
    footerStyle: Dict[str, Any] = Field(default_factory=dict, description="Footer CSS properties")
    slideStyle: Dict[str, Any] = Field(default_factory=dict, description="Slide CSS properties")


class SlideTemplateCreateRequest(BaseModel):
    """Request to create a new slide template."""
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    description: Optional[str] = Field(default=None, max_length=500)
    template_config: Optional[TemplateConfigModel] = Field(default_factory=TemplateConfigModel)
    header_html: Optional[str] = Field(default=None, description="Header HTML content")
    footer_html: Optional[str] = Field(default=None, description="Footer HTML content")
    logo_url: Optional[str] = Field(default=None, max_length=500)
    background_image_url: Optional[str] = Field(default=None, max_length=500)
    is_default: bool = Field(default=False, description="Set as default template")


class SlideTemplateUpdateRequest(BaseModel):
    """Request to update an existing slide template."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    template_config: Optional[TemplateConfigModel] = None
    header_html: Optional[str] = None
    footer_html: Optional[str] = None
    logo_url: Optional[str] = Field(default=None, max_length=500)
    background_image_url: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class SlideTemplateResponse(BaseModel):
    """Response containing slide template data."""
    id: str
    name: str
    description: Optional[str] = None
    organization_id: str
    template_config: Dict[str, Any]
    header_html: Optional[str] = None
    footer_html: Optional[str] = None
    logo_url: Optional[str] = None
    background_image_url: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TemplateListResponse(BaseModel):
    """Response containing list of templates."""
    templates: List[SlideTemplateResponse]
    total: int
    organization_id: str


# =============================================================================
# Organization Template Endpoints
# =============================================================================

organization_router = APIRouter(prefix="/organizations", tags=["Slide Templates"])


@organization_router.get(
    "/{org_id}/templates",
    response_model=TemplateListResponse,
    summary="List organization templates",
    description="Get all slide templates for an organization."
)
async def list_organization_templates(
    org_id: str,
    include_inactive: bool = Query(default=False, description="Include inactive templates"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    List all slide templates for an organization.

    BUSINESS LOGIC:
    1. Query templates by organization_id
    2. Optionally filter by is_active status
    3. Return paginated list with default template first

    Args:
        org_id: Organization UUID
        include_inactive: Include deactivated templates
        limit: Maximum results
        offset: Pagination offset

    Returns:
        TemplateListResponse with list of templates
    """
    try:
        logger.info(f"Listing templates for organization {org_id}")

        # Placeholder - in production, queries slide_templates table
        return TemplateListResponse(
            templates=[],
            total=0,
            organization_id=org_id
        )

    except DatabaseException as db_err:
        logger.error(f"Database error listing templates: {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {db_err.message}"
        )


@organization_router.post(
    "/{org_id}/templates",
    response_model=SlideTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create slide template",
    description="Create a new slide template for the organization."
)
async def create_template(
    org_id: str,
    template_data: SlideTemplateCreateRequest
):
    """
    Create a new slide template for an organization.

    BUSINESS LOGIC:
    1. Validate organization exists and user has permission
    2. Validate template name uniqueness within organization
    3. Create template with provided configuration
    4. If is_default=True, update other templates (handled by DB trigger)

    Args:
        org_id: Organization UUID
        template_data: Template creation data

    Returns:
        SlideTemplateResponse with created template
    """
    try:
        logger.info(f"Creating template '{template_data.name}' for organization {org_id}")

        # Create template entity
        template = SlideTemplate(
            name=template_data.name,
            organization_id=org_id,
            description=template_data.description,
            template_config=template_data.template_config.model_dump() if template_data.template_config else {},
            header_html=template_data.header_html,
            footer_html=template_data.footer_html,
            logo_url=template_data.logo_url,
            background_image_url=template_data.background_image_url,
            is_default=template_data.is_default
        )

        # Placeholder - in production, saves via DAO
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Template creation endpoint - implementation pending"
        )

    except SlideTemplateValidationException as val_err:
        logger.error(f"Template validation error: {val_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=val_err.message
        )
    except AuthorizationException as auth_err:
        logger.error(f"Authorization error: {auth_err}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=auth_err.message
        )
    except DatabaseException as db_err:
        logger.error(f"Database error creating template: {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {db_err.message}"
        )


@organization_router.get(
    "/{org_id}/templates/default",
    response_model=SlideTemplateResponse,
    summary="Get default template",
    description="Get the default slide template for an organization."
)
async def get_default_template(org_id: str):
    """
    Get the default template for an organization.

    BUSINESS LOGIC:
    Query for template where organization_id = org_id AND is_default = TRUE.

    Args:
        org_id: Organization UUID

    Returns:
        SlideTemplateResponse with default template

    Raises:
        404 if no default template is set
    """
    try:
        logger.info(f"Getting default template for organization {org_id}")

        # Placeholder - in production, queries for default template
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default template found for organization"
        )

    except SlideTemplateNotFoundException as not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found.message
        )
    except DatabaseException as db_err:
        logger.error(f"Database error: {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {db_err.message}"
        )


# =============================================================================
# Individual Template Endpoints
# =============================================================================

template_router = APIRouter(prefix="/templates", tags=["Slide Templates"])


@template_router.get(
    "/{template_id}",
    response_model=SlideTemplateResponse,
    summary="Get template details",
    description="Get details for a specific slide template."
)
async def get_template(template_id: str):
    """
    Get slide template by ID.

    Args:
        template_id: Template UUID

    Returns:
        SlideTemplateResponse with template details
    """
    try:
        logger.info(f"Getting template {template_id}")

        # Placeholder - in production, queries by ID
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )

    except SlideTemplateNotFoundException as not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found.message
        )
    except DatabaseException as db_err:
        logger.error(f"Database error: {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {db_err.message}"
        )


@template_router.put(
    "/{template_id}",
    response_model=SlideTemplateResponse,
    summary="Update template",
    description="Update an existing slide template."
)
async def update_template(
    template_id: str,
    template_data: SlideTemplateUpdateRequest
):
    """
    Update an existing slide template.

    BUSINESS LOGIC:
    1. Load existing template
    2. Apply partial updates from request
    3. Validate updated template
    4. Save changes

    Args:
        template_id: Template UUID
        template_data: Partial update data

    Returns:
        SlideTemplateResponse with updated template
    """
    try:
        logger.info(f"Updating template {template_id}")

        # Placeholder - in production, updates via DAO
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Template update endpoint - implementation pending"
        )

    except SlideTemplateNotFoundException as not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found.message
        )
    except SlideTemplateValidationException as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=val_err.message
        )
    except DatabaseException as db_err:
        logger.error(f"Database error: {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {db_err.message}"
        )


@template_router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete template",
    description="Soft-delete a slide template by marking it as inactive."
)
async def delete_template(template_id: str):
    """
    Soft-delete a slide template.

    BUSINESS LOGIC:
    Sets is_active = FALSE rather than hard delete.
    Template data preserved for historical reference.

    Args:
        template_id: Template UUID
    """
    try:
        logger.info(f"Deleting template {template_id}")

        # Placeholder - in production, soft-deletes via DAO
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Template delete endpoint - implementation pending"
        )

    except SlideTemplateNotFoundException as not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found.message
        )
    except DatabaseException as db_err:
        logger.error(f"Database error: {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {db_err.message}"
        )


@template_router.post(
    "/{template_id}/set-default",
    response_model=SlideTemplateResponse,
    summary="Set as default template",
    description="Set this template as the default for its organization."
)
async def set_default_template(template_id: str):
    """
    Set template as default for its organization.

    BUSINESS LOGIC:
    1. Load template
    2. Set is_default = TRUE
    3. Database trigger automatically unsets previous default

    Args:
        template_id: Template UUID

    Returns:
        SlideTemplateResponse with updated template
    """
    try:
        logger.info(f"Setting template {template_id} as default")

        # Placeholder - in production, updates via DAO
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Set default endpoint - implementation pending"
        )

    except SlideTemplateNotFoundException as not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found.message
        )
    except DatabaseException as db_err:
        logger.error(f"Database error: {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {db_err.message}"
        )


@template_router.post(
    "/{template_id}/upload-logo",
    response_model=SlideTemplateResponse,
    summary="Upload template logo",
    description="Upload a logo image for the template."
)
async def upload_template_logo(
    template_id: str,
    logo: UploadFile = File(..., description="Logo image file (PNG, JPG, SVG)")
):
    """
    Upload a logo image for a slide template.

    BUSINESS LOGIC:
    1. Validate file type (PNG, JPG, SVG)
    2. Upload to file storage
    3. Update template logo_url
    4. Return updated template

    Args:
        template_id: Template UUID
        logo: Uploaded image file

    Returns:
        SlideTemplateResponse with updated logo_url
    """
    try:
        logger.info(f"Uploading logo for template {template_id}")

        # Validate file type
        allowed_types = ["image/png", "image/jpeg", "image/svg+xml"]
        if logo.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: PNG, JPG, SVG"
            )

        # Placeholder - in production, uploads to storage and updates template
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Logo upload endpoint - implementation pending"
        )

    except SlideTemplateNotFoundException as not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found.message
        )
    except SlideTemplateException as template_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=template_err.message
        )
    except DatabaseException as db_err:
        logger.error(f"Database error: {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {db_err.message}"
        )


# Combined router for main.py registration
router = APIRouter()
router.include_router(organization_router)
router.include_router(template_router)
