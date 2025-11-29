"""
Integration Data Access Object (DAO)

What: Data Access Object for external integration operations (LTI, Calendar, Slack, Webhooks).
Where: Organization Management service data access layer.
Why: Provides:
     1. Centralized SQL queries and database interactions for integrations
     2. LTI 1.3 platform and context management operations
     3. Calendar provider and event synchronization
     4. Slack workspace and channel integration data access
     5. Webhook management (inbound and outbound)
     6. OAuth token storage and retrieval
     7. Consistent error handling with custom exceptions
     8. Multi-tenant data isolation through organization_id filters

Technical Implementation:
- Uses asyncpg for high-performance PostgreSQL operations
- Implements connection pooling for optimal resource usage
- Provides transaction support for complex multi-table operations
- Includes comprehensive error handling and security logging
- Supports prepared statements for performance optimization
- Enforces multi-tenant data isolation through proper WHERE clauses
"""

import asyncpg
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, time
from decimal import Decimal
from uuid import UUID

from organization_management.exceptions import (
    CourseCreatorBaseException,
    DatabaseException,
    ValidationException
)
from organization_management.domain.entities.integrations import (
    LTIPlatformRegistration,
    LTIContext,
    LTIUserMapping,
    LTIGradeSync,
    CalendarProvider,
    CalendarEvent,
    SlackWorkspace,
    SlackChannelMapping,
    SlackUserMapping,
    SlackMessage,
    OutboundWebhook,
    WebhookDeliveryLog,
    InboundWebhook,
    OAuthToken,
    LTIVersion,
    LTIScope,
    GradeSyncStatus,
    CalendarProviderType,
    SyncDirection,
    CalendarSyncStatus,
    SlackChannelType,
    SlackMessageType,
    WebhookAuthType,
    WebhookDeliveryStatus,
    WebhookHandlerType,
    OAuthProvider
)


