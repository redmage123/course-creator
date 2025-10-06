"""
Role Models

Pydantic models for role management.
"""

from pydantic import BaseModel
from typing import Optional, List


class RoleBase(BaseModel):
    """Base role model."""
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Role creation model."""
    pass


class Role(RoleBase):
    """Complete role model."""
    id: int
    
    class Config:
        orm_mode = True


class RolePermission(BaseModel):
    """Role permission model."""
    role: str
    permissions: List[str]


class PermissionCheck(BaseModel):
    """Permission check model."""
    user_id: str
    permission: str
    granted: bool