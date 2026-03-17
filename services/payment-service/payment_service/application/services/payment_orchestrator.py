"""
Payment Orchestrator — routes payment operations to the correct provider.

Business Context:
The orchestrator is the central coordination point for all payment operations.
It resolves which provider to use for a given organization (based on their
subscription), delegates the operation to the provider, and persists results
via the DAO. This ensures that the API layer never needs to know about
specific providers.

Technical Rationale:
Uses the Strategy Pattern — the orchestrator holds a reference to the Container
to lazily resolve provider instances. Provider failures are caught and recorded
in the transaction table with failure details.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

from payment_service.data_access.payment_dao import PaymentDAO
from payment_service.exceptions import (
    PaymentFailedException,
    PaymentNotFoundException,
    RefundException,
    PaymentDatabaseException,
)

logger = logging.getLogger(__name__)


class PaymentOrchestrator:
    """
    Coordinates payment operations across providers and persistence.

    All payment mutations flow through here:
    1. Resolve the provider for the organization
    2. Delegate to the provider
    3. Record the result in the database
    4. Write audit log entry
    """

    def __init__(self, dao: PaymentDAO, container):
        self._dao = dao
        self._container = container

    async def _resolve_provider_for_org(self, org_id: str):
        """
        Determine which payment provider to use for an organization.
        Looks at the org's active subscription to find the provider name.
        Falls back to 'null' if no subscription exists.
        """
        subscription = await self._dao.get_active_subscription_for_org(org_id)
        provider_name = subscription.get("provider_name", "null") if subscription else "null"
        return self._container.get_provider(provider_name)

    async def create_payment(
        self,
        organization_id: str,
        amount_cents: int,
        currency: str = "USD",
        invoice_id: Optional[str] = None,
        payment_method_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        actor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a one-time payment for an organization.

        Steps:
        1. Create a pending transaction record
        2. Resolve the provider
        3. Call provider.create_checkout_session
        4. Update transaction with result
        5. Log audit entry
        """
        txn_id = str(uuid4())
        txn_data = {
            "id": txn_id,
            "organization_id": organization_id,
            "invoice_id": invoice_id,
            "amount_cents": amount_cents,
            "currency": currency,
            "status": "pending",
            "provider_name": "null",
            "payment_method_id": payment_method_id,
            "metadata": metadata or {},
        }

        await self._dao.create_transaction(txn_data)

        provider = await self._resolve_provider_for_org(organization_id)
        provider_name = await provider.get_provider_name()
        txn_data["provider_name"] = provider_name

        result = await provider.create_checkout_session(
            amount_cents=amount_cents,
            currency=currency,
            metadata={"transaction_id": txn_id, **(metadata or {})},
        )

        if result.success:
            updates = {
                "status": "completed",
                "provider_name": provider_name,
                "provider_transaction_id": result.provider_id,
            }
            await self._dao.update_transaction(txn_id, updates)

            await self._dao.create_audit_entry({
                "entity_type": "transaction",
                "entity_id": txn_id,
                "action": "payment_completed",
                "actor_id": actor_id,
                "organization_id": organization_id,
                "new_values": {"amount_cents": amount_cents, "provider": provider_name},
            })

            logger.info(f"Payment completed: txn={txn_id} org={organization_id} amount={amount_cents}")
        else:
            updates = {
                "status": "failed",
                "provider_name": provider_name,
                "failure_reason": result.error_message,
            }
            await self._dao.update_transaction(txn_id, updates)

            await self._dao.create_audit_entry({
                "entity_type": "transaction",
                "entity_id": txn_id,
                "action": "payment_failed",
                "actor_id": actor_id,
                "organization_id": organization_id,
                "new_values": {"error": result.error_message},
            })

            raise PaymentFailedException(
                reason=result.error_message or "Provider declined the payment",
                provider_name=provider_name,
            )

        return await self._dao.get_transaction_by_id(txn_id)

    async def refund_payment(
        self,
        transaction_id: str,
        amount_cents: Optional[int] = None,
        actor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Refund a completed payment (full or partial).

        If amount_cents is None, performs a full refund.
        """
        txn = await self._dao.get_transaction_by_id(transaction_id)
        if not txn:
            raise PaymentNotFoundException(transaction_id)

        if txn["status"] not in ("completed", "partially_refunded"):
            raise RefundException(
                transaction_id,
                f"Cannot refund transaction in status '{txn['status']}'",
            )

        refund_amount = amount_cents if amount_cents is not None else txn["amount_cents"]
        max_refundable = txn["amount_cents"] - txn.get("refund_amount_cents", 0)
        if refund_amount > max_refundable:
            raise RefundException(
                transaction_id,
                f"Refund amount ({refund_amount}) exceeds refundable balance ({max_refundable})",
            )

        provider = self._container.get_provider(txn["provider_name"])
        result = await provider.refund_payment(
            provider_payment_id=txn.get("provider_transaction_id", ""),
            amount_cents=refund_amount,
        )

        if not result.success:
            raise RefundException(transaction_id, result.error_message or "Provider refused refund")

        new_refund_total = txn.get("refund_amount_cents", 0) + refund_amount
        new_status = "refunded" if new_refund_total >= txn["amount_cents"] else "partially_refunded"
        updates = {
            "status": new_status,
            "refund_amount_cents": new_refund_total,
        }
        await self._dao.update_transaction(transaction_id, updates)

        await self._dao.create_audit_entry({
            "entity_type": "transaction",
            "entity_id": transaction_id,
            "action": "refund_processed",
            "actor_id": actor_id,
            "organization_id": str(txn["organization_id"]),
            "old_values": {"refund_amount_cents": txn.get("refund_amount_cents", 0)},
            "new_values": {"refund_amount_cents": new_refund_total, "status": new_status},
        })

        logger.info(f"Refund processed: txn={transaction_id} amount={refund_amount} status={new_status}")
        return await self._dao.get_transaction_by_id(transaction_id)

    async def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Retrieve a single transaction."""
        txn = await self._dao.get_transaction_by_id(transaction_id)
        if not txn:
            raise PaymentNotFoundException(transaction_id)
        return txn

    async def list_transactions(
        self, organization_id: str, limit: int = 50, offset: int = 0
    ) -> list:
        """List transactions for an organization."""
        return await self._dao.list_transactions_for_org(organization_id, limit, offset)
