"""
Project Repository Interface
Single Responsibility: Abstract data access contract for projects
Interface Segregation: Only project-specific operations
Dependency Inversion: Abstract interface for concrete implementations
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from domain.entities.project import Project, ProjectStatus


class IProjectRepository(ABC):
    """
    Abstract repository interface for project data access
    """

    @abstractmethod
    async def create(self, project: Project) -> Project:
        """Create a new project"""
        pass

    @abstractmethod
    async def get_by_id(self, project_id: UUID) -> Optional[Project]:
        """Get project by ID"""
        pass

    @abstractmethod
    async def get_by_organization_and_slug(self, organization_id: UUID, slug: str) -> Optional[Project]:
        """Get project by organization ID and slug"""
        pass

    @abstractmethod
    async def update(self, project: Project) -> Project:
        """Update project"""
        pass

    @abstractmethod
    async def delete(self, project_id: UUID) -> bool:
        """Delete project"""
        pass

    @abstractmethod
    async def exists_by_organization_and_slug(self, organization_id: UUID, slug: str) -> bool:
        """Check if project exists by organization ID and slug"""
        pass

    @abstractmethod
    async def get_by_organization(self, organization_id: UUID, limit: int = 100, offset: int = 0) -> List[Project]:
        """Get projects by organization"""
        pass

    @abstractmethod
    async def get_by_status(self, status: ProjectStatus, limit: int = 100, offset: int = 0) -> List[Project]:
        """Get projects by status"""
        pass

    @abstractmethod
    async def get_by_organization_and_status(self, organization_id: UUID, status: ProjectStatus) -> List[Project]:
        """Get projects by organization and status"""
        pass

    @abstractmethod
    async def search_by_organization(self, organization_id: UUID, query: str, limit: int = 50) -> List[Project]:
        """Search projects within organization"""
        pass

    @abstractmethod
    async def get_by_creator(self, creator_id: UUID) -> List[Project]:
        """Get projects created by user"""
        pass

    @abstractmethod
    async def count_by_organization(self, organization_id: UUID) -> int:
        """Count projects in organization"""
        pass

    @abstractmethod
    async def count_by_status(self, status: ProjectStatus) -> int:
        """Count projects by status"""
        pass

    @abstractmethod
    async def get_recent_by_organization(self, organization_id: UUID, days: int = 30) -> List[Project]:
        """Get recently created projects in organization"""
        pass