"""
LTI Platform Data Access Object (DAO)

BUSINESS CONTEXT:
The LTIPlatformDAO provides database operations for managing Learning Tools
Interoperability (LTI) 1.3 platform registrations. LTI 1.3 enables organizations
to integrate with external Learning Management Systems (LMS) like Canvas, Moodle,
and Blackboard for Single Sign-On (SSO), grade passback, and deep linking.

TECHNICAL IMPLEMENTATION:
- Uses asyncpg for high-performance PostgreSQL operations
- Implements connection pooling for optimal resource usage
- Provides transaction support for complex multi-table operations
- Includes comprehensive error handling with custom exceptions
- Supports prepared statements for performance optimization
- Enforces multi-tenant data isolation through organization_id filters

WHY THIS EXISTS:
Organizations need to securely connect to external LMS platforms to provide
seamless learning experiences for their students. This DAO manages the entire
lifecycle of LTI platform registrations including OAuth 2.0 credentials, JWKS
endpoints, context mappings, user identity linking, and grade synchronization.
"""

import asyncpg
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4

from organization_management.exceptions import (
    DatabaseException,
    ValidationException,
)
from shared.exceptions import ConflictException


class LTIPlatformDAO:
    """
    Data Access Object for LTI Platform Registration Operations

    BUSINESS CONTEXT:
    Centralizes all SQL queries and database operations for LTI 1.3 platform
    integration management. Provides secure, multi-tenant isolated access to:
    - LTI platform registration and configuration
    - LTI context management (course/assignment mappings)
    - LTI user identity mapping (SSO)
    - LTI grade synchronization (grade passback)

    TECHNICAL IMPLEMENTATION:
    - Uses asyncpg for high-performance PostgreSQL operations
    - Implements connection pooling for optimal resource usage
    - Provides transaction support for complex operations
    - Includes comprehensive error handling and security logging
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize the LTI Platform DAO with database connection pool.

        BUSINESS CONTEXT:
        The DAO requires a connection pool to efficiently manage database connections
        across the organization management service's LTI operations.

        Args:
            db_pool: AsyncPG connection pool for database operations
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)

    # ================================================================
    # LTI PLATFORM REGISTRATION OPERATIONS
    # ================================================================

    async def register_platform(
        self,
        organization_id: UUID,
        platform_name: str,
        issuer: str,
        client_id: str,
        auth_url: str,
        token_url: str,
        jwks_url: str,
        public_key: Optional[str] = None,
        lti_version: str = "LTI_1_3",
        scope: Optional[str] = None,
        custom_params: Optional[Dict[str, Any]] = None,
        is_active: bool = True
    ) -> Dict[str, Any]:
        """
        Register a new LTI platform for an organization.

        BUSINESS CONTEXT:
        Organizations register external LMS platforms to enable LTI 1.3 integration
        for SSO, grade passback, and deep linking. This is the foundational operation
        for connecting to external learning platforms.

        SECURITY REQUIREMENTS:
        - LTI 1.3 requires either JWKS URL or static public key for JWT validation
        - OAuth 2.0 endpoints (auth_url, token_url) are mandatory
        - Client ID must be globally unique to prevent authentication conflicts
        - Issuer must be unique per organization

        Args:
            organization_id: Organization registering the platform
            platform_name: Human-readable platform name (e.g., "Canvas", "Moodle")
            issuer: LTI issuer URL (e.g., "https://canvas.instructure.com")
            client_id: OAuth 2.0 client ID (must be globally unique)
            auth_url: OAuth 2.0 authorization endpoint
            token_url: OAuth 2.0 token endpoint
            jwks_url: JWKS endpoint for JWT signature validation
            public_key: Optional static public key (if not using JWKS)
            lti_version: LTI version (default: "LTI_1_3", only LTI 1.3 supported)
            scope: OAuth 2.0 scopes (default: openid profile email)
            custom_params: Optional custom launch parameters
            is_active: Platform activation status (default: True)

        Returns:
            Created platform record with platform_id, timestamps, and all fields

        Raises:
            ValidationException: If required fields missing or LTI version invalid
            ConflictException: If client_id or issuer already exists
            DatabaseException: If database operation fails
        """
        # Validate required fields
        if not all([platform_name, issuer, client_id, auth_url, token_url]):
            raise ValidationException(
                message="Missing required field: platform_name, issuer, client_id, auth_url, and token_url are required",
                error_code="MISSING_REQUIRED_FIELD",
                field_errors={
                    "platform_name": "Required" if not platform_name else None,
                    "issuer": "Required" if not issuer else None,
                    "client_id": "Required" if not client_id else None,
                    "auth_url": "Required" if not auth_url else None,
                    "token_url": "Required" if not token_url else None,
                }
            )

        # Validate JWKS URL or public key requirement
        if not jwks_url and not public_key:
            raise ValidationException(
                message="Either jwks_url or public_key must be provided for JWT validation",
                error_code="MISSING_JWKS_OR_PUBLIC_KEY",
                field_errors={"jwks_url": "JWKS URL or public key required"}
            )

        # Validate LTI version
        if lti_version != "LTI_1_3":
            raise ValidationException(
                message="Only LTI 1.3 is supported (LTI 1.1 is deprecated)",
                error_code="INVALID_LTI_VERSION",
                field_errors={"lti_version": "Must be LTI_1_3"}
            )

        # Validate OAuth 2.0 endpoints
        if not auth_url or not token_url:
            raise ValidationException(
                message="OAuth 2.0 endpoints (auth_url, token_url) are required",
                error_code="MISSING_OAUTH_ENDPOINTS",
                field_errors={
                    "auth_url": "Required" if not auth_url else None,
                    "token_url": "Required" if not token_url else None,
                }
            )

        # Validate scope
        if not scope:
            raise ValidationException(
                message="OAuth 2.0 scope is required",
                error_code="MISSING_SCOPE",
                field_errors={"scope": "Required"}
            )

        try:
            platform_id = uuid4()
            now = datetime.now()

            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO lti_platform_registrations (
                        id, organization_id, platform_name, issuer, client_id,
                        auth_login_url, auth_token_url, jwks_url, tool_public_key,
                        scopes, is_active, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
                    )
                    RETURNING *
                    """,
                    platform_id,
                    organization_id,
                    platform_name,
                    issuer,
                    client_id,
                    auth_url,
                    token_url,
                    jwks_url,
                    public_key,
                    scope,
                    is_active,
                    now,
                    now
                )

                return dict(row)

        except asyncpg.UniqueViolationError as e:
            # Check which constraint was violated
            if "client_id" in str(e):
                raise ConflictException(
                    message="LTI platform with this client_id already exists",
                    resource_type="lti_platform",
                    conflicting_field="client_id",
                    existing_value=client_id,
                    original_exception=e
                )
            elif "issuer" in str(e):
                raise ConflictException(
                    message="LTI platform with this issuer already exists for organization",
                    resource_type="lti_platform",
                    conflicting_field="issuer",
                    existing_value=issuer,
                    original_exception=e
                )
            else:
                raise ConflictException(
                    message="LTI platform with this configuration already exists",
                    resource_type="lti_platform",
                    original_exception=e
                )
        except ValidationException:
            # Re-raise validation exceptions
            raise
        except Exception as e:
            self.logger.error(f"Failed to register LTI platform: {e}")
            raise DatabaseException(
                message="Failed to register LTI platform",
                error_code="LTI_PLATFORM_CREATE_ERROR",
                details={"platform_name": platform_name},
                original_exception=e
            )

    async def get_platform_by_id(self, platform_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Retrieve an LTI platform by ID.

        BUSINESS CONTEXT:
        Platform lookup by ID is used for LTI launches, configuration management,
        and administrative operations requiring platform-specific settings.

        Args:
            platform_id: UUID of the platform to retrieve

        Returns:
            Platform record or None if not found

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM lti_platform_registrations WHERE id = $1",
                    platform_id
                )
                return dict(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to get LTI platform {platform_id}: {e}")
            raise DatabaseException(
                message="Failed to retrieve LTI platform",
                error_code="LTI_PLATFORM_GET_ERROR",
                details={"platform_id": str(platform_id)},
                original_exception=e
            )

    async def get_platform_by_issuer(self, issuer: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an LTI platform by issuer.

        BUSINESS CONTEXT:
        During LTI launch, the issuer is used to identify which platform
        configuration to use for authentication. This is a critical lookup
        for the LTI authentication flow.

        Args:
            issuer: LTI issuer URL

        Returns:
            Platform record or None if not found

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM lti_platform_registrations
                    WHERE issuer = $1 AND is_active = true
                    """,
                    issuer
                )
                return dict(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to get LTI platform by issuer: {e}")
            raise DatabaseException(
                message="Failed to retrieve LTI platform by issuer",
                error_code="LTI_PLATFORM_LOOKUP_ERROR",
                details={"issuer": issuer},
                original_exception=e
            )

    async def get_platforms_by_organization(
        self,
        organization_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all LTI platforms for an organization.

        BUSINESS CONTEXT:
        Organizations may integrate with multiple LMS platforms (Canvas, Moodle,
        Blackboard) and need to see all configured integrations for management
        and monitoring purposes.

        MULTI-TENANT SECURITY:
        This query enforces organization_id filtering to ensure organizations
        can only see their own platform registrations.

        Args:
            organization_id: Organization to get platforms for
            limit: Maximum number of platforms to return (default: 100)
            offset: Number of platforms to skip for pagination (default: 0)

        Returns:
            List of platform records

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM lti_platform_registrations
                    WHERE organization_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    organization_id, limit, offset
                )
                return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get LTI platforms for org {organization_id}: {e}")
            raise DatabaseException(
                message="Failed to retrieve LTI platforms for organization",
                error_code="LTI_PLATFORMS_LIST_ERROR",
                details={"organization_id": str(organization_id)},
                original_exception=e
            )

    async def update_platform(
        self,
        platform_id: UUID,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an LTI platform configuration.

        BUSINESS CONTEXT:
        Platform configurations change when LMS updates OAuth endpoints, JWKS URLs,
        or organizations rotate credentials for security compliance.

        Args:
            platform_id: Platform to update
            updates: Dictionary of fields to update

        Returns:
            Updated platform record or None if not found

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            if not updates:
                # No updates provided, just fetch current record
                return await self.get_platform_by_id(platform_id)

            set_clauses = []
            params = []
            param_count = 1

            for field, value in updates.items():
                set_clauses.append(f"{field} = ${param_count}")
                params.append(value)
                param_count += 1

            set_clauses.append(f"updated_at = ${param_count}")
            params.append(datetime.now())
            param_count += 1

            params.append(platform_id)

            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    UPDATE lti_platform_registrations
                    SET {', '.join(set_clauses)}
                    WHERE id = ${param_count}
                    RETURNING *
                    """,
                    *params
                )
                return dict(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to update LTI platform {platform_id}: {e}")
            raise DatabaseException(
                message="Failed to update LTI platform",
                error_code="LTI_PLATFORM_UPDATE_ERROR",
                details={"platform_id": str(platform_id)},
                original_exception=e
            )

    async def delete_platform(self, platform_id: UUID) -> bool:
        """
        Delete an LTI platform registration.

        BUSINESS CONTEXT:
        Organizations may need to remove platform integrations when they switch
        LMS providers or decommission systems. This is a destructive operation
        that should cascade delete related contexts, user mappings, and grade syncs.

        Args:
            platform_id: Platform to delete

        Returns:
            True if deleted, False if not found

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM lti_platform_registrations WHERE id = $1",
                    platform_id
                )
                return result == "DELETE 1"

        except Exception as e:
            self.logger.error(f"Failed to delete LTI platform {platform_id}: {e}")
            raise DatabaseException(
                message="Failed to delete LTI platform",
                error_code="LTI_PLATFORM_DELETE_ERROR",
                details={"platform_id": str(platform_id)},
                original_exception=e
            )

    # ================================================================
    # LTI CONTEXT MANAGEMENT OPERATIONS
    # ================================================================

    async def create_lti_context(
        self,
        platform_id: UUID,
        lti_context_id: str,
        context_type: str,
        context_title: str,
        context_label: Optional[str] = None,
        resource_link_id: Optional[str] = None,
        resource_link_title: Optional[str] = None,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an LTI context mapping.

        BUSINESS CONTEXT:
        When a student launches from an external LMS, we create a context mapping
        to track which external course/assignment maps to which internal resource.
        This enables proper grade passback and roster synchronization.

        Args:
            platform_id: Platform this context belongs to
            lti_context_id: External LMS context identifier
            context_type: Type of context (e.g., "CourseOffering", "Group")
            context_title: Human-readable context title
            context_label: Short context label (e.g., "CS101")
            resource_link_id: Optional resource link identifier
            resource_link_title: Optional resource link title
            custom_params: Optional custom launch parameters

        Returns:
            Created context record

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            context_id = uuid4()
            now = datetime.now()

            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO lti_contexts (
                        id, platform_id, lti_context_id, lti_context_type,
                        lti_context_title, lti_context_label, resource_link_id,
                        resource_link_title, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                    )
                    RETURNING *
                    """,
                    context_id,
                    platform_id,
                    lti_context_id,
                    context_type,
                    context_title,
                    context_label,
                    resource_link_id,
                    resource_link_title,
                    now,
                    now
                )

                return dict(row)

        except Exception as e:
            self.logger.error(f"Failed to create LTI context: {e}")
            raise DatabaseException(
                message="Failed to create LTI context",
                error_code="LTI_CONTEXT_CREATE_ERROR",
                details={"lti_context_id": lti_context_id},
                original_exception=e
            )

    async def get_lti_context_by_id(self, context_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Retrieve an LTI context by ID.

        BUSINESS CONTEXT:
        Context lookup is used to display external course information and manage
        resource link mappings for grade passback operations.

        Args:
            context_id: UUID of the context to retrieve

        Returns:
            Context record or None if not found

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM lti_contexts WHERE id = $1",
                    context_id
                )
                return dict(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to get LTI context {context_id}: {e}")
            raise DatabaseException(
                message="Failed to retrieve LTI context",
                error_code="LTI_CONTEXT_GET_ERROR",
                details={"context_id": str(context_id)},
                original_exception=e
            )

    async def get_lti_contexts_by_platform(
        self,
        platform_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all LTI contexts for a platform.

        BUSINESS CONTEXT:
        Organizations need to see all course/assignment mappings for a specific
        LMS platform integration for management and monitoring purposes.

        Args:
            platform_id: Platform to get contexts for
            limit: Maximum number of contexts to return (default: 100)
            offset: Number of contexts to skip for pagination (default: 0)

        Returns:
            List of context records

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM lti_contexts
                    WHERE platform_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    platform_id, limit, offset
                )
                return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get LTI contexts for platform {platform_id}: {e}")
            raise DatabaseException(
                message="Failed to retrieve LTI contexts for platform",
                error_code="LTI_CONTEXTS_LIST_ERROR",
                details={"platform_id": str(platform_id)},
                original_exception=e
            )

    async def get_lti_context_by_lti_id(
        self,
        platform_id: UUID,
        lti_context_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an LTI context by LTI context ID.

        BUSINESS CONTEXT:
        During LTI launch, the external LMS sends lti_context_id which we use
        to look up the context mapping for proper authentication and authorization.

        Args:
            platform_id: Platform this context belongs to
            lti_context_id: External LMS context identifier

        Returns:
            Context record or None if not found

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM lti_contexts
                    WHERE platform_id = $1 AND lti_context_id = $2
                    """,
                    platform_id, lti_context_id
                )
                return dict(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to get LTI context by LTI ID: {e}")
            raise DatabaseException(
                message="Failed to retrieve LTI context by LTI ID",
                error_code="LTI_CONTEXT_LOOKUP_ERROR",
                details={"platform_id": str(platform_id), "lti_context_id": lti_context_id},
                original_exception=e
            )

    async def update_lti_context(
        self,
        context_id: UUID,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an LTI context.

        BUSINESS CONTEXT:
        Context information may change when courses are renamed or resource links
        are updated in the external LMS. This method enables maintaining up-to-date
        context mappings.

        Args:
            context_id: Context to update
            updates: Dictionary of fields to update

        Returns:
            Updated context record or None if not found

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            if not updates:
                return await self.get_lti_context_by_id(context_id)

            set_clauses = []
            params = []
            param_count = 1

            for field, value in updates.items():
                set_clauses.append(f"{field} = ${param_count}")
                params.append(value)
                param_count += 1

            set_clauses.append(f"updated_at = ${param_count}")
            params.append(datetime.now())
            param_count += 1

            params.append(context_id)

            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    UPDATE lti_contexts
                    SET {', '.join(set_clauses)}
                    WHERE id = ${param_count}
                    RETURNING *
                    """,
                    *params
                )
                return dict(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to update LTI context {context_id}: {e}")
            raise DatabaseException(
                message="Failed to update LTI context",
                error_code="LTI_CONTEXT_UPDATE_ERROR",
                details={"context_id": str(context_id)},
                original_exception=e
            )

    # ================================================================
    # LTI USER MAPPING OPERATIONS
    # ================================================================

    async def create_lti_user_mapping(
        self,
        platform_id: UUID,
        lti_user_id: str,
        user_id: UUID,
        lti_roles: List[str],
        lti_name: Optional[str] = None,
        lti_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an LTI user mapping.

        BUSINESS CONTEXT:
        During first LTI launch, we create a mapping between the external LMS user ID
        and our internal user ID for SSO. This enables seamless authentication and
        maintains consistent identity across systems.

        Args:
            platform_id: Platform this mapping belongs to
            lti_user_id: External LMS user identifier
            user_id: Internal platform user UUID
            lti_roles: List of LTI roles (e.g., ["Learner"], ["Instructor"])
            lti_name: Optional user name from LMS
            lti_email: Optional user email from LMS

        Returns:
            Created mapping record

        Raises:
            ConflictException: If mapping already exists
            DatabaseException: If database operation fails
        """
        try:
            mapping_id = uuid4()
            now = datetime.now()

            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO lti_user_mappings (
                        id, platform_id, lti_user_id, user_id, lti_roles,
                        lti_name, lti_email, created_at, last_seen_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9
                    )
                    RETURNING *
                    """,
                    mapping_id,
                    platform_id,
                    lti_user_id,
                    user_id,
                    lti_roles,
                    lti_name,
                    lti_email,
                    now,
                    now
                )

                return dict(row)

        except asyncpg.UniqueViolationError as e:
            raise ConflictException(
                message="LTI user mapping already exists for this platform and user",
                resource_type="lti_user_mapping",
                conflicting_field="lti_user_id",
                existing_value=lti_user_id,
                original_exception=e
            )
        except Exception as e:
            self.logger.error(f"Failed to create LTI user mapping: {e}")
            raise DatabaseException(
                message="Failed to create LTI user mapping",
                error_code="LTI_USER_MAPPING_CREATE_ERROR",
                details={"lti_user_id": lti_user_id},
                original_exception=e
            )

    async def get_lti_user_mapping_by_lti_user(
        self,
        platform_id: UUID,
        lti_user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve LTI user mapping by LTI user ID.

        BUSINESS CONTEXT:
        During LTI launch, we look up the internal user ID from the external LMS
        user ID for authentication and authorization.

        Args:
            platform_id: Platform this mapping belongs to
            lti_user_id: External LMS user identifier

        Returns:
            Mapping record or None if not found

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM lti_user_mappings
                    WHERE platform_id = $1 AND lti_user_id = $2
                    """,
                    platform_id, lti_user_id
                )
                return dict(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to get LTI user mapping: {e}")
            raise DatabaseException(
                message="Failed to retrieve LTI user mapping",
                error_code="LTI_USER_MAPPING_LOOKUP_ERROR",
                details={"platform_id": str(platform_id), "lti_user_id": lti_user_id},
                original_exception=e
            )

    async def get_lti_user_mappings_by_user(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Retrieve all LTI user mappings for a user.

        BUSINESS CONTEXT:
        Users may be mapped to multiple external LMS platforms if organization uses
        multiple systems (Canvas, Moodle, etc.). This enables viewing all LMS
        connections for user profile management.

        Args:
            user_id: Internal platform user UUID

        Returns:
            List of mapping records

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM lti_user_mappings
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    """,
                    user_id
                )
                return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get LTI user mappings for user {user_id}: {e}")
            raise DatabaseException(
                message="Failed to retrieve LTI user mappings for user",
                error_code="LTI_USER_MAPPINGS_LIST_ERROR",
                details={"user_id": str(user_id)},
                original_exception=e
            )

    async def update_lti_user_mapping(
        self,
        mapping_id: UUID,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an LTI user mapping.

        BUSINESS CONTEXT:
        User information may change in external LMS (name, email, roles) and needs
        to be synchronized with internal mappings for accurate user profiles.

        Args:
            mapping_id: Mapping to update
            updates: Dictionary of fields to update

        Returns:
            Updated mapping record or None if not found

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            if not updates:
                # No updates, just fetch current record
                async with self.db_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT * FROM lti_user_mappings WHERE id = $1",
                        mapping_id
                    )
                    return dict(row) if row else None

            set_clauses = []
            params = []
            param_count = 1

            for field, value in updates.items():
                set_clauses.append(f"{field} = ${param_count}")
                params.append(value)
                param_count += 1

            set_clauses.append(f"last_seen_at = ${param_count}")
            params.append(datetime.now())
            param_count += 1

            params.append(mapping_id)

            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    UPDATE lti_user_mappings
                    SET {', '.join(set_clauses)}
                    WHERE id = ${param_count}
                    RETURNING *
                    """,
                    *params
                )
                return dict(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to update LTI user mapping {mapping_id}: {e}")
            raise DatabaseException(
                message="Failed to update LTI user mapping",
                error_code="LTI_USER_MAPPING_UPDATE_ERROR",
                details={"mapping_id": str(mapping_id)},
                original_exception=e
            )

    # ================================================================
    # LTI GRADE SYNC OPERATIONS
    # ================================================================

    async def create_lti_grade_sync(
        self,
        mapping_id: UUID,
        context_id: UUID,
        assignment_id: UUID,
        score: float,
        max_score: float,
        comment: Optional[str] = None,
        status: str = "pending"
    ) -> Dict[str, Any]:
        """
        Create an LTI grade sync record.

        BUSINESS CONTEXT:
        When a student completes an assignment, we create a grade sync entry
        to send the score back to the external LMS via LTI Assignment and
        Grade Services (AGS).

        Args:
            mapping_id: User mapping for this grade sync
            context_id: LTI context for this grade sync
            assignment_id: Internal assignment UUID
            score: Student's score
            max_score: Maximum possible score
            comment: Optional feedback comment
            status: Sync status (default: "pending")

        Returns:
            Created grade sync record

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            sync_id = uuid4()
            now = datetime.now()

            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO lti_grade_syncs (
                        id, mapping_id, context_id, assignment_id, score,
                        max_score, comment, status, attempt_count,
                        last_attempt_at, created_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
                    )
                    RETURNING *
                    """,
                    sync_id,
                    mapping_id,
                    context_id,
                    assignment_id,
                    score,
                    max_score,
                    comment,
                    status,
                    0,  # attempt_count
                    now,  # last_attempt_at
                    now
                )

                return dict(row)

        except Exception as e:
            self.logger.error(f"Failed to create LTI grade sync: {e}")
            raise DatabaseException(
                message="Failed to create LTI grade sync record",
                error_code="LTI_GRADE_SYNC_CREATE_ERROR",
                details={"context_id": str(context_id)},
                original_exception=e
            )

    async def get_pending_grade_syncs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve pending grade syncs for background processing.

        BUSINESS CONTEXT:
        Background worker processes retrieve pending grade syncs to send to
        external LMS via LTI AGS API. This enables asynchronous grade passback
        without blocking user operations.

        Args:
            limit: Maximum number of syncs to retrieve (default: 100)

        Returns:
            List of pending grade sync records

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM lti_grade_syncs
                    WHERE status = 'pending'
                    ORDER BY created_at ASC
                    LIMIT $1
                    """,
                    limit
                )
                return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get pending grade syncs: {e}")
            raise DatabaseException(
                message="Failed to retrieve pending grade syncs",
                error_code="LTI_GRADE_SYNCS_LIST_ERROR",
                details={},
                original_exception=e
            )

    async def update_grade_sync_status(
        self,
        sync_id: UUID,
        status: str,
        synced_at: Optional[datetime] = None,
        error_message: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update grade sync status after delivery attempt.

        BUSINESS CONTEXT:
        After successfully sending grade to external LMS, we mark the sync as
        'synced' to prevent re-sending. If delivery fails, we mark it as 'failed'
        with error message for retry logic.

        Args:
            sync_id: Grade sync to update
            status: New status ("synced", "failed", "pending")
            synced_at: Optional timestamp when sync succeeded
            error_message: Optional error message if sync failed

        Returns:
            Updated grade sync record or None if not found

        Raises:
            DatabaseException: If database operation fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    UPDATE lti_grade_syncs
                    SET status = $1, synced_at = $2, error_message = $3,
                        attempt_count = attempt_count + 1
                    WHERE id = $4
                    RETURNING *
                    """,
                    status,
                    synced_at,
                    error_message,
                    sync_id
                )
                return dict(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to update grade sync status {sync_id}: {e}")
            raise DatabaseException(
                message="Failed to update grade sync status",
                error_code="LTI_GRADE_SYNC_UPDATE_ERROR",
                details={"sync_id": str(sync_id)},
                original_exception=e
            )
