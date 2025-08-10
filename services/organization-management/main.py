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
import re
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
from api.organization_endpoints import router as organization_router
from api.project_endpoints import router as project_router
# from api import rbac_endpoints, site_admin_endpoints, track_endpoints

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
    """
    Organization creation request with professional requirements.
    
    BUSINESS REQUIREMENTS:
    - Organization name and address are required
    - Contact phone must be professional business number
    - Contact email must be professional domain (no Gmail, Yahoo, etc.)
    - Optional logo file upload (JPG, GIF, PNG only)
    - Organization admin details must be provided
    """
    # Required organization information
    name: str = Field(..., min_length=2, max_length=255, description="Official organization name")
    slug: str = Field(..., min_length=2, max_length=100, pattern=r'^[a-z0-9-]+$', description="URL-friendly organization identifier")
    address: str = Field(..., min_length=10, max_length=500, description="Complete physical address")
    contact_phone: str = Field(..., min_length=10, max_length=20, description="Professional contact phone number")
    contact_email: EmailStr = Field(..., description="Professional contact email (no Gmail, Yahoo, etc.)")
    
    # Organization admin information  
    admin_full_name: str = Field(..., min_length=2, max_length=100, description="Full name of organization administrator")
    admin_email: EmailStr = Field(..., description="Administrator email address (professional domain required)")
    admin_phone: Optional[str] = Field(None, min_length=10, max_length=20, description="Administrator phone number")
    
    # Optional fields
    description: Optional[str] = Field(None, max_length=1000, description="Organization description")
    logo_url: Optional[str] = Field(None, description="URL to organization logo")
    domain: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', description="Organization website domain")
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('contact_email', 'admin_email')
    def validate_professional_email(cls, v):
        """Validate that email addresses are from professional domains"""
        if not v:
            return v
            
        # Check against common personal email providers
        personal_domains = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 
            'aol.com', 'icloud.com', 'me.com', 'live.com'
        }
        
        domain = v.split('@')[-1].lower()
        if domain in personal_domains:
            raise ValueError(f'Personal email provider {domain} not allowed. Please use a professional business email address.')
        
        return v.lower()
    
    @validator('contact_phone', 'admin_phone')
    def validate_phone_format(cls, v):
        """Validate phone number format"""
        if not v:
            return v
        
        # Remove common phone formatting characters
        cleaned = re.sub(r'[^\d+]', '', str(v))
        
        # Basic phone validation (10+ digits, optional + prefix)
        if not re.match(r'^\+?\d{10,15}$', cleaned):
            raise ValueError('Invalid phone number format. Please provide a valid business phone number.')
        
        return cleaned


class OrganizationUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    domain: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    # Contact information updates
    address: Optional[str] = Field(None, min_length=10, max_length=500)
    contact_phone: Optional[str] = Field(None, min_length=10, max_length=20)
    contact_email: Optional[EmailStr] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    
    @validator('contact_email')
    def validate_professional_email_update(cls, v):
        """Validate that email addresses are from professional domains"""
        if not v:
            return v
            
        # Check against common personal email providers
        personal_domains = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 
            'aol.com', 'icloud.com', 'me.com', 'live.com'
        }
        
        domain = v.split('@')[-1].lower()
        if domain in personal_domains:
            raise ValueError(f'Personal email provider {domain} not allowed. Please use a professional business email address.')
        
        return v.lower()
    
    @validator('contact_phone')
    def validate_phone_format_update(cls, v):
        """Validate phone number format"""
        if not v:
            return v
        
        # Remove common phone formatting characters
        cleaned = re.sub(r'[^\d+]', '', str(v))
        
        # Basic phone validation (10+ digits, optional + prefix)
        if not re.match(r'^\+?\d{10,15}$', cleaned):
            raise ValueError('Invalid phone number format. Please provide a valid business phone number.')
        
        return cleaned


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
    """Organization response with complete contact information"""
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    # Contact information
    address: str
    contact_phone: str
    contact_email: str
    # Optional fields
    logo_url: Optional[str]
    logo_file_path: Optional[str] 
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event handler with container management"""
    global container
    
    # Startup
    logging.info("Initializing Organization Management Service...")
    
    # Initialize dependency injection container
    container = initialize_container(current_config)
    logging.info("Dependency injection container initialized")
    
    logging.info("Organization Management Service initialized successfully")

    yield

    # Shutdown  
    logging.info("Shutting down Organization Management Service...")
    
    # Cleanup container
    if container:
        cleanup_container(container)
        logging.info("Dependency injection container cleaned up")
    
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
    app.include_router(organization_router)
    app.include_router(project_router)
    # app.include_router(rbac_endpoints.router)
    # app.include_router(site_admin_endpoints.router)
    # app.include_router(track_endpoints.router)

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

    # Test endpoint
    @app.get("/test")
    async def test_endpoint():
        """Test endpoint to verify routing works"""
        return {"message": "Organization service is working!", "test": True}

    return app

app = create_app()

# All organization endpoints have been moved to api/organization_endpoints.py
# and are now properly registered via router inclusion with complex dependency injection

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