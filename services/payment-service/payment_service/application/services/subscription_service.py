"""
Subscription Service — manages organization subscription lifecycle.

Business Context:
Handles creating, upgrading, downgrading, cancelling, and resuming subscriptions.
Each organization has at most one active subscription. When switching plans, the
old subscription is cancelled and a new one created. Trial periods are managed here.

Technical Rationale:
Coordinates between the DAO (persistence), the provider (external operations), and
the container (provider resolution). All mutations are audit-logged.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import uuid4

from payment_service.data_access.payment_dao import PaymentDAO
from payment_service.exceptions import (
    SubscriptionNotFoundException,
    SubscriptionAlreadyExistsException,
    SubscriptionStateException,
    PlanNotFoundException,
    PaymentProviderException,
)

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Manages the full subscription lifecycle for organizations.

    An organization can have at most one active subscription (enforced by
    a partial unique index on organization_id WHERE status is active-like).
    """

    def __init__(self, dao: PaymentDAO, container):
        self._dao = dao
        self._container = container

    async def create_subscription(
        self,
        organization_id: str,
        plan_id: str,
        actor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new subscription for an organization.

        If the plan has trial_days > 0, the subscription starts in TRIAL status.
        Otherwise it starts as ACTIVE. Uses NullProvider by default until a
        real provider is configured.
        """
        existing = await self._dao.get_active_subscription_for_org(organization_id)
        if existing:
            raise SubscriptionAlreadyExistsException(organization_id)

        plan = await self._dao.get_plan_by_id(plan_id)
        if not plan:
            raise PlanNotFoundException(plan_id)

        provider_name = plan.get("provider_name", "null")
        provider = self._container.get_provider(provider_name)

        now = datetime.utcnow()
        sub_id = str(uuid4())
        trial_end = None
        status = "active"

        if plan.get("trial_days", 0) > 0:
            trial_end = now + timedelta(days=plan["trial_days"])
            status = "trial"

        result = await provider.create_subscription(
            plan_external_id=str(plan["id"]),
            customer_id=organization_id,
            metadata={"subscription_id": sub_id, "plan_name": plan["name"]},
        )

        sub_data = {
            "id": sub_id,
            "organization_id": organization_id,
            "plan_id": plan_id,
            "status": status,
            "provider_name": provider_name,
            "provider_subscription_id": result.provider_id if result.success else None,
            "current_period_start": now,
            "current_period_end": now + timedelta(days=30),
            "trial_end": trial_end,
        }
        await self._dao.create_subscription(sub_data)

        await self._dao.create_audit_entry({
            "entity_type": "subscription",
            "entity_id": sub_id,
            "action": "created",
            "actor_id": actor_id,
            "organization_id": organization_id,
            "new_values": {"plan": plan["name"], "status": status, "provider": provider_name},
        })

        logger.info(f"Subscription created: sub={sub_id} org={organization_id} plan={plan['name']}")
        return await self._dao.get_subscription_by_id(sub_id)

    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Retrieve a subscription by ID."""
        sub = await self._dao.get_subscription_by_id(subscription_id)
        if not sub:
            raise SubscriptionNotFoundException(subscription_id)
        return sub

    async def get_org_subscription(self, organization_id: str) -> Optional[Dict[str, Any]]:
        """Get the current active subscription for an organization (or None)."""
        return await self._dao.get_active_subscription_for_org(organization_id)

    async def upgrade_subscription(
        self,
        subscription_id: str,
        new_plan_id: str,
        actor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Change subscription to a different plan (upgrade or downgrade).

        Cancels the old provider subscription and creates a new one for the new plan.
        """
        sub = await self._dao.get_subscription_by_id(subscription_id)
        if not sub:
            raise SubscriptionNotFoundException(subscription_id)

        if sub["status"] not in ("active", "trial", "past_due"):
            raise SubscriptionStateException(subscription_id, sub["status"], "upgrade")

        new_plan = await self._dao.get_plan_by_id(new_plan_id)
        if not new_plan:
            raise PlanNotFoundException(new_plan_id)

        old_plan_id = str(sub["plan_id"])
        provider_name = sub.get("provider_name", "null")
        provider = self._container.get_provider(provider_name)

        if sub.get("provider_subscription_id"):
            await provider.cancel_subscription(sub["provider_subscription_id"])

        result = await provider.create_subscription(
            plan_external_id=str(new_plan["id"]),
            customer_id=str(sub["organization_id"]),
            metadata={"subscription_id": subscription_id, "plan_name": new_plan["name"]},
        )

        now = datetime.utcnow()
        updates = {
            "plan_id": new_plan_id,
            "status": "active",
            "provider_subscription_id": result.provider_id if result.success else sub.get("provider_subscription_id"),
            "current_period_start": now,
            "current_period_end": now + timedelta(days=30),
        }
        await self._dao.update_subscription(subscription_id, updates)

        await self._dao.create_audit_entry({
            "entity_type": "subscription",
            "entity_id": subscription_id,
            "action": "upgraded",
            "actor_id": actor_id,
            "organization_id": str(sub["organization_id"]),
            "old_values": {"plan_id": old_plan_id},
            "new_values": {"plan_id": new_plan_id, "plan_name": new_plan["name"]},
        })

        logger.info(f"Subscription upgraded: sub={subscription_id} new_plan={new_plan['name']}")
        return await self._dao.get_subscription_by_id(subscription_id)

    async def cancel_subscription(
        self,
        subscription_id: str,
        reason: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Cancel an active subscription."""
        sub = await self._dao.get_subscription_by_id(subscription_id)
        if not sub:
            raise SubscriptionNotFoundException(subscription_id)

        if sub["status"] in ("cancelled", "expired"):
            raise SubscriptionStateException(subscription_id, sub["status"], "cancel")

        provider_name = sub.get("provider_name", "null")
        provider = self._container.get_provider(provider_name)

        if sub.get("provider_subscription_id"):
            await provider.cancel_subscription(sub["provider_subscription_id"])

        now = datetime.utcnow()
        updates = {
            "status": "cancelled",
            "cancelled_at": now,
            "cancel_reason": reason,
        }
        await self._dao.update_subscription(subscription_id, updates)

        await self._dao.create_audit_entry({
            "entity_type": "subscription",
            "entity_id": subscription_id,
            "action": "cancelled",
            "actor_id": actor_id,
            "organization_id": str(sub["organization_id"]),
            "new_values": {"reason": reason, "cancelled_at": now.isoformat()},
        })

        logger.info(f"Subscription cancelled: sub={subscription_id} reason={reason}")
        return await self._dao.get_subscription_by_id(subscription_id)

    async def list_subscriptions(self, organization_id: str) -> list:
        """List all subscriptions (including historical) for an organization."""
        return await self._dao.list_subscriptions_for_org(organization_id)
