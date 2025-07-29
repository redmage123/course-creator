"""
Role Domain Entity
Single Responsibility: Encapsulates role and permission business logic
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Set, Dict, Any, Optional
from enum import Enum
import uuid

class Permission(Enum):
    # User permissions
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    
    # Course permissions
    CREATE_COURSE = "create_course"
    READ_COURSE = "read_course"
    UPDATE_COURSE = "update_course"
    DELETE_COURSE = "delete_course"
    PUBLISH_COURSE = "publish_course"
    ENROLL_STUDENT = "enroll_student"
    
    # Content permissions
    CREATE_CONTENT = "create_content"
    READ_CONTENT = "read_content"
    UPDATE_CONTENT = "update_content"
    DELETE_CONTENT = "delete_content"
    EXPORT_CONTENT = "export_content"
    
    # Analytics permissions
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_ANALYTICS = "export_analytics"
    VIEW_ALL_ANALYTICS = "view_all_analytics"
    
    # System administration
    MANAGE_SYSTEM = "manage_system"
    MANAGE_ROLES = "manage_roles"
    VIEW_LOGS = "view_logs"
    
    # Lab permissions
    ACCESS_LAB = "access_lab"
    MANAGE_LABS = "manage_labs"

@dataclass
class Role:
    """
    Role domain entity with permissions and business logic
    """
    name: str
    description: str
    permissions: Set[Permission] = field(default_factory=set)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_system_role: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate role data after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate role data"""
        if not self.name:
            raise ValueError("Role name is required")
        
        if len(self.name) < 2:
            raise ValueError("Role name must be at least 2 characters")
        
        if not self.description:
            raise ValueError("Role description is required")
        
        # Validate permissions are Permission enum values
        for permission in self.permissions:
            if not isinstance(permission, Permission):
                raise ValueError(f"Invalid permission: {permission}")
    
    def add_permission(self, permission: Permission) -> None:
        """Add permission to role"""
        if not isinstance(permission, Permission):
            raise ValueError("Permission must be a Permission enum value")
        
        self.permissions.add(permission)
        self.updated_at = datetime.utcnow()
    
    def remove_permission(self, permission: Permission) -> None:
        """Remove permission from role"""
        self.permissions.discard(permission)
        self.updated_at = datetime.utcnow()
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if role has specific permission"""
        return permission in self.permissions
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if role has any of the specified permissions"""
        return any(perm in self.permissions for perm in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if role has all specified permissions"""
        return all(perm in self.permissions for perm in permissions)
    
    def can_manage_users(self) -> bool:
        """Check if role can manage users"""
        user_management_permissions = [
            Permission.CREATE_USER, Permission.UPDATE_USER, Permission.DELETE_USER
        ]
        return self.has_any_permission(user_management_permissions)
    
    def can_manage_courses(self) -> bool:
        """Check if role can manage courses"""
        course_management_permissions = [
            Permission.CREATE_COURSE, Permission.UPDATE_COURSE, 
            Permission.DELETE_COURSE, Permission.PUBLISH_COURSE
        ]
        return self.has_any_permission(course_management_permissions)
    
    def can_view_analytics(self) -> bool:
        """Check if role can view analytics"""
        return self.has_permission(Permission.VIEW_ANALYTICS)
    
    def can_access_system_admin(self) -> bool:
        """Check if role can access system administration"""
        return self.has_permission(Permission.MANAGE_SYSTEM)
    
    def set_permissions(self, permissions: List[Permission]) -> None:
        """Set role permissions (replaces existing)"""
        # Validate all permissions
        for permission in permissions:
            if not isinstance(permission, Permission):
                raise ValueError(f"Invalid permission: {permission}")
        
        self.permissions = set(permissions)
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate the role"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the role"""
        if self.is_system_role:
            raise ValueError("Cannot deactivate system role")
        
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def update_description(self, description: str) -> None:
        """Update role description"""
        if not description:
            raise ValueError("Description is required")
        
        self.description = description
        self.updated_at = datetime.utcnow()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to role"""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert role to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'permissions': [perm.value for perm in self.permissions],
            'is_system_role': self.is_system_role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }

# Default system roles
def create_default_roles() -> List[Role]:
    """Create default system roles"""
    
    # Student role
    student_permissions = {
        Permission.READ_COURSE,
        Permission.READ_CONTENT,
        Permission.ACCESS_LAB,
        Permission.VIEW_ANALYTICS  # Own analytics only
    }
    
    student_role = Role(
        name="student",
        description="Default student role with basic course access",
        permissions=student_permissions,
        is_system_role=True
    )
    
    # Instructor role
    instructor_permissions = {
        Permission.CREATE_COURSE,
        Permission.READ_COURSE,
        Permission.UPDATE_COURSE,
        Permission.PUBLISH_COURSE,
        Permission.ENROLL_STUDENT,
        Permission.CREATE_CONTENT,
        Permission.READ_CONTENT,
        Permission.UPDATE_CONTENT,
        Permission.DELETE_CONTENT,
        Permission.EXPORT_CONTENT,
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_ANALYTICS,
        Permission.MANAGE_LABS,
        Permission.ACCESS_LAB
    }
    
    instructor_role = Role(
        name="instructor",
        description="Instructor role with course and content management permissions",
        permissions=instructor_permissions,
        is_system_role=True
    )
    
    # Admin role
    admin_permissions = set(Permission)  # All permissions
    
    admin_role = Role(
        name="admin",
        description="Administrator role with full system permissions",
        permissions=admin_permissions,
        is_system_role=True
    )
    
    return [student_role, instructor_role, admin_role]