class IntegrationsDAO:
    """
    Data Access Object for Integration Operations

    What: Centralizes all SQL queries and database operations for external integrations.
    Where: Organization Management service data layer.
    Why: Provides:
         1. Clean separation between business logic and data access
         2. Consistent error handling with custom exceptions
         3. Multi-tenant data isolation for organization-scoped integrations
         4. High-performance async database operations

    Technical Implementation:
    - Uses asyncpg for high-performance PostgreSQL operations
    - Implements connection pooling for optimal resource usage
    - Provides transaction support for complex multi-table operations
    - Includes comprehensive error handling and security logging
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize the Integrations DAO with database connection pool.

        What: Constructor for IntegrationsDAO.
        Where: Called during service initialization.
        Why: Injects database connection pool dependency for all operations.

        Args:
            db_pool: AsyncPG connection pool for database operations
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)

    # ================================================================
    # LTI PLATFORM REGISTRATION OPERATIONS
    # ================================================================

    async def create_lti_platform(
        self,
        platform: LTIPlatformRegistration
    ) -> LTIPlatformRegistration:
        """
        Create a new LTI platform registration.

        What: Persists an LTI platform registration to the database.
        Where: Called when connecting a new LMS (Canvas, Moodle, etc.).
        Why: Enables LTI 1.3 tool integration with external learning platforms.

        Args:
            platform: LTI platform registration entity to persist

        Returns:
            Created platform with database-generated timestamps

        Raises:
            ValidationException: If platform with same issuer/client_id exists
            DatabaseException: If database operation fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO lti_platform_registrations (
                        id, organization_id, platform_name, issuer, client_id,
                        deployment_id, auth_login_url, auth_token_url, jwks_url,
                        tool_public_key, tool_private_key, platform_public_keys,
                        scopes, deep_linking_enabled, names_role_service_enabled,
                        assignment_grade_service_enabled, is_active, verified_at,
                        last_connection_at, created_by, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb,
                        $13, $14, $15, $16, $17, $18, $19, $20, $21, $22
                    )
                    RETURNING *
                    """,
                    platform.id,
                    platform.organization_id,
                    platform.platform_name,
                    platform.issuer,
                    platform.client_id,
                    platform.deployment_id,
                    platform.auth_login_url,
                    platform.auth_token_url,
                    platform.jwks_url,
                    platform.tool_public_key,
                    platform.tool_private_key,
                    json.dumps(platform.platform_public_keys),
                    platform.scopes,
                    platform.deep_linking_enabled,
                    platform.names_role_service_enabled,
                    platform.assignment_grade_service_enabled,
                    platform.is_active,
                    platform.verified_at,
                    platform.last_connection_at,
                    platform.created_by,
                    datetime.now(),
                    datetime.now()
                )

                return self._row_to_lti_platform(row)

        except asyncpg.UniqueViolationError as e:
            raise ValidationException(
                message="LTI platform with this issuer and client_id already exists",
                error_code="DUPLICATE_LTI_PLATFORM",
                validation_errors={"issuer": platform.issuer, "client_id": platform.client_id},
                original_exception=e
            )
        except Exception as e:
            self.logger.error(f"Failed to create LTI platform: {e}")
            raise DatabaseException(
                message="Failed to create LTI platform registration",
                error_code="LTI_PLATFORM_CREATE_ERROR",
                details={"platform_name": platform.platform_name},
                original_exception=e
            )

    async def get_lti_platform_by_id(
        self,
        platform_id: UUID
    ) -> Optional[LTIPlatformRegistration]:
        """
        Retrieve an LTI platform by ID.

        What: Fetches LTI platform registration by unique identifier.
        Where: Called for platform configuration and LTI launches.
        Why: Enables platform-specific configuration lookup.

        Args:
            platform_id: UUID of the platform to retrieve

        Returns:
            LTI platform registration or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM lti_platform_registrations WHERE id = $1
                    """,
                    platform_id
                )
                return self._row_to_lti_platform(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to get LTI platform {platform_id}: {e}")
            raise DatabaseException(
                message="Failed to retrieve LTI platform",
                error_code="LTI_PLATFORM_GET_ERROR",
                details={"platform_id": str(platform_id)},
                original_exception=e
            )

    async def get_lti_platform_by_issuer(
        self,
        issuer: str,
        client_id: str
    ) -> Optional[LTIPlatformRegistration]:
        """
        Retrieve an LTI platform by issuer and client_id.

        What: Fetches LTI platform by LTI 1.3 identifiers.
        Where: Called during LTI launch to identify the platform.
        Why: Enables platform lookup during LTI authentication flow.

        Args:
            issuer: LTI issuer URL
            client_id: LTI client ID

        Returns:
            LTI platform registration or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM lti_platform_registrations
                    WHERE issuer = $1 AND client_id = $2 AND is_active = true
                    """,
                    issuer, client_id
                )
                return self._row_to_lti_platform(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to get LTI platform by issuer: {e}")
            raise DatabaseException(
                message="Failed to retrieve LTI platform by issuer",
                error_code="LTI_PLATFORM_LOOKUP_ERROR",
                details={"issuer": issuer, "client_id": client_id},
                original_exception=e
            )

    async def get_lti_platforms_by_organization(
        self,
        organization_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[LTIPlatformRegistration]:
        """
        Retrieve all LTI platforms for an organization.

        What: Fetches all LTI platform registrations for an organization.
        Where: Called for organization integration management.
        Why: Enables organization admins to view and manage LTI integrations.

        Args:
            organization_id: UUID of the organization
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of LTI platform registrations
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
                return [self._row_to_lti_platform(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get LTI platforms for org {organization_id}: {e}")
            raise DatabaseException(
                message="Failed to retrieve LTI platforms for organization",
                error_code="LTI_PLATFORMS_LIST_ERROR",
                details={"organization_id": str(organization_id)},
                original_exception=e
            )

    async def update_lti_platform(
        self,
        platform_id: UUID,
        updates: Dict[str, Any]
    ) -> Optional[LTIPlatformRegistration]:
        """
        Update an LTI platform registration.

        What: Updates specified fields of an LTI platform.
        Where: Called when modifying platform configuration.
        Why: Enables updating platform settings without recreating.

        Args:
            platform_id: UUID of the platform to update
            updates: Dictionary of fields to update

        Returns:
            Updated platform or None if not found
        """
        try:
            set_clauses = []
            params = []
            param_count = 1

            for field, value in updates.items():
                if field in ['platform_public_keys', 'scopes']:
                    set_clauses.append(f"{field} = ${param_count}::jsonb" if field == 'platform_public_keys' else f"{field} = ${param_count}")
                    params.append(json.dumps(value) if field == 'platform_public_keys' else value)
                else:
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
                return self._row_to_lti_platform(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to update LTI platform {platform_id}: {e}")
            raise DatabaseException(
                message="Failed to update LTI platform",
                error_code="LTI_PLATFORM_UPDATE_ERROR",
                details={"platform_id": str(platform_id)},
                original_exception=e
            )

    async def delete_lti_platform(self, platform_id: UUID) -> bool:
        """
        Delete an LTI platform registration.

        What: Removes an LTI platform and all associated data.
        Where: Called when disconnecting an LMS.
        Why: Enables clean removal of LTI integration.

        Args:
            platform_id: UUID of the platform to delete

        Returns:
            True if deleted, False if not found
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
    # LTI CONTEXT OPERATIONS
    # ================================================================

    async def create_lti_context(self, context: LTIContext) -> LTIContext:
        """
        Create an LTI context mapping.

        What: Persists an LTI context to link external course to internal course.
        Where: Called when LTI launch creates new course context.
        Why: Enables course mapping between LMS and platform.

        Args:
            context: LTI context entity to persist

        Returns:
            Created context with timestamps
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO lti_contexts (
                        id, platform_id, lti_context_id, lti_context_type,
                        lti_context_title, lti_context_label, course_id,
                        course_instance_id, resource_link_id, resource_link_title,
                        last_roster_sync, auto_roster_sync, roster_sync_interval_hours,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
                    )
                    RETURNING *
                    """,
                    context.id,
                    context.platform_id,
                    context.lti_context_id,
                    context.lti_context_type,
                    context.lti_context_title,
                    context.lti_context_label,
                    context.course_id,
                    context.course_instance_id,
                    context.resource_link_id,
                    context.resource_link_title,
                    context.last_roster_sync,
                    context.auto_roster_sync,
                    context.roster_sync_interval_hours,
                    datetime.now(),
                    datetime.now()
                )

                return self._row_to_lti_context(row)

        except asyncpg.UniqueViolationError as e:
            raise ValidationException(
                message="LTI context already exists for this platform",
                error_code="DUPLICATE_LTI_CONTEXT",
                validation_errors={"lti_context_id": context.lti_context_id},
                original_exception=e
            )
        except Exception as e:
            self.logger.error(f"Failed to create LTI context: {e}")
            raise DatabaseException(
                message="Failed to create LTI context",
                error_code="LTI_CONTEXT_CREATE_ERROR",
                details={"lti_context_id": context.lti_context_id},
                original_exception=e
            )

    async def get_lti_context_by_id(self, context_id: UUID) -> Optional[LTIContext]:
        """
        Retrieve an LTI context by ID.

        What: Fetches LTI context by unique identifier.
        Where: Called for context configuration and grade passback.
        Why: Enables context-specific operations.

        Args:
            context_id: UUID of the context to retrieve

        Returns:
            LTI context or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM lti_contexts WHERE id = $1",
                    context_id
                )
                return self._row_to_lti_context(row) if row else None

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
    ) -> List[LTIContext]:
        """
        Retrieve all LTI contexts for a platform.

        What: Fetches all contexts linked to an LTI platform.
        Where: Called for platform management and sync operations.
        Why: Enables bulk context operations for a platform.

        Args:
            platform_id: UUID of the platform
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of LTI contexts
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
                return [self._row_to_lti_context(row) for row in rows]

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
    ) -> Optional[LTIContext]:
        """
        Retrieve an LTI context by LTI context ID.

        What: Fetches context by LTI identifier.
        Where: Called during LTI launch to find existing context.
        Why: Enables context lookup during LTI authentication.

        Args:
            platform_id: UUID of the platform
            lti_context_id: LTI context identifier

        Returns:
            LTI context or None if not found
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
                return self._row_to_lti_context(row) if row else None

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
    ) -> Optional[LTIContext]:
        """
        Update an LTI context.

        What: Updates specified fields of an LTI context.
        Where: Called when modifying context configuration.
        Why: Enables updating context settings.

        Args:
            context_id: UUID of the context to update
            updates: Dictionary of fields to update

        Returns:
            Updated context or None if not found
        """
        try:
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
                return self._row_to_lti_context(row) if row else None

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
        mapping: LTIUserMapping
    ) -> LTIUserMapping:
        """
        Create an LTI user mapping.

        What: Persists mapping between LMS user and platform user.
        Where: Called during LTI launch for new users.
        Why: Enables user identity linking across systems.

        Args:
            mapping: LTI user mapping entity to persist

        Returns:
            Created mapping with timestamps
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO lti_user_mappings (
                        id, platform_id, user_id, lti_user_id, lti_email,
                        lti_name, lti_given_name, lti_family_name, lti_picture_url,
                        lti_roles, mapped_role_name, is_active, last_login_at,
                        login_count, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
                    )
                    RETURNING *
                    """,
                    mapping.id,
                    mapping.platform_id,
                    mapping.user_id,
                    mapping.lti_user_id,
                    mapping.lti_email,
                    mapping.lti_name,
                    mapping.lti_given_name,
                    mapping.lti_family_name,
                    mapping.lti_picture_url,
                    mapping.lti_roles,
                    mapping.mapped_role_name,
                    mapping.is_active,
                    mapping.last_login_at,
                    mapping.login_count,
                    datetime.now(),
                    datetime.now()
                )

                return self._row_to_lti_user_mapping(row)

        except asyncpg.UniqueViolationError as e:
            raise ValidationException(
                message="LTI user mapping already exists",
                error_code="DUPLICATE_LTI_USER_MAPPING",
                validation_errors={"lti_user_id": mapping.lti_user_id},
                original_exception=e
            )
        except Exception as e:
            self.logger.error(f"Failed to create LTI user mapping: {e}")
            raise DatabaseException(
                message="Failed to create LTI user mapping",
                error_code="LTI_USER_MAPPING_CREATE_ERROR",
                details={"lti_user_id": mapping.lti_user_id},
                original_exception=e
            )

    async def get_lti_user_mapping_by_lti_user(
        self,
        platform_id: UUID,
        lti_user_id: str
    ) -> Optional[LTIUserMapping]:
        """
        Retrieve LTI user mapping by LTI user ID.

        What: Fetches user mapping by LTI identifier.
        Where: Called during LTI launch to find existing user.
        Why: Enables user lookup during LTI authentication.

        Args:
            platform_id: UUID of the platform
            lti_user_id: LTI user identifier

        Returns:
            LTI user mapping or None if not found
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
                return self._row_to_lti_user_mapping(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to get LTI user mapping: {e}")
            raise DatabaseException(
                message="Failed to retrieve LTI user mapping",
                error_code="LTI_USER_MAPPING_LOOKUP_ERROR",
                details={"platform_id": str(platform_id), "lti_user_id": lti_user_id},
                original_exception=e
            )

    async def get_lti_user_mappings_by_user(
        self,
        user_id: UUID
    ) -> List[LTIUserMapping]:
        """
        Retrieve all LTI user mappings for a user.

        What: Fetches all LMS connections for a platform user.
        Where: Called for user profile and integration management.
        Why: Enables user to view and manage LMS connections.

        Args:
            user_id: UUID of the platform user

        Returns:
            List of LTI user mappings
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
                return [self._row_to_lti_user_mapping(row) for row in rows]

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
    ) -> Optional[LTIUserMapping]:
        """
        Update an LTI user mapping.

        What: Updates specified fields of an LTI user mapping.
        Where: Called when updating user roles or recording login.
        Why: Enables maintaining up-to-date user mapping data.

        Args:
            mapping_id: UUID of the mapping to update
            updates: Dictionary of fields to update

        Returns:
            Updated mapping or None if not found
        """
        try:
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
                return self._row_to_lti_user_mapping(row) if row else None

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
        grade_sync: LTIGradeSync
    ) -> LTIGradeSync:
        """
        Create an LTI grade sync record.

        What: Persists a grade sync record for LTI AGS.
        Where: Called when sending grades to LMS.
        Why: Tracks grade passback attempts and status.

        Args:
            grade_sync: LTI grade sync entity to persist

        Returns:
            Created grade sync with timestamps
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO lti_grade_sync (
                        id, context_id, user_mapping_id, lineitem_id, score,
                        max_score, comment, quiz_attempt_id, assignment_id,
                        sync_status, last_sync_attempt, last_sync_success,
                        sync_error_message, retry_count, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
                    )
                    RETURNING *
                    """,
                    grade_sync.id,
                    grade_sync.context_id,
                    grade_sync.user_mapping_id,
                    grade_sync.lineitem_id,
                    grade_sync.score,
                    grade_sync.max_score,
                    grade_sync.comment,
                    grade_sync.quiz_attempt_id,
                    grade_sync.assignment_id,
                    grade_sync.sync_status.value if hasattr(grade_sync.sync_status, 'value') else str(grade_sync.sync_status),
                    grade_sync.last_sync_attempt,
                    grade_sync.last_sync_success,
                    grade_sync.sync_error_message,
                    grade_sync.retry_count,
                    datetime.now(),
                    datetime.now()
                )

                return self._row_to_lti_grade_sync(row)

        except Exception as e:
            self.logger.error(f"Failed to create LTI grade sync: {e}")
            raise DatabaseException(
                message="Failed to create LTI grade sync record",
                error_code="LTI_GRADE_SYNC_CREATE_ERROR",
                details={"context_id": str(grade_sync.context_id)},
                original_exception=e
            )

    async def get_pending_grade_syncs(
        self,
        limit: int = 100
    ) -> List[LTIGradeSync]:
        """
        Retrieve pending grade syncs for processing.

        What: Fetches grades that need to be synced to LMS.
        Where: Called by grade sync worker.
        Why: Enables batch processing of grade passback.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of pending grade syncs
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM lti_grade_sync
                    WHERE sync_status IN ('pending', 'retry_scheduled')
                    ORDER BY created_at ASC
                    LIMIT $1
                    """,
                    limit
                )
                return [self._row_to_lti_grade_sync(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get pending grade syncs: {e}")
            raise DatabaseException(
                message="Failed to retrieve pending grade syncs",
                error_code="LTI_GRADE_SYNC_LIST_ERROR",
                details={"limit": limit},
                original_exception=e
            )

    async def update_grade_sync_status(
        self,
        grade_sync_id: UUID,
        status: GradeSyncStatus,
        error_message: Optional[str] = None
    ) -> Optional[LTIGradeSync]:
        """
        Update grade sync status.

        What: Updates the sync status of a grade record.
        Where: Called after sync attempt completes.
        Why: Tracks success/failure of grade passback.

        Args:
            grade_sync_id: UUID of the grade sync record
            status: New sync status
            error_message: Error message if failed

        Returns:
            Updated grade sync or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    UPDATE lti_grade_sync
                    SET sync_status = $1,
                        sync_error_message = $2,
                        last_sync_attempt = $3,
                        last_sync_success = CASE WHEN $1 = 'confirmed' THEN $3 ELSE last_sync_success END,
                        retry_count = CASE WHEN $1 = 'failed' THEN retry_count + 1 ELSE retry_count END,
                        updated_at = $3
                    WHERE id = $4
                    RETURNING *
                    """,
                    status.value if hasattr(status, 'value') else str(status),
                    error_message,
                    datetime.now(),
                    grade_sync_id
                )
                return self._row_to_lti_grade_sync(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to update grade sync status {grade_sync_id}: {e}")
            raise DatabaseException(
                message="Failed to update grade sync status",
                error_code="LTI_GRADE_SYNC_UPDATE_ERROR",
                details={"grade_sync_id": str(grade_sync_id)},
                original_exception=e
            )

    # ================================================================
    # CALENDAR PROVIDER OPERATIONS
    # ================================================================

    async def create_calendar_provider(
        self,
        provider: CalendarProvider
    ) -> CalendarProvider:
        """
        Create a calendar provider configuration.

        What: Persists calendar provider settings for a user.
        Where: Called when user connects calendar (Google, Outlook, etc.).
        Why: Enables calendar synchronization for the user.

        Args:
            provider: Calendar provider entity to persist

        Returns:
            Created provider with timestamps
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO calendar_providers (
                        id, user_id, provider_type, provider_name, access_token,
                        refresh_token, token_expires_at, calendar_id, calendar_name,
                        calendar_timezone, sync_enabled, sync_direction,
                        sync_deadline_reminders, sync_class_schedules, sync_quiz_dates,
                        reminder_minutes_before, is_connected, last_sync_at,
                        last_sync_error, connection_error_count, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22
                    )
                    RETURNING *
                    """,
                    provider.id,
                    provider.user_id,
                    provider.provider_type.value if hasattr(provider.provider_type, 'value') else str(provider.provider_type),
                    provider.provider_name,
                    provider.access_token,
                    provider.refresh_token,
                    provider.token_expires_at,
                    provider.calendar_id,
                    provider.calendar_name,
                    provider.calendar_timezone,
                    provider.sync_enabled,
                    provider.sync_direction.value if hasattr(provider.sync_direction, 'value') else str(provider.sync_direction),
                    provider.sync_deadline_reminders,
                    provider.sync_class_schedules,
                    provider.sync_quiz_dates,
                    provider.reminder_minutes_before,
                    provider.is_connected,
                    provider.last_sync_at,
                    provider.last_sync_error,
                    provider.connection_error_count,
                    datetime.now(),
                    datetime.now()
                )

                return self._row_to_calendar_provider(row)

        except asyncpg.UniqueViolationError as e:
            raise ValidationException(
                message="Calendar provider already configured for this user",
                error_code="DUPLICATE_CALENDAR_PROVIDER",
                validation_errors={"provider_type": str(provider.provider_type)},
                original_exception=e
            )
        except Exception as e:
            self.logger.error(f"Failed to create calendar provider: {e}")
            raise DatabaseException(
                message="Failed to create calendar provider",
                error_code="CALENDAR_PROVIDER_CREATE_ERROR",
                details={"user_id": str(provider.user_id)},
                original_exception=e
            )

    async def get_calendar_providers_by_user(
        self,
        user_id: UUID
    ) -> List[CalendarProvider]:
        """
        Retrieve all calendar providers for a user.

        What: Fetches all connected calendars for a user.
        Where: Called for user calendar management.
        Why: Enables user to view and manage calendar integrations.

        Args:
            user_id: UUID of the user

        Returns:
            List of calendar providers
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM calendar_providers
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    """,
                    user_id
                )
                return [self._row_to_calendar_provider(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get calendar providers for user {user_id}: {e}")
            raise DatabaseException(
                message="Failed to retrieve calendar providers for user",
                error_code="CALENDAR_PROVIDERS_LIST_ERROR",
                details={"user_id": str(user_id)},
                original_exception=e
            )

    async def update_calendar_provider(
        self,
        provider_id: UUID,
        updates: Dict[str, Any]
    ) -> Optional[CalendarProvider]:
        """
        Update a calendar provider.

        What: Updates specified fields of a calendar provider.
        Where: Called when updating tokens or settings.
        Why: Enables maintaining calendar connection.

        Args:
            provider_id: UUID of the provider to update
            updates: Dictionary of fields to update

        Returns:
            Updated provider or None if not found
        """
        try:
            set_clauses = []
            params = []
            param_count = 1

            for field, value in updates.items():
                if hasattr(value, 'value'):  # Handle enums
                    set_clauses.append(f"{field} = ${param_count}")
                    params.append(value.value)
                else:
                    set_clauses.append(f"{field} = ${param_count}")
                    params.append(value)
                param_count += 1

            set_clauses.append(f"updated_at = ${param_count}")
            params.append(datetime.now())
            param_count += 1

            params.append(provider_id)

            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    UPDATE calendar_providers
                    SET {', '.join(set_clauses)}
                    WHERE id = ${param_count}
                    RETURNING *
                    """,
                    *params
                )
                return self._row_to_calendar_provider(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to update calendar provider {provider_id}: {e}")
            raise DatabaseException(
                message="Failed to update calendar provider",
                error_code="CALENDAR_PROVIDER_UPDATE_ERROR",
                details={"provider_id": str(provider_id)},
                original_exception=e
            )

    async def delete_calendar_provider(self, provider_id: UUID) -> bool:
        """
        Delete a calendar provider.

        What: Removes a calendar provider and all events.
        Where: Called when user disconnects calendar.
        Why: Enables clean removal of calendar integration.

        Args:
            provider_id: UUID of the provider to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM calendar_providers WHERE id = $1",
                    provider_id
                )
                return result == "DELETE 1"

        except Exception as e:
            self.logger.error(f"Failed to delete calendar provider {provider_id}: {e}")
            raise DatabaseException(
                message="Failed to delete calendar provider",
                error_code="CALENDAR_PROVIDER_DELETE_ERROR",
                details={"provider_id": str(provider_id)},
                original_exception=e
            )

    # ================================================================
    # CALENDAR EVENT OPERATIONS
    # ================================================================

    async def create_calendar_event(
        self,
        event: CalendarEvent
    ) -> CalendarEvent:
        """
        Create a calendar event.

        What: Persists a calendar event for sync tracking.
        Where: Called when syncing events with external calendar.
        Why: Enables bidirectional calendar synchronization.

        Args:
            event: Calendar event entity to persist

        Returns:
            Created event with timestamps
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO calendar_events (
                        id, provider_id, user_id, external_event_id, external_calendar_id,
                        title, description, location, start_time, end_time, all_day,
                        timezone, is_recurring, recurrence_rule, recurring_event_id,
                        event_type, source_type, source_id, sync_status, local_updated_at,
                        remote_updated_at, last_sync_at, reminder_sent, reminder_sent_at,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26
                    )
                    RETURNING *
                    """,
                    event.id,
                    event.provider_id,
                    event.user_id,
                    event.external_event_id,
                    event.external_calendar_id,
                    event.title,
                    event.description,
                    event.location,
                    event.start_time,
                    event.end_time,
                    event.all_day,
                    event.timezone,
                    event.is_recurring,
                    event.recurrence_rule,
                    event.recurring_event_id,
                    event.event_type,
                    event.source_type,
                    event.source_id,
                    event.sync_status.value if hasattr(event.sync_status, 'value') else str(event.sync_status),
                    event.local_updated_at,
                    event.remote_updated_at,
                    event.last_sync_at,
                    event.reminder_sent,
                    event.reminder_sent_at,
                    datetime.now(),
                    datetime.now()
                )

                return self._row_to_calendar_event(row)

        except Exception as e:
            self.logger.error(f"Failed to create calendar event: {e}")
            raise DatabaseException(
                message="Failed to create calendar event",
                error_code="CALENDAR_EVENT_CREATE_ERROR",
                details={"title": event.title},
                original_exception=e
            )

    async def get_calendar_events_by_user(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[CalendarEvent]:
        """
        Retrieve calendar events for a user.

        What: Fetches synced calendar events for a user.
        Where: Called for calendar display and sync operations.
        Why: Enables calendar event listing and management.

        Args:
            user_id: UUID of the user
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of records to return

        Returns:
            List of calendar events
        """
        try:
            async with self.db_pool.acquire() as conn:
                if start_date and end_date:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM calendar_events
                        WHERE user_id = $1 AND start_time >= $2 AND end_time <= $3
                        ORDER BY start_time ASC
                        LIMIT $4
                        """,
                        user_id, start_date, end_date, limit
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM calendar_events
                        WHERE user_id = $1
                        ORDER BY start_time ASC
                        LIMIT $2
                        """,
                        user_id, limit
                    )
                return [self._row_to_calendar_event(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get calendar events for user {user_id}: {e}")
            raise DatabaseException(
                message="Failed to retrieve calendar events for user",
                error_code="CALENDAR_EVENTS_LIST_ERROR",
                details={"user_id": str(user_id)},
                original_exception=e
            )

    async def get_events_needing_reminder(
        self,
        limit: int = 100
    ) -> List[CalendarEvent]:
        """
        Retrieve events needing reminders.

        What: Fetches upcoming events that need reminders sent.
        Where: Called by reminder worker.
        Why: Enables automated event reminders.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of events needing reminders
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT ce.* FROM calendar_events ce
                    JOIN calendar_providers cp ON ce.provider_id = cp.id
                    WHERE ce.reminder_sent = false
                      AND ce.start_time > NOW()
                      AND ce.start_time <= NOW() + (cp.reminder_minutes_before || ' minutes')::interval
                    ORDER BY ce.start_time ASC
                    LIMIT $1
                    """,
                    limit
                )
                return [self._row_to_calendar_event(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get events needing reminder: {e}")
            raise DatabaseException(
                message="Failed to retrieve events needing reminder",
                error_code="CALENDAR_EVENTS_REMINDER_ERROR",
                details={"limit": limit},
                original_exception=e
            )

    # ================================================================
    # SLACK WORKSPACE OPERATIONS
    # ================================================================

    async def create_slack_workspace(
        self,
        workspace: SlackWorkspace
    ) -> SlackWorkspace:
        """
        Create a Slack workspace configuration.

        What: Persists Slack workspace integration settings.
        Where: Called when organization connects Slack.
        Why: Enables Slack notifications and commands.

        Args:
            workspace: Slack workspace entity to persist

        Returns:
            Created workspace with timestamps
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO slack_workspaces (
                        id, organization_id, workspace_id, workspace_name, workspace_domain,
                        bot_token, bot_user_id, app_id, scopes, default_announcements_channel,
                        default_alerts_channel, enable_notifications, enable_commands,
                        enable_ai_assistant, is_active, installed_at, last_activity_at,
                        installed_by, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
                    )
                    RETURNING *
                    """,
                    workspace.id,
                    workspace.organization_id,
                    workspace.workspace_id,
                    workspace.workspace_name,
                    workspace.workspace_domain,
                    workspace.bot_token,
                    workspace.bot_user_id,
                    workspace.app_id,
                    workspace.scopes,
                    workspace.default_announcements_channel,
                    workspace.default_alerts_channel,
                    workspace.enable_notifications,
                    workspace.enable_commands,
                    workspace.enable_ai_assistant,
                    workspace.is_active,
                    workspace.installed_at or datetime.now(),
                    workspace.last_activity_at,
                    workspace.installed_by,
                    datetime.now(),
                    datetime.now()
                )

                return self._row_to_slack_workspace(row)

        except asyncpg.UniqueViolationError as e:
            raise ValidationException(
                message="Slack workspace already connected to this organization",
                error_code="DUPLICATE_SLACK_WORKSPACE",
                validation_errors={"workspace_id": workspace.workspace_id},
                original_exception=e
            )
        except Exception as e:
            self.logger.error(f"Failed to create Slack workspace: {e}")
            raise DatabaseException(
                message="Failed to create Slack workspace",
                error_code="SLACK_WORKSPACE_CREATE_ERROR",
                details={"organization_id": str(workspace.organization_id)},
                original_exception=e
            )

    async def get_slack_workspace_by_organization(
        self,
        organization_id: UUID
    ) -> Optional[SlackWorkspace]:
        """
        Retrieve Slack workspace for an organization.

        What: Fetches Slack workspace config for an organization.
        Where: Called for Slack operations.
        Why: Enables Slack integration for organization.

        Args:
            organization_id: UUID of the organization

        Returns:
            Slack workspace or None if not connected
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM slack_workspaces
                    WHERE organization_id = $1 AND is_active = true
                    """,
                    organization_id
                )
                return self._row_to_slack_workspace(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to get Slack workspace for org {organization_id}: {e}")
            raise DatabaseException(
                message="Failed to retrieve Slack workspace for organization",
                error_code="SLACK_WORKSPACE_GET_ERROR",
                details={"organization_id": str(organization_id)},
                original_exception=e
            )

    async def update_slack_workspace(
        self,
        workspace_id: UUID,
        updates: Dict[str, Any]
    ) -> Optional[SlackWorkspace]:
        """
        Update a Slack workspace configuration.

        What: Updates specified fields of a Slack workspace.
        Where: Called when updating Slack settings.
        Why: Enables modifying Slack integration configuration.

        Args:
            workspace_id: UUID of the workspace to update
            updates: Dictionary of fields to update

        Returns:
            Updated workspace or None if not found
        """
        try:
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

            params.append(workspace_id)

            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    UPDATE slack_workspaces
                    SET {', '.join(set_clauses)}
                    WHERE id = ${param_count}
                    RETURNING *
                    """,
                    *params
                )
                return self._row_to_slack_workspace(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to update Slack workspace {workspace_id}: {e}")
            raise DatabaseException(
                message="Failed to update Slack workspace",
                error_code="SLACK_WORKSPACE_UPDATE_ERROR",
                details={"workspace_id": str(workspace_id)},
                original_exception=e
            )

    # ================================================================
    # SLACK CHANNEL MAPPING OPERATIONS
    # ================================================================

    async def create_slack_channel_mapping(
        self,
        mapping: SlackChannelMapping
    ) -> SlackChannelMapping:
        """
        Create a Slack channel mapping.

        What: Persists mapping between Slack channel and entity.
        Where: Called when linking channel to course/project.
        Why: Enables targeted notifications to specific channels.

        Args:
            mapping: Slack channel mapping entity to persist

        Returns:
            Created mapping with timestamps
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO slack_channel_mappings (
                        id, workspace_id, channel_id, channel_name, channel_type,
                        entity_type, entity_id, notify_announcements, notify_deadlines,
                        notify_grades, notify_new_content, notify_discussions,
                        is_active, last_message_at, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
                    )
                    RETURNING *
                    """,
                    mapping.id,
                    mapping.workspace_id,
                    mapping.channel_id,
                    mapping.channel_name,
                    mapping.channel_type.value if hasattr(mapping.channel_type, 'value') else str(mapping.channel_type),
                    mapping.entity_type,
                    mapping.entity_id,
                    mapping.notify_announcements,
                    mapping.notify_deadlines,
                    mapping.notify_grades,
                    mapping.notify_new_content,
                    mapping.notify_discussions,
                    mapping.is_active,
                    mapping.last_message_at,
                    datetime.now(),
                    datetime.now()
                )

                return self._row_to_slack_channel_mapping(row)

        except asyncpg.UniqueViolationError as e:
            raise ValidationException(
                message="Slack channel already mapped",
                error_code="DUPLICATE_SLACK_CHANNEL_MAPPING",
                validation_errors={"channel_id": mapping.channel_id},
                original_exception=e
            )
        except Exception as e:
            self.logger.error(f"Failed to create Slack channel mapping: {e}")
            raise DatabaseException(
                message="Failed to create Slack channel mapping",
                error_code="SLACK_CHANNEL_MAPPING_CREATE_ERROR",
                details={"channel_id": mapping.channel_id},
                original_exception=e
            )

    async def get_slack_channel_mappings_by_entity(
        self,
        entity_type: str,
        entity_id: UUID
    ) -> List[SlackChannelMapping]:
        """
        Retrieve Slack channel mappings for an entity.

        What: Fetches channels linked to a specific entity.
        Where: Called when sending notifications.
        Why: Enables finding target channels for notifications.

        Args:
            entity_type: Type of entity (course, project, etc.)
            entity_id: UUID of the entity

        Returns:
            List of channel mappings
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM slack_channel_mappings
                    WHERE entity_type = $1 AND entity_id = $2 AND is_active = true
                    """,
                    entity_type, entity_id
                )
                return [self._row_to_slack_channel_mapping(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get Slack channel mappings: {e}")
            raise DatabaseException(
                message="Failed to retrieve Slack channel mappings",
                error_code="SLACK_CHANNEL_MAPPINGS_LIST_ERROR",
                details={"entity_type": entity_type, "entity_id": str(entity_id)},
                original_exception=e
            )

    # ================================================================
    # SLACK USER MAPPING OPERATIONS
    # ================================================================

    async def create_slack_user_mapping(
        self,
        mapping: SlackUserMapping
    ) -> SlackUserMapping:
        """
        Create a Slack user mapping.

        What: Persists mapping between Slack user and platform user.
        Where: Called when user links Slack account.
        Why: Enables personalized DM notifications.

        Args:
            mapping: Slack user mapping entity to persist

        Returns:
            Created mapping with timestamps
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO slack_user_mappings (
                        id, workspace_id, user_id, slack_user_id, slack_username,
                        slack_email, slack_real_name, slack_display_name,
                        dm_notifications_enabled, mention_notifications_enabled,
                        daily_digest_enabled, digest_time, is_active, last_dm_at,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
                    )
                    RETURNING *
                    """,
                    mapping.id,
                    mapping.workspace_id,
                    mapping.user_id,
                    mapping.slack_user_id,
                    mapping.slack_username,
                    mapping.slack_email,
                    mapping.slack_real_name,
                    mapping.slack_display_name,
                    mapping.dm_notifications_enabled,
                    mapping.mention_notifications_enabled,
                    mapping.daily_digest_enabled,
                    mapping.digest_time,
                    mapping.is_active,
                    mapping.last_dm_at,
                    datetime.now(),
                    datetime.now()
                )

                return self._row_to_slack_user_mapping(row)

        except asyncpg.UniqueViolationError as e:
            raise ValidationException(
                message="Slack user already mapped",
                error_code="DUPLICATE_SLACK_USER_MAPPING",
                validation_errors={"slack_user_id": mapping.slack_user_id},
                original_exception=e
            )
        except Exception as e:
            self.logger.error(f"Failed to create Slack user mapping: {e}")
            raise DatabaseException(
                message="Failed to create Slack user mapping",
                error_code="SLACK_USER_MAPPING_CREATE_ERROR",
                details={"slack_user_id": mapping.slack_user_id},
                original_exception=e
            )

    async def get_slack_user_mapping_by_user(
        self,
        user_id: UUID,
        workspace_id: UUID
    ) -> Optional[SlackUserMapping]:
        """
        Retrieve Slack user mapping for a user.

        What: Fetches Slack mapping for a platform user.
        Where: Called when sending DM notifications.
        Why: Enables finding Slack user ID for notifications.

        Args:
            user_id: UUID of the platform user
            workspace_id: UUID of the Slack workspace

        Returns:
            Slack user mapping or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM slack_user_mappings
                    WHERE user_id = $1 AND workspace_id = $2 AND is_active = true
                    """,
                    user_id, workspace_id
                )
                return self._row_to_slack_user_mapping(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to get Slack user mapping: {e}")
            raise DatabaseException(
                message="Failed to retrieve Slack user mapping",
                error_code="SLACK_USER_MAPPING_GET_ERROR",
                details={"user_id": str(user_id)},
                original_exception=e
            )

    # ================================================================
    # SLACK MESSAGE HISTORY OPERATIONS
    # ================================================================

    async def create_slack_message(
        self,
        message: SlackMessage
    ) -> SlackMessage:
        """
        Create a Slack message record.

        What: Persists a Slack message for history/audit.
        Where: Called when sending Slack messages.
        Why: Enables message tracking and analytics.

        Args:
            message: Slack message entity to persist

        Returns:
            Created message with timestamps
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO slack_message_history (
                        id, workspace_id, channel_mapping_id, user_mapping_id,
                        slack_message_ts, message_type, message_text, source_type,
                        source_id, delivery_status, sent_at, error_message,
                        reaction_count, reply_count, created_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
                    )
                    RETURNING *
                    """,
                    message.id,
                    message.workspace_id,
                    message.channel_mapping_id,
                    message.user_mapping_id,
                    message.slack_message_ts,
                    message.message_type.value if hasattr(message.message_type, 'value') else str(message.message_type),
                    message.message_text,
                    message.source_type,
                    message.source_id,
                    message.delivery_status,
                    message.sent_at,
                    message.error_message,
                    message.reaction_count,
                    message.reply_count,
                    datetime.now()
                )

                return self._row_to_slack_message(row)

        except Exception as e:
            self.logger.error(f"Failed to create Slack message: {e}")
            raise DatabaseException(
                message="Failed to create Slack message record",
                error_code="SLACK_MESSAGE_CREATE_ERROR",
                details={"message_type": str(message.message_type)},
                original_exception=e
            )

    async def get_slack_message_history(
        self,
        workspace_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[SlackMessage]:
        """
        Retrieve Slack message history.

        What: Fetches message history for a workspace.
        Where: Called for message analytics and audit.
        Why: Enables reviewing sent messages.

        Args:
            workspace_id: UUID of the workspace
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of Slack messages
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM slack_message_history
                    WHERE workspace_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    workspace_id, limit, offset
                )
                return [self._row_to_slack_message(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get Slack message history: {e}")
            raise DatabaseException(
                message="Failed to retrieve Slack message history",
                error_code="SLACK_MESSAGES_LIST_ERROR",
                details={"workspace_id": str(workspace_id)},
                original_exception=e
            )

    # ================================================================
    # OUTBOUND WEBHOOK OPERATIONS
    # ================================================================

    async def create_outbound_webhook(
        self,
        webhook: OutboundWebhook
    ) -> OutboundWebhook:
        """
        Create an outbound webhook configuration.

        What: Persists outbound webhook for external notifications.
        Where: Called when setting up webhook integration.
        Why: Enables sending events to external services.

        Args:
            webhook: Outbound webhook entity to persist

        Returns:
            Created webhook with timestamps
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO outbound_webhooks (
                        id, organization_id, name, description, target_url,
                        auth_type, auth_secret, event_types, filter_conditions,
                        retry_count, retry_delay_seconds, timeout_seconds,
                        is_active, last_triggered_at, success_count, failure_count,
                        created_by, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19
                    )
                    RETURNING *
                    """,
                    webhook.id,
                    webhook.organization_id,
                    webhook.name,
                    webhook.description,
                    webhook.target_url,
                    webhook.auth_type.value if hasattr(webhook.auth_type, 'value') else str(webhook.auth_type),
                    webhook.auth_secret,
                    webhook.event_types,
                    json.dumps(webhook.filter_conditions),
                    webhook.retry_count,
                    webhook.retry_delay_seconds,
                    webhook.timeout_seconds,
                    webhook.is_active,
                    webhook.last_triggered_at,
                    webhook.success_count,
                    webhook.failure_count,
                    webhook.created_by,
                    datetime.now(),
                    datetime.now()
                )

                return self._row_to_outbound_webhook(row)

        except Exception as e:
            self.logger.error(f"Failed to create outbound webhook: {e}")
            raise DatabaseException(
                message="Failed to create outbound webhook",
                error_code="OUTBOUND_WEBHOOK_CREATE_ERROR",
                details={"name": webhook.name},
                original_exception=e
            )

    async def get_outbound_webhooks_by_organization(
        self,
        organization_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[OutboundWebhook]:
        """
        Retrieve outbound webhooks for an organization.

        What: Fetches all webhooks for an organization.
        Where: Called for webhook management.
        Why: Enables viewing and managing webhooks.

        Args:
            organization_id: UUID of the organization
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of outbound webhooks
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM outbound_webhooks
                    WHERE organization_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    organization_id, limit, offset
                )
                return [self._row_to_outbound_webhook(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get outbound webhooks for org {organization_id}: {e}")
            raise DatabaseException(
                message="Failed to retrieve outbound webhooks for organization",
                error_code="OUTBOUND_WEBHOOKS_LIST_ERROR",
                details={"organization_id": str(organization_id)},
                original_exception=e
            )

    async def get_active_webhooks_for_event(
        self,
        organization_id: UUID,
        event_type: str
    ) -> List[OutboundWebhook]:
        """
        Retrieve active webhooks that should receive an event.

        What: Fetches webhooks subscribed to an event type.
        Where: Called when events occur.
        Why: Enables finding target webhooks for delivery.

        Args:
            organization_id: UUID of the organization
            event_type: Type of event being triggered

        Returns:
            List of active webhooks for the event
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM outbound_webhooks
                    WHERE organization_id = $1 AND is_active = true
                    AND (event_types = '{}' OR $2 = ANY(event_types))
                    """,
                    organization_id, event_type
                )
                return [self._row_to_outbound_webhook(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get webhooks for event: {e}")
            raise DatabaseException(
                message="Failed to retrieve webhooks for event",
                error_code="WEBHOOKS_FOR_EVENT_ERROR",
                details={"event_type": event_type},
                original_exception=e
            )

    async def update_webhook_stats(
        self,
        webhook_id: UUID,
        success: bool
    ) -> Optional[OutboundWebhook]:
        """
        Update webhook delivery statistics.

        What: Updates success/failure counts for a webhook.
        Where: Called after webhook delivery attempt.
        Why: Tracks webhook reliability.

        Args:
            webhook_id: UUID of the webhook
            success: Whether delivery was successful

        Returns:
            Updated webhook or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    UPDATE outbound_webhooks
                    SET success_count = success_count + CASE WHEN $1 THEN 1 ELSE 0 END,
                        failure_count = failure_count + CASE WHEN $1 THEN 0 ELSE 1 END,
                        last_triggered_at = $2,
                        updated_at = $2
                    WHERE id = $3
                    RETURNING *
                    """,
                    success,
                    datetime.now(),
                    webhook_id
                )
                return self._row_to_outbound_webhook(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to update webhook stats {webhook_id}: {e}")
            raise DatabaseException(
                message="Failed to update webhook stats",
                error_code="WEBHOOK_STATS_UPDATE_ERROR",
                details={"webhook_id": str(webhook_id)},
                original_exception=e
            )

    # ================================================================
    # WEBHOOK DELIVERY LOG OPERATIONS
    # ================================================================

    async def create_webhook_delivery_log(
        self,
        log: WebhookDeliveryLog
    ) -> WebhookDeliveryLog:
        """
        Create a webhook delivery log entry.

        What: Persists delivery attempt for tracking.
        Where: Called when attempting webhook delivery.
        Why: Enables debugging and retry management.

        Args:
            log: Webhook delivery log entity to persist

        Returns:
            Created log entry
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO webhook_delivery_logs (
                        id, webhook_id, event_type, event_id, payload,
                        attempt_number, request_timestamp, response_timestamp,
                        response_status_code, response_body, response_headers,
                        delivery_status, error_message, next_retry_at
                    ) VALUES (
                        $1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10, $11::jsonb, $12, $13, $14
                    )
                    RETURNING *
                    """,
                    log.id,
                    log.webhook_id,
                    log.event_type,
                    log.event_id,
                    json.dumps(log.payload),
                    log.attempt_number,
                    log.request_timestamp,
                    log.response_timestamp,
                    log.response_status_code,
                    log.response_body,
                    json.dumps(log.response_headers) if log.response_headers else None,
                    log.delivery_status.value if hasattr(log.delivery_status, 'value') else str(log.delivery_status),
                    log.error_message,
                    log.next_retry_at
                )

                return self._row_to_webhook_delivery_log(row)

        except Exception as e:
            self.logger.error(f"Failed to create webhook delivery log: {e}")
            raise DatabaseException(
                message="Failed to create webhook delivery log",
                error_code="WEBHOOK_DELIVERY_LOG_CREATE_ERROR",
                details={"webhook_id": str(log.webhook_id)},
                original_exception=e
            )

    async def get_delivery_logs_for_webhook(
        self,
        webhook_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[WebhookDeliveryLog]:
        """
        Retrieve delivery logs for a webhook.

        What: Fetches delivery history for a webhook.
        Where: Called for webhook debugging.
        Why: Enables reviewing delivery attempts.

        Args:
            webhook_id: UUID of the webhook
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of delivery log entries
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM webhook_delivery_logs
                    WHERE webhook_id = $1
                    ORDER BY request_timestamp DESC
                    LIMIT $2 OFFSET $3
                    """,
                    webhook_id, limit, offset
                )
                return [self._row_to_webhook_delivery_log(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get delivery logs for webhook {webhook_id}: {e}")
            raise DatabaseException(
                message="Failed to retrieve webhook delivery logs",
                error_code="WEBHOOK_DELIVERY_LOGS_LIST_ERROR",
                details={"webhook_id": str(webhook_id)},
                original_exception=e
            )

    async def get_pending_retries(
        self,
        limit: int = 100
    ) -> List[WebhookDeliveryLog]:
        """
        Retrieve delivery logs pending retry.

        What: Fetches failed deliveries ready for retry.
        Where: Called by retry worker.
        Why: Enables automated delivery retries.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of delivery logs pending retry
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM webhook_delivery_logs
                    WHERE delivery_status = 'retry_scheduled'
                    AND next_retry_at <= NOW()
                    ORDER BY next_retry_at ASC
                    LIMIT $1
                    """,
                    limit
                )
                return [self._row_to_webhook_delivery_log(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get pending retries: {e}")
            raise DatabaseException(
                message="Failed to retrieve pending webhook retries",
                error_code="WEBHOOK_RETRIES_LIST_ERROR",
                details={"limit": limit},
                original_exception=e
            )

    # ================================================================
    # INBOUND WEBHOOK OPERATIONS
    # ================================================================

    async def create_inbound_webhook(
        self,
        webhook: InboundWebhook
    ) -> InboundWebhook:
        """
        Create an inbound webhook endpoint.

        What: Persists inbound webhook for receiving external events.
        Where: Called when setting up webhook receiver.
        Why: Enables receiving events from external services.

        Args:
            webhook: Inbound webhook entity to persist

        Returns:
            Created webhook with timestamps
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO inbound_webhooks (
                        id, organization_id, name, description, webhook_token,
                        auth_type, auth_secret, allowed_ips, handler_type,
                        handler_config, is_active, last_received_at, total_received,
                        total_processed, total_failed, created_by, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11, $12, $13, $14, $15, $16, $17, $18
                    )
                    RETURNING *
                    """,
                    webhook.id,
                    webhook.organization_id,
                    webhook.name,
                    webhook.description,
                    webhook.webhook_token,
                    webhook.auth_type.value if hasattr(webhook.auth_type, 'value') else str(webhook.auth_type),
                    webhook.auth_secret,
                    webhook.allowed_ips,
                    webhook.handler_type.value if hasattr(webhook.handler_type, 'value') else str(webhook.handler_type),
                    json.dumps(webhook.handler_config),
                    webhook.is_active,
                    webhook.last_received_at,
                    webhook.total_received,
                    webhook.total_processed,
                    webhook.total_failed,
                    webhook.created_by,
                    datetime.now(),
                    datetime.now()
                )

                return self._row_to_inbound_webhook(row)

        except asyncpg.UniqueViolationError as e:
            raise ValidationException(
                message="Webhook token already exists",
                error_code="DUPLICATE_WEBHOOK_TOKEN",
                validation_errors={"webhook_token": webhook.webhook_token},
                original_exception=e
            )
        except Exception as e:
            self.logger.error(f"Failed to create inbound webhook: {e}")
            raise DatabaseException(
                message="Failed to create inbound webhook",
                error_code="INBOUND_WEBHOOK_CREATE_ERROR",
                details={"name": webhook.name},
                original_exception=e
            )

    async def get_inbound_webhook_by_token(
        self,
        webhook_token: str
    ) -> Optional[InboundWebhook]:
        """
        Retrieve inbound webhook by token.

        What: Fetches webhook by URL token.
        Where: Called when receiving webhook requests.
        Why: Enables webhook lookup for validation and processing.

        Args:
            webhook_token: Token from webhook URL

        Returns:
            Inbound webhook or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM inbound_webhooks
                    WHERE webhook_token = $1 AND is_active = true
                    """,
                    webhook_token
                )
                return self._row_to_inbound_webhook(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to get inbound webhook by token: {e}")
            raise DatabaseException(
                message="Failed to retrieve inbound webhook by token",
                error_code="INBOUND_WEBHOOK_GET_ERROR",
                details={"webhook_token": webhook_token},
                original_exception=e
            )

    async def update_inbound_webhook_stats(
        self,
        webhook_id: UUID,
        processed: bool
    ) -> Optional[InboundWebhook]:
        """
        Update inbound webhook processing statistics.

        What: Updates received/processed/failed counts.
        Where: Called after processing webhook request.
        Why: Tracks webhook reliability and processing.

        Args:
            webhook_id: UUID of the webhook
            processed: Whether processing was successful

        Returns:
            Updated webhook or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    UPDATE inbound_webhooks
                    SET total_received = total_received + 1,
                        total_processed = total_processed + CASE WHEN $1 THEN 1 ELSE 0 END,
                        total_failed = total_failed + CASE WHEN $1 THEN 0 ELSE 1 END,
                        last_received_at = $2,
                        updated_at = $2
                    WHERE id = $3
                    RETURNING *
                    """,
                    processed,
                    datetime.now(),
                    webhook_id
                )
                return self._row_to_inbound_webhook(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to update inbound webhook stats {webhook_id}: {e}")
            raise DatabaseException(
                message="Failed to update inbound webhook stats",
                error_code="INBOUND_WEBHOOK_STATS_ERROR",
                details={"webhook_id": str(webhook_id)},
                original_exception=e
            )

    # ================================================================
    # OAUTH TOKEN OPERATIONS
    # ================================================================

    async def create_oauth_token(
        self,
        token: OAuthToken
    ) -> OAuthToken:
        """
        Create an OAuth token.

        What: Persists OAuth token for external service.
        Where: Called when user authorizes external service.
        Why: Enables token storage for API access.

        Args:
            token: OAuth token entity to persist

        Returns:
            Created token with timestamps
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO oauth_tokens (
                        id, user_id, organization_id, provider, provider_user_id,
                        access_token, refresh_token, token_type, expires_at,
                        refresh_expires_at, scopes, is_valid, last_used_at,
                        last_refreshed_at, consecutive_failures, last_error,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18
                    )
                    RETURNING *
                    """,
                    token.id,
                    token.user_id,
                    token.organization_id,
                    token.provider.value if hasattr(token.provider, 'value') else str(token.provider),
                    token.provider_user_id,
                    token.access_token,
                    token.refresh_token,
                    token.token_type,
                    token.expires_at,
                    token.refresh_expires_at,
                    token.scopes,
                    token.is_valid,
                    token.last_used_at,
                    token.last_refreshed_at,
                    token.consecutive_failures,
                    token.last_error,
                    datetime.now(),
                    datetime.now()
                )

                return self._row_to_oauth_token(row)

        except asyncpg.UniqueViolationError as e:
            raise ValidationException(
                message="OAuth token already exists for this user and provider",
                error_code="DUPLICATE_OAUTH_TOKEN",
                validation_errors={"provider": str(token.provider)},
                original_exception=e
            )
        except Exception as e:
            self.logger.error(f"Failed to create OAuth token: {e}")
            raise DatabaseException(
                message="Failed to create OAuth token",
                error_code="OAUTH_TOKEN_CREATE_ERROR",
                details={"provider": str(token.provider)},
                original_exception=e
            )

    async def get_oauth_token(
        self,
        user_id: Optional[UUID],
        organization_id: Optional[UUID],
        provider: OAuthProvider
    ) -> Optional[OAuthToken]:
        """
        Retrieve OAuth token for user/org and provider.

        What: Fetches OAuth token for external service access.
        Where: Called when accessing external APIs.
        Why: Enables retrieving stored access tokens.

        Args:
            user_id: UUID of the user (optional)
            organization_id: UUID of the organization (optional)
            provider: OAuth provider type

        Returns:
            OAuth token or None if not found
        """
        try:
            provider_value = provider.value if hasattr(provider, 'value') else str(provider)

            async with self.db_pool.acquire() as conn:
                if user_id:
                    row = await conn.fetchrow(
                        """
                        SELECT * FROM oauth_tokens
                        WHERE user_id = $1 AND provider = $2 AND is_valid = true
                        """,
                        user_id, provider_value
                    )
                elif organization_id:
                    row = await conn.fetchrow(
                        """
                        SELECT * FROM oauth_tokens
                        WHERE organization_id = $1 AND provider = $2 AND is_valid = true
                        """,
                        organization_id, provider_value
                    )
                else:
                    return None

                return self._row_to_oauth_token(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to get OAuth token: {e}")
            raise DatabaseException(
                message="Failed to retrieve OAuth token",
                error_code="OAUTH_TOKEN_GET_ERROR",
                details={"provider": str(provider)},
                original_exception=e
            )

    async def update_oauth_token(
        self,
        token_id: UUID,
        updates: Dict[str, Any]
    ) -> Optional[OAuthToken]:
        """
        Update an OAuth token.

        What: Updates OAuth token fields (e.g., after refresh).
        Where: Called when refreshing or invalidating tokens.
        Why: Enables maintaining valid token state.

        Args:
            token_id: UUID of the token to update
            updates: Dictionary of fields to update

        Returns:
            Updated token or None if not found
        """
        try:
            set_clauses = []
            params = []
            param_count = 1

            for field, value in updates.items():
                if hasattr(value, 'value'):  # Handle enums
                    set_clauses.append(f"{field} = ${param_count}")
                    params.append(value.value)
                else:
                    set_clauses.append(f"{field} = ${param_count}")
                    params.append(value)
                param_count += 1

            set_clauses.append(f"updated_at = ${param_count}")
            params.append(datetime.now())
            param_count += 1

            params.append(token_id)

            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    UPDATE oauth_tokens
                    SET {', '.join(set_clauses)}
                    WHERE id = ${param_count}
                    RETURNING *
                    """,
                    *params
                )
                return self._row_to_oauth_token(row) if row else None

        except Exception as e:
            self.logger.error(f"Failed to update OAuth token {token_id}: {e}")
            raise DatabaseException(
                message="Failed to update OAuth token",
                error_code="OAUTH_TOKEN_UPDATE_ERROR",
                details={"token_id": str(token_id)},
                original_exception=e
            )

    async def delete_oauth_token(self, token_id: UUID) -> bool:
        """
        Delete an OAuth token.

        What: Removes an OAuth token.
        Where: Called when user revokes access.
        Why: Enables token cleanup and revocation.

        Args:
            token_id: UUID of the token to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM oauth_tokens WHERE id = $1",
                    token_id
                )
                return result == "DELETE 1"

        except Exception as e:
            self.logger.error(f"Failed to delete OAuth token {token_id}: {e}")
            raise DatabaseException(
                message="Failed to delete OAuth token",
                error_code="OAUTH_TOKEN_DELETE_ERROR",
                details={"token_id": str(token_id)},
                original_exception=e
            )

    # ================================================================
    # ROW CONVERSION HELPERS
    # ================================================================

    def _row_to_lti_platform(self, row) -> LTIPlatformRegistration:
        """Convert database row to LTIPlatformRegistration entity."""
        return LTIPlatformRegistration(
            id=row['id'],
            organization_id=row['organization_id'],
            platform_name=row['platform_name'],
            issuer=row['issuer'],
            client_id=row['client_id'],
            deployment_id=row['deployment_id'],
            auth_login_url=row['auth_login_url'],
            auth_token_url=row['auth_token_url'],
            jwks_url=row['jwks_url'],
            tool_public_key=row['tool_public_key'],
            tool_private_key=row['tool_private_key'],
            platform_public_keys=row['platform_public_keys'] if row['platform_public_keys'] else [],
            scopes=list(row['scopes']) if row['scopes'] else [],
            deep_linking_enabled=row['deep_linking_enabled'],
            names_role_service_enabled=row['names_role_service_enabled'],
            assignment_grade_service_enabled=row['assignment_grade_service_enabled'],
            is_active=row['is_active'],
            verified_at=row['verified_at'],
            last_connection_at=row['last_connection_at'],
            created_by=row['created_by'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_lti_context(self, row) -> LTIContext:
        """Convert database row to LTIContext entity."""
        return LTIContext(
            id=row['id'],
            platform_id=row['platform_id'],
            lti_context_id=row['lti_context_id'],
            lti_context_type=row['lti_context_type'],
            lti_context_title=row['lti_context_title'],
            lti_context_label=row['lti_context_label'],
            course_id=row['course_id'],
            course_instance_id=row['course_instance_id'],
            resource_link_id=row['resource_link_id'],
            resource_link_title=row['resource_link_title'],
            last_roster_sync=row['last_roster_sync'],
            auto_roster_sync=row['auto_roster_sync'],
            roster_sync_interval_hours=row['roster_sync_interval_hours'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_lti_user_mapping(self, row) -> LTIUserMapping:
        """Convert database row to LTIUserMapping entity."""
        return LTIUserMapping(
            id=row['id'],
            platform_id=row['platform_id'],
            user_id=row['user_id'],
            lti_user_id=row['lti_user_id'],
            lti_email=row['lti_email'],
            lti_name=row['lti_name'],
            lti_given_name=row['lti_given_name'],
            lti_family_name=row['lti_family_name'],
            lti_picture_url=row['lti_picture_url'],
            lti_roles=list(row['lti_roles']) if row['lti_roles'] else [],
            mapped_role_name=row['mapped_role_name'],
            is_active=row['is_active'],
            last_login_at=row['last_login_at'],
            login_count=row['login_count'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_lti_grade_sync(self, row) -> LTIGradeSync:
        """Convert database row to LTIGradeSync entity."""
        return LTIGradeSync(
            id=row['id'],
            context_id=row['context_id'],
            user_mapping_id=row['user_mapping_id'],
            lineitem_id=row['lineitem_id'],
            score=row['score'],
            max_score=row['max_score'],
            comment=row['comment'],
            quiz_attempt_id=row['quiz_attempt_id'],
            assignment_id=row['assignment_id'],
            sync_status=GradeSyncStatus(row['sync_status']) if row['sync_status'] else GradeSyncStatus.PENDING,
            last_sync_attempt=row['last_sync_attempt'],
            last_sync_success=row['last_sync_success'],
            sync_error_message=row['sync_error_message'],
            retry_count=row['retry_count'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_calendar_provider(self, row) -> CalendarProvider:
        """Convert database row to CalendarProvider entity."""
        return CalendarProvider(
            id=row['id'],
            user_id=row['user_id'],
            provider_type=CalendarProviderType(row['provider_type']) if row['provider_type'] else CalendarProviderType.GOOGLE,
            provider_name=row['provider_name'],
            access_token=row['access_token'],
            refresh_token=row['refresh_token'],
            token_expires_at=row['token_expires_at'],
            calendar_id=row['calendar_id'],
            calendar_name=row['calendar_name'],
            calendar_timezone=row['calendar_timezone'],
            sync_enabled=row['sync_enabled'],
            sync_direction=SyncDirection(row['sync_direction']) if row['sync_direction'] else SyncDirection.BIDIRECTIONAL,
            sync_deadline_reminders=row['sync_deadline_reminders'],
            sync_class_schedules=row['sync_class_schedules'],
            sync_quiz_dates=row['sync_quiz_dates'],
            reminder_minutes_before=row['reminder_minutes_before'],
            is_connected=row['is_connected'],
            last_sync_at=row['last_sync_at'],
            last_sync_error=row['last_sync_error'],
            connection_error_count=row['connection_error_count'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_calendar_event(self, row) -> CalendarEvent:
        """Convert database row to CalendarEvent entity."""
        return CalendarEvent(
            id=row['id'],
            provider_id=row['provider_id'],
            user_id=row['user_id'],
            external_event_id=row['external_event_id'],
            external_calendar_id=row['external_calendar_id'],
            title=row['title'],
            description=row['description'],
            location=row['location'],
            start_time=row['start_time'],
            end_time=row['end_time'],
            all_day=row['all_day'],
            timezone=row['timezone'],
            is_recurring=row['is_recurring'],
            recurrence_rule=row['recurrence_rule'],
            recurring_event_id=row['recurring_event_id'],
            event_type=row['event_type'],
            source_type=row['source_type'],
            source_id=row['source_id'],
            sync_status=CalendarSyncStatus(row['sync_status']) if row['sync_status'] else CalendarSyncStatus.SYNCED,
            local_updated_at=row['local_updated_at'],
            remote_updated_at=row['remote_updated_at'],
            last_sync_at=row['last_sync_at'],
            reminder_sent=row['reminder_sent'],
            reminder_sent_at=row['reminder_sent_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_slack_workspace(self, row) -> SlackWorkspace:
        """Convert database row to SlackWorkspace entity."""
        return SlackWorkspace(
            id=row['id'],
            organization_id=row['organization_id'],
            workspace_id=row['workspace_id'],
            workspace_name=row['workspace_name'],
            workspace_domain=row['workspace_domain'],
            bot_token=row['bot_token'],
            bot_user_id=row['bot_user_id'],
            app_id=row['app_id'],
            scopes=list(row['scopes']) if row['scopes'] else [],
            default_announcements_channel=row['default_announcements_channel'],
            default_alerts_channel=row['default_alerts_channel'],
            enable_notifications=row['enable_notifications'],
            enable_commands=row['enable_commands'],
            enable_ai_assistant=row['enable_ai_assistant'],
            is_active=row['is_active'],
            installed_at=row['installed_at'],
            last_activity_at=row['last_activity_at'],
            installed_by=row['installed_by'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_slack_channel_mapping(self, row) -> SlackChannelMapping:
        """Convert database row to SlackChannelMapping entity."""
        return SlackChannelMapping(
            id=row['id'],
            workspace_id=row['workspace_id'],
            channel_id=row['channel_id'],
            channel_name=row['channel_name'],
            channel_type=SlackChannelType(row['channel_type']) if row['channel_type'] else SlackChannelType.PUBLIC,
            entity_type=row['entity_type'],
            entity_id=row['entity_id'],
            notify_announcements=row['notify_announcements'],
            notify_deadlines=row['notify_deadlines'],
            notify_grades=row['notify_grades'],
            notify_new_content=row['notify_new_content'],
            notify_discussions=row['notify_discussions'],
            is_active=row['is_active'],
            last_message_at=row['last_message_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_slack_user_mapping(self, row) -> SlackUserMapping:
        """Convert database row to SlackUserMapping entity."""
        return SlackUserMapping(
            id=row['id'],
            workspace_id=row['workspace_id'],
            user_id=row['user_id'],
            slack_user_id=row['slack_user_id'],
            slack_username=row['slack_username'],
            slack_email=row['slack_email'],
            slack_real_name=row['slack_real_name'],
            slack_display_name=row['slack_display_name'],
            dm_notifications_enabled=row['dm_notifications_enabled'],
            mention_notifications_enabled=row['mention_notifications_enabled'],
            daily_digest_enabled=row['daily_digest_enabled'],
            digest_time=row['digest_time'],
            is_active=row['is_active'],
            last_dm_at=row['last_dm_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_slack_message(self, row) -> SlackMessage:
        """Convert database row to SlackMessage entity."""
        return SlackMessage(
            id=row['id'],
            workspace_id=row['workspace_id'],
            channel_mapping_id=row['channel_mapping_id'],
            user_mapping_id=row['user_mapping_id'],
            slack_message_ts=row['slack_message_ts'],
            message_type=SlackMessageType(row['message_type']) if row['message_type'] else SlackMessageType.ANNOUNCEMENT,
            message_text=row['message_text'],
            source_type=row['source_type'],
            source_id=row['source_id'],
            delivery_status=row['delivery_status'],
            sent_at=row['sent_at'],
            error_message=row['error_message'],
            reaction_count=row['reaction_count'],
            reply_count=row['reply_count'],
            created_at=row['created_at']
        )

    def _row_to_outbound_webhook(self, row) -> OutboundWebhook:
        """Convert database row to OutboundWebhook entity."""
        return OutboundWebhook(
            id=row['id'],
            organization_id=row['organization_id'],
            name=row['name'],
            description=row['description'],
            target_url=row['target_url'],
            auth_type=WebhookAuthType(row['auth_type']) if row['auth_type'] else WebhookAuthType.NONE,
            auth_secret=row['auth_secret'],
            event_types=list(row['event_types']) if row['event_types'] else [],
            filter_conditions=row['filter_conditions'] if row['filter_conditions'] else {},
            retry_count=row['retry_count'],
            retry_delay_seconds=row['retry_delay_seconds'],
            timeout_seconds=row['timeout_seconds'],
            is_active=row['is_active'],
            last_triggered_at=row['last_triggered_at'],
            success_count=row['success_count'],
            failure_count=row['failure_count'],
            created_by=row['created_by'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_webhook_delivery_log(self, row) -> WebhookDeliveryLog:
        """Convert database row to WebhookDeliveryLog entity."""
        return WebhookDeliveryLog(
            id=row['id'],
            webhook_id=row['webhook_id'],
            event_type=row['event_type'],
            event_id=row['event_id'],
            payload=row['payload'] if row['payload'] else {},
            attempt_number=row['attempt_number'],
            request_timestamp=row['request_timestamp'],
            response_timestamp=row['response_timestamp'],
            response_status_code=row['response_status_code'],
            response_body=row['response_body'],
            response_headers=row['response_headers'] if row['response_headers'] else None,
            delivery_status=WebhookDeliveryStatus(row['delivery_status']) if row['delivery_status'] else WebhookDeliveryStatus.PENDING,
            error_message=row['error_message'],
            next_retry_at=row['next_retry_at']
        )

    def _row_to_inbound_webhook(self, row) -> InboundWebhook:
        """Convert database row to InboundWebhook entity."""
        return InboundWebhook(
            id=row['id'],
            organization_id=row['organization_id'],
            name=row['name'],
            description=row['description'],
            webhook_token=row['webhook_token'],
            auth_type=WebhookAuthType(row['auth_type']) if row['auth_type'] else WebhookAuthType.API_KEY,
            auth_secret=row['auth_secret'],
            allowed_ips=list(row['allowed_ips']) if row['allowed_ips'] else [],
            handler_type=WebhookHandlerType(row['handler_type']) if row['handler_type'] else WebhookHandlerType.CUSTOM,
            handler_config=row['handler_config'] if row['handler_config'] else {},
            is_active=row['is_active'],
            last_received_at=row['last_received_at'],
            total_received=row['total_received'],
            total_processed=row['total_processed'],
            total_failed=row['total_failed'],
            created_by=row['created_by'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_oauth_token(self, row) -> OAuthToken:
        """Convert database row to OAuthToken entity."""
        return OAuthToken(
            id=row['id'],
            user_id=row['user_id'],
            organization_id=row['organization_id'],
            provider=OAuthProvider(row['provider']) if row['provider'] else OAuthProvider.GOOGLE,
            provider_user_id=row['provider_user_id'],
            access_token=row['access_token'],
            refresh_token=row['refresh_token'],
            token_type=row['token_type'],
            expires_at=row['expires_at'],
            refresh_expires_at=row['refresh_expires_at'],
            scopes=list(row['scopes']) if row['scopes'] else [],
            is_valid=row['is_valid'],
            last_used_at=row['last_used_at'],
            last_refreshed_at=row['last_refreshed_at'],
            consecutive_failures=row['consecutive_failures'],
            last_error=row['last_error'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
