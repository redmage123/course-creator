"""
Role Domain Entity - Fine-Grained Permission Management System

This module defines the Role domain entity and Permission enumeration for the
Course Creator Platform's authorization system. It provides fine-grained
permission control that complements the basic role system in the User entity.

Domain Model Design:
    - Role Entity: Contains permissions and metadata for flexible authorization
    - Permission Enum: Defines atomic permissions for specific operations
    - Rich Domain Model: Business logic for permission management and validation
    - System Roles: Predefined roles for standard platform operations

Integration with Enhanced RBAC:
    This service provides basic role and permission management that is extended
    by the Organization Management Service for enhanced RBAC with:
    - Multi-tenant organization permissions
    - Granular resource-level authorization
    - Track-based learning permissions
    - Meeting room access controls

Permission Categories:
    - User Management: Create, read, update, delete users
    - Course Management: Full course lifecycle permissions
    - Content Management: Content creation and modification
    - Analytics Access: Various levels of analytics viewing
    - System Administration: Platform-wide administrative access
    - Lab Management: Container and environment permissions

Design Patterns Applied:
    - Entity Pattern: Role has identity and lifecycle
    - Strategy Pattern: Different permission sets for different roles
    - Enum Pattern: Type-safe permission definitions
    - Factory Pattern: Default role creation

Security Principles:
    - Principle of Least Privilege: Minimal permissions for each role
    - Defense in Depth: Multiple layers of permission checking
    - Immutable Permissions: Enum values prevent permission modification
    - Audit Trail: Timestamp tracking for all permission changes

Author: Course Creator Platform Team
Version: 2.3.0
Last Updated: 2025-08-02
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Set, Dict, Any, Optional
from enum import Enum
import uuid

class Permission(Enum):
    """
    Atomic Permission Enumeration for Fine-Grained Access Control
    
    This enumeration defines all atomic permissions available in the Course Creator
    Platform. Each permission represents a specific operation that can be granted
    or denied to users through their roles.
    
    Permission Design Principles:
        - Atomic: Each permission represents a single, specific operation
        - Immutable: Enum values cannot be modified at runtime
        - Descriptive: Clear naming indicates the operation allowed
        - Granular: Fine-grained control over platform features
        - Extensible: New permissions can be added without breaking existing code
    
    Permission Categories and Business Logic:
        
        User Management Permissions:
            - Controls who can manage user accounts and profiles
            - Critical for platform administration and security
            - Should be restricted to administrative roles
        
        Course Management Permissions:
            - Controls course lifecycle from creation to deletion
            - Instructors need most course permissions for their content
            - Publishing permissions may be restricted for quality control
        
        Content Management Permissions:
            - Controls creation and modification of learning materials
            - Export permissions enable content sharing and backup
            - Read permissions allow content consumption
        
        Analytics Permissions:
            - VIEW_ANALYTICS: User's own analytics or instructor's course analytics
            - EXPORT_ANALYTICS: Download analytics data and reports
            - VIEW_ALL_ANALYTICS: Platform-wide analytics (admin only)
        
        System Administration Permissions:
            - Highest privilege permissions for platform management
            - Should be restricted to system administrators only
            - Enable platform configuration and monitoring
        
        Lab Management Permissions:
            - ACCESS_LAB: Basic lab container access for students/instructors
            - MANAGE_LABS: Administrative control over lab environments
    
    Integration Notes:
        - These permissions are checked by authorization decorators
        - Enhanced RBAC system extends these with organization-specific permissions
        - Permission checks are performed at API endpoint and service levels
        - Caching strategies should be implemented for frequent permission checks
    """
    
    # User Management Permissions - Control user account operations
    CREATE_USER = "create_user"        # Create new user accounts
    READ_USER = "read_user"            # View user profiles and information
    UPDATE_USER = "update_user"        # Modify user accounts and profiles
    DELETE_USER = "delete_user"        # Remove user accounts from system
    
    # Course Management Permissions - Control course lifecycle operations
    CREATE_COURSE = "create_course"    # Create new courses and curricula
    READ_COURSE = "read_course"        # View course content and information
    UPDATE_COURSE = "update_course"    # Modify existing course content
    DELETE_COURSE = "delete_course"    # Remove courses from the platform
    PUBLISH_COURSE = "publish_course"  # Make courses available to students
    ENROLL_STUDENT = "enroll_student"  # Manage student course enrollments
    
    # Content Management Permissions - Control learning material operations
    CREATE_CONTENT = "create_content"  # Create slides, exercises, quizzes
    READ_CONTENT = "read_content"      # Access learning materials
    UPDATE_CONTENT = "update_content"  # Modify existing content
    DELETE_CONTENT = "delete_content"  # Remove content from courses
    EXPORT_CONTENT = "export_content"  # Download content in various formats
    
    # Analytics Permissions - Control access to platform analytics
    VIEW_ANALYTICS = "view_analytics"        # View relevant analytics dashboards
    EXPORT_ANALYTICS = "export_analytics"    # Download analytics reports
    VIEW_ALL_ANALYTICS = "view_all_analytics" # Platform-wide analytics access
    
    # System Administration Permissions - Platform management operations
    MANAGE_SYSTEM = "manage_system"    # System configuration and administration
    MANAGE_ROLES = "manage_roles"      # Role and permission management
    VIEW_LOGS = "view_logs"           # Access system logs and audit trails
    
    # Lab Environment Permissions - Container and development environment access
    ACCESS_LAB = "access_lab"          # Basic lab container access
    MANAGE_LABS = "manage_labs"        # Administrative lab environment control

@dataclass
class Role:
    """
    Role Domain Entity - Permission Container with Business Logic
    
    This class represents a role within the Course Creator Platform, implementing
    a flexible permission-based authorization system. Roles aggregate permissions
    and provide business logic for authorization decisions.
    
    Domain Model Characteristics:
        - Entity Pattern: Has unique identity and lifecycle management
        - Aggregate Root: Manages permissions as value objects within the role
        - Rich Domain Model: Contains business logic for permission operations
        - Immutable Permissions: Permissions are validated enum values
        - Audit Trail: Tracks creation and modification timestamps
    
    Core Responsibilities:
        - Permission aggregation and management
        - Authorization decision support
        - Role lifecycle management (active/inactive)
        - System role protection (prevent modification)
        - Metadata storage for extensibility
        - Validation of role integrity
    
    Business Rules:
        1. Role names must be unique and descriptive
        2. Descriptions are required for clarity
        3. Only valid Permission enum values are allowed
        4. System roles cannot be deactivated
        5. Permission changes update modification timestamp
        6. Roles must have at least a name and description
    
    Permission Management Strategy:
        - Set-based storage prevents duplicate permissions
        - Type safety through Permission enum validation
        - Atomic operations for permission addition/removal
        - Bulk operations for permission set management
        - Query methods for authorization decisions
    
    Integration with Authorization:
        - Used by authorization decorators for endpoint protection
        - Integrated with JWT tokens for stateless authorization
        - Cached for performance in high-frequency authorization
        - Extended by Enhanced RBAC for organization-specific permissions
    
    Usage Examples:
        # Create custom role
        role = Role(
            name="content_creator",
            description="Can create and edit content",
            permissions={Permission.CREATE_CONTENT, Permission.UPDATE_CONTENT}
        )
        
        # Check permissions
        if role.has_permission(Permission.CREATE_COURSE):
            # Allow course creation
        
        # Manage permissions
        role.add_permission(Permission.PUBLISH_COURSE)
        role.remove_permission(Permission.DELETE_CONTENT)
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
        """
        Post-initialization validation and setup for role entity.
        
        Ensures the role is in a valid state immediately after creation
        by validating all business rules and constraints.
        
        Raises:
            ValueError: If any validation rule fails
        """
        self.validate()
    
    def validate(self) -> None:
        """
        Comprehensive validation of role data against business rules.
        
        Validates role integrity including name, description, and permissions
        to ensure the role can be safely used for authorization decisions.
        
        Business Rules Enforced:
            - Name is required and meaningful (minimum 2 characters)
            - Description is required for role clarity
            - All permissions must be valid Permission enum values
        
        Raises:
            ValueError: Specific error message for validation failures
        """
        if not self.name:
            raise ValueError("Role name is required")
        
        if len(self.name) < 2:
            raise ValueError("Role name must be at least 2 characters")
        
        if not self.description:
            raise ValueError("Role description is required")
        
        # Validate permissions are Permission enum values for type safety
        for permission in self.permissions:
            if not isinstance(permission, Permission):
                raise ValueError(f"Invalid permission: {permission}")
    
    def add_permission(self, permission: Permission) -> None:
        """
        Add a single permission to this role with validation and audit trail.

        This method enables dynamic permission management by adding individual
        permissions to a role's permission set. It ensures type safety and
        maintains an audit trail through timestamp updates.

        Business Logic:
            - Only valid Permission enum values are accepted
            - Duplicate permissions are automatically handled by set data structure
            - Permission additions are immediately effective
            - Timestamp is updated for audit purposes

        Args:
            permission (Permission): The permission to add to this role.
                                    Must be a valid Permission enum value.

        Returns:
            None: Method modifies the role object in place

        Raises:
            ValueError: If permission is not a valid Permission enum value

        Usage Examples:
            # Add course creation permission to a role
            role.add_permission(Permission.CREATE_COURSE)

            # Add multiple permissions sequentially
            role.add_permission(Permission.READ_CONTENT)
            role.add_permission(Permission.UPDATE_CONTENT)

        Integration Notes:
            - Permission changes should be logged by calling services
            - May trigger cache invalidation in authorization systems
            - Should be accompanied by user notifications if affecting active users
            - Consider authorization checks before allowing permission additions

        Design Rationale:
            - Set-based storage prevents duplicate permissions automatically
            - Type validation ensures only valid permissions are added
            - Atomic operation maintains data integrity
            - Audit trail supports compliance requirements
        """
        if not isinstance(permission, Permission):
            raise ValueError("Permission must be a Permission enum value")

        self.permissions.add(permission)
        self.updated_at = datetime.utcnow()
    
    def remove_permission(self, permission: Permission) -> None:
        """
        Remove a single permission from this role safely with audit trail.

        This method enables permission revocation by removing individual permissions
        from a role's permission set. It uses safe removal that doesn't fail if the
        permission doesn't exist, making it idempotent.

        Business Logic:
            - Safely removes permission even if not present (idempotent operation)
            - Uses discard() instead of remove() to avoid KeyError
            - Permission removals are immediately effective
            - Timestamp is updated for audit purposes

        Args:
            permission (Permission): The permission to remove from this role.
                                    Can be any Permission enum value.

        Returns:
            None: Method modifies the role object in place

        Usage Examples:
            # Remove course deletion permission from a role
            role.remove_permission(Permission.DELETE_COURSE)

            # Safe removal even if permission doesn't exist
            role.remove_permission(Permission.MANAGE_SYSTEM)  # No error if not present

        Security Implications:
            - Permission removal immediately affects authorization decisions
            - Active users with this role lose access instantly
            - Should be logged for security auditing
            - May require user notification for compliance

        Integration Notes:
            - Permission changes should trigger cache invalidation
            - Calling services should log permission removals
            - Consider session invalidation for affected users
            - May need to notify users of permission changes

        Design Rationale:
            - Idempotent operation prevents errors from repeated calls
            - discard() method is safer than remove() for this use case
            - Immediate effect ensures security constraints are enforced
            - Audit trail maintained through timestamp update
        """
        self.permissions.discard(permission)
        self.updated_at = datetime.utcnow()
    
    def has_permission(self, permission: Permission) -> bool:
        """
        Check if role has a specific permission.
        
        This is the primary method for authorization decisions, used
        throughout the platform to determine if operations are allowed.
        
        Args:
            permission (Permission): The permission to check for
        
        Returns:
            bool: True if role has the permission, False otherwise
        
        Usage:
            if role.has_permission(Permission.CREATE_COURSE):
                # Allow course creation
        """
        return permission in self.permissions
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """
        Check if role has at least one permission from a list of permissions.

        This method implements "OR" logic for permission checking, determining
        if a role has ANY of the specified permissions. Useful for authorization
        scenarios where multiple permissions could grant access.

        Business Logic:
            - Returns True if role has one or more of the specified permissions
            - Returns False only if role has none of the specified permissions
            - Empty permission list returns False (no permissions to check)
            - Efficient short-circuit evaluation stops at first match

        Args:
            permissions (List[Permission]): List of permissions to check against.
                                           Any one match will return True.

        Returns:
            bool: True if role has any of the permissions, False otherwise

        Usage Examples:
            # Check if role can perform any user management operation
            user_mgmt_perms = [Permission.CREATE_USER, Permission.UPDATE_USER, Permission.DELETE_USER]
            if role.has_any_permission(user_mgmt_perms):
                # User can perform at least one user management operation

            # Check for read access to either courses or content
            read_perms = [Permission.READ_COURSE, Permission.READ_CONTENT]
            if role.has_any_permission(read_perms):
                # User has some form of read access

        Authorization Pattern:
            - "OR" logic: Multiple valid permissions for the same operation
            - Useful for feature access where different permissions grant access
            - More permissive than has_all_permissions()
            - Common pattern for read access and viewing capabilities

        Performance Notes:
            - Short-circuit evaluation for efficiency
            - Stops checking after first matching permission found
            - Suitable for frequent authorization checks
        """
        return any(perm in self.permissions for perm in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """
        Check if role has all permissions from a list of permissions.

        This method implements "AND" logic for permission checking, determining
        if a role has ALL of the specified permissions. Useful for authorization
        scenarios that require multiple permissions simultaneously.

        Business Logic:
            - Returns True only if role has every specified permission
            - Returns False if role is missing even one of the permissions
            - Empty permission list returns True (vacuous truth)
            - Efficient short-circuit evaluation stops at first missing permission

        Args:
            permissions (List[Permission]): List of permissions to check against.
                                           All must be present for True result.

        Returns:
            bool: True if role has all specified permissions, False otherwise

        Usage Examples:
            # Check if role can fully manage courses (requires all permissions)
            full_course_mgmt = [
                Permission.CREATE_COURSE,
                Permission.UPDATE_COURSE,
                Permission.DELETE_COURSE,
                Permission.PUBLISH_COURSE
            ]
            if role.has_all_permissions(full_course_mgmt):
                # User has complete course management capabilities

            # Check for complete analytics access
            analytics_perms = [Permission.VIEW_ANALYTICS, Permission.EXPORT_ANALYTICS]
            if role.has_all_permissions(analytics_perms):
                # User can both view and export analytics

        Authorization Pattern:
            - "AND" logic: All permissions required for operation
            - More restrictive than has_any_permission()
            - Used for privileged operations requiring multiple capabilities
            - Common pattern for administrative functions

        Performance Notes:
            - Short-circuit evaluation for efficiency
            - Stops checking after first missing permission found
            - Suitable for frequent authorization checks
        """
        return all(perm in self.permissions for perm in permissions)
    
    def can_manage_users(self) -> bool:
        """
        Check if role has user management capabilities.
        
        Determines if the role can perform any user administration tasks
        by checking for user management permissions.
        
        Returns:
            bool: True if role can manage users, False otherwise
        
        Business Logic:
            Role can manage users if it has any of:
            - CREATE_USER: Can create new accounts
            - UPDATE_USER: Can modify existing accounts
            - DELETE_USER: Can remove accounts
        """
        user_management_permissions = [
            Permission.CREATE_USER, Permission.UPDATE_USER, Permission.DELETE_USER
        ]
        return self.has_any_permission(user_management_permissions)
    
    def can_manage_courses(self) -> bool:
        """
        Check if role has course management capabilities.

        Determines if the role can perform any course administration tasks
        by checking for course management permissions. This is a convenience
        method for authorization decisions related to course operations.

        Business Logic:
            Role can manage courses if it has any of:
            - CREATE_COURSE: Can create new courses
            - UPDATE_COURSE: Can modify existing courses
            - DELETE_COURSE: Can remove courses
            - PUBLISH_COURSE: Can publish courses to students

        Returns:
            bool: True if role can manage courses, False otherwise

        Usage Examples:
            if role.can_manage_courses():
                # Show course management interface
                # Allow access to course admin features

        Authorization Pattern:
            - Uses "OR" logic - any course permission grants access
            - Suitable for gating course management features
            - Less restrictive than requiring all course permissions
            - Common in instructor and admin roles

        Integration Notes:
            - Used by course management UI to show/hide features
            - API endpoints use this for coarse-grained authorization
            - Fine-grained permissions checked for specific operations
            - Enhanced RBAC may add organization-specific course permissions
        """
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
    """
    Factory function for creating default system roles.
    
    Creates the three standard roles used throughout the platform:
    student, instructor, and admin. These roles define the basic
    permission hierarchy for the Course Creator Platform.
    
    Returns:
        List[Role]: List of default system roles with appropriate permissions
        
    Usage:
        roles = create_default_roles()
        for role in roles:
            role_repository.create(role)
    """
    
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