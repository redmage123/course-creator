"""
Payment Service Data Access Object (DAO)

This module implements the Data Access Object (DAO) pattern for payment service operations,
centralizing all SQL queries and database interactions in a single, maintainable location.

Business Context:
The Payment Service manages subscription billing, invoicing, transaction processing, and
payment method storage for all organizations on the Course Creator Platform. By centralizing
all SQL operations in this DAO, we achieve:
- Single source of truth for all payment-related database queries
- Enhanced security through consistent parameterized query patterns
- Improved maintainability and testing capabilities
- Clear separation between business logic and data access concerns
- Auditability through immutable payment audit log entries

Technical Rationale:
- Follows the Single Responsibility Principle by isolating data access concerns
- Enables comprehensive transaction support for complex payment operations
- Provides consistent error handling using the payment service exception hierarchy
- Supports connection pooling for optimal database resource utilization
- Facilitates database schema evolution without affecting business logic
- Enables easier unit testing through clear interface boundaries
- All monetary amounts stored in cents (integer) to avoid floating point issues
- All JSONB columns serialized via json.dumps before insertion
"""

import asyncpg
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from payment_service.exceptions import (
    PaymentDatabaseException,
    PaymentValidationException,
    PlanNotFoundException,
    SubscriptionNotFoundException,
    InvoiceNotFoundException,
    PaymentNotFoundException,
    PaymentMethodNotFoundException,
)


