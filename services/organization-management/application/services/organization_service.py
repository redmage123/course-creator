"""
Organization Service - Business Logic Orchestration
Single Responsibility: Organization business operations
Open/Closed: Extensible through dependency injection
Dependency Inversion: Depends on repository abstractions

Enhanced to automatically create organization administrators during org registration
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
import httpx
import os

from domain.entities.organization import Organization
from domain.interfaces.organization_repository import IOrganizationRepository


class OrganizationService:
    """
    Service class for organization business operations
    """

    def __init__(self, organization_repository: IOrganizationRepository):
        self._organization_repository = organization_repository
        self._logger = logging.getLogger(__name__)
        
        # HTTP client configuration for user management service
        self._user_management_url = os.getenv('USER_MANAGEMENT_URL', 'http://localhost:8000')
        self._http_client = httpx.AsyncClient(timeout=30.0)

    async def _create_organization_admin_user(self, admin_full_name: str, admin_email: str, 
                                              admin_phone: str = None, admin_roles: List[str] = None,
                                              organization_slug: str = None) -> Dict[str, Any]:
        """
        Create organization administrator user in user management service
        
        PURPOSE: Automatically create the organization admin user when registering organization
        WHY: Organizations need an administrative user to manage the organization
        BUSINESS REQUIREMENT: Every organization must have at least one administrator
        
        Args:
            admin_full_name: Full name of the administrator
            admin_email: Email address for the administrator
            admin_phone: Phone number (optional)
            admin_roles: List of roles to assign to the admin
            organization_slug: Organization identifier for linking
            
        Returns:
            Dict containing the created user information
            
        Raises:
            Exception: If user creation fails
        """
        try:
            # Generate username from email (simple approach)
            username = admin_email.split('@')[0].lower()
            
            # Generate a temporary password (should be reset by admin on first login)
            import secrets
            import string
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(12))
            
            # Default role is organization admin
            primary_role = "org_admin" if "org_admin" in (admin_roles or []) else "instructor"
            
            # Prepare user registration request
            user_registration_data = {
                "email": admin_email,
                "username": username,
                "full_name": admin_full_name,
                "password": temp_password,
                "role": primary_role,
                "organization": organization_slug,
                "phone": admin_phone,
                "language": "en"
            }
            
            # Make HTTP request to user management service
            response = await self._http_client.post(
                f"{self._user_management_url}/auth/register",
                json=user_registration_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self._logger.info(f"Organization admin user created successfully: {admin_email}")
                
                # Return user info including temporary password for organization setup
                return {
                    "user_id": user_data.get("id"),
                    "username": user_data.get("username"),
                    "email": user_data.get("email"),
                    "full_name": user_data.get("full_name"),
                    "role": user_data.get("role"),
                    "temp_password": temp_password,  # Include for organization setup notification
                    "organization": organization_slug
                }
            else:
                error_detail = response.text
                self._logger.error(f"Failed to create organization admin user: {response.status_code} - {error_detail}")
                raise Exception(f"User creation failed: {error_detail}")
                
        except httpx.RequestError as e:
            self._logger.error(f"HTTP request failed when creating admin user: {str(e)}")
            raise Exception(f"Failed to communicate with user management service: {str(e)}")
        except Exception as e:
            self._logger.error(f"Error creating organization admin user: {str(e)}")
            raise

    async def create_organization(self, name: str, slug: str, address: str,
                                  contact_phone: str, contact_email: str, description: str = None,
                                  logo_url: str = None, domain: str = None,
                                  settings: Dict[str, Any] = None,
                                  # Organization admin parameters
                                  admin_full_name: str = None, admin_email: str = None,
                                  admin_phone: str = None, admin_roles: List[str] = None) -> Dict[str, Any]:
        """
        Create a new organization with automatic administrator user creation
        
        PURPOSE: Complete organization registration including admin user setup
        WHY: Organizations need both entity and administrative user for full functionality
        BUSINESS REQUIREMENT: Every organization must have an administrator
        
        Returns:
            Dict containing organization and admin user information
        """
        try:
            # Validate admin information is provided
            if not admin_full_name or not admin_email:
                raise ValueError("Organization administrator information (full name and email) is required")
            
            # Check if slug already exists
            if await self._organization_repository.exists_by_slug(slug):
                raise ValueError(f"Organization with slug '{slug}' already exists")

            # Check if domain already exists (if provided)
            if domain and await self._organization_repository.exists_by_domain(domain):
                raise ValueError(f"Organization with domain '{domain}' already exists")

            # Step 1: Create organization administrator user first
            self._logger.info(f"Creating organization administrator: {admin_email}")
            admin_user_info = await self._create_organization_admin_user(
                admin_full_name=admin_full_name,
                admin_email=admin_email,
                admin_phone=admin_phone,
                admin_roles=admin_roles,
                organization_slug=slug
            )

            # Step 2: Create organization entity
            organization = Organization(
                name=name,
                slug=slug,
                address=address,
                contact_phone=contact_phone,
                contact_email=contact_email,
                description=description,
                logo_url=logo_url,
                domain=domain,
                settings=settings or {}
            )

            # Validate organization
            if not organization.is_valid():
                raise ValueError("Invalid organization data")

            # Persist organization
            created_organization = await self._organization_repository.create(organization)

            self._logger.info(f"Organization created successfully: {created_organization.slug}")
            
            # Return comprehensive information including admin user details
            return {
                "organization": {
                    "id": str(created_organization.id),
                    "name": created_organization.name,
                    "slug": created_organization.slug,
                    "description": created_organization.description,
                    "address": created_organization.address,
                    "contact_phone": created_organization.contact_phone,
                    "contact_email": created_organization.contact_email,
                    "logo_url": created_organization.logo_url,
                    "domain": created_organization.domain,
                    "is_active": created_organization.is_active,
                    "created_at": created_organization.created_at.isoformat() if created_organization.created_at else None,
                    "updated_at": created_organization.updated_at.isoformat() if created_organization.updated_at else None
                },
                "admin_user": admin_user_info,
                "success": True,
                "message": f"Organization '{name}' and administrator account created successfully"
            }

        except Exception as e:
            self._logger.error(f"Error creating organization: {str(e)}")
            raise
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup HTTP client"""
        if hasattr(self, '_http_client'):
            await self._http_client.aclose()

    async def get_organization(self, organization_id: UUID) -> Optional[Organization]:
        """Get organization by ID"""
        try:
            return await self._organization_repository.get_by_id(organization_id)
        except Exception as e:
            self._logger.error(f"Error getting organization {organization_id}: {str(e)}")
            raise

    async def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug"""
        try:
            return await self._organization_repository.get_by_slug(slug)
        except Exception as e:
            self._logger.error(f"Error getting organization by slug {slug}: {str(e)}")
            raise

    async def get_organization_by_domain(self, domain: str) -> Optional[Organization]:
        """Get organization by domain"""
        try:
            return await self._organization_repository.get_by_domain(domain)
        except Exception as e:
            self._logger.error(f"Error getting organization by domain {domain}: {str(e)}")
            raise

    async def update_organization(self, organization_id: UUID, name: str = None,
                                  description: str = None, logo_url: str = None,
                                  domain: str = None, address: str = None,
                                  contact_phone: str = None, contact_email: str = None,
                                  settings: Dict[str, Any] = None,
                                  is_active: bool = None) -> Organization:
        """Update organization"""
        try:
            # Get existing organization
            organization = await self._organization_repository.get_by_id(organization_id)
            if not organization:
                raise ValueError(f"Organization with ID {organization_id} not found")

            # Check domain uniqueness if being changed
            if domain and domain != organization.domain:
                if await self._organization_repository.exists_by_domain(domain):
                    raise ValueError(f"Organization with domain '{domain}' already exists")

            # Update organization
            organization.update_info(name, description, logo_url, None, domain, address, contact_phone, contact_email, settings)
            if is_active is not None:
                if is_active:
                    organization.activate()
                else:
                    organization.deactivate()

            # Validate updated organization
            if not organization.is_valid():
                raise ValueError("Invalid organization data")

            # Persist changes
            updated_organization = await self._organization_repository.update(organization)

            self._logger.info(f"Organization updated successfully: {organization.slug}")
            return updated_organization

        except Exception as e:
            self._logger.error(f"Error updating organization {organization_id}: {str(e)}")
            raise

    async def delete_organization(self, organization_id: UUID) -> bool:
        """Delete organization"""
        try:
            # Check if organization exists
            organization = await self._organization_repository.get_by_id(organization_id)
            if not organization:
                raise ValueError(f"Organization with ID {organization_id} not found")

            # Delete organization
            result = await self._organization_repository.delete(organization_id)

            if result:
                self._logger.info(f"Organization deleted successfully: {organization.slug}")

            return result

        except Exception as e:
            self._logger.error(f"Error deleting organization {organization_id}: {str(e)}")
            raise

    async def list_organizations(self, limit: int = 100, offset: int = 0) -> List[Organization]:
        """List all organizations with pagination"""
        try:
            return await self._organization_repository.get_all(limit, offset)
        except Exception as e:
            self._logger.error(f"Error listing organizations: {str(e)}")
            raise

    async def list_active_organizations(self) -> List[Organization]:
        """List all active organizations"""
        try:
            return await self._organization_repository.get_active()
        except Exception as e:
            self._logger.error(f"Error listing active organizations: {str(e)}")
            raise

    async def search_organizations(self, query: str, limit: int = 50) -> List[Organization]:
        """Search organizations"""
        try:
            return await self._organization_repository.search(query, limit)
        except Exception as e:
            self._logger.error(f"Error searching organizations: {str(e)}")
            raise

    async def get_organization_stats(self, organization_id: UUID) -> Dict[str, Any]:
        """Get organization statistics"""
        try:
            organization = await self._organization_repository.get_by_id(organization_id)
            if not organization:
                raise ValueError(f"Organization with ID {organization_id} not found")

            # Basic stats for now - could be extended with project counts, member counts, etc.
            return {
                "id": str(organization.id),
                "name": organization.name,
                "slug": organization.slug,
                "is_active": organization.is_active,
                "created_at": organization.created_at.isoformat() if organization.created_at else None,
                "updated_at": organization.updated_at.isoformat() if organization.updated_at else None
            }

        except Exception as e:
            self._logger.error(f"Error getting organization stats {organization_id}: {str(e)}")
            raise
