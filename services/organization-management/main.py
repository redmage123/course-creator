#!/usr/bin/env python3
"""
Organization Management Service - Project-Based Multi-Tenant System
Single Responsibility: API layer only - business logic delegated to services
Open/Closed: Extensible through dependency injection
Liskov Substitution: Uses interface abstractions
Interface Segregation: Clean, focused interfaces
Dependency Inversion: Depends on abstractions, not concretions
"""
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
import logging
import os
import sys
import hydra
from omegaconf import DictConfig
import uvicorn
from datetime import datetime, date
from contextlib import asynccontextmanager
import jwt  # PyJWT package
from enum import Enum
from uuid import UUID

from logging_setup import setup_docker_logging
from infrastructure.container import initialize_container, cleanup_container
from app_dependencies import get_organization_service, get_current_user, require_org_admin, require_project_manager
from application.services.organization_service import OrganizationService
from auth.jwt_auth import JWTAuthenticator

# Import API route modules
from api import rbac_endpoints, site_admin_endpoints, track_endpoints

# Custom exceptions
from exceptions import (
    OrganizationManagementException, OrganizationException, ProjectException,
    MembershipException, AuthenticationException, AuthorizationException,
    ValidationException, OrganizationNotFoundException, ProjectNotFoundException,
    DatabaseException, InstructorManagementException, DuplicateResourceException
)

# Pydantic models for API (Data Transfer Objects)
from pydantic import BaseModel, Field, EmailStr, validator
from uuid import UUID

# Domain entities and enums

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    PROJECT_MANAGER = "project_manager"
    INSTRUCTOR = "instructor"
    STUDENT = "student"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectMemberRole(str, Enum):
    PARTICIPANT = "participant"
    INSTRUCTOR = "instructor"
    MANAGER = "manager"

# API Models (DTOs)

class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r'^[a-z0-9-]+$')
    description: Optional[str] = None
    logo_url: Optional[str] = None
    domain: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    settings: Dict[str, Any] = Field(default_factory=dict)


class OrganizationUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    domain: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r'^[a-z0-9-]+$')
    description: Optional[str] = None
    objectives: List[str] = Field(default_factory=list)
    target_roles: List[str] = Field(default_factory=list)
    duration_weeks: Optional[int] = Field(None, ge=1, le=104)
    max_participants: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    settings: Dict[str, Any] = Field(default_factory=dict)

    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if v and values.get('start_date') and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    objectives: Optional[List[str]] = None
    target_roles: Optional[List[str]] = None
    duration_weeks: Optional[int] = Field(None, ge=1, le=104)
    max_participants: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[ProjectStatus] = None
    settings: Optional[Dict[str, Any]] = None


class OrganizationMembershipRequest(BaseModel):
    user_email: EmailStr
    role: UserRole = UserRole.STUDENT
    permissions: Dict[str, Any] = Field(default_factory=dict)


class ProjectMembershipRequest(BaseModel):
    user_id: UUID
    role: ProjectMemberRole = ProjectMemberRole.PARTICIPANT


