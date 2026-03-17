"""
LLM Configuration Data Access Object (DAO)

BUSINESS PURPOSE:
Manages database operations for organization-level LLM provider configuration.
Enables organizations to store their API keys, select providers, and track
usage for screenshot-to-course generation and other AI features.

TECHNICAL IMPLEMENTATION:
- Secure API key storage with encryption
- Multi-provider support per organization
- Usage tracking and quota management
- Audit logging for compliance

WHY:
Organizations need to configure their own LLM providers based on:
- Cost considerations
- Data residency requirements
- Performance preferences
- Existing cloud infrastructure
This DAO provides the persistence layer for these configurations.
"""

import asyncpg
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from organization_management.exceptions import (
    DatabaseException,
    ValidationException
)


logger = logging.getLogger(__name__)


class LLMConfigDAO:
    """
    Data Access Object for LLM Configuration Management

    BUSINESS CONTEXT:
    Provides database operations for:
    - Organization LLM provider configuration
    - API key secure storage
    - Provider preference management
    - Usage tracking and quotas
    - Configuration audit logging

    TECHNICAL IMPLEMENTATION:
    - Uses asyncpg for async PostgreSQL operations
    - Implements secure API key handling
    - Supports multiple providers per organization
    - Tracks usage for billing and quotas
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize the LLM Config DAO

        Args:
            db_pool: AsyncPG connection pool
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)

    # ================================================================
    # PROVIDER REFERENCE DATA
    # ================================================================

    async def get_available_providers(self) -> List[Dict[str, Any]]:
        """
        Get all available LLM providers

        BUSINESS CONTEXT:
        Returns the list of supported providers that organizations
        can configure for their AI operations.

        Returns:
            List of provider dictionaries with metadata
        """
        query = """
            SELECT
                id,
                provider_name,
                display_name,
                api_base_url,
                vision_endpoint,
                text_endpoint,
                auth_type,
                supports_vision,
                supports_streaming,
                default_model,
                available_models,
                rate_limit_requests_per_minute,
                max_tokens_per_request,
                is_local,
                is_active,
                metadata
            FROM llm_providers
            WHERE is_active = TRUE
            ORDER BY display_name
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query)
                return [dict(row) for row in rows]
        except asyncpg.PostgresError as e:
            self.logger.error(f"Failed to fetch providers: {e}")
            raise DatabaseException(f"Failed to fetch LLM providers: {e}")

    async def get_provider_by_name(
        self,
        provider_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get provider by name

        Args:
            provider_name: Provider identifier

        Returns:
            Provider data or None
        """
        query = """
            SELECT *
            FROM llm_providers
            WHERE provider_name = $1 AND is_active = TRUE
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(query, provider_name)
                return dict(row) if row else None
        except asyncpg.PostgresError as e:
            self.logger.error(f"Failed to fetch provider {provider_name}: {e}")
            raise DatabaseException(f"Failed to fetch provider: {e}")

    # ================================================================
    # ORGANIZATION LLM CONFIGURATION
    # ================================================================

    async def create_org_llm_config(
        self,
        organization_id: UUID,
        provider_name: str,
        api_key: str,
        model_name: Optional[str] = None,
        custom_base_url: Optional[str] = None,
        is_primary: bool = False,
        usage_quota_monthly: Optional[int] = None,
        settings: Optional[Dict[str, Any]] = None,
        created_by: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Create LLM configuration for an organization

        BUSINESS CONTEXT:
        Stores an organization's LLM provider configuration including
        their API key for accessing AI services.

        SECURITY:
        - API keys are hashed before storage
        - Original keys are encrypted (encryption handled externally)
        - Audit trail created for compliance

        Args:
            organization_id: Organization UUID
            provider_name: Provider identifier
            api_key: API key (will be stored encrypted externally)
            model_name: Preferred model (optional)
            custom_base_url: Custom API URL (optional)
            is_primary: Whether this is the primary provider
            usage_quota_monthly: Monthly token quota (optional, None = unlimited)
            settings: Additional settings JSON
            created_by: User ID who created config

        Returns:
            Created configuration record

        Raises:
            ValidationException: If provider not found
            DatabaseException: If database operation fails
        """
        # Get provider ID
        provider = await self.get_provider_by_name(provider_name)
        if not provider:
            raise ValidationException(f"Unknown provider: {provider_name}")

        # Hash API key for lookup/validation (actual key stored encrypted)
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:64]

        config_id = uuid4()

        # If setting as primary, unset other primaries first
        if is_primary:
            await self._unset_primary_config(organization_id)

        query = """
            INSERT INTO organization_llm_config (
                id, organization_id, provider_id, api_key_encrypted,
                api_key_hash, model_name, custom_base_url, is_primary,
                is_active, usage_quota_monthly, settings, created_by, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, TRUE, $9, $10, $11, NOW(), NOW())
            RETURNING *
        """

        try:
            import json
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    config_id,
                    organization_id,
                    provider["id"],
                    api_key,  # Should be encrypted by caller
                    api_key_hash,
                    model_name or provider["default_model"],
                    custom_base_url,
                    is_primary,
                    usage_quota_monthly,
                    json.dumps(settings or {}),  # Serialize dict to JSON string for JSONB column
                    created_by
                )

                self.logger.info(
                    f"Created LLM config for org {organization_id}, "
                    f"provider {provider_name}"
                )

                return dict(row)

        except asyncpg.UniqueViolationError:
            raise ValidationException(
                f"LLM config already exists for this organization and provider"
            )
        except asyncpg.PostgresError as e:
            self.logger.error(f"Failed to create LLM config: {e}")
            raise DatabaseException(f"Failed to create LLM config: {e}")

    async def get_org_llm_configs(
        self,
        organization_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get all LLM configurations for an organization

        BUSINESS CONTEXT:
        Returns all configured providers for an organization,
        allowing them to manage multiple AI service integrations.

        Args:
            organization_id: Organization UUID

        Returns:
            List of configuration records with provider details
        """
        query = """
            SELECT
                olc.id,
                olc.organization_id,
                olc.provider_id,
                olc.model_name,
                olc.custom_base_url,
                olc.is_primary,
                olc.is_active,
                olc.usage_quota_monthly,
                olc.usage_current_month,
                olc.last_used_at,
                olc.settings,
                olc.created_at,
                olc.updated_at,
                lp.provider_name,
                lp.display_name,
                lp.api_base_url,
                lp.supports_vision,
                lp.supports_streaming,
                lp.available_models,
                lp.is_local
            FROM organization_llm_config olc
            JOIN llm_providers lp ON olc.provider_id = lp.id
            WHERE olc.organization_id = $1
            ORDER BY olc.is_primary DESC, olc.created_at
        """

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, organization_id)
                return [dict(row) for row in rows]
        except asyncpg.PostgresError as e:
            self.logger.error(
                f"Failed to fetch LLM configs for org {organization_id}: {e}"
            )
            raise DatabaseException(f"Failed to fetch LLM configs: {e}")

    async def get_org_primary_config(
        self,
        organization_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get the primary LLM configuration for an organization

        BUSINESS CONTEXT:
        Returns the default provider configuration used for
        AI operations when no specific provider is requested.

        Args:
            organization_id: Organization UUID

        Returns:
            Primary configuration or None
        """
        query = """
            SELECT
                olc.*,
                lp.provider_name,
                lp.display_name,
                lp.api_base_url,
                lp.vision_endpoint,
                lp.text_endpoint,
                lp.supports_vision,
                lp.auth_type,
                lp.available_models
            FROM organization_llm_config olc
            JOIN llm_providers lp ON olc.provider_id = lp.id
            WHERE olc.organization_id = $1
              AND olc.is_primary = TRUE
              AND olc.is_active = TRUE
              AND lp.is_active = TRUE
        """

        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(query, organization_id)
                return dict(row) if row else None
        except asyncpg.PostgresError as e:
            self.logger.error(f"Failed to fetch primary config: {e}")
            raise DatabaseException(f"Failed to fetch primary config: {e}")

    async def get_org_vision_config(
        self,
        organization_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get a vision-capable LLM configuration for an organization

        BUSINESS CONTEXT:
        Returns a provider configuration that supports vision
        for screenshot analysis operations.

        Args:
            organization_id: Organization UUID

        Returns:
            Vision-capable configuration or None
        """
        query = """
            SELECT
                olc.*,
                lp.provider_name,
                lp.display_name,
                lp.api_base_url,
                lp.vision_endpoint,
                lp.supports_vision,
                lp.auth_type,
                lp.available_models
            FROM organization_llm_config olc
            JOIN llm_providers lp ON olc.provider_id = lp.id
            WHERE olc.organization_id = $1
              AND olc.is_active = TRUE
              AND lp.is_active = TRUE
              AND lp.supports_vision = TRUE
            ORDER BY olc.is_primary DESC, olc.created_at
            LIMIT 1
        """

        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(query, organization_id)
                return dict(row) if row else None
        except asyncpg.PostgresError as e:
            self.logger.error(f"Failed to fetch vision config: {e}")
            raise DatabaseException(f"Failed to fetch vision config: {e}")

    async def update_org_llm_config(
        self,
        config_id: UUID,
        organization_id: UUID,
        updates: Dict[str, Any],
        updated_by: Optional[UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update an organization's LLM configuration

        BUSINESS CONTEXT:
        Allows organizations to modify their provider settings,
        change models, or update API keys.

        Args:
            config_id: Configuration UUID
            organization_id: Organization UUID (for security)
            updates: Fields to update
            updated_by: User ID making the update

        Returns:
            Updated configuration or None if not found
        """
        # Build dynamic update query
        allowed_fields = {
            "model_name", "custom_base_url", "is_primary",
            "is_active", "settings", "usage_quota_monthly"
        }

        set_clauses = ["updated_at = NOW()"]
        values = []
        param_idx = 1

        # Handle api_key update specially (needs hashing)
        if "api_key" in updates:
            new_api_key = updates["api_key"]
            new_key_hash = hashlib.sha256(new_api_key.encode()).hexdigest()[:64]
            set_clauses.append(f"api_key_encrypted = ${param_idx}")
            values.append(new_api_key)
            param_idx += 1
            set_clauses.append(f"api_key_hash = ${param_idx}")
            values.append(new_key_hash)
            param_idx += 1

        for field, value in updates.items():
            if field in allowed_fields:
                set_clauses.append(f"{field} = ${param_idx}")
                values.append(value)
                param_idx += 1

        if updated_by:
            set_clauses.append(f"updated_by = ${param_idx}")
            values.append(updated_by)
            param_idx += 1

        values.extend([config_id, organization_id])

        query = f"""
            UPDATE organization_llm_config
            SET {', '.join(set_clauses)}
            WHERE id = ${param_idx} AND organization_id = ${param_idx + 1}
            RETURNING *
        """

        try:
            async with self.db_pool.acquire() as conn:
                # Handle is_primary change
                if updates.get("is_primary"):
                    await self._unset_primary_config(
                        organization_id,
                        exclude_id=config_id,
                        conn=conn
                    )

                row = await conn.fetchrow(query, *values)

                if row:
                    self.logger.info(
                        f"Updated LLM config {config_id} for org {organization_id}"
                    )
                    return dict(row)
                return None

        except asyncpg.PostgresError as e:
            self.logger.error(f"Failed to update LLM config: {e}")
            raise DatabaseException(f"Failed to update LLM config: {e}")

    async def delete_org_llm_config(
        self,
        config_id: UUID,
        organization_id: UUID
    ) -> bool:
        """
        Delete an organization's LLM configuration

        BUSINESS CONTEXT:
        Removes a provider configuration when no longer needed.

        Args:
            config_id: Configuration UUID
            organization_id: Organization UUID (for security)

        Returns:
            True if deleted, False if not found
        """
        query = """
            DELETE FROM organization_llm_config
            WHERE id = $1 AND organization_id = $2
            RETURNING id
        """

        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, config_id, organization_id)

                if result:
                    self.logger.info(
                        f"Deleted LLM config {config_id} for org {organization_id}"
                    )
                    return True
                return False

        except asyncpg.PostgresError as e:
            self.logger.error(f"Failed to delete LLM config: {e}")
            raise DatabaseException(f"Failed to delete LLM config: {e}")

    async def _unset_primary_config(
        self,
        organization_id: UUID,
        exclude_id: Optional[UUID] = None,
        conn: Optional[asyncpg.Connection] = None
    ):
        """Unset primary flag on all other configs for an organization"""
        query = """
            UPDATE organization_llm_config
            SET is_primary = FALSE, updated_at = NOW()
            WHERE organization_id = $1 AND is_primary = TRUE
        """
        params = [organization_id]

        if exclude_id:
            query += " AND id != $2"
            params.append(exclude_id)

        if conn:
            await conn.execute(query, *params)
        else:
            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

    # ================================================================
    # USAGE TRACKING
    # ================================================================

    async def log_llm_usage(
        self,
        organization_id: UUID,
        config_id: Optional[UUID],
        provider_name: str,
        model_name: str,
        operation_type: str,
        input_tokens: int,
        output_tokens: int,
        cost_estimate: float,
        latency_ms: int,
        success: bool = True,
        error_message: Optional[str] = None,
        user_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Log LLM API usage for billing and analytics

        BUSINESS CONTEXT:
        Tracks all LLM API calls for:
        - Usage-based billing
        - Quota enforcement
        - Analytics and optimization
        - Audit compliance

        Args:
            organization_id: Organization UUID
            config_id: Configuration used (if known)
            provider_name: Provider name
            model_name: Model used
            operation_type: Type of operation (vision, text, etc.)
            input_tokens: Input token count
            output_tokens: Output token count
            cost_estimate: Estimated cost in USD
            latency_ms: Request latency
            success: Whether request succeeded
            error_message: Error message if failed
            user_id: User who made the request
            metadata: Additional metadata

        Returns:
            Log entry UUID
        """
        log_id = uuid4()
        total_tokens = input_tokens + output_tokens

        query = """
            INSERT INTO llm_usage_log (
                id, organization_id, config_id, provider_name, model_name,
                operation_type, input_tokens, output_tokens, total_tokens,
                cost_estimate, latency_ms, success, error_message,
                request_metadata, user_id, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, NOW())
        """

        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    query,
                    log_id,
                    organization_id,
                    config_id,
                    provider_name,
                    model_name,
                    operation_type,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    cost_estimate,
                    latency_ms,
                    success,
                    error_message,
                    metadata or {},
                    user_id
                )

                # Update usage counter on config
                if config_id and success:
                    await conn.execute(
                        """
                        UPDATE organization_llm_config
                        SET usage_current_month = usage_current_month + $1,
                            last_used_at = NOW(),
                            updated_at = NOW()
                        WHERE id = $2
                        """,
                        total_tokens,
                        config_id
                    )

                return log_id

        except asyncpg.PostgresError as e:
            self.logger.error(f"Failed to log LLM usage: {e}")
            # Don't raise - usage logging shouldn't break operations
            return log_id

    async def get_org_usage_stats(
        self,
        organization_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics for an organization

        BUSINESS CONTEXT:
        Returns aggregated usage data for billing, reporting,
        and optimization analysis.

        Args:
            organization_id: Organization UUID
            start_date: Start of period (optional)
            end_date: End of period (optional)

        Returns:
            Usage statistics dictionary
        """
        query = """
            SELECT
                COUNT(*) as total_requests,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(total_tokens) as total_tokens,
                SUM(cost_estimate) as total_cost,
                AVG(latency_ms) as avg_latency_ms,
                COUNT(*) FILTER (WHERE success = TRUE) as successful_requests,
                COUNT(*) FILTER (WHERE success = FALSE) as failed_requests
            FROM llm_usage_log
            WHERE organization_id = $1
        """
        params = [organization_id]
        param_idx = 2

        if start_date:
            query += f" AND created_at >= ${param_idx}"
            params.append(start_date)
            param_idx += 1

        if end_date:
            query += f" AND created_at <= ${param_idx}"
            params.append(end_date)

        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(query, *params)
                return dict(row) if row else {}
        except asyncpg.PostgresError as e:
            self.logger.error(f"Failed to fetch usage stats: {e}")
            raise DatabaseException(f"Failed to fetch usage stats: {e}")

    async def get_org_usage_by_provider(
        self,
        organization_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get usage statistics grouped by provider

        Args:
            organization_id: Organization UUID
            start_date: Start of period
            end_date: End of period

        Returns:
            List of usage stats per provider
        """
        query = """
            SELECT
                provider_name,
                COUNT(*) as request_count,
                SUM(total_tokens) as total_tokens,
                SUM(cost_estimate) as total_cost,
                AVG(latency_ms) as avg_latency_ms
            FROM llm_usage_log
            WHERE organization_id = $1
        """
        params = [organization_id]
        param_idx = 2

        if start_date:
            query += f" AND created_at >= ${param_idx}"
            params.append(start_date)
            param_idx += 1

        if end_date:
            query += f" AND created_at <= ${param_idx}"
            params.append(end_date)

        query += " GROUP BY provider_name ORDER BY total_tokens DESC"

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
        except asyncpg.PostgresError as e:
            self.logger.error(f"Failed to fetch usage by provider: {e}")
            raise DatabaseException(f"Failed to fetch usage by provider: {e}")

    async def check_quota_available(
        self,
        config_id: UUID,
        tokens_needed: int
    ) -> bool:
        """
        Check if usage quota allows for more tokens

        BUSINESS CONTEXT:
        Enforces usage quotas to prevent unexpected costs.

        Args:
            config_id: Configuration UUID
            tokens_needed: Tokens about to be used

        Returns:
            True if quota available, False otherwise
        """
        query = """
            SELECT
                usage_quota_monthly,
                usage_current_month
            FROM organization_llm_config
            WHERE id = $1 AND is_active = TRUE
        """

        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(query, config_id)

                if not row:
                    return False

                quota = row["usage_quota_monthly"]
                current = row["usage_current_month"] or 0

                # No quota set means unlimited
                if quota is None:
                    return True

                return (current + tokens_needed) <= quota

        except asyncpg.PostgresError as e:
            self.logger.error(f"Failed to check quota: {e}")
            return False  # Fail safe - deny if can't check
