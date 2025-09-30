"""
Organization Management Data Access Object (DAO)

This module implements the Data Access Object (DAO) pattern for organization management operations,
centralizing all SQL queries and database interactions in a single, maintainable location.

Business Context:
The Organization Management service is the foundation of the Course Creator Platform's multi-tenant
architecture. It handles organization creation, user membership management, project tracking,
and role-based access control. By centralizing all SQL operations in this DAO, we achieve:
- Single source of truth for all organization-related database queries
- Enhanced security through consistent multi-tenant data access patterns
- Improved maintainability and testing capabilities
- Clear separation between business logic and data access concerns
- Better performance through optimized query patterns

Technical Rationale:
- Follows the Single Responsibility Principle by isolating data access concerns
- Enables comprehensive transaction support for complex organizational operations
- Provides consistent error handling using shared platform exceptions
- Supports connection pooling for optimal database resource utilization
- Facilitates database schema evolution without affecting business logic
- Enables easier unit testing through clear interface boundaries
"""

import asyncpg
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import json
import sys
sys.path.append('/app/shared')
from exceptions import (
    CourseCreatorBaseException,
    DatabaseException,
    UserNotFoundException,
    UserValidationException,
    AuthenticationException,
    ValidationException
)


class OrganizationManagementDAO:
    """
    Data Access Object for Organization Management Operations
    
    This class centralizes all SQL queries and database operations for the organization
    management service, following the DAO pattern for clean architecture.
    
    Business Context:
    Provides comprehensive data access methods for multi-tenant organization management including:
    - Organization creation, configuration, and lifecycle management
    - User membership and role assignment operations
    - Project creation, tracking, and resource allocation
    - Meeting room management and scheduling
    - Track management for educational content organization
    - Audit logging and compliance tracking
    
    Technical Implementation:
    - Uses asyncpg for high-performance PostgreSQL operations
    - Implements connection pooling for optimal resource usage
    - Provides transaction support for complex multi-table operations
    - Includes comprehensive error handling and security logging
    - Supports prepared statements for performance optimization
    - Enforces multi-tenant data isolation through proper WHERE clauses
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize the Organization Management DAO with database connection pool.
        
        Business Context:
        The DAO requires a connection pool to efficiently manage database connections
        across the organization management service's operations.
        
        Args:
            db_pool: AsyncPG connection pool for database operations
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)
    
    # ================================================================
    # ORGANIZATION MANAGEMENT QUERIES
    # ================================================================
    
    async def create_organization(self, org_data: Dict[str, Any]) -> str:
        """
        Create a new organization with comprehensive configuration.
        
        Business Context:
        Organization creation is the foundational operation for multi-tenant setup.
        This operation creates the organizational structure, default settings,
        and initial administrative access for platform usage.
        
        Technical Implementation:
        - Validates organization slug uniqueness
        - Sets up default organizational settings
        - Creates initial audit trail
        - Generates unique organization ID for tenant isolation
        
        Args:
            org_data: Dictionary containing organization information
                - name: Organization display name
                - slug: Unique organization identifier (URL-safe)
                - description: Organization description
                - domain: Optional organization domain
                - contact_email: Primary contact email
                - contact_phone: Optional contact phone
                - settings: JSON configuration object
                
        Returns:
            Created organization ID as string
        """
        try:
            print(f"=== DAO DEBUG: Starting create_organization")
            print(f"=== DAO DEBUG: Received org_data keys: {list(org_data.keys())}")
            print(f"=== DAO DEBUG: org_data values: name='{org_data.get('name')}', slug='{org_data.get('slug')}', id='{org_data.get('id')}'")
            self.logger.info(f"DAO DEBUG: Starting create_organization for slug: {org_data.get('slug')}")
            
            print(f"=== DAO DEBUG: About to acquire database connection")
            async with self.db_pool.acquire() as conn:
                print(f"=== DAO DEBUG: Database connection acquired successfully")
                print(f"=== DAO DEBUG: About to execute INSERT query")
                print(f"=== DAO DEBUG: Query parameters - id: {org_data['id']}, name: {org_data['name']}, slug: {org_data['slug']}")
                
                org_id = await conn.fetchval(
                    """INSERT INTO course_creator.organizations (
                        id, name, slug, description, domain, contact_email, 
                        contact_phone, settings, is_active, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) 
                    RETURNING id""",
                    org_data['id'],
                    org_data['name'],
                    org_data['slug'],
                    org_data.get('description'),
                    org_data.get('domain'),
                    org_data['contact_email'],
                    org_data.get('contact_phone'),
                    json.dumps(org_data.get('settings', {})),
                    org_data.get('is_active', True),
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                print(f"=== DAO DEBUG: INSERT query completed successfully, returned ID: {org_id}")
                self.logger.info(f"DAO DEBUG: Organization created successfully with ID: {org_id}")
                return str(org_id)
        except asyncpg.UniqueViolationError as e:
            # Handle duplicate organization slug gracefully
            print(f"=== DAO ERROR: UniqueViolationError - {str(e)}")
            self.logger.error(f"DAO ERROR: UniqueViolationError - {str(e)}")
            raise ValidationException(
                message="Organization with this slug already exists",
                error_code="DUPLICATE_ORGANIZATION_SLUG",
                validation_errors={"slug": "Slug already in use"},
                original_exception=e
            )
        except Exception as e:
            print(f"=== DAO ERROR: Exception in create_organization: {type(e).__name__}: {str(e)}")
            self.logger.error(f"DAO ERROR: Exception in create_organization: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"=== DAO ERROR TRACEBACK: {traceback.format_exc()}")
            self.logger.error(f"DAO ERROR TRACEBACK: {traceback.format_exc()}")
            raise DatabaseException(
                message="Failed to create organization",
                error_code="ORGANIZATION_CREATION_ERROR",
                details={
                    "name": org_data.get('name'),
                    "slug": org_data.get('slug')
                },
                original_exception=e
            )
    
    async def get_organization_by_id(self, org_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve organization information by unique ID.
        
        Business Context:
        Organization lookup by ID is used for tenant validation, configuration
        retrieval, and administrative operations requiring organizational context.
        
        Args:
            org_id: Unique organization identifier
            
        Returns:
            Complete organization record or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                org = await conn.fetchrow(
                    """SELECT id, name, slug, description, logo_url, domain,
                              address, contact_phone, contact_email, logo_file_path,
                              settings, is_active, created_at, updated_at
                       FROM course_creator.organizations WHERE id = $1""",
                    UUID(org_id)
                )
                return dict(org) if org else None
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve organization by ID",
                error_code="ORGANIZATION_LOOKUP_ERROR",
                details={"org_id": org_id},
                original_exception=e
            )
    
    async def get_organization_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve organization information by slug (URL identifier).
        
        Business Context:
        Slug-based organization lookup supports URL routing and public-facing
        organization identification for branded experiences.
        
        Args:
            slug: Organization slug identifier
            
        Returns:
            Complete organization record or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                org = await conn.fetchrow(
                    """SELECT id, name, slug, description, logo_url, domain,
                              address, contact_phone, contact_email, logo_file_path,
                              settings, is_active, created_at, updated_at
                       FROM course_creator.organizations WHERE slug = $1""",
                    slug
                )
                return dict(org) if org else None
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve organization by slug",
                error_code="ORGANIZATION_LOOKUP_ERROR",
                details={"slug": slug},
                original_exception=e
            )
    
    async def exists_by_slug(self, slug: str) -> bool:
        """
        Check if an organization exists with the given slug.
        
        Args:
            slug: Organization slug to check
            
        Returns:
            bool: True if organization exists, False otherwise
        """
        try:
            async with self.db_pool.acquire() as connection:
                result = await connection.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM course_creator.organizations WHERE slug = $1)",
                    slug
                )
                return bool(result)
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to check organization existence by slug",
                error_code="ORGANIZATION_EXISTS_CHECK_ERROR",
                details={"slug": slug},
                original_exception=e
            )
    
    async def exists_by_domain(self, domain: str) -> bool:
        """
        Check if an organization exists with the given domain.
        
        Args:
            domain: Organization domain to check
            
        Returns:
            bool: True if organization exists, False otherwise
        """
        try:
            async with self.db_pool.acquire() as connection:
                result = await connection.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM course_creator.organizations WHERE domain = $1)",
                    domain
                )
                return bool(result)
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to check organization existence by domain",
                error_code="ORGANIZATION_EXISTS_CHECK_ERROR",
                details={"domain": domain},
                original_exception=e
            )
    
    async def update_organization_settings(self, org_id: str, settings: Dict[str, Any]) -> bool:
        """
        Update organization configuration settings.
        
        Business Context:
        Organization settings control feature availability, branding, and
        operational parameters for the multi-tenant platform experience.
        
        Args:
            org_id: Organization to update settings for
            settings: New settings configuration object
            
        Returns:
            True if settings were updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE course_creator.organizations 
                       SET settings = $1, updated_at = $2 
                       WHERE id = $3""",
                    json.dumps(settings),
                    datetime.utcnow(),
                    UUID(org_id)
                )
                return result.split()[-1] == '1'
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to update organization settings",
                error_code="ORGANIZATION_UPDATE_ERROR",
                details={"org_id": org_id},
                original_exception=e
            )
    
    # ================================================================
    # MEMBERSHIP MANAGEMENT QUERIES
    # ================================================================
    
    async def create_membership(self, membership_data: Dict[str, Any]) -> str:
        """
        Create a new organizational membership with role assignment.
        
        Business Context:
        Memberships link users to organizations with specific roles and permissions.
        This enables multi-tenant access control and organizational resource management.
        
        Args:
            membership_data: Dictionary containing membership information
                - user_id: User being granted membership
                - organization_id: Organization granting membership
                - role: User role within the organization
                - permissions: Optional additional permissions
                
        Returns:
            Created membership ID as string
        """
        try:
            async with self.db_pool.acquire() as conn:
                membership_id = await conn.fetchval(
                    """INSERT INTO course_creator.memberships (
                        id, user_id, organization_id, role, permissions,
                        is_active, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) 
                    RETURNING id""",
                    membership_data['id'],
                    UUID(membership_data['user_id']),
                    UUID(membership_data['organization_id']),
                    membership_data['role'],
                    json.dumps(membership_data.get('permissions', {})),
                    membership_data.get('is_active', True),
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                return str(membership_id)
        except asyncpg.UniqueViolationError as e:
            # Handle duplicate membership gracefully
            raise ValidationException(
                message="User is already a member of this organization",
                error_code="DUPLICATE_MEMBERSHIP_ERROR",
                validation_errors={"user_id": "User already has membership"},
                original_exception=e
            )
        except Exception as e:
            raise DatabaseException(
                message="Failed to create organizational membership",
                error_code="MEMBERSHIP_CREATION_ERROR",
                details=membership_data,
                original_exception=e
            )
    
    async def get_user_memberships(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all organizational memberships for a specific user.
        
        Business Context:
        User membership lookup enables multi-tenant navigation, permission
        validation, and organizational context switching for users.
        
        Args:
            user_id: User to get memberships for
            
        Returns:
            List of membership records with organization information
        """
        try:
            async with self.db_pool.acquire() as conn:
                memberships = await conn.fetch(
                    """SELECT m.id, m.role, m.permissions, m.is_active, m.created_at,
                              o.id as org_id, o.name as org_name, o.slug as org_slug,
                              o.logo_url as org_logo
                       FROM course_creator.memberships m
                       JOIN course_creator.organizations o ON m.organization_id = o.id
                       WHERE m.user_id = $1 AND m.is_active = true
                       ORDER BY o.name""",
                    UUID(user_id)
                )
                return [dict(membership) for membership in memberships]
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve user memberships",
                error_code="MEMBERSHIP_LOOKUP_ERROR",
                details={"user_id": user_id},
                original_exception=e
            )
    
    async def get_organization_members(self, org_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve organization members with pagination support.
        
        Business Context:
        Organization member listing supports administrative tasks, communication,
        and membership management operations within organizations.
        
        Args:
            org_id: Organization to get members for
            limit: Maximum number of members to return
            offset: Number of members to skip (for pagination)
            
        Returns:
            List of member records with user information
        """
        try:
            async with self.db_pool.acquire() as conn:
                members = await conn.fetch(
                    """SELECT m.id, m.role, m.permissions, m.is_active, m.created_at,
                              u.id as user_id, u.email, u.username, u.full_name
                       FROM course_creator.memberships m
                       JOIN users u ON m.user_id = u.id
                       WHERE m.organization_id = $1 AND m.is_active = true
                       ORDER BY m.created_at DESC
                       LIMIT $2 OFFSET $3""",
                    UUID(org_id), limit, offset
                )
                return [dict(member) for member in members]
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve organization members",
                error_code="MEMBERSHIP_QUERY_ERROR",
                details={"org_id": org_id, "limit": limit, "offset": offset},
                original_exception=e
            )
    
    async def update_membership_role(self, membership_id: str, new_role: str) -> bool:
        """
        Update the role for an organizational membership.
        
        Business Context:
        Role updates support promotion, role changes, and permission management
        within organizational hierarchies and access control systems.
        
        Args:
            membership_id: Membership to update role for
            new_role: New role to assign
            
        Returns:
            True if role was updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE course_creator.memberships 
                       SET role = $1, updated_at = $2 
                       WHERE id = $3""",
                    new_role,
                    datetime.utcnow(),
                    UUID(membership_id)
                )
                return result.split()[-1] == '1'
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to update membership role",
                error_code="MEMBERSHIP_UPDATE_ERROR",
                details={"membership_id": membership_id, "new_role": new_role},
                original_exception=e
            )
    
    # ================================================================
    # PROJECT MANAGEMENT QUERIES
    # ================================================================
    
    async def create_project(self, project_data: Dict[str, Any]) -> str:
        """
        Create a new project within an organization.
        
        Business Context:
        Projects organize educational content, courses, and resources within
        organizations, enabling structured content management and collaboration.
        
        Args:
            project_data: Dictionary containing project information
                - name: Project display name
                - description: Project description
                - organization_id: Parent organization
                - created_by: User creating the project
                - settings: Project configuration
                
        Returns:
            Created project ID as string
        """
        try:
            async with self.db_pool.acquire() as conn:
                project_id = await conn.fetchval(
                    """INSERT INTO course_creator.projects (
                        id, name, description, organization_id, created_by,
                        settings, is_active, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) 
                    RETURNING id""",
                    project_data['id'],
                    project_data['name'],
                    project_data.get('description'),
                    UUID(project_data['organization_id']),
                    UUID(project_data['created_by']),
                    json.dumps(project_data.get('settings', {})),
                    project_data.get('is_active', True),
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                return str(project_id)
        except Exception as e:
            raise DatabaseException(
                message="Failed to create project",
                error_code="PROJECT_CREATION_ERROR",
                details=project_data,
                original_exception=e
            )
    
    async def get_organization_projects(self, org_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve projects belonging to an organization with pagination.
        
        Business Context:
        Project listing supports organizational content management, resource
        allocation, and project overview operations for administrative users.
        
        Args:
            org_id: Organization to get projects for
            limit: Maximum number of projects to return
            offset: Number of projects to skip (for pagination)
            
        Returns:
            List of project records with creator information
        """
        try:
            async with self.db_pool.acquire() as conn:
                projects = await conn.fetch(
                    """SELECT p.id, p.name, p.description, p.settings, p.is_active, 
                              p.created_at, p.updated_at,
                              u.full_name as creator_name, u.email as creator_email
                       FROM course_creator.projects p
                       JOIN users u ON p.created_by = u.id
                       WHERE p.organization_id = $1 AND p.is_active = true
                       ORDER BY p.created_at DESC
                       LIMIT $2 OFFSET $3""",
                    UUID(org_id), limit, offset
                )
                return [dict(project) for project in projects]
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve organization projects",
                error_code="PROJECT_QUERY_ERROR",
                details={"org_id": org_id, "limit": limit, "offset": offset},
                original_exception=e
            )
    
    async def get_project_by_id(self, project_id: str, org_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve project information by ID with organization validation.
        
        Business Context:
        Project lookup with organization validation ensures multi-tenant
        data isolation and prevents cross-organizational data access.
        
        Args:
            project_id: Project identifier
            org_id: Organization identifier for validation
            
        Returns:
            Project record or None if not found or not accessible
        """
        try:
            async with self.db_pool.acquire() as conn:
                project = await conn.fetchrow(
                    """SELECT p.*, u.full_name as creator_name, u.email as creator_email
                       FROM course_creator.projects p
                       JOIN users u ON p.created_by = u.id
                       WHERE p.id = $1 AND p.organization_id = $2""",
                    UUID(project_id), UUID(org_id)
                )
                return dict(project) if project else None
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve project by ID",
                error_code="PROJECT_LOOKUP_ERROR",
                details={"project_id": project_id, "org_id": org_id},
                original_exception=e
            )
    
    # ================================================================
    # AUDIT LOGGING AND ANALYTICS QUERIES
    # ================================================================
    
    async def log_audit_event(self, audit_data: Dict[str, Any]) -> str:
        """
        Log an audit event for compliance and security tracking.
        
        Business Context:
        Audit logging supports compliance requirements, security monitoring,
        and administrative oversight of organizational activities.
        
        Args:
            audit_data: Dictionary containing audit information
                - user_id: User performing the action
                - organization_id: Organization context
                - action: Action performed
                - resource_type: Type of resource affected
                - resource_id: Specific resource identifier
                - details: Additional audit details
                
        Returns:
            Created audit log ID as string
        """
        try:
            async with self.db_pool.acquire() as conn:
                audit_id = await conn.fetchval(
                    """INSERT INTO course_creator.audit_logs (
                        id, user_id, organization_id, action, resource_type,
                        resource_id, details, timestamp, ip_address
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) 
                    RETURNING id""",
                    audit_data['id'],
                    UUID(audit_data['user_id']) if audit_data.get('user_id') else None,
                    UUID(audit_data['organization_id']) if audit_data.get('organization_id') else None,
                    audit_data['action'],
                    audit_data['resource_type'],
                    audit_data.get('resource_id'),
                    json.dumps(audit_data.get('details', {})),
                    datetime.utcnow(),
                    audit_data.get('ip_address')
                )
                return str(audit_id)
        except Exception as e:
            raise DatabaseException(
                message="Failed to create audit log entry",
                error_code="AUDIT_LOG_ERROR",
                details=audit_data,
                original_exception=e
            )
    
    async def get_organization_statistics(self, org_id: str) -> Dict[str, Any]:
        """
        Retrieve comprehensive statistics for an organization.
        
        Business Context:
        Organization statistics support administrative decision making, resource
        planning, and organizational growth analysis by providing key metrics.
        
        Args:
            org_id: Organization to get statistics for
            
        Returns:
            Dictionary containing organizational statistics and metrics
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Get member count
                member_count = await conn.fetchval(
                    """SELECT COUNT(*) FROM course_creator.memberships 
                       WHERE organization_id = $1 AND is_active = true""",
                    UUID(org_id)
                )
                
                # Get project count
                project_count = await conn.fetchval(
                    """SELECT COUNT(*) FROM course_creator.projects 
                       WHERE organization_id = $1 AND is_active = true""",
                    UUID(org_id)
                )
                
                # Get role distribution
                role_distribution = await conn.fetch(
                    """SELECT role, COUNT(*) as count 
                       FROM course_creator.memberships 
                       WHERE organization_id = $1 AND is_active = true 
                       GROUP BY role""",
                    UUID(org_id)
                )
                
                # Get recent activity count (last 30 days)
                recent_activity = await conn.fetchval(
                    """SELECT COUNT(*) FROM course_creator.audit_logs 
                       WHERE organization_id = $1 AND timestamp > $2""",
                    UUID(org_id), datetime.utcnow() - timedelta(days=30)
                )
                
                return {
                    "member_count": member_count or 0,
                    "project_count": project_count or 0,
                    "role_distribution": {row['role']: row['count'] for row in role_distribution},
                    "recent_activity_count": recent_activity or 0
                }
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve organization statistics",
                error_code="ORGANIZATION_STATS_ERROR",
                details={"org_id": org_id},
                original_exception=e
            )
    
    # ================================================================
    # TRANSACTION SUPPORT AND BATCH OPERATIONS
    # ================================================================
    
    async def execute_organization_transaction(self, operations: List[tuple]) -> List[Any]:
        """
        Execute multiple organization-related database operations within a single transaction.
        
        Business Context:
        Complex organizational operations often require multiple database changes that must
        succeed or fail together to maintain data consistency and referential integrity.
        
        Args:
            operations: List of (query, params) tuples to execute
            
        Returns:
            List of operation results
        """
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    results = []
                    for query, params in operations:
                        if params:
                            result = await conn.execute(query, *params)
                        else:
                            result = await conn.execute(query)
                        results.append(result)
                    return results
        except Exception as e:
            raise DatabaseException(
                message="Failed to execute organization transaction operations",
                error_code="ORGANIZATION_TRANSACTION_ERROR",
                details={"operation_count": len(operations)},
                original_exception=e
            )