class InstructorCreateRequest(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = Field(UserRole.INSTRUCTOR, description="Role within organization")
    send_welcome_email: bool = True
    permissions: Dict[str, Any] = Field(default_factory=dict)

# Response Models

class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    logo_url: Optional[str]
    domain: Optional[str]
    is_active: bool
    member_count: int
    project_count: int
    created_at: datetime
    updated_at: datetime


class ProjectResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: Optional[str]
    objectives: List[str]
    target_roles: List[str]
    duration_weeks: Optional[int]
    max_participants: Optional[int]
    current_participants: int
    start_date: Optional[date]
    end_date: Optional[date]
    status: ProjectStatus
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime


class OrganizationMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: UserRole
    is_active: bool
    joined_at: datetime
    last_login: Optional[datetime]


class ProjectMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: ProjectMemberRole
    is_active: bool
    joined_at: datetime
    progress_percentage: Optional[float]

# Global container and config
container = None
current_config: Optional[DictConfig] = None
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event handler"""
    global container, current_config

    # Startup
    logging.info("Initializing Organization Management Service...")
    
    # Initialize caching infrastructure for RBAC performance optimization
    sys.path.append('/home/bbrelin/course-creator')
    from shared.cache import initialize_cache_manager
    
    redis_url = current_config.get("redis", {}).get("url", "redis://redis:6379")
    await initialize_cache_manager(redis_url)
    logging.info("Cache manager initialized for RBAC permission checking optimization")
    
    # Initialize your dependency injection container here
    # container = OrganizationContainer(current_config)
    # await container.initialize()
    logging.info("Organization Management Service initialized successfully")

    yield

    # Shutdown
    logging.info("Shutting down Organization Management Service...")
    if container:
        await container.cleanup()
    logging.info("Organization Management Service shutdown complete")


def create_app(config: DictConfig = None) -> FastAPI:
    """Application factory following SOLID principles"""
    global current_config
    current_config = config or {}

    app = FastAPI(
        title="Organization Management Service",
        description="Multi-tenant organization and project management system",
        version="1.0.0",
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
        AuthenticationException: 401,
        AuthorizationException: 403,
        OrganizationNotFoundException: 404,
        ProjectNotFoundException: 404,
        DuplicateResourceException: 409,
        OrganizationException: 422,
        ProjectException: 422,
        MembershipException: 422,
        InstructorManagementException: 422,
        DatabaseException: 500,
    }
    
    # Custom exception handler
    @app.exception_handler(OrganizationManagementException)
    async def organization_management_exception_handler(request, exc: OrganizationManagementException):
        """Handle custom organization management exceptions."""
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

    # Include API routers
    app.include_router(rbac_endpoints.router)
    app.include_router(site_admin_endpoints.router)
    app.include_router(track_endpoints.router)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "organization-management",
            "version": "1.0.0",
            "timestamp": datetime.utcnow()
        }

    return app

app = create_app()

# Dependency injection helpers

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Extract and validate user from JWT token"""
    try:
        # In production, validate JWT token properly
        # For now, mock user data
        return {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "admin@example.com",
            "role": "org_admin",
            "organization_id": "456e7890-e89b-12d3-a456-426614174000"
        }
    except Exception as e:
        raise AuthenticationException(
            message="Invalid authentication credentials",
            auth_method="jwt_bearer",
            original_exception=e
        )


async def require_org_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require organization admin role"""
    if current_user["role"] not in ["super_admin", "org_admin"]:
        raise AuthorizationException(
            message="Organization admin access required",
            user_id=current_user.get("id"),
            user_role=current_user.get("role"),
            required_role="org_admin",
            action="organization_management"
        )
    return current_user


# Organization Management Endpoints
@app.post("/api/v1/organizations", response_model=OrganizationResponse)
async def create_organization(
    request: OrganizationCreateRequest,
    organization_service: OrganizationService = Depends(get_organization_service),
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """Create a new organization"""
    try:
        # Use organization service with DAO pattern
        organization = await organization_service.create_organization(
            name=request.name,
            slug=request.slug,
            description=request.description,
            logo_url=request.logo_url,
            domain=request.domain,
            settings=request.settings
        )

        return OrganizationResponse(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            description=organization.description,
            logo_url=organization.logo_url,
            domain=organization.domain,
            is_active=organization.is_active,
            member_count=0,  # TODO: Implement member count query
            project_count=0,  # TODO: Implement project count query
            created_at=organization.created_at,
            updated_at=organization.updated_at
        )
    except ValueError as e:
        raise ValidationException(
            message="Invalid organization data provided",
            validation_errors={"organization_data": str(e)},
            original_exception=e
        )
    except OrganizationManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise OrganizationException(
            message="Failed to create organization",
            operation="create_organization",
            original_exception=e
        )

@app.get("/api/v1/organizations", response_model=List[OrganizationResponse])
async def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List organizations (filtered by user permissions)"""
    try:
        # Implementation would filter based on user permissions
        return []
    except OrganizationManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise OrganizationException(
            message="Failed to list organizations",
            operation="list_organizations",
            original_exception=e
        )

@app.get("/api/v1/organizations/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get organization details"""
    try:
        # Implementation would check user access to organization
        raise OrganizationNotFoundException(
            message="Organization not found",
            organization_id=str(org_id)
        )
    except OrganizationManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise OrganizationException(
            message="Failed to retrieve organization details",
            organization_id=str(org_id),
            operation="get_organization",
            original_exception=e
        )

@app.put("/api/v1/organizations/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    request: OrganizationUpdateRequest,
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """Update organization"""
    try:
        # Implementation here
        raise OrganizationNotFoundException(
            message="Organization not found",
            organization_id=str(org_id)
        )
    except OrganizationManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise OrganizationException(
            message="Failed to update organization",
            organization_id=str(org_id),
            operation="update_organization",
            original_exception=e
        )

# Project Management Endpoints
@app.post("/api/v1/organizations/{org_id}/projects", response_model=ProjectResponse)
async def create_project(
    org_id: UUID,
    request: ProjectCreateRequest,
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """Create a new project within an organization"""
    try:
        # Implementation would create project
        return ProjectResponse(
            id=UUID("789e0123-e89b-12d3-a456-426614174000"),
            organization_id=org_id,
            name=request.name,
            slug=request.slug,
            description=request.description,
            objectives=request.objectives,
            target_roles=request.target_roles,
            duration_weeks=request.duration_weeks,
            max_participants=request.max_participants,
            current_participants=0,
            start_date=request.start_date,
            end_date=request.end_date,
            status=ProjectStatus.DRAFT,
            created_by=UUID(current_user["id"]),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    except OrganizationManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise ProjectException(
            message="Failed to create project",
            organization_id=str(org_id),
            project_slug=request.slug,
            operation="create_project",
            original_exception=e
        )

@app.get("/api/v1/organizations/{org_id}/projects", response_model=List[ProjectResponse])
async def list_projects(
    org_id: UUID,
    status: Optional[ProjectStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List projects within an organization"""
    try:
        # Implementation would filter projects by organization and user access
        return []
    except OrganizationManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise ProjectException(
            message="Failed to list projects",
            organization_id=str(org_id),
            operation="list_projects",
            original_exception=e
        )

# Organization Member Management
@app.post("/api/v1/organizations/{org_id}/members")
async def add_organization_member(
    org_id: UUID,
    request: OrganizationMembershipRequest,
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """Add a user to an organization"""
    try:
        # Implementation would add user to organization
        return {"message": "User added to organization successfully"}
    except OrganizationManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise MembershipException(
            message="Failed to add organization member",
            user_email=request.user_email,
            organization_id=str(org_id),
            role=request.role.value,
            operation="add_organization_member",
            original_exception=e
        )

@app.get("/api/v1/organizations/{org_id}/members", response_model=List[OrganizationMemberResponse])
async def list_organization_members(
    org_id: UUID,
    role: Optional[UserRole] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """List organization members"""
    try:
        # Implementation would list organization members
        return []
    except OrganizationManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise MembershipException(
            message="Failed to list organization members",
            organization_id=str(org_id),
            operation="list_organization_members",
            original_exception=e
        )

@app.delete("/api/v1/organizations/{org_id}/members/{user_id}")
async def remove_organization_member(
    org_id: UUID,
    user_id: UUID,
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """Remove a user from an organization"""
    try:
        # Implementation would remove user from organization
        return {"message": "User removed from organization successfully"}
    except OrganizationManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise MembershipException(
            message="Failed to remove organization member",
            user_id=str(user_id),
            organization_id=str(org_id),
            operation="remove_organization_member",
            original_exception=e
        )

# Instructor Management (Specialized endpoints for org admins)
@app.post("/api/v1/organizations/{org_id}/instructors")
async def create_instructor(
    org_id: UUID,
    request: InstructorCreateRequest,
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """Create a new instructor within the organization"""
    try:
        # Implementation would:
        # 1. Create user account if doesn't exist
        # 2. Add to organization with instructor role
        # 3. Send welcome email if requested
        return {
            "message": "Instructor created successfully",
            "user_id": "new-instructor-id",
            "email_sent": request.send_welcome_email
        }
    except OrganizationManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise InstructorManagementException(
            message="Failed to create instructor",
            instructor_email=request.email,
            organization_id=str(org_id),
            operation="create_instructor",
            original_exception=e
        )

@app.get("/api/v1/organizations/{org_id}/instructors", response_model=List[OrganizationMemberResponse])
async def list_instructors(
    org_id: UUID,
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """List all instructors in the organization"""
    try:
        # Implementation would filter organization members by instructor role
        return []
    except OrganizationManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise InstructorManagementException(
            message="Failed to list instructors",
            organization_id=str(org_id),
            operation="list_instructors",
            original_exception=e
        )

@app.put("/api/v1/organizations/{org_id}/instructors/{user_id}/permissions")
async def update_instructor_permissions(
    org_id: UUID,
    user_id: UUID,
    permissions: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """Update instructor permissions within the organization"""
    try:
        # Implementation would update instructor permissions
        return {"message": "Instructor permissions updated successfully"}
    except OrganizationManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise InstructorManagementException(
            message="Failed to update instructor permissions",
            instructor_id=str(user_id),
            organization_id=str(org_id),
            operation="update_instructor_permissions",
            original_exception=e
        )

@app.delete("/api/v1/organizations/{org_id}/instructors/{user_id}")
async def remove_instructor(
    org_id: UUID,
    user_id: UUID,
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """Remove an instructor from the organization"""
    try:
        # Implementation would remove instructor role/membership
        return {"message": "Instructor removed successfully"}
    except OrganizationManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise InstructorManagementException(
            message="Failed to remove instructor",
            instructor_id=str(user_id),
            organization_id=str(org_id),
            operation="remove_instructor",
            original_exception=e
        )

# Project Member Management
@app.post("/api/v1/projects/{project_id}/members")
async def add_project_member(
    project_id: UUID,
    request: ProjectMembershipRequest,
    current_user: Dict[str, Any] = Depends(require_org_admin)
):
    """Add a user to a project"""
    try:
        # Implementation would add user to project
        return {"message": "User added to project successfully"}
    except OrganizationManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise MembershipException(
            message="Failed to add project member",
            user_id=str(request.user_id),
            project_id=str(project_id),
            role=request.role.value,
            operation="add_project_member",
            original_exception=e
        )

@app.get("/api/v1/projects/{project_id}/members", response_model=List[ProjectMemberResponse])
async def list_project_members(
    project_id: UUID,
    role: Optional[ProjectMemberRole] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List project members"""
    try:
        # Implementation would list project members
        return []
    except OrganizationManagementException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise MembershipException(
            message="Failed to list project members",
            project_id=str(project_id),
            operation="list_project_members",
            original_exception=e
        )

@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """Main entry point using Hydra configuration"""
    global current_config
    current_config = cfg

    # Setup centralized logging
    service_name = os.environ.get('SERVICE_NAME', 'organization-management')
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    if not log_level:
        try:
            log_level = cfg.get('logging', {}).get('level', 'INFO')
        except:
            log_level = 'INFO'

    logger = setup_docker_logging(service_name, log_level)
    port = cfg.get('server', {}).get('port', 8008)
    host = cfg.get('server', {}).get('host', '0.0.0.0')

    logger.info("Starting Organization Management Service on %s:%s", host, port)

    # Create app with configuration
    global app
    app = create_app(cfg)

    # Run server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="warning",  # Reduce uvicorn log level
        access_log=False      # Disable uvicorn access log
    )

if __name__ == "__main__":
    main()