class PaymentDAO:
    """
    Data Access Object for Payment Service Operations

    This class centralizes all SQL queries and database operations for the payment
    service, following the DAO pattern for clean architecture.

    Business Context:
    Provides comprehensive data access methods for payment lifecycle management including:
    - Subscription plan definition and retrieval
    - Organization subscription creation and lifecycle tracking
    - Invoice generation and status management
    - Invoice line item creation and retrieval
    - Transaction recording for payments and refunds
    - Payment method tokenized storage and default selection
    - Payment provider registration and lookup
    - Immutable audit log for all payment mutations

    Technical Implementation:
    - Uses asyncpg for high-performance PostgreSQL operations
    - Implements connection pooling for optimal resource usage
    - Provides parameterized queries to prevent SQL injection
    - Includes comprehensive error handling with custom exceptions
    - All tables reside in the course_creator schema for tenant isolation
    - UUID primary keys converted from string parameters before query execution
    - JSONB columns serialized with json.dumps before insertion
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize the Payment DAO with a database connection pool.

        Business Context:
        The DAO requires a connection pool to efficiently manage database connections
        across the payment service's operations.  Every public method acquires a
        connection from this pool, executes its query, and releases the connection
        back so that concurrent requests are not blocked.

        Args:
            db_pool: AsyncPG connection pool for database operations
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)

    # ================================================================
    # SUBSCRIPTION PLANS
    # ================================================================

    async def create_plan(self, plan_data: Dict[str, Any]) -> str:
        """
        Create a new subscription plan.

        Business Context:
        Subscription plans define the available tiers (Free, Pro, Enterprise) that
        organizations can subscribe to.  Each plan specifies pricing, billing interval,
        included features, and an optional trial period.  Plans are referenced by
        subscriptions and must exist before an organization can be billed.

        Technical Implementation:
        Inserts a row into course_creator.subscription_plans.  The features column is
        stored as JSONB and serialized from a Python dict.  Returns the generated UUID.

        Args:
            plan_data: Dictionary containing plan attributes:
                - name: Plan display name (e.g. 'Pro')
                - description: Human-readable plan description
                - price_cents: Monthly price in cents (integer)
                - currency: ISO 4217 currency code (default 'USD')
                - billing_interval: 'monthly' or 'yearly'
                - features: Dict of feature flags and limits
                - trial_days: Number of free trial days (default 0)
                - sort_order: Display ordering integer
                - provider_name: Registered provider name
                - is_active: Whether the plan is currently offered

        Returns:
            Created plan ID as string

        Raises:
            PaymentValidationException: If a plan with duplicate attributes violates a constraint
            PaymentDatabaseException: On any other database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                plan_id = await conn.fetchval(
                    """INSERT INTO course_creator.subscription_plans (
                        name, description, price_cents, currency, billing_interval,
                        features, trial_days, sort_order, provider_name, is_active,
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING id""",
                    plan_data.get("name"),
                    plan_data.get("description", ""),
                    plan_data.get("price_cents", 0),
                    plan_data.get("currency", "USD"),
                    plan_data.get("billing_interval", "monthly"),
                    json.dumps(plan_data.get("features", {})),
                    plan_data.get("trial_days", 0),
                    plan_data.get("sort_order", 0),
                    plan_data.get("provider_name", "null"),
                    plan_data.get("is_active", True),
                    datetime.utcnow(),
                    datetime.utcnow(),
                )
                return str(plan_id)
        except asyncpg.UniqueViolationError as e:
            raise PaymentValidationException(
                message=f"Subscription plan already exists or violates unique constraint: {e}",
                validation_errors={"name": plan_data.get("name", "unknown")},
            )
        except Exception as e:
            self.logger.error(f"Failed to create subscription plan: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to create subscription plan: {e}",
                operation="create_plan",
                original_exception=e,
            )

    async def get_plan_by_id(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a subscription plan by its unique identifier.

        Business Context:
        Used when displaying plan details during the subscription checkout flow, when
        validating a plan selection, or when computing invoice line items for a
        billing cycle.

        Technical Implementation:
        Performs a simple primary-key lookup on course_creator.subscription_plans.
        The UUID string is converted before query execution.

        Args:
            plan_id: UUID string of the subscription plan

        Returns:
            Dictionary of plan attributes if found, None otherwise

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(
                    """SELECT id, name, description, price_cents, currency,
                              billing_interval, features, trial_days, sort_order,
                              provider_name, is_active, created_at, updated_at
                       FROM course_creator.subscription_plans
                       WHERE id = $1""",
                    UUID(plan_id),
                )
                return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"Failed to get plan by id {plan_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to retrieve subscription plan {plan_id}: {e}",
                operation="get_plan_by_id",
                original_exception=e,
            )

    async def list_active_plans(self) -> List[Dict[str, Any]]:
        """
        List all active subscription plans ordered by sort_order.

        Business Context:
        Powers the pricing page and plan selection UI.  Only active plans are shown
        to prospective subscribers so that deprecated or internal-only plans remain
        hidden from the catalog.

        Technical Implementation:
        Filters on is_active=true and orders by sort_order ascending so that the
        cheapest or most popular plan appears first.

        Returns:
            List of dictionaries representing active plans in display order

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT id, name, description, price_cents, currency,
                              billing_interval, features, trial_days, sort_order,
                              provider_name, is_active, created_at, updated_at
                       FROM course_creator.subscription_plans
                       WHERE is_active = true
                       ORDER BY sort_order ASC""",
                )
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to list active plans: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to list active subscription plans: {e}",
                operation="list_active_plans",
                original_exception=e,
            )

    async def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a subscription plan's mutable attributes.

        Business Context:
        Allows administrators to adjust pricing, rename plans, change feature limits,
        or reorder the plan catalog.  The features column is re-serialized if present.
        The updated_at timestamp is always refreshed.

        Technical Implementation:
        Dynamically builds a SET clause from the provided updates dictionary.  Only
        columns present in the allowed set are included to prevent injection of
        arbitrary column names.

        Args:
            plan_id: UUID string of the plan to update
            updates: Dictionary of column names to new values (only allowed columns are applied)

        Returns:
            Updated plan as a dictionary

        Raises:
            PlanNotFoundException: If the plan does not exist
            PaymentDatabaseException: On database error
        """
        allowed_columns = {
            "name", "description", "price_cents", "currency", "billing_interval",
            "features", "trial_days", "sort_order", "provider_name", "is_active",
        }
        try:
            filtered = {k: v for k, v in updates.items() if k in allowed_columns}
            if not filtered:
                existing = await self.get_plan_by_id(plan_id)
                if existing is None:
                    raise PlanNotFoundException(plan_id)
                return existing

            set_clauses = []
            params: List[Any] = []
            idx = 1
            for col, val in filtered.items():
                idx += 1
                if col == "features":
                    set_clauses.append(f"{col} = ${idx}")
                    params.append(json.dumps(val))
                else:
                    set_clauses.append(f"{col} = ${idx}")
                    params.append(val)

            idx += 1
            set_clauses.append(f"updated_at = ${idx}")
            params.append(datetime.utcnow())

            query = f"""UPDATE course_creator.subscription_plans
                        SET {', '.join(set_clauses)}
                        WHERE id = $1
                        RETURNING id, name, description, price_cents, currency,
                                  billing_interval, features, trial_days, sort_order,
                                  provider_name, is_active, created_at, updated_at"""

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, UUID(plan_id), *params)
                if result is None:
                    raise PlanNotFoundException(plan_id)
                return dict(result)
        except PlanNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update plan {plan_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to update subscription plan {plan_id}: {e}",
                operation="update_plan",
                original_exception=e,
            )

    async def deactivate_plan(self, plan_id: str) -> bool:
        """
        Soft-delete a subscription plan by marking it inactive.

        Business Context:
        Plans are never hard-deleted because existing subscriptions reference them.
        Deactivating a plan removes it from the catalog while preserving historical
        billing records.

        Technical Implementation:
        Sets is_active=false and refreshes updated_at.  Returns True if the row
        was found and updated, False otherwise.

        Args:
            plan_id: UUID string of the plan to deactivate

        Returns:
            True if the plan was deactivated, False if no matching plan was found

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE course_creator.subscription_plans
                       SET is_active = false, updated_at = $2
                       WHERE id = $1""",
                    UUID(plan_id),
                    datetime.utcnow(),
                )
                return result == "UPDATE 1"
        except Exception as e:
            self.logger.error(f"Failed to deactivate plan {plan_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to deactivate subscription plan {plan_id}: {e}",
                operation="deactivate_plan",
                original_exception=e,
            )

    # ================================================================
    # SUBSCRIPTIONS
    # ================================================================

    async def create_subscription(self, sub_data: Dict[str, Any]) -> str:
        """
        Create a new subscription binding an organization to a plan.

        Business Context:
        A subscription represents the contractual relationship between an organization
        and a billing plan.  It tracks the current billing period, trial window, and
        lifecycle status (trial, active, past_due, paused, cancelled, expired).

        Technical Implementation:
        Inserts into course_creator.subscriptions.  The unique partial index
        idx_subscriptions_active_org ensures only one active-family subscription per
        organization, so a UniqueViolationError is mapped to PaymentValidationException.

        Args:
            sub_data: Dictionary containing subscription attributes:
                - organization_id: UUID string of the subscribing organization
                - plan_id: UUID string of the selected plan
                - status: Initial status (default 'trial')
                - provider_name: Provider handling billing
                - provider_subscription_id: External reference from the provider
                - current_period_start: Start of the first billing period
                - current_period_end: End of the first billing period
                - trial_end: When the trial period expires

        Returns:
            Created subscription ID as string

        Raises:
            PaymentValidationException: If the org already has an active subscription
            PaymentDatabaseException: On any other database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                sub_id = await conn.fetchval(
                    """INSERT INTO course_creator.subscriptions (
                        organization_id, plan_id, status, provider_name,
                        provider_subscription_id, current_period_start,
                        current_period_end, trial_end,
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id""",
                    UUID(sub_data["organization_id"]),
                    UUID(sub_data["plan_id"]),
                    sub_data.get("status", "trial"),
                    sub_data.get("provider_name", "null"),
                    sub_data.get("provider_subscription_id"),
                    sub_data.get("current_period_start"),
                    sub_data.get("current_period_end"),
                    sub_data.get("trial_end"),
                    datetime.utcnow(),
                    datetime.utcnow(),
                )
                return str(sub_id)
        except asyncpg.UniqueViolationError as e:
            raise PaymentValidationException(
                message=f"Organization already has an active subscription: {e}",
                validation_errors={"organization_id": sub_data.get("organization_id", "unknown")},
            )
        except Exception as e:
            self.logger.error(f"Failed to create subscription: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to create subscription: {e}",
                operation="create_subscription",
                original_exception=e,
            )

    async def get_subscription_by_id(self, sub_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a subscription by its unique identifier.

        Business Context:
        Used when displaying subscription details, processing renewals, or performing
        lifecycle transitions (e.g. trial-to-active, cancel, pause).

        Technical Implementation:
        Simple primary-key lookup on course_creator.subscriptions.

        Args:
            sub_id: UUID string of the subscription

        Returns:
            Dictionary of subscription attributes if found, None otherwise

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(
                    """SELECT id, organization_id, plan_id, status, provider_name,
                              provider_subscription_id, current_period_start,
                              current_period_end, trial_end, cancelled_at,
                              cancel_reason, created_at, updated_at
                       FROM course_creator.subscriptions
                       WHERE id = $1""",
                    UUID(sub_id),
                )
                return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"Failed to get subscription {sub_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to retrieve subscription {sub_id}: {e}",
                operation="get_subscription_by_id",
                original_exception=e,
            )

    async def get_active_subscription_for_org(self, org_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the active-family subscription for an organization.

        Business Context:
        At any given time an organization may have at most one subscription in an
        active-family status (trial, active, past_due, paused).  This method is the
        primary lookup used to determine an organization's current entitlements, to
        decide whether to show a paywall, and to calculate usage limits.

        Technical Implementation:
        Filters subscriptions by organization_id and the four active-family statuses.
        The partial unique index guarantees at most one row.

        Args:
            org_id: UUID string of the organization

        Returns:
            Dictionary of subscription attributes if found, None if the org has no active subscription

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(
                    """SELECT id, organization_id, plan_id, status, provider_name,
                              provider_subscription_id, current_period_start,
                              current_period_end, trial_end, cancelled_at,
                              cancel_reason, created_at, updated_at
                       FROM course_creator.subscriptions
                       WHERE organization_id = $1
                         AND status IN ('trial', 'active', 'past_due', 'paused')""",
                    UUID(org_id),
                )
                return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"Failed to get active subscription for org {org_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to retrieve active subscription for organization {org_id}: {e}",
                operation="get_active_subscription_for_org",
                original_exception=e,
            )

    async def update_subscription(self, sub_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update mutable attributes of an existing subscription.

        Business Context:
        Subscription updates occur during lifecycle transitions (e.g. trial-to-active),
        period renewals, plan changes, cancellations, and pause/resume operations.
        Every mutation also refreshes the updated_at timestamp for audit purposes.

        Technical Implementation:
        Dynamically builds a SET clause from the provided updates dictionary.
        Only columns in the allowed set are applied to prevent arbitrary column writes.

        Args:
            sub_id: UUID string of the subscription to update
            updates: Dictionary of column names to new values

        Returns:
            Updated subscription as a dictionary

        Raises:
            SubscriptionNotFoundException: If the subscription does not exist
            PaymentDatabaseException: On database error
        """
        allowed_columns = {
            "plan_id", "status", "provider_name", "provider_subscription_id",
            "current_period_start", "current_period_end", "trial_end",
            "cancelled_at", "cancel_reason",
        }
        try:
            filtered = {k: v for k, v in updates.items() if k in allowed_columns}
            if not filtered:
                existing = await self.get_subscription_by_id(sub_id)
                if existing is None:
                    raise SubscriptionNotFoundException(sub_id)
                return existing

            set_clauses = []
            params: List[Any] = []
            idx = 1
            for col, val in filtered.items():
                idx += 1
                if col == "plan_id":
                    set_clauses.append(f"{col} = ${idx}")
                    params.append(UUID(val) if isinstance(val, str) else val)
                else:
                    set_clauses.append(f"{col} = ${idx}")
                    params.append(val)

            idx += 1
            set_clauses.append(f"updated_at = ${idx}")
            params.append(datetime.utcnow())

            query = f"""UPDATE course_creator.subscriptions
                        SET {', '.join(set_clauses)}
                        WHERE id = $1
                        RETURNING id, organization_id, plan_id, status, provider_name,
                                  provider_subscription_id, current_period_start,
                                  current_period_end, trial_end, cancelled_at,
                                  cancel_reason, created_at, updated_at"""

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, UUID(sub_id), *params)
                if result is None:
                    raise SubscriptionNotFoundException(sub_id)
                return dict(result)
        except SubscriptionNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update subscription {sub_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to update subscription {sub_id}: {e}",
                operation="update_subscription",
                original_exception=e,
            )

    async def list_subscriptions_for_org(self, org_id: str) -> List[Dict[str, Any]]:
        """
        List all subscriptions (active and historical) for an organization.

        Business Context:
        Provides the full subscription history for an organization, including cancelled
        and expired records.  Useful for billing history views, audit reports, and
        support investigations.

        Technical Implementation:
        Returns all subscriptions for the organization ordered by creation date
        descending so the most recent subscription appears first.

        Args:
            org_id: UUID string of the organization

        Returns:
            List of subscription dictionaries ordered by created_at descending

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT id, organization_id, plan_id, status, provider_name,
                              provider_subscription_id, current_period_start,
                              current_period_end, trial_end, cancelled_at,
                              cancel_reason, created_at, updated_at
                       FROM course_creator.subscriptions
                       WHERE organization_id = $1
                       ORDER BY created_at DESC""",
                    UUID(org_id),
                )
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to list subscriptions for org {org_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to list subscriptions for organization {org_id}: {e}",
                operation="list_subscriptions_for_org",
                original_exception=e,
            )

    # ================================================================
    # INVOICES
    # ================================================================

    async def create_invoice(self, invoice_data: Dict[str, Any]) -> str:
        """
        Create a new invoice for an organization.

        Business Context:
        Invoices are the billing documents sent to organizations at the end of each
        billing cycle or when a one-time charge occurs.  Each invoice references a
        subscription (optional for one-time charges), carries a unique invoice number,
        and tracks status through draft, issued, paid, void, and overdue states.

        Technical Implementation:
        Inserts into course_creator.invoices.  The invoice_number column has a UNIQUE
        constraint to prevent duplicate invoice identifiers.

        Args:
            invoice_data: Dictionary containing invoice attributes:
                - organization_id: UUID string of the billed organization
                - subscription_id: Optional UUID string of the related subscription
                - invoice_number: Unique human-readable invoice identifier
                - amount_cents: Total amount in cents
                - currency: ISO 4217 currency code
                - status: Initial status (default 'draft')
                - provider_invoice_id: External provider reference
                - issued_at: When the invoice was issued
                - due_at: Payment due date
                - paid_at: When payment was received (if already paid)

        Returns:
            Created invoice ID as string

        Raises:
            PaymentValidationException: If the invoice number already exists
            PaymentDatabaseException: On any other database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                subscription_id = invoice_data.get("subscription_id")
                invoice_id = await conn.fetchval(
                    """INSERT INTO course_creator.invoices (
                        organization_id, subscription_id, invoice_number,
                        amount_cents, currency, status, provider_invoice_id,
                        issued_at, due_at, paid_at, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING id""",
                    UUID(invoice_data["organization_id"]),
                    UUID(subscription_id) if subscription_id else None,
                    invoice_data.get("invoice_number"),
                    invoice_data.get("amount_cents", 0),
                    invoice_data.get("currency", "USD"),
                    invoice_data.get("status", "draft"),
                    invoice_data.get("provider_invoice_id"),
                    invoice_data.get("issued_at"),
                    invoice_data.get("due_at"),
                    invoice_data.get("paid_at"),
                    datetime.utcnow(),
                    datetime.utcnow(),
                )
                return str(invoice_id)
        except asyncpg.UniqueViolationError as e:
            raise PaymentValidationException(
                message=f"Invoice number already exists: {e}",
                validation_errors={"invoice_number": invoice_data.get("invoice_number", "unknown")},
            )
        except Exception as e:
            self.logger.error(f"Failed to create invoice: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to create invoice: {e}",
                operation="create_invoice",
                original_exception=e,
            )

    async def get_invoice_by_id(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an invoice by its unique identifier.

        Business Context:
        Used when displaying invoice details, generating PDF receipts, or processing
        payment against an outstanding invoice.

        Technical Implementation:
        Simple primary-key lookup on course_creator.invoices.

        Args:
            invoice_id: UUID string of the invoice

        Returns:
            Dictionary of invoice attributes if found, None otherwise

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(
                    """SELECT id, organization_id, subscription_id, invoice_number,
                              amount_cents, currency, status, provider_invoice_id,
                              issued_at, due_at, paid_at, created_at, updated_at
                       FROM course_creator.invoices
                       WHERE id = $1""",
                    UUID(invoice_id),
                )
                return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"Failed to get invoice {invoice_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to retrieve invoice {invoice_id}: {e}",
                operation="get_invoice_by_id",
                original_exception=e,
            )

    async def list_invoices_for_org(
        self, org_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List invoices for an organization with pagination.

        Business Context:
        Powers the billing history UI where organization admins review past and
        outstanding invoices.  Results are paginated and ordered by creation date
        descending so the most recent invoice appears first.

        Technical Implementation:
        Uses LIMIT/OFFSET pagination.  For very large billing histories a cursor-based
        approach may be preferable, but LIMIT/OFFSET is sufficient for typical
        organization invoice volumes.

        Args:
            org_id: UUID string of the organization
            limit: Maximum number of invoices to return (default 50)
            offset: Number of invoices to skip (default 0)

        Returns:
            List of invoice dictionaries

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT id, organization_id, subscription_id, invoice_number,
                              amount_cents, currency, status, provider_invoice_id,
                              issued_at, due_at, paid_at, created_at, updated_at
                       FROM course_creator.invoices
                       WHERE organization_id = $1
                       ORDER BY created_at DESC
                       LIMIT $2 OFFSET $3""",
                    UUID(org_id),
                    limit,
                    offset,
                )
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to list invoices for org {org_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to list invoices for organization {org_id}: {e}",
                operation="list_invoices_for_org",
                original_exception=e,
            )

    async def update_invoice_status(
        self,
        invoice_id: str,
        status: str,
        paid_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Update the status of an invoice and optionally record the paid_at timestamp.

        Business Context:
        Invoice status transitions drive downstream workflows.  For example, marking
        an invoice as 'paid' triggers receipt generation and subscription renewal.
        Marking as 'void' cancels the billing obligation.

        Technical Implementation:
        Updates status and optionally paid_at.  Always refreshes updated_at.  Returns
        the full updated row.

        Args:
            invoice_id: UUID string of the invoice
            status: New status value (e.g. 'paid', 'void', 'overdue')
            paid_at: Optional timestamp when payment was received

        Returns:
            Updated invoice as a dictionary

        Raises:
            InvoiceNotFoundException: If the invoice does not exist
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(
                    """UPDATE course_creator.invoices
                       SET status = $2, paid_at = $3, updated_at = $4
                       WHERE id = $1
                       RETURNING id, organization_id, subscription_id, invoice_number,
                                 amount_cents, currency, status, provider_invoice_id,
                                 issued_at, due_at, paid_at, created_at, updated_at""",
                    UUID(invoice_id),
                    status,
                    paid_at,
                    datetime.utcnow(),
                )
                if result is None:
                    raise InvoiceNotFoundException(invoice_id)
                return dict(result)
        except InvoiceNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update invoice status {invoice_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to update invoice status for {invoice_id}: {e}",
                operation="update_invoice_status",
                original_exception=e,
            )

    # ================================================================
    # INVOICE LINE ITEMS
    # ================================================================

    async def create_line_item(self, item_data: Dict[str, Any]) -> str:
        """
        Create an invoice line item.

        Business Context:
        Line items break down the charges on an invoice into individual components
        (e.g. base plan fee, overage charges, add-on features).  Each line item
        carries a description, quantity, unit price, and computed total.

        Technical Implementation:
        Inserts into course_creator.invoice_line_items.  The invoice_id FK ensures
        referential integrity and ON DELETE CASCADE propagates invoice deletions.

        Args:
            item_data: Dictionary containing line item attributes:
                - invoice_id: UUID string of the parent invoice
                - description: Human-readable charge description
                - quantity: Number of units (default 1)
                - unit_price_cents: Price per unit in cents
                - amount_cents: Total line amount in cents

        Returns:
            Created line item ID as string

        Raises:
            PaymentValidationException: If the referenced invoice does not exist
            PaymentDatabaseException: On any other database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                item_id = await conn.fetchval(
                    """INSERT INTO course_creator.invoice_line_items (
                        invoice_id, description, quantity, unit_price_cents,
                        amount_cents, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id""",
                    UUID(item_data["invoice_id"]),
                    item_data.get("description", ""),
                    item_data.get("quantity", 1),
                    item_data.get("unit_price_cents", 0),
                    item_data.get("amount_cents", 0),
                    datetime.utcnow(),
                )
                return str(item_id)
        except asyncpg.ForeignKeyViolationError as e:
            raise PaymentValidationException(
                message=f"Referenced invoice does not exist: {e}",
                validation_errors={"invoice_id": item_data.get("invoice_id", "unknown")},
            )
        except Exception as e:
            self.logger.error(f"Failed to create invoice line item: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to create invoice line item: {e}",
                operation="create_line_item",
                original_exception=e,
            )

    async def get_line_items_for_invoice(self, invoice_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all line items for a given invoice.

        Business Context:
        Used when rendering an invoice detail view, generating a PDF receipt, or
        recalculating invoice totals after an adjustment.

        Technical Implementation:
        Fetches all rows matching the invoice_id FK, ordered by created_at ascending
        so items appear in the order they were added.

        Args:
            invoice_id: UUID string of the parent invoice

        Returns:
            List of line item dictionaries

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT id, invoice_id, description, quantity,
                              unit_price_cents, amount_cents, created_at
                       FROM course_creator.invoice_line_items
                       WHERE invoice_id = $1
                       ORDER BY created_at ASC""",
                    UUID(invoice_id),
                )
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get line items for invoice {invoice_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to retrieve line items for invoice {invoice_id}: {e}",
                operation="get_line_items_for_invoice",
                original_exception=e,
            )

    # ================================================================
    # TRANSACTIONS
    # ================================================================

    async def create_transaction(self, txn_data: Dict[str, Any]) -> str:
        """
        Create a transaction record representing an actual money movement.

        Business Context:
        Transactions capture real payment attempts and refunds.  Each transaction
        references the payment provider, the optional invoice it settles, and the
        payment method used.  The metadata JSONB column stores provider-specific
        response details for reconciliation and dispute resolution.

        Technical Implementation:
        Inserts into course_creator.transactions.  The metadata column is serialized
        from a Python dict via json.dumps.

        Args:
            txn_data: Dictionary containing transaction attributes:
                - organization_id: UUID string of the organization
                - invoice_id: Optional UUID string of the related invoice
                - amount_cents: Transaction amount in cents
                - currency: ISO 4217 currency code
                - status: Initial status (default 'pending')
                - provider_name: Provider handling the transaction
                - provider_transaction_id: External reference from the provider
                - payment_method_id: Optional UUID of the payment method used
                - refund_amount_cents: Refunded amount in cents (default 0)
                - failure_reason: Text explanation if the transaction failed
                - metadata: Dict of provider-specific response data

        Returns:
            Created transaction ID as string

        Raises:
            PaymentValidationException: If a FK constraint is violated
            PaymentDatabaseException: On any other database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                invoice_id = txn_data.get("invoice_id")
                payment_method_id = txn_data.get("payment_method_id")
                txn_id = await conn.fetchval(
                    """INSERT INTO course_creator.transactions (
                        organization_id, invoice_id, amount_cents, currency,
                        status, provider_name, provider_transaction_id,
                        payment_method_id, refund_amount_cents, failure_reason,
                        metadata, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    RETURNING id""",
                    UUID(txn_data["organization_id"]),
                    UUID(invoice_id) if invoice_id else None,
                    txn_data.get("amount_cents", 0),
                    txn_data.get("currency", "USD"),
                    txn_data.get("status", "pending"),
                    txn_data.get("provider_name", "null"),
                    txn_data.get("provider_transaction_id"),
                    UUID(payment_method_id) if payment_method_id else None,
                    txn_data.get("refund_amount_cents", 0),
                    txn_data.get("failure_reason"),
                    json.dumps(txn_data.get("metadata", {})),
                    datetime.utcnow(),
                    datetime.utcnow(),
                )
                return str(txn_id)
        except asyncpg.ForeignKeyViolationError as e:
            raise PaymentValidationException(
                message=f"Referenced entity does not exist: {e}",
                validation_errors={"detail": str(e)},
            )
        except Exception as e:
            self.logger.error(f"Failed to create transaction: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to create transaction: {e}",
                operation="create_transaction",
                original_exception=e,
            )

    async def get_transaction_by_id(self, txn_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a transaction by its unique identifier.

        Business Context:
        Used when displaying transaction details, checking payment status, processing
        refunds, or resolving disputes with the payment provider.

        Technical Implementation:
        Simple primary-key lookup on course_creator.transactions.

        Args:
            txn_id: UUID string of the transaction

        Returns:
            Dictionary of transaction attributes if found, None otherwise

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(
                    """SELECT id, organization_id, invoice_id, amount_cents, currency,
                              status, provider_name, provider_transaction_id,
                              payment_method_id, refund_amount_cents, failure_reason,
                              metadata, created_at, updated_at
                       FROM course_creator.transactions
                       WHERE id = $1""",
                    UUID(txn_id),
                )
                return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"Failed to get transaction {txn_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to retrieve transaction {txn_id}: {e}",
                operation="get_transaction_by_id",
                original_exception=e,
            )

    async def list_transactions_for_org(
        self, org_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List transactions for an organization with pagination.

        Business Context:
        Powers the transaction history UI where organization admins review past
        payments, refunds, and failed charges.  Results are paginated and ordered
        by creation date descending.

        Technical Implementation:
        Uses LIMIT/OFFSET pagination with an index on organization_id.

        Args:
            org_id: UUID string of the organization
            limit: Maximum number of transactions to return (default 50)
            offset: Number of transactions to skip (default 0)

        Returns:
            List of transaction dictionaries

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT id, organization_id, invoice_id, amount_cents, currency,
                              status, provider_name, provider_transaction_id,
                              payment_method_id, refund_amount_cents, failure_reason,
                              metadata, created_at, updated_at
                       FROM course_creator.transactions
                       WHERE organization_id = $1
                       ORDER BY created_at DESC
                       LIMIT $2 OFFSET $3""",
                    UUID(org_id),
                    limit,
                    offset,
                )
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to list transactions for org {org_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to list transactions for organization {org_id}: {e}",
                operation="list_transactions_for_org",
                original_exception=e,
            )

    async def update_transaction(self, txn_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update mutable attributes of an existing transaction.

        Business Context:
        Transaction updates occur when a provider webhook reports a status change
        (e.g. pending-to-succeeded, pending-to-failed), when a partial refund is
        processed, or when failure details are recorded.

        Technical Implementation:
        Dynamically builds a SET clause from the provided updates dictionary.
        The metadata column is re-serialized if present.  Only allowed columns
        are applied to prevent arbitrary writes.

        Args:
            txn_id: UUID string of the transaction to update
            updates: Dictionary of column names to new values

        Returns:
            Updated transaction as a dictionary

        Raises:
            PaymentNotFoundException: If the transaction does not exist
            PaymentDatabaseException: On database error
        """
        allowed_columns = {
            "status", "provider_transaction_id", "refund_amount_cents",
            "failure_reason", "metadata",
        }
        try:
            filtered = {k: v for k, v in updates.items() if k in allowed_columns}
            if not filtered:
                existing = await self.get_transaction_by_id(txn_id)
                if existing is None:
                    raise PaymentNotFoundException(txn_id)
                return existing

            set_clauses = []
            params: List[Any] = []
            idx = 1
            for col, val in filtered.items():
                idx += 1
                if col == "metadata":
                    set_clauses.append(f"{col} = ${idx}")
                    params.append(json.dumps(val))
                else:
                    set_clauses.append(f"{col} = ${idx}")
                    params.append(val)

            idx += 1
            set_clauses.append(f"updated_at = ${idx}")
            params.append(datetime.utcnow())

            query = f"""UPDATE course_creator.transactions
                        SET {', '.join(set_clauses)}
                        WHERE id = $1
                        RETURNING id, organization_id, invoice_id, amount_cents, currency,
                                  status, provider_name, provider_transaction_id,
                                  payment_method_id, refund_amount_cents, failure_reason,
                                  metadata, created_at, updated_at"""

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, UUID(txn_id), *params)
                if result is None:
                    raise PaymentNotFoundException(txn_id)
                return dict(result)
        except PaymentNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update transaction {txn_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to update transaction {txn_id}: {e}",
                operation="update_transaction",
                original_exception=e,
            )

    # ================================================================
    # PAYMENT METHODS
    # ================================================================

    async def create_payment_method(self, method_data: Dict[str, Any]) -> str:
        """
        Create a tokenized payment method for an organization.

        Business Context:
        Payment methods represent stored cards, bank accounts, or platform credits
        that an organization can use to settle invoices.  Sensitive card data is
        never stored directly; instead the provider returns an opaque token that
        is persisted in provider_token.

        Technical Implementation:
        Inserts into course_creator.payment_methods.  The label and last_four columns
        provide a safe display identifier (e.g. "Visa ending in 4242").

        Args:
            method_data: Dictionary containing payment method attributes:
                - organization_id: UUID string of the owning organization
                - method_type: Type of method (e.g. 'card', 'bank_account', 'platform_credit')
                - provider_name: Provider that tokenized the method
                - provider_token: Opaque token from the provider
                - label: Human-readable label
                - last_four: Last four digits of the instrument
                - expiry_month: Card expiry month (1-12)
                - expiry_year: Card expiry year (e.g. 2027)
                - is_default: Whether this is the default method
                - is_active: Whether this method is active

        Returns:
            Created payment method ID as string

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                method_id = await conn.fetchval(
                    """INSERT INTO course_creator.payment_methods (
                        organization_id, method_type, provider_name, provider_token,
                        label, last_four, expiry_month, expiry_year,
                        is_default, is_active, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING id""",
                    UUID(method_data["organization_id"]),
                    method_data.get("method_type", "platform_credit"),
                    method_data.get("provider_name", "null"),
                    method_data.get("provider_token"),
                    method_data.get("label"),
                    method_data.get("last_four"),
                    method_data.get("expiry_month"),
                    method_data.get("expiry_year"),
                    method_data.get("is_default", False),
                    method_data.get("is_active", True),
                    datetime.utcnow(),
                    datetime.utcnow(),
                )
                return str(method_id)
        except Exception as e:
            self.logger.error(f"Failed to create payment method: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to create payment method: {e}",
                operation="create_payment_method",
                original_exception=e,
            )

    async def get_payment_method_by_id(self, method_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a payment method by its unique identifier.

        Business Context:
        Used when initiating a charge against a specific payment method, displaying
        method details in the settings UI, or validating that a method is still
        active before processing a transaction.

        Technical Implementation:
        Simple primary-key lookup on course_creator.payment_methods.

        Args:
            method_id: UUID string of the payment method

        Returns:
            Dictionary of payment method attributes if found, None otherwise

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(
                    """SELECT id, organization_id, method_type, provider_name,
                              provider_token, label, last_four, expiry_month,
                              expiry_year, is_default, is_active, created_at, updated_at
                       FROM course_creator.payment_methods
                       WHERE id = $1""",
                    UUID(method_id),
                )
                return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"Failed to get payment method {method_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to retrieve payment method {method_id}: {e}",
                operation="get_payment_method_by_id",
                original_exception=e,
            )

    async def list_payment_methods_for_org(self, org_id: str) -> List[Dict[str, Any]]:
        """
        List active payment methods for an organization.

        Business Context:
        Powers the payment method selector in the checkout and settings UIs.  Only
        active methods are returned so that deactivated or expired methods do not
        appear as options.

        Technical Implementation:
        Filters on organization_id and is_active=true.  Orders by is_default DESC
        so the default method appears first, then by created_at DESC.

        Args:
            org_id: UUID string of the organization

        Returns:
            List of active payment method dictionaries

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT id, organization_id, method_type, provider_name,
                              provider_token, label, last_four, expiry_month,
                              expiry_year, is_default, is_active, created_at, updated_at
                       FROM course_creator.payment_methods
                       WHERE organization_id = $1 AND is_active = true
                       ORDER BY is_default DESC, created_at DESC""",
                    UUID(org_id),
                )
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to list payment methods for org {org_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to list payment methods for organization {org_id}: {e}",
                operation="list_payment_methods_for_org",
                original_exception=e,
            )

    async def set_default_payment_method(self, org_id: str, method_id: str) -> bool:
        """
        Set a payment method as the default for an organization.

        Business Context:
        Organizations designate one payment method as their default.  When an invoice
        is due the system charges the default method automatically.  This operation
        unsets the current default (if any) and promotes the specified method in a
        single atomic transaction to prevent race conditions.

        Technical Implementation:
        Executes two statements inside an explicit transaction:
        1. UPDATE all methods for the org to is_default=false
        2. UPDATE the target method to is_default=true
        Returns True if the target method was found and promoted.

        Args:
            org_id: UUID string of the organization
            method_id: UUID string of the payment method to set as default

        Returns:
            True if the method was successfully set as default, False if not found

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        """UPDATE course_creator.payment_methods
                           SET is_default = false, updated_at = $2
                           WHERE organization_id = $1 AND is_default = true""",
                        UUID(org_id),
                        datetime.utcnow(),
                    )
                    result = await conn.execute(
                        """UPDATE course_creator.payment_methods
                           SET is_default = true, updated_at = $3
                           WHERE id = $1 AND organization_id = $2 AND is_active = true""",
                        UUID(method_id),
                        UUID(org_id),
                        datetime.utcnow(),
                    )
                    return result == "UPDATE 1"
        except Exception as e:
            self.logger.error(f"Failed to set default payment method {method_id} for org {org_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to set default payment method {method_id} for organization {org_id}: {e}",
                operation="set_default_payment_method",
                original_exception=e,
            )

    async def deactivate_payment_method(self, method_id: str) -> bool:
        """
        Soft-delete a payment method by marking it inactive.

        Business Context:
        Payment methods are never hard-deleted because transactions reference them.
        Deactivating a method removes it from the active method list while preserving
        historical transaction records.  If the deactivated method was the default,
        the organization will need to select a new default before the next charge.

        Technical Implementation:
        Sets is_active=false and is_default=false, then refreshes updated_at.
        Returns True if the row was found and updated.

        Args:
            method_id: UUID string of the payment method to deactivate

        Returns:
            True if the method was deactivated, False if not found

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE course_creator.payment_methods
                       SET is_active = false, is_default = false, updated_at = $2
                       WHERE id = $1""",
                    UUID(method_id),
                    datetime.utcnow(),
                )
                return result == "UPDATE 1"
        except Exception as e:
            self.logger.error(f"Failed to deactivate payment method {method_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to deactivate payment method {method_id}: {e}",
                operation="deactivate_payment_method",
                original_exception=e,
            )

    # ================================================================
    # PAYMENT PROVIDERS
    # ================================================================

    async def get_provider_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a payment provider by its unique name.

        Business Context:
        Payment providers are registered configurations that define how the platform
        communicates with external payment processors (Stripe, Square, etc.) or with
        the built-in NullProvider for free plans.  This lookup is used during
        transaction processing to load provider configuration.

        Technical Implementation:
        Looks up by the name column (VARCHAR UNIQUE) on course_creator.payment_providers.

        Args:
            name: Provider name string (e.g. 'null', 'stripe', 'square')

        Returns:
            Dictionary of provider attributes if found, None otherwise

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(
                    """SELECT id, name, display_name, is_active, config,
                              created_at, updated_at
                       FROM course_creator.payment_providers
                       WHERE name = $1""",
                    name,
                )
                return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"Failed to get provider by name '{name}': {e}")
            raise PaymentDatabaseException(
                message=f"Failed to retrieve payment provider '{name}': {e}",
                operation="get_provider_by_name",
                original_exception=e,
            )

    async def list_active_providers(self) -> List[Dict[str, Any]]:
        """
        List all active payment providers.

        Business Context:
        Powers the provider selection UI in platform administration and determines
        which payment integrations are available when creating new subscriptions
        or processing transactions.

        Technical Implementation:
        Filters on is_active=true and orders by name for deterministic output.

        Returns:
            List of active provider dictionaries

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT id, name, display_name, is_active, config,
                              created_at, updated_at
                       FROM course_creator.payment_providers
                       WHERE is_active = true
                       ORDER BY name ASC""",
                )
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to list active providers: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to list active payment providers: {e}",
                operation="list_active_providers",
                original_exception=e,
            )

    # ================================================================
    # PAYMENT AUDIT LOG
    # ================================================================

    async def create_audit_entry(self, entry_data: Dict[str, Any]) -> str:
        """
        Create an immutable audit log entry for a payment mutation.

        Business Context:
        Every significant mutation in the payment system (subscription created,
        invoice paid, transaction refunded, payment method added, etc.) is recorded
        in the audit log.  This provides a tamper-evident trail for compliance,
        dispute resolution, and forensic analysis.  Audit entries are append-only
        and never updated or deleted.

        Technical Implementation:
        Inserts into course_creator.payment_audit_log.  The old_values and new_values
        columns store JSONB snapshots of the entity before and after the mutation.
        The metadata column holds additional context such as IP address or request ID.

        Args:
            entry_data: Dictionary containing audit entry attributes:
                - entity_type: Type of entity mutated (e.g. 'subscription', 'invoice')
                - entity_id: UUID string of the mutated entity
                - action: Description of the action (e.g. 'created', 'updated', 'cancelled')
                - actor_id: Optional UUID string of the user who triggered the action
                - organization_id: Optional UUID string of the organization context
                - old_values: Optional dict of entity state before the mutation
                - new_values: Optional dict of entity state after the mutation
                - metadata: Optional dict of additional context

        Returns:
            Created audit entry ID as string

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                actor_id = entry_data.get("actor_id")
                organization_id = entry_data.get("organization_id")
                old_values = entry_data.get("old_values")
                new_values = entry_data.get("new_values")

                entry_id = await conn.fetchval(
                    """INSERT INTO course_creator.payment_audit_log (
                        entity_type, entity_id, action, actor_id,
                        organization_id, old_values, new_values,
                        metadata, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id""",
                    entry_data["entity_type"],
                    UUID(entry_data["entity_id"]),
                    entry_data["action"],
                    UUID(actor_id) if actor_id else None,
                    UUID(organization_id) if organization_id else None,
                    json.dumps(old_values) if old_values else None,
                    json.dumps(new_values) if new_values else None,
                    json.dumps(entry_data.get("metadata", {})),
                    datetime.utcnow(),
                )
                return str(entry_id)
        except Exception as e:
            self.logger.error(f"Failed to create audit entry: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to create payment audit entry: {e}",
                operation="create_audit_entry",
                original_exception=e,
            )

    async def get_audit_log_for_entity(
        self, entity_type: str, entity_id: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the audit trail for a specific entity.

        Business Context:
        Enables detailed investigation of all mutations that have occurred on a
        particular subscription, invoice, transaction, or payment method.  Used by
        support staff and administrators when investigating billing issues or disputes.

        Technical Implementation:
        Filters on entity_type and entity_id using the composite index
        idx_payment_audit_entity.  Results are ordered by created_at ascending to
        show the chronological history of the entity.

        Args:
            entity_type: Type of the entity (e.g. 'subscription', 'invoice', 'transaction')
            entity_id: UUID string of the entity

        Returns:
            List of audit entry dictionaries in chronological order

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT id, entity_type, entity_id, action, actor_id,
                              organization_id, old_values, new_values,
                              metadata, created_at
                       FROM course_creator.payment_audit_log
                       WHERE entity_type = $1 AND entity_id = $2
                       ORDER BY created_at ASC""",
                    entity_type,
                    UUID(entity_id),
                )
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(
                f"Failed to get audit log for {entity_type} {entity_id}: {e}"
            )
            raise PaymentDatabaseException(
                message=f"Failed to retrieve audit log for {entity_type} {entity_id}: {e}",
                operation="get_audit_log_for_entity",
                original_exception=e,
            )

    async def get_audit_log_for_org(
        self, org_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent audit log entries for an organization.

        Business Context:
        Provides a consolidated view of all payment-related activity within an
        organization.  Used in the organization admin dashboard to monitor billing
        activity, detect anomalies, and satisfy compliance audit requirements.

        Technical Implementation:
        Filters on organization_id using the index idx_payment_audit_org.  Results
        are ordered by created_at descending so the most recent events appear first.
        The limit parameter caps the result set to prevent excessive memory usage.

        Args:
            org_id: UUID string of the organization
            limit: Maximum number of entries to return (default 100)

        Returns:
            List of audit entry dictionaries, most recent first

        Raises:
            PaymentDatabaseException: On database error
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT id, entity_type, entity_id, action, actor_id,
                              organization_id, old_values, new_values,
                              metadata, created_at
                       FROM course_creator.payment_audit_log
                       WHERE organization_id = $1
                       ORDER BY created_at DESC
                       LIMIT $2""",
                    UUID(org_id),
                    limit,
                )
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get audit log for org {org_id}: {e}")
            raise PaymentDatabaseException(
                message=f"Failed to retrieve audit log for organization {org_id}: {e}",
                operation="get_audit_log_for_org",
                original_exception=e,
            )
