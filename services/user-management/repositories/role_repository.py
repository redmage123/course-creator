"""
Role Repository

Database operations for role management.
"""

import logging
from typing import Dict, Any, Optional, List

from .base_repository import BaseRepository
from ..models.role import Role


class RoleRepository(BaseRepository):
    """
    Repository for role data operations.
    
    Handles database operations for role management.
    """
    
    def __init__(self, database):
        """
        Initialize role repository.
        
        Args:
            database: Database connection instance
        """
        super().__init__(database)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def get_all_roles(self) -> List[Role]:
        """
        Get all available roles.
        
        Returns:
            List of all roles
        """
        try:
            # For now, return hardcoded roles
            # In a more complex system, this would query a roles table
            return [
                Role(id=1, name="admin", description="Administrator"),
                Role(id=2, name="instructor", description="Course Instructor"),
                Role(id=3, name="student", description="Student")
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting all roles: {e}")
            return []
    
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """
        Get role by name.
        
        Args:
            name: Role name
            
        Returns:
            Role or None if not found
        """
        try:
            roles = await self.get_all_roles()
            for role in roles:
                if role.name == name:
                    return role
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting role by name {name}: {e}")
            return None
    
    async def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """
        Get role by ID.
        
        Args:
            role_id: Role ID
            
        Returns:
            Role or None if not found
        """
        try:
            roles = await self.get_all_roles()
            for role in roles:
                if role.id == role_id:
                    return role
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting role by ID {role_id}: {e}")
            return None
    
    async def validate_role(self, role_name: str) -> bool:
        """
        Validate if a role exists.
        
        Args:
            role_name: Role name to validate
            
        Returns:
            True if role exists, False otherwise
        """
        try:
            role = await self.get_role_by_name(role_name)
            return role is not None
            
        except Exception as e:
            self.logger.error(f"Error validating role {role_name}: {e}")
            return False
    
    async def get_role_permissions(self, role_name: str) -> List[str]:
        """
        Get permissions for a role.
        
        Args:
            role_name: Role name
            
        Returns:
            List of permissions
        """
        try:
            # Define role permissions
            role_permissions = {
                "admin": [
                    "user:create",
                    "user:read",
                    "user:update", 
                    "user:delete",
                    "course:create",
                    "course:read",
                    "course:update",
                    "course:delete",
                    "system:admin"
                ],
                "instructor": [
                    "user:read",
                    "course:create",
                    "course:read",
                    "course:update",
                    "course:delete_own",
                    "student:grade"
                ],
                "student": [
                    "course:read",
                    "course:enroll",
                    "exercise:submit",
                    "quiz:take"
                ]
            }
            
            return role_permissions.get(role_name, [])
            
        except Exception as e:
            self.logger.error(f"Error getting permissions for role {role_name}: {e}")
            return []
    
    async def check_permission(self, role_name: str, permission: str) -> bool:
        """
        Check if a role has a specific permission.
        
        Args:
            role_name: Role name
            permission: Permission to check
            
        Returns:
            True if role has permission, False otherwise
        """
        try:
            permissions = await self.get_role_permissions(role_name)
            return permission in permissions
            
        except Exception as e:
            self.logger.error(f"Error checking permission {permission} for role {role_name}: {e}")
            return False