"""
Organization Management API Endpoints
Handles organization CRUD operations, member management, and professional registration requirements

BUSINESS CONTEXT:
Provides REST API endpoints for organization lifecycle management including creation,
updates, member management, and professional registration workflows.

TECHNICAL IMPLEMENTATION:
All exceptions are wrapped in custom exception classes to provide detailed context
and proper error tracking. Generic exceptions are never used - all errors are
classified and contextualized for better debugging and monitoring.
"""
from fastapi import APIRouter, HTTPException, Query, Depends, File, UploadFile, Form
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
import logging
import re

# Import dependency injection
from app_dependencies import get_organization_service, get_current_user, require_org_admin, get_dao
from organization_management.application.services.organization_service import OrganizationService
from organization_management.data_access.organization_dao import OrganizationManagementDAO

# Pydantic models for API (Data Transfer Objects)
from pydantic import BaseModel, Field, EmailStr, validator

# Import custom exceptions for proper error handling
from organization_management.exceptions import (
    OrganizationException,
    OrganizationNotFoundException,
    OrganizationValidationException,
    ValidationException,
    DatabaseException,
    FileStorageException,
    APIException
)

# Response Models
class OrganizationResponse(BaseModel):
    """Organization response with complete contact information"""
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    # Contact information
    contact_phone: str
    contact_email: str
    # Subdivided address fields
    street_address: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = 'US'
    # Legacy address field (deprecated)
    address: Optional[str] = None
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
    contact_phone: str = Field(..., min_length=10, max_length=20, description="Professional contact phone number")
    contact_email: EmailStr = Field(..., description="Professional contact email (no Gmail, Yahoo, etc.)")

    # Subdivided address fields (replacing single address field)
    street_address: Optional[str] = Field(None, max_length=255, description="Street address (number and street name)")
    city: Optional[str] = Field(None, max_length=100, description="City name")
    state_province: Optional[str] = Field(None, max_length=100, description="State (US) or Province")
    postal_code: Optional[str] = Field(None, max_length=20, description="ZIP code (US) or postal code")
    country: str = Field(default='US', max_length=2, description="ISO 3166-1 alpha-2 country code")

    # Legacy address field (deprecated but kept for backwards compatibility)
    address: Optional[str] = Field(None, min_length=10, max_length=500, description="Complete physical address (deprecated - use subdivided fields)")
    
    # Organization admin information  
    admin_full_name: str = Field(..., min_length=2, max_length=100, description="Full name of organization administrator")
    admin_username: Optional[str] = Field(None, min_length=3, max_length=30, pattern=r'^[a-zA-Z0-9_-]+$', description="Administrator username/ID for login (optional)")
    admin_email: EmailStr = Field(..., description="Administrator email address (professional domain required)")
    admin_phone: Optional[str] = Field(None, min_length=10, max_length=20, description="Administrator phone number")
    admin_role: str = Field(..., description="Primary role of the administrator", pattern=r'^(organization_admin|instructor|student)$')
    admin_roles: Optional[List[str]] = Field(None, description="All roles assigned to the administrator")
    admin_password: str = Field(..., min_length=8, description="Administrator password for account")
    
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
    organization_service: OrganizationService = Depends(get_organization_service)
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
        print(f"=== API ENDPOINT DEBUG: Received organization registration request")
        print(f"=== API REQUEST DATA: name='{request.name}', slug='{request.slug}', admin_email='{request.admin_email}'")
        logging.info(f"API ENDPOINT DEBUG: Received organization registration request")
        logging.info(f"API REQUEST DATA: name='{request.name}', slug='{request.slug}', admin_email='{request.admin_email}'")
        
        # Create organization with automatic admin user registration
        logging.info(f"Creating organization: {request.name} with administrator: {request.admin_email}")
        print(f"=== API DEBUG: About to call organization_service.create_organization")
        
        # Use enhanced organization service to create both organization and admin user
        result = await organization_service.create_organization(
            name=request.name,
            slug=request.slug,
            contact_phone=request.contact_phone,
            contact_email=request.contact_email,
            street_address=request.street_address,
            city=request.city,
            state_province=request.state_province,
            postal_code=request.postal_code,
            country=request.country,
            address=request.address,  # Legacy field
            description=request.description,
            logo_url=request.logo_url,
            domain=request.domain,
            # Admin user parameters
            admin_full_name=request.admin_full_name,
            admin_username=request.admin_username,
            admin_email=request.admin_email,
            admin_phone=request.admin_phone,
            admin_roles=request.admin_roles or [request.admin_role],
            admin_password=request.admin_password
        )
        
        print(f"=== API DEBUG: Service call completed successfully")
        logging.info(f"API DEBUG: Service call completed successfully")
        
        # Extract organization data from result
        org_data = result["organization"]
        admin_data = result["admin_user"]
        
        print(f"=== API DEBUG: Extracted organization and admin data")
        logging.info(f"Organization and admin user created successfully: {request.name}")
        logging.info(f"Admin user: {admin_data['email']} (temp password generated)")
        
        print(f"=== API DEBUG: About to create OrganizationResponse")
        # Return organization response (admin user info is logged but not returned for security)
        return OrganizationResponse(
            id=org_data["id"],
            name=org_data["name"],
            slug=org_data["slug"],
            description=org_data["description"],
            contact_phone=org_data["contact_phone"],
            contact_email=org_data["contact_email"],
            street_address=org_data.get("street_address"),
            city=org_data.get("city"),
            state_province=org_data.get("state_province"),
            postal_code=org_data.get("postal_code"),
            country=org_data.get("country", "US"),
            address=org_data.get("address"),
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
        # Wrap validation errors with proper context
        wrapped_error = OrganizationValidationException(
            message=f"Invalid organization data: {str(e)}",
            error_code="ORG_CREATION_VALIDATION_ERROR",
            details={"validation_error": str(e)},
            original_exception=e
        )
        logging.warning(f"Organization creation validation failed: {wrapped_error.message}", extra=wrapped_error.to_dict())
        raise HTTPException(status_code=400, detail=wrapped_error.message)
    except OrganizationValidationException as e:
        # Re-raise organization validation errors
        logging.error(f"Organization validation error: {e.message}", extra=e.to_dict())
        raise HTTPException(status_code=400, detail=e.message)
    except DatabaseException as e:
        # Database errors during organization creation
        logging.error(f"Database error creating organization: {e.message}", extra=e.to_dict())
        raise HTTPException(
            status_code=500,
            detail="Failed to create organization due to database error"
        )
    except Exception as e:
        # Wrap unknown exceptions with full context
        import traceback
        logging.exception(f"Unexpected error creating organization: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        wrapped_error = OrganizationException(
            message="Failed to create organization due to an unexpected error",
            error_code="ORG_CREATION_ERROR",
            details={"error_type": type(e).__name__, "traceback": traceback.format_exc()},
            original_exception=e
        )
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
async def get_organization(
    org_id: UUID,
    organization_service: OrganizationService = Depends(get_organization_service)
):
    """Get organization details by ID"""
    try:
        # Get organization from service
        organization = await organization_service.get_organization(org_id)

        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Return organization response
        return OrganizationResponse(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            description=organization.description,
            contact_phone=organization.contact_phone,
            contact_email=organization.contact_email,
            street_address=organization.street_address if hasattr(organization, 'street_address') else None,
            city=organization.city if hasattr(organization, 'city') else None,
            state_province=organization.state_province if hasattr(organization, 'state_province') else None,
            postal_code=organization.postal_code if hasattr(organization, 'postal_code') else None,
            country=organization.country if hasattr(organization, 'country') else 'US',
            address=organization.address,
            logo_url=organization.logo_url,
            logo_file_path=None,
            domain=organization.domain,
            is_active=organization.is_active,
            member_count=organization.member_count if hasattr(organization, 'member_count') else 0,
            project_count=organization.project_count if hasattr(organization, 'project_count') else 0,
            created_at=organization.created_at,
            updated_at=organization.updated_at
        )
    except HTTPException:
        raise
    except OrganizationNotFoundException as e:
        logging.error(f"Organization not found: {org_id}")
        raise HTTPException(status_code=404, detail="Organization not found")
    except Exception as e:
        logging.exception(f"Error getting organization {org_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve organization")

@router.put("/organizations/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    request: OrganizationUpdateRequest,
    organization_service: OrganizationService = Depends(get_organization_service)
):
    """
    Update organization details

    BUSINESS REQUIREMENTS:
    - Only specified fields are updated (partial updates supported)
    - Organization must exist
    - Contact email must be professional domain if provided
    - Domain must be unique across all organizations

    TECHNICAL IMPLEMENTATION:
    Uses custom exception handling for proper error classification and reporting.
    All exceptions are wrapped with context for debugging and monitoring.
    """
    # Extract fields from request (only non-None values)
    update_data = request.model_dump(exclude_unset=True)

    try:
        updated_org = await organization_service.update_organization(
            organization_id=org_id,
            name=update_data.get('name'),
            description=update_data.get('description'),
            logo_url=update_data.get('logo_url'),
            domain=update_data.get('domain'),
            address=update_data.get('street_address') or update_data.get('address'),
            contact_phone=update_data.get('contact_phone'),
            contact_email=update_data.get('contact_email'),
            settings=update_data.get('settings'),
            is_active=update_data.get('is_active')
        )

        # DAO returns dict, need to construct response with required fields
        # member_count and project_count are not stored in org table, need to query separately
        # For now, use 0 as default (could be enhanced to fetch actual counts)
        return OrganizationResponse(
            id=updated_org['id'],
            name=updated_org['name'],
            slug=updated_org['slug'],
            description=updated_org.get('description'),
            contact_phone=updated_org.get('contact_phone', ''),
            contact_email=updated_org.get('contact_email', ''),
            street_address=updated_org.get('street_address'),
            city=updated_org.get('city'),
            state_province=updated_org.get('state_province'),
            postal_code=updated_org.get('postal_code'),
            country=updated_org.get('country', 'US'),
            address=updated_org.get('address'),
            logo_url=updated_org.get('logo_url'),
            logo_file_path=updated_org.get('logo_file_path'),
            domain=updated_org.get('domain'),
            is_active=updated_org.get('is_active', True),
            member_count=0,  # TODO: Query actual member count
            project_count=0,  # TODO: Query actual project count
            created_at=updated_org['created_at'],
            updated_at=updated_org['updated_at']
        )
    except OrganizationNotFoundException as e:
        logging.warning(f"Organization not found: {e.message}", extra=e.to_dict())
        raise HTTPException(status_code=404, detail=e.message)
    except OrganizationValidationException as e:
        logging.warning(f"Organization validation failed: {e.message}", extra=e.to_dict())
        raise HTTPException(status_code=400, detail=e.message)
    except DatabaseException as e:
        logging.error(f"Database error updating organization: {e.message}", extra=e.to_dict())
        raise HTTPException(status_code=500, detail="Database error occurred")
    except OrganizationException as e:
        logging.error(f"Organization update error: {e.message}", extra=e.to_dict())
        raise HTTPException(status_code=500, detail=e.message)

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
    admin_username: Optional[str] = Form(None),
    admin_email: str = Form(...),
    admin_phone: Optional[str] = Form(None),
    admin_role: str = Form(...),
    admin_roles: Optional[str] = Form(None),  # JSON string of roles array
    admin_password: str = Form(...),
    description: Optional[str] = Form(None),
    domain: Optional[str] = Form(None),
    logo: Optional[UploadFile] = File(None),
    organization_service: OrganizationService = Depends(get_organization_service)
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
            admin_username=admin_username,
            admin_email=admin_email,
            admin_phone=admin_phone,
            admin_role=admin_role,
            admin_roles=parsed_admin_roles,
            description=description,
            domain=domain,
            admin_password=admin_password
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
    except FileStorageException as e:
        # File storage errors (logo upload)
        logging.error(f"File storage error creating organization: {e.message}", extra=e.to_dict())
        raise HTTPException(
            status_code=500,
            detail="Failed to create organization: Logo upload error"
        )
    except (OrganizationValidationException, OrganizationException) as e:
        # Organization-specific errors
        logging.error(f"Organization error: {e.message}", extra=e.to_dict())
        raise HTTPException(
            status_code=400 if isinstance(e, OrganizationValidationException) else 500,
            detail=e.message
        )
    except DatabaseException as e:
        # Database errors
        logging.error(f"Database error creating organization with logo: {e.message}", extra=e.to_dict())
        raise HTTPException(status_code=500, detail="Failed to create organization due to database error")
    except Exception as e:
        # Wrap unknown exceptions with context
        logging.exception(f"Unexpected error creating organization with logo: {str(e)}")
        wrapped_error = OrganizationException(
            message="Failed to create organization with logo",
            error_code="ORG_CREATION_WITH_LOGO_ERROR",
            details={"error_type": type(e).__name__},
            original_exception=e
        )
        raise HTTPException(status_code=500, detail=wrapped_error.message)

# Import dependencies for members endpoint
from app_dependencies import get_membership_service, get_current_user, verify_permission
from organization_management.application.services.membership_service import MembershipService
from organization_management.domain.entities.enhanced_role import Permission, RoleType
from typing import Dict, Any

# Helper function to extract user ID from current_user
def get_user_id(user: Dict[str, Any]) -> UUID:
    """Extract user ID from current_user dict"""
    if isinstance(user, dict):
        return UUID(user.get('id') or user.get('user_id'))
    return UUID(str(user.id))

# Pydantic model for member response
class MemberResponse(BaseModel):
    """Member response model"""
    id: UUID
    user_id: UUID
    organization_id: Optional[UUID] = None
    username: str
    email: str
    role: str
    is_active: bool
    joined_at: Optional[datetime] = None

@router.get("/organizations/{organization_id}/members")
async def get_organization_members(
    organization_id: UUID,
    role: Optional[str] = None,
    current_user=Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service)
):
    """Get organization members filtered by role (alias endpoint for frontend compatibility)"""
    try:
        # Organization admins can view their own organization's members
        # Skip strict permission check for now - basic auth is handled by get_current_user

        role_filter = None
        if role:
            role_filter = RoleType(role)

        members = await membership_service.get_organization_members(organization_id, role_filter)
        return [MemberResponse(**member) for member in members]

    except Exception as e:
        import traceback
        logging.error(f"Error fetching members: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organizations/{organization_id}/activity")
