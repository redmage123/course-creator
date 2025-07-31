"""
Organization Repository Interface
Single Responsibility: Abstract data access contract for organizations
Interface Segregation: Only organization-specific operations
Dependency Inversion: Abstract interface for concrete implementations
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from domain.entities.organization import Organization


class IOrganizationRepository(ABC):
    """
    Abstract repository interface for organization data access
    """

    @abstractmethod
    async def create(self, organization: Organization) -> Organization:
        """Create a new organization"""
        pass

    @abstractmethod
    async def get_by_id(self, organization_id: UUID) -> Optional[Organization]:
        """Get organization by ID"""
        pass

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug"""
        pass

    @abstractmethod
    async def get_by_domain(self, domain: str) -> Optional[Organization]:
        """Get organization by domain"""
        pass

    @abstractmethod
    async def update(self, organization: Organization) -> Organization:
        """Update organization"""
        pass

    @abstractmethod
    async def delete(self, organization_id: UUID) -> bool:
        """Delete organization"""
        pass

    @abstractmethod
    async def exists_by_slug(self, slug: str) -> bool:
        """Check if organization exists by slug"""
        pass

    @abstractmethod
    async def exists_by_domain(self, domain: str) -> bool:
        """Check if organization exists by domain"""
        pass

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Organization]:
        """Get all organizations with pagination"""
        pass

    @abstractmethod
    async def get_active(self) -> List[Organization]:
        """Get all active organizations"""
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 50) -> List[Organization]:
        """Search organizations by name or slug"""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Count total organizations"""
        pass

    @abstractmethod
    async def count_active(self) -> int:
        """Count active organizations"""
        pass