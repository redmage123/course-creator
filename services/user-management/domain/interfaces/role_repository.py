"""
Role Repository Interface - Permission Management Data Access Layer

This module defines the abstract interface for role and permission data access
operations within the User Management Service. It follows the Repository pattern
to abstract role storage concerns from business logic.

Architectural Benefits:
    Interface Segregation: Focused specifically on role data operations
    Dependency Inversion: Business logic depends on this abstraction
    Testability: Enables easy mocking for unit tests
    Database Agnostic: Supports multiple storage implementations
    Clean Architecture: Separates domain logic from infrastructure

Repository Pattern Implementation:
    - Centralizes role data access logic
    - Provides consistent API for role operations
    - Enables caching strategies at implementation level
    - Supports complex permission-based queries
    - Facilitates role management optimization

Role Management Features:
    - CRUD operations for role entities
    - System vs custom role distinction
    - Permission-based role queries
    - User assignment tracking
    - Active role filtering for security

Integration with Enhanced RBAC:
    This basic role repository is extended by the Organization Management
    Service for enhanced RBAC features including:
    - Organization-specific roles
    - Hierarchical permission structures
    - Resource-level authorization
    - Track-based role assignments

Author: Course Creator Platform Team
Version: 2.3.0
Last Updated: 2025-08-02
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.role import Role, Permission

class IRoleRepository(ABC):
    """
    Abstract base class defining the contract for role data access operations.
    
    This interface defines all methods required for role and permission management
    within the User Management Service. It serves as the boundary between the
    domain layer and infrastructure layer for role-related operations.
    
    Design Principles:
        - All operations are async for high-concurrency support
        - Methods operate on domain entities, not database types
        - Clear naming follows domain language
        - Support for both system and custom roles
        - Permission-based querying capabilities
        
    Role Management Capabilities:
        - Complete CRUD operations for roles
        - System role protection and management
        - Permission-based role discovery
        - User assignment tracking
        - Active role filtering for security
        
    Thread Safety:
        Implementations should be thread-safe and support concurrent access
        patterns common in async web applications.
    """
    
    @abstractmethod
    async def create(self, role: Role) -> Role:
        """
        Create a new role in the data store.
        
        Args:
            role (Role): Role entity to create
        
        Returns:
            Role: Created role with database-generated fields
        
        Raises:
            DuplicateRoleError: If role name already exists
            ValidationError: If role data is invalid
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, role_id: str) -> Optional[Role]:
        """Get role by ID"""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Role]:
        """
        Retrieve role by unique name.
        
        Args:
            name (str): Role name to search for
        
        Returns:
            Optional[Role]: Role if found, None otherwise
        """
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
        """
        Find all roles that have a specific permission.
        
        Used for authorization queries to determine which roles
        can perform specific operations.
        
        Args:
            permission (Permission): Permission to search for
        
        Returns:
            List[Role]: All roles containing the specified permission
        """
        pass
    
    @abstractmethod
    async def count_users_with_role(self, role_id: str) -> int:
        """
        Count number of users assigned to a specific role.
        
        Used for role impact analysis and deletion safety checks.
        
        Args:
            role_id (str): Role identifier
        
        Returns:
            int: Number of users with this role
        """
        pass