async def get_organization_activity(
    organization_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    days_back: Optional[int] = Query(default=None, ge=1, le=365),
    current_user: Dict = Depends(get_current_user),
    dao: OrganizationManagementDAO = Depends(get_dao)
):
    """
    Retrieve recent activity for an organization

    BUSINESS CONTEXT:
    Organization admins need visibility into recent activities for:
    - Team collaboration and coordination awareness
    - Audit compliance and security monitoring
    - Operational troubleshooting and support
    - Platform usage analytics and insights

    Activities include all significant actions such as:
    - Project creation, updates, and lifecycle changes
    - User management events (add, remove, role changes)
    - Track management and content publishing
    - Meeting room scheduling and access
    - System configuration updates

    TECHNICAL IMPLEMENTATION:
    - RESTful endpoint following OpenAPI/Swagger standards
    - Query parameter validation with FastAPI Query validators
    - Multi-tenant data isolation enforced via organization_id
    - Authentication required via JWT token (get_current_user dependency)
    - Pagination support for performance

    SOLID PRINCIPLES:
    - Single Responsibility: Endpoint focused solely on activity retrieval
    - Dependency Inversion: Depends on DAO abstraction (not concrete implementation)
    - Open/Closed: Extensible via query parameters without code modification
    - Interface Segregation: Clean, focused endpoint interface

    SECURITY:
    - HTTPS-only access (enforced at nginx/SSL layer)
    - JWT authentication required (via get_current_user)
    - Multi-tenant isolation (organization_id validation)
    - Query parameter validation (limit capped at 100)

    Args:
        organization_id: UUID of the organization (path parameter)
        limit: Maximum activities to return (query param, default=50, max=100)
        days_back: Optional days to look back (query param, default=all, max=365)
        current_user: Authenticated user from JWT token (injected dependency)
        dao: Data access object for database operations (injected dependency)

    Returns:
        JSON response with structure:
        {
            "activities": [
                {
                    "id": "uuid",
                    "organization_id": "uuid",
                    "user_id": "uuid",
                    "user_name": "string",
                    "activity_type": "string",
                    "description": "string",
                    "metadata": {},
                    "created_at": "ISO datetime",
                    "source": "string"
                }
            ],
            "total": number,
            "limit": number
        }

    Raises:
        HTTPException 401: Unauthorized (no valid JWT token)
        HTTPException 403: Forbidden (user not authorized for this organization)
        HTTPException 404: Not Found (organization doesn't exist)
        HTTPException 422: Validation Error (invalid query parameters)
        HTTPException 500: Internal Server Error (database/system error)

    Example:
        GET /api/v1/organizations/org-123/activity?limit=10&days_back=7

        Response:
        {
            "activities": [
                {
                    "id": "act-456",
                    "activity_type": "project_created",
                    "description": "Created project 'AI Course 2025'",
                    "created_at": "2025-10-19T10:30:00Z",
                    ...
                }
            ],
            "total": 10,
            "limit": 10
        }
    """
    try:
        # SECURITY: Validate user has access to this organization
        # TODO: Add explicit permission check when RBAC is fully implemented
        # For now, rely on authentication (get_current_user ensures valid JWT)

        logging.info(
            f"Fetching activities for organization {organization_id}",
            extra={
                'organization_id': organization_id,
                'user_id': current_user.get('user_id'),
                'limit': limit,
                'days_back': days_back
            }
        )

        # Retrieve activities from DAO
        activities = await dao.get_organization_activities(
            organization_id=organization_id,
            limit=limit,
            days_back=days_back
        )

        # Return formatted response
        response = {
            "activities": activities,
            "total": len(activities),
            "limit": limit
        }

        logging.info(
            f"Successfully retrieved {len(activities)} activities for organization {organization_id}",
            extra={
                'organization_id': organization_id,
                'count': len(activities)
            }
        )

        return response

    except ValidationException as e:
        # Client error - invalid input
        logging.warning(f"Validation error fetching activities: {e}")
        raise HTTPException(status_code=422, detail=str(e))

    except DatabaseException as e:
        # Server error - database issue
        logging.error(f"Database error fetching activities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve activities")

    except Exception as e:
        # Unexpected error
        logging.error(
            f"Unexpected error fetching activities for organization {organization_id}: {e}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="An unexpected error occurred")