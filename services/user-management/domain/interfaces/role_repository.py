"""
Role Repository Interface
Interface Segregation: Focused interface for role data access  
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.role import Role, Permission

class IRoleRepository(ABC):
    """Interface for role data access operations"""
    
    @abstractmethod
    async def create(self, role: Role) -> Role:
        """Create a new role"""
        pass
    
    @abstractmethod
    async def get_by_id(self, role_id: str) -> Optional[Role]:
        """Get role by ID"""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name"""
        pass
    
    @abstractmethod
    async def update(self, role: Role) -> Role:
        """Update role"""
        pass
    
    @abstractmethod
    async def delete(self, role_id: str) -> bool:
        """Delete role"""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[Role]:
        """Get all roles"""
        pass
    
    @abstractmethod
    async def get_active_roles(self) -> List[Role]:
        """Get active roles only"""
        pass
    
    @abstractmethod
    async def get_system_roles(self) -> List[Role]:
        """Get system roles"""
        pass
    
    @abstractmethod
    async def get_custom_roles(self) -> List[Role]:
        """Get custom (non-system) roles"""
        pass
    
    @abstractmethod
    async def exists_by_name(self, name: str) -> bool:
        """Check if role exists by name"""
        pass
    
    @abstractmethod
    async def get_roles_with_permission(self, permission: Permission) -> List[Role]:
        """Get roles that have specific permission"""
        pass
    
    @abstractmethod
    async def count_users_with_role(self, role_id: str) -> int:
        """Count users assigned to a role"""
        pass