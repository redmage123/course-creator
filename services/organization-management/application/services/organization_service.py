"""
Organization Service - Business Logic Orchestration
Single Responsibility: Organization business operations
Open/Closed: Extensible through dependency injection
Dependency Inversion: Depends on repository abstractions
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from domain.entities.organization import Organization
from domain.interfaces.organization_repository import IOrganizationRepository


class OrganizationService:
    """
    Service class for organization business operations
    """

    def __init__(self, organization_repository: IOrganizationRepository):
        self._organization_repository = organization_repository
        self._logger = logging.getLogger(__name__)

    async def create_organization(self, name: str, slug: str, address: str,
                                  contact_phone: str, contact_email: str, description: str = None,
                                  logo_url: str = None, domain: str = None,
                                  settings: Dict[str, Any] = None) -> Organization:
        """Create a new organization"""
        try:
            # Check if slug already exists
            if await self._organization_repository.exists_by_slug(slug):
                raise ValueError(f"Organization with slug '{slug}' already exists")

            # Check if domain already exists (if provided)
            if domain and await self._organization_repository.exists_by_domain(domain):
                raise ValueError(f"Organization with domain '{domain}' already exists")

            # Create organization entity
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
            return created_organization

        except Exception as e:
            self._logger.error(f"Error creating organization: {str(e)}")
            raise

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
