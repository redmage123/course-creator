"""
Billing Service — organization billing summaries and account status.

Business Context:
Provides read-oriented views of an organization's billing state: current plan,
subscription status, upcoming invoice, payment history, and stored payment methods.
This powers the org admin dashboard's billing/account status section.

Technical Rationale:
Aggregates data from multiple DAO queries into a single summary response.
No mutations happen here — this is purely a query service.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from payment_service.data_access.payment_dao import PaymentDAO

logger = logging.getLogger(__name__)


class BillingService:
    """Read-only billing summary and account status queries."""

    def __init__(self, dao: PaymentDAO):
        self._dao = dao

    async def get_billing_summary(self, organization_id: str) -> Dict[str, Any]:
        """
        Build a comprehensive billing summary for an organization.

        Returns current plan details, subscription status, recent invoices,
        recent payments, stored payment methods, and account health indicators.
        This is the primary data source for the org admin billing dashboard.
        """
        subscription = await self._dao.get_active_subscription_for_org(organization_id)

        plan = None
        if subscription:
            plan = await self._dao.get_plan_by_id(str(subscription["plan_id"]))

        recent_invoices = await self._dao.list_invoices_for_org(organization_id, limit=5)
        recent_payments = await self._dao.list_transactions_for_org(organization_id, limit=5)
        payment_methods = await self._dao.list_payment_methods_for_org(organization_id)

        has_overdue = any(inv["status"] == "overdue" for inv in recent_invoices)
        has_failed_payment = any(txn["status"] == "failed" for txn in recent_payments)

        account_status = "good"
        if subscription and subscription["status"] == "past_due":
            account_status = "past_due"
        elif has_overdue:
            account_status = "overdue"
        elif has_failed_payment:
            account_status = "attention"
        elif not subscription:
            account_status = "no_subscription"

        return {
            "organization_id": organization_id,
            "account_status": account_status,
            "current_plan": {
                "id": str(plan["id"]) if plan else None,
                "name": plan["name"] if plan else "No Plan",
                "price_cents": plan["price_cents"] if plan else 0,
                "currency": plan.get("currency", "USD") if plan else "USD",
                "billing_interval": plan.get("billing_interval", "monthly") if plan else None,
                "features": plan.get("features", {}) if plan else {},
            } if plan else None,
            "subscription": {
                "id": str(subscription["id"]),
                "status": subscription["status"],
                "current_period_start": subscription.get("current_period_start"),
                "current_period_end": subscription.get("current_period_end"),
                "trial_end": subscription.get("trial_end"),
                "cancelled_at": subscription.get("cancelled_at"),
            } if subscription else None,
            "recent_invoices": [
                {
                    "id": str(inv["id"]),
                    "invoice_number": inv.get("invoice_number"),
                    "amount_cents": inv["amount_cents"],
                    "currency": inv.get("currency", "USD"),
                    "status": inv["status"],
                    "issued_at": inv.get("issued_at"),
                    "paid_at": inv.get("paid_at"),
                }
                for inv in recent_invoices
            ],
            "recent_payments": [
                {
                    "id": str(txn["id"]),
                    "amount_cents": txn["amount_cents"],
                    "currency": txn.get("currency", "USD"),
                    "status": txn["status"],
                    "provider_name": txn.get("provider_name"),
                    "created_at": txn.get("created_at"),
                }
                for txn in recent_payments
            ],
            "payment_methods": [
                {
                    "id": str(pm["id"]),
                    "type": pm["method_type"],
                    "last_four": pm.get("last_four"),
                    "expiry_month": pm.get("expiry_month"),
                    "expiry_year": pm.get("expiry_year"),
                    "is_default": pm.get("is_default", False),
                    "label": pm.get("label"),
                }
                for pm in payment_methods
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def get_payment_history(
        self, organization_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Full payment history for an organization."""
        return await self._dao.list_transactions_for_org(organization_id, limit, offset)

    async def get_available_plans(self) -> List[Dict[str, Any]]:
        """List all active subscription plans for display."""
        plans = await self._dao.list_active_plans()
        return [
            {
                "id": str(p["id"]),
                "name": p["name"],
                "description": p.get("description", ""),
                "price_cents": p["price_cents"],
                "currency": p.get("currency", "USD"),
                "billing_interval": p.get("billing_interval", "monthly"),
                "features": p.get("features", {}),
                "trial_days": p.get("trial_days", 0),
            }
            for p in plans
        ]
