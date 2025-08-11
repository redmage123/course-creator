"""
Organization Management API Endpoints
Handles organization CRUD operations, member management, and professional registration requirements
"""
from fastapi import APIRouter, HTTPException, Query, Depends, File, UploadFile, Form
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
import logging
import re

# Import dependency injection
from app_dependencies import get_organization_service, get_current_user, require_org_admin
from application.services.organization_service import OrganizationService

# Pydantic models for API (Data Transfer Objects)
from pydantic import BaseModel, Field, EmailStr, validator

# Response Models
class OrganizationResponse(BaseModel):
    """Organization response with complete contact information"""
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    # Contact information
    address: str
    contact_phone: str
    contact_email: str
    # Optional fields
    logo_url: Optional[str] = None
    logo_file_path: Optional[str] = None 
    domain: Optional[str] = None
    is_active: bool
    member_count: int
    project_count: int
    created_at: datetime
    updated_at: datetime

# Request Models
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
    admin_phone: str = Field(None, min_length=10, max_length=20, description="Administrator phone number")
    admin_role: str = Field(..., description="Primary role of the administrator", pattern=r'^(organization_admin|instructor|student)$')
    admin_roles: Optional[List[str]] = Field(None, description="All roles assigned to the administrator")
    
    # Optional fields
    description: str = Field(None, max_length=1000, description="Organization description")
    logo_url: str = Field(None, description="URL to organization logo")
    domain: str = Field(None, pattern=r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', description="Organization website domain")
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
    """Organization update request with optional professional fields"""
    name: str = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    domain: str = Field(None, pattern=r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    # Contact information updates
    address: str = Field(None, min_length=10, max_length=500)
    contact_phone: str = Field(None, min_length=10, max_length=20)
    contact_email: EmailStr = None
    settings: Dict[str, Any] = None
    is_active: bool = None
    
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

# Create the router
router = APIRouter(prefix="/api/v1", tags=["organizations"])

# Custom exceptions
class ValidationException(Exception):
    def __init__(self, message: str, validation_errors: dict = None, original_exception: Exception = None):
        self.message = message
        self.validation_errors = validation_errors or {}
        self.original_exception = original_exception
        super().__init__(self.message)

@router.post("/organizations", response_model=OrganizationResponse)
async def create_organization(
    request: OrganizationCreateRequest,
    organization_service: OrganizationService = Depends(get_organization_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new organization with professional requirements and admin user.
    
    BUSINESS REQUIREMENTS:
    - Organization must have complete contact information
    - Contact email must be professional domain (no Gmail, Yahoo, etc.)
    - Organization admin user is created with appropriate roles
    - All fields validated according to business rules
    """
    try:
        # Create organization with automatic admin user registration
        logging.info(f"Creating organization: {request.name} with administrator: {request.admin_email}")
        
        # Use enhanced organization service to create both organization and admin user
        result = await organization_service.create_organization(
            name=request.name,
            slug=request.slug,
            address=request.address,
            contact_phone=request.contact_phone,
            contact_email=request.contact_email,
            description=request.description,
            logo_url=request.logo_url,
            domain=request.domain,
            # Admin user parameters
            admin_full_name=request.admin_full_name,
            admin_email=request.admin_email,
            admin_phone=request.admin_phone,
            admin_roles=request.admin_roles or [request.admin_role]
        )
        
        # Extract organization data from result
        org_data = result["organization"]
        admin_data = result["admin_user"]
        
        logging.info(f"Organization and admin user created successfully: {request.name}")
        logging.info(f"Admin user: {admin_data['email']} (temp password generated)")
        
        # Return organization response (admin user info is logged but not returned for security)
        return OrganizationResponse(
            id=org_data["id"],
            name=org_data["name"],
            slug=org_data["slug"],
            description=org_data["description"],
            address=org_data["address"],
            contact_phone=org_data["contact_phone"],
            contact_email=org_data["contact_email"],
            logo_url=org_data["logo_url"],
            logo_file_path=None,
            domain=org_data["domain"],
            is_active=org_data["is_active"],
            member_count=1,  # Admin user created
            project_count=0,
            created_at=datetime.fromisoformat(org_data["created_at"]) if org_data["created_at"] else datetime.utcnow(),
            updated_at=datetime.fromisoformat(org_data["updated_at"]) if org_data["updated_at"] else datetime.utcnow()
        )
    except ValueError as e:
        # This catches Pydantic validation errors from our custom validators
        raise HTTPException(
            status_code=400,
            detail=f"Invalid organization data: {str(e)}"
        )
    except Exception as e:
        logging.error(f"Error creating organization: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create organization"
        )

@router.get("/organizations", response_model=List[OrganizationResponse])
async def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """List organizations (filtered by user permissions)"""
    # For now, return empty list - will implement with database service
    return []

@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
async def get_organization(org_id: UUID):
    """Get organization details"""
    # For now, return 404 - will implement with database service
    raise HTTPException(status_code=404, detail="Organization not found")

@router.put("/organizations/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    request: OrganizationUpdateRequest
):
    """Update organization"""
    # For now, return 404 - will implement with database service
    raise HTTPException(status_code=404, detail="Organization not found")

# Test endpoint
@router.get("/test")
async def test_organization_endpoint():
    """Test endpoint to verify organization router is working"""
    return {
        "message": "Organization router is working!",
        "service": "organization-management",
        "router": "organization_endpoints",
        "professional_validation": "enabled"
    }

@router.post("/organizations/upload", response_model=OrganizationResponse)
async def create_organization_with_logo(
    name: str = Form(...),
    slug: str = Form(...),
    address: str = Form(...),
    contact_phone: str = Form(...),
    contact_email: str = Form(...),
    admin_full_name: str = Form(...),
    admin_email: str = Form(...),
    admin_phone: Optional[str] = Form(None),
    admin_role: str = Form(...),
    admin_roles: Optional[str] = Form(None),  # JSON string of roles array
    description: Optional[str] = Form(None),
    domain: Optional[str] = Form(None),
    logo: Optional[UploadFile] = File(None),
    organization_service: OrganizationService = Depends(get_organization_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new organization with optional logo upload using multipart form data.
    
    BUSINESS REQUIREMENTS:
    - Organization must have complete contact information
    - Contact email must be professional domain (no Gmail, Yahoo, etc.)
    - Logo file must be JPG, PNG, or GIF format (max 5MB)
    - Organization admin user is created with appropriate roles
    """
    try:
        # Parse admin roles from JSON string
        parsed_admin_roles = None
        if admin_roles:
            try:
                import json
                parsed_admin_roles = json.loads(admin_roles)
            except json.JSONDecodeError:
                parsed_admin_roles = [admin_role]  # fallback to primary role only
        else:
            parsed_admin_roles = [admin_role]  # default to primary role only

        # Create organization data object from form fields
        organization_data = OrganizationCreateRequest(
            name=name,
            slug=slug,
            address=address,
            contact_phone=contact_phone,
            contact_email=contact_email,
            admin_full_name=admin_full_name,
            admin_email=admin_email,
            admin_phone=admin_phone,
            admin_role=admin_role,
            admin_roles=parsed_admin_roles,
            description=description,
            domain=domain
        )
        
        # Validate logo file if provided
        if logo:
            # Validate file type
            allowed_types = {'image/jpeg', 'image/jpg', 'image/png', 'image/gif'}
            if logo.content_type not in allowed_types:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type. Please upload JPG, PNG, or GIF files only."
                )
            
            # Validate file size (5MB max)
            max_size = 5 * 1024 * 1024  # 5MB
            file_content = await logo.read()
            if len(file_content) > max_size:
                raise HTTPException(
                    status_code=400,
                    detail="File too large. Maximum size is 5MB."
                )
            
            # Reset file pointer for potential future use
            await logo.seek(0)
            
            logging.info(f"Logo file uploaded: {logo.filename}, size: {len(file_content)} bytes")

        # Handle logo file upload if provided
        logo_url = None
        logo_file_path = None
        if logo:
            # In production, this would save the file and return actual paths
            # For now, we'll create placeholder paths
            temp_org_id = uuid4()
            logo_file_path = f"/uploads/organizations/{temp_org_id}/logo_{logo.filename}"
            logo_url = f"https://api.coursecreat.com/files{logo_file_path}"
            logging.info(f"Logo file processed: {logo.filename}")
        
        # Create organization with automatic admin user registration
        logging.info(f"Creating organization with logo: {organization_data.name} and administrator: {organization_data.admin_email}")
        
        # Use enhanced organization service to create both organization and admin user
        result = await organization_service.create_organization(
            name=organization_data.name,
            slug=organization_data.slug,
            address=organization_data.address,
            contact_phone=organization_data.contact_phone,
            contact_email=organization_data.contact_email,
            description=organization_data.description,
            logo_url=logo_url,
            domain=organization_data.domain,
            # Admin user parameters
            admin_full_name=organization_data.admin_full_name,
            admin_email=organization_data.admin_email,
            admin_phone=organization_data.admin_phone,
            admin_roles=organization_data.admin_roles or [organization_data.admin_role]
        )
        
        # Extract organization data from result
        org_data = result["organization"]
        admin_data = result["admin_user"]
        
        logging.info(f"Organization and admin user created successfully: {organization_data.name}")
        logging.info(f"Admin user: {admin_data['email']} (temp password generated)")
        
        return OrganizationResponse(
            id=org_data["id"],
            name=org_data["name"],
            slug=org_data["slug"],
            description=org_data["description"],
            address=org_data["address"],
            contact_phone=org_data["contact_phone"],
            contact_email=org_data["contact_email"],
            logo_url=org_data["logo_url"] or logo_url,
            logo_file_path=logo_file_path,
            domain=org_data["domain"],
            is_active=org_data["is_active"],
            member_count=1,  # Admin user created
            project_count=0,
            created_at=datetime.fromisoformat(org_data["created_at"]) if org_data["created_at"] else datetime.utcnow(),
            updated_at=datetime.fromisoformat(org_data["updated_at"]) if org_data["updated_at"] else datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating organization with logo: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create organization")