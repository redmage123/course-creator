"""
Role Management System for Course Creator Platform

BUSINESS REQUIREMENT:
Users can have multiple roles within an organization (e.g., an instructor who is also
an organization admin, or a student who becomes an instructor). This system manages
the complex role relationships and permissions that arise from multiple role assignments.

TECHNICAL IMPLEMENTATION:
- Roles are stored as JSON arrays in the database
- Role hierarchy and permissions are managed programmatically  
- Role conflicts are resolved through precedence rules
- Audit trails track role changes for security compliance

ROLE HIERARCHY (highest to lowest precedence):
1. site_admin - Platform super admin
2. organization_admin - Organization administrator  
3. instructor - Course instructor
4. student - Course student

SECURITY CONSIDERATIONS:
- Role elevation must be approved by higher-privilege users
- All role changes are logged for audit purposes
- Role combinations are validated for business logic consistency
- Permissions are calculated from the union of all assigned roles
"""

import json
from typing import List, Set, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class UserRole(str, Enum):
    """User roles in order of precedence (highest to lowest)"""
    SITE_ADMIN = "site_admin"
    ORGANIZATION_ADMIN = "organization_admin" 
    INSTRUCTOR = "instructor"
    STUDENT = "student"


class RoleManager:
    """
    Role Management System for Multi-Role Users
    
    Handles the complexity of users having multiple roles within organizations,
    including role precedence, permission calculation, and business rule validation.
    """
    
    # Role precedence mapping (lower number = higher precedence)
    ROLE_PRECEDENCE = {
        UserRole.SITE_ADMIN: 1,
        UserRole.ORGANIZATION_ADMIN: 2,
        UserRole.INSTRUCTOR: 3,
        UserRole.STUDENT: 4
    }
    
    # Valid role combinations (which roles can coexist)
    VALID_ROLE_COMBINATIONS = {
        frozenset([UserRole.SITE_ADMIN]),  # Site admin can be standalone
        frozenset([UserRole.ORGANIZATION_ADMIN]),  # Org admin can be standalone
        frozenset([UserRole.ORGANIZATION_ADMIN, UserRole.INSTRUCTOR]),  # Org admin + instructor
        frozenset([UserRole.ORGANIZATION_ADMIN, UserRole.STUDENT]),  # Org admin + student (rare but valid)
        frozenset([UserRole.INSTRUCTOR]),  # Instructor can be standalone
        frozenset([UserRole.INSTRUCTOR, UserRole.STUDENT]),  # Instructor + student (learning while teaching)
        frozenset([UserRole.STUDENT]),  # Student can be standalone
        frozenset([UserRole.ORGANIZATION_ADMIN, UserRole.INSTRUCTOR, UserRole.STUDENT])  # All teaching roles
    }
    
    def __init__(self):
        """Initialize role manager with business rules"""
        pass
    
    def validate_role_combination(self, roles: List[str]) -> dict:
        """
        Validate that a combination of roles is allowed by business rules.
        
        Args:
            roles: List of role strings to validate
            
        Returns:
            dict: Validation result with is_valid, roles, and reason
        """
        result = {
            'is_valid': False,
            'roles': [],
            'highest_role': None,
            'reason': None
        }
        
        try:
            # Convert to UserRole enums and validate
            role_enums = []
            for role_str in roles:
                try:
                    role_enum = UserRole(role_str)
                    role_enums.append(role_enum)
                except ValueError:
                    result['reason'] = f"Invalid role: {role_str}"
                    return result
            
            # Remove duplicates and sort by precedence
            unique_roles = list(set(role_enums))
            unique_roles.sort(key=lambda r: self.ROLE_PRECEDENCE[r])
            
            result['roles'] = [r.value for r in unique_roles]
            result['highest_role'] = unique_roles[0].value
            
            # Check if combination is valid
            role_set = frozenset(unique_roles)
            
            # Site admin cannot have other roles (too much power)
            if UserRole.SITE_ADMIN in role_set and len(role_set) > 1:
                result['reason'] = "Site admin cannot have additional roles for security reasons"
                return result
            
            # Check against valid combinations
            if role_set in self.VALID_ROLE_COMBINATIONS:
                result['is_valid'] = True
                result['reason'] = f"Valid role combination: {', '.join(result['roles'])}"
                return result
            
            result['reason'] = f"Invalid role combination: {', '.join(result['roles'])}"
            return result
            
        except Exception as e:
            result['reason'] = f"Role validation error: {str(e)}"
            return result
    
    def get_effective_permissions(self, roles: List[str]) -> Set[str]:
        """
        Calculate effective permissions from multiple roles.
        
        Args:
            roles: List of user roles
            
        Returns:
            Set of permission strings
        """
        all_permissions = set()
        
        for role_str in roles:
            try:
                role = UserRole(role_str)
                permissions = self._get_role_permissions(role)
                all_permissions.update(permissions)
            except ValueError:
                continue  # Skip invalid roles
        
        return all_permissions
    
    def _get_role_permissions(self, role: UserRole) -> Set[str]:
        """Get permissions for a specific role"""
        permission_map = {
            UserRole.SITE_ADMIN: {
                'manage_platform', 'manage_all_organizations', 'manage_all_users',
                'view_system_analytics', 'configure_platform', 'manage_billing'
            },
            UserRole.ORGANIZATION_ADMIN: {
                'manage_organization', 'manage_org_users', 'create_courses',
                'manage_instructors', 'view_org_analytics', 'manage_org_settings',
                'approve_courses', 'manage_lab_environments'
            },
            UserRole.INSTRUCTOR: {
                'create_courses', 'manage_own_courses', 'grade_students',
                'view_student_progress', 'manage_course_content', 'create_assessments',
                'manage_lab_sessions', 'view_course_analytics'
            },
            UserRole.STUDENT: {
                'enroll_courses', 'submit_assignments', 'take_assessments',
                'view_own_progress', 'access_course_materials', 'participate_labs',
                'provide_feedback'
            }
        }
        
        return permission_map.get(role, set())
    
    def can_assign_role(self, assigner_roles: List[str], target_role: str) -> bool:
        """
        Check if a user with assigner_roles can assign target_role to another user.
        
        Business Rule: Users can only assign roles of equal or lower precedence than their highest role.
        """
        if not assigner_roles:
            return False
        
        try:
            # Get highest role of assigner
            assigner_role_enums = [UserRole(r) for r in assigner_roles if r in UserRole.__members__.values()]
            if not assigner_role_enums:
                return False
            
            highest_assigner_role = min(assigner_role_enums, key=lambda r: self.ROLE_PRECEDENCE[r])
            target_role_enum = UserRole(target_role)
            
            # Site admin can assign any role
            if highest_assigner_role == UserRole.SITE_ADMIN:
                return True
            
            # Others can only assign roles with equal or lower precedence
            return self.ROLE_PRECEDENCE[target_role_enum] >= self.ROLE_PRECEDENCE[highest_assigner_role]
            
        except ValueError:
            return False
    
    def get_user_display_role(self, roles: List[str]) -> str:
        """
        Get the primary role for display purposes (highest precedence).
        
        Args:
            roles: List of user roles
            
        Returns:
            Primary role string for UI display
        """
        if not roles:
            return "student"  # Default role
        
        try:
            valid_roles = [UserRole(r) for r in roles if r in UserRole.__members__.values()]
            if not valid_roles:
                return "student"
            
            # Return highest precedence role
            primary_role = min(valid_roles, key=lambda r: self.ROLE_PRECEDENCE[r])
            return primary_role.value
            
        except Exception:
            return "student"  # Fallback
    
    def format_roles_for_database(self, roles: List[str]) -> str:
        """
        Format roles list as JSON string for database storage.
        
        Args:
            roles: List of role strings
            
        Returns:
            JSON string for database storage
        """
        validation = self.validate_role_combination(roles)
        if not validation['is_valid']:
            raise ValueError(f"Invalid role combination: {validation['reason']}")
        
        return json.dumps(validation['roles'])
    
    def parse_roles_from_database(self, roles_json: str) -> List[str]:
        """
        Parse roles from database JSON format.
        
        Args:
            roles_json: JSON string from database
            
        Returns:
            List of role strings
        """
        try:
            if isinstance(roles_json, str):
                return json.loads(roles_json)
            elif isinstance(roles_json, list):
                return roles_json
            else:
                return ["student"]  # Default fallback
        except (json.JSONDecodeError, TypeError):
            return ["student"]  # Default fallback
    
    def add_role_to_user(self, current_roles: List[str], new_role: str) -> List[str]:
        """
        Add a new role to user's existing roles.
        
        Args:
            current_roles: User's current roles
            new_role: Role to add
            
        Returns:
            Updated list of roles
        """
        updated_roles = list(set(current_roles + [new_role]))
        validation = self.validate_role_combination(updated_roles)
        
        if not validation['is_valid']:
            raise ValueError(f"Cannot add role {new_role}: {validation['reason']}")
        
        return validation['roles']
    
    def remove_role_from_user(self, current_roles: List[str], role_to_remove: str) -> List[str]:
        """
        Remove a role from user's existing roles.
        
        Args:
            current_roles: User's current roles
            role_to_remove: Role to remove
            
        Returns:
            Updated list of roles
        """
        updated_roles = [r for r in current_roles if r != role_to_remove]
        
        # Ensure user always has at least student role
        if not updated_roles:
            updated_roles = ["student"]
        
        validation = self.validate_role_combination(updated_roles)
        if not validation['is_valid']:
            raise ValueError(f"Cannot remove role {role_to_remove}: {validation['reason']}")
        
        return validation['roles']


# Global role manager instance
_role_manager = None

def get_role_manager() -> RoleManager:
    """Get shared role manager instance"""
    global _role_manager
    if _role_manager is None:
        _role_manager = RoleManager()
    return _role_manager