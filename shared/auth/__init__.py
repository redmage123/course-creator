"""
Authentication and Authorization utilities for Course Creator Platform

This module provides:
- Multi-role user management
- Role-based access control (RBAC)
- Permission calculation and validation
- Authentication middleware
"""

from .role_manager import (
    RoleManager,
    UserRole,
    get_role_manager
)

__all__ = [
    'RoleManager',
    'UserRole', 
    'get_role_manager'
]