"""
Null Payment Provider Implementation

Business Context:
The NullProvider is a concrete implementation of the PaymentProvider ABC that
always succeeds and generates fake identifiers. It serves two critical roles:

1. Free/Trial Plans — Organizations on free tiers still flow through the same
   payment orchestration pipeline. The NullProvider handles these operations
   without hitting any external API, ensuring consistent domain event emission
   and audit trail generation regardless of whether money is involved.

2. Development & Testing — Provides a fully functional payment provider for
   local development, integration tests, and staging environments without
   requiring real payment gateway credentials.

Technical Rationale:
Implements the Null Object Pattern within the Strategy Pattern. Every method
logs the operation for audit visibility and returns a successful ProviderResult
with a deterministic ID format (null_xxx_{hex}) that is easily identifiable
in logs and database records.
"""

import logging
from typing import Dict, Any, Optional
from uuid import uuid4

from payment_service.infrastructure.providers.base import (
    PaymentProvider,
    ProviderResult,
    WebhookEvent,
)

logger = logging.getLogger(__name__)


class NullProvider(PaymentProvider):
    """
    Payment provider that always succeeds without contacting any external service.

    Used for free/trial plans and development environments. All operations
    are logged for audit trail purposes and return predictable, identifiable
    provider IDs with the 'null_' prefix.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the NullProvider.

        Args:
            config: Optional configuration dictionary. Accepted but not required
                    since the NullProvider has no external dependencies to configure.
        """
        self._config = config or {}
        logger.info("NullProvider initialized (no external payment gateway)")

    def _generate_id(self, prefix: str) -> str:
        """
        Generate a unique identifier with a recognizable null-provider prefix.

        Args:
            prefix: Operation-specific prefix (e.g., 'pay', 'sub', 'ref').

        Returns:
            String identifier in the format 'null_{prefix}_{12-char-hex}'.
        """
        return f"null_{prefix}_{uuid4().hex[:12]}"

    async def get_provider_name(self) -> str:
        """Return the registered name of this provider."""
        return "null"

    async def create_checkout_session(
        self,
        amount_cents: int,
        currency: str,
        metadata: Dict[str, Any]
    ) -> ProviderResult:
        """
        Create a simulated checkout session.

        Always succeeds immediately — no redirect or client secret is needed
        because there is no actual payment to collect.

        Args:
            amount_cents: Payment amount in smallest currency unit.
            currency: ISO 4217 currency code.
            metadata: Pass-through metadata from the caller.

        Returns:
            Successful ProviderResult with a generated session ID.
        """
        session_id = self._generate_id("pay")
        logger.info(
            "NullProvider.create_checkout_session: amount_cents=%d currency=%s session_id=%s metadata=%s",
            amount_cents,
            currency,
            session_id,
            metadata,
        )
        return ProviderResult(
            success=True,
            provider_id=session_id,
            provider_name="null",
            data={
                "amount_cents": amount_cents,
                "currency": currency,
                "metadata": metadata,
                "status": "completed",
            },
        )

    async def capture_payment(self, provider_payment_id: str) -> ProviderResult:
        """
        Simulate payment capture.

        The NullProvider considers all payments immediately captured, so this
        is effectively a no-op that confirms success.

        Args:
            provider_payment_id: The identifier returned from create_checkout_session.

        Returns:
            Successful ProviderResult confirming capture.
        """
        logger.info(
            "NullProvider.capture_payment: provider_payment_id=%s",
            provider_payment_id,
        )
        return ProviderResult(
            success=True,
            provider_id=provider_payment_id,
            provider_name="null",
            data={"status": "captured", "original_payment_id": provider_payment_id},
        )

    async def refund_payment(
        self,
        provider_payment_id: str,
        amount_cents: Optional[int] = None
    ) -> ProviderResult:
        """
        Simulate a refund operation.

        Generates a new refund ID linked to the original payment. Supports
        both full refunds (amount_cents=None) and partial refunds.

        Args:
            provider_payment_id: The identifier of the original payment.
            amount_cents: Amount to refund, or None for a full refund.

        Returns:
            Successful ProviderResult with a generated refund ID.
        """
        refund_id = self._generate_id("ref")
        refund_type = "full" if amount_cents is None else "partial"
        logger.info(
            "NullProvider.refund_payment: provider_payment_id=%s refund_id=%s type=%s amount_cents=%s",
            provider_payment_id,
            refund_id,
            refund_type,
            amount_cents,
        )
        return ProviderResult(
            success=True,
            provider_id=refund_id,
            provider_name="null",
            data={
                "original_payment_id": provider_payment_id,
                "refund_type": refund_type,
                "amount_cents": amount_cents,
                "status": "refunded",
            },
        )

    async def create_subscription(
        self,
        plan_external_id: str,
        customer_id: str,
        metadata: Dict[str, Any]
    ) -> ProviderResult:
        """
        Simulate subscription creation.

        Immediately creates an active subscription without any billing cycle
        setup, since no actual recurring charges will occur.

        Args:
            plan_external_id: The plan identifier (used for reference only).
            customer_id: The customer identifier (used for reference only).
            metadata: Pass-through metadata from the caller.

        Returns:
            Successful ProviderResult with a generated subscription ID.
        """
        subscription_id = self._generate_id("sub")
        logger.info(
            "NullProvider.create_subscription: plan=%s customer=%s subscription_id=%s metadata=%s",
            plan_external_id,
            customer_id,
            subscription_id,
            metadata,
        )
        return ProviderResult(
            success=True,
            provider_id=subscription_id,
            provider_name="null",
            data={
                "plan_external_id": plan_external_id,
                "customer_id": customer_id,
                "metadata": metadata,
                "status": "active",
            },
        )

    async def cancel_subscription(self, provider_subscription_id: str) -> ProviderResult:
        """
        Simulate subscription cancellation.

        Marks the subscription as cancelled immediately.

        Args:
            provider_subscription_id: The identifier of the subscription to cancel.

        Returns:
            Successful ProviderResult confirming cancellation.
        """
        logger.info(
            "NullProvider.cancel_subscription: provider_subscription_id=%s",
            provider_subscription_id,
        )
        return ProviderResult(
            success=True,
            provider_id=provider_subscription_id,
            provider_name="null",
            data={
                "status": "cancelled",
                "original_subscription_id": provider_subscription_id,
            },
        )

    async def update_subscription(
        self,
        provider_subscription_id: str,
        new_plan_external_id: str
    ) -> ProviderResult:
        """
        Simulate a subscription plan change (upgrade/downgrade).

        Updates the plan reference immediately without proration calculations.

        Args:
            provider_subscription_id: The identifier of the subscription to update.
            new_plan_external_id: The identifier of the new plan.

        Returns:
            Successful ProviderResult confirming the plan change.
        """
        logger.info(
            "NullProvider.update_subscription: provider_subscription_id=%s new_plan=%s",
            provider_subscription_id,
            new_plan_external_id,
        )
        return ProviderResult(
            success=True,
            provider_id=provider_subscription_id,
            provider_name="null",
            data={
                "status": "active",
                "new_plan_external_id": new_plan_external_id,
                "original_subscription_id": provider_subscription_id,
            },
        )

    async def tokenize_payment_method(self, raw_data: Dict[str, Any]) -> ProviderResult:
        """
        Simulate payment method tokenization.

        Generates a token ID without storing any sensitive data, since the
        NullProvider has no vault or token store.

        Args:
            raw_data: Payment method data (ignored by NullProvider).

        Returns:
            Successful ProviderResult with a generated token ID.
        """
        token_id = self._generate_id("tok")
        logger.info(
            "NullProvider.tokenize_payment_method: token_id=%s data_keys=%s",
            token_id,
            list(raw_data.keys()),
        )
        return ProviderResult(
            success=True,
            provider_id=token_id,
            provider_name="null",
            data={"status": "tokenized", "token_id": token_id},
        )

    async def delete_payment_method(self, provider_token: str) -> ProviderResult:
        """
        Simulate payment method deletion.

        Confirms deletion immediately since there is no actual stored method.

        Args:
            provider_token: The token/ID of the payment method to remove.

        Returns:
            Successful ProviderResult confirming deletion.
        """
        logger.info(
            "NullProvider.delete_payment_method: provider_token=%s",
            provider_token,
        )
        return ProviderResult(
            success=True,
            provider_id=provider_token,
            provider_name="null",
            data={"status": "deleted", "deleted_token": provider_token},
        )

    async def handle_webhook(self, headers: Dict[str, str], body: bytes) -> WebhookEvent:
        """
        Handle an incoming webhook for the NullProvider.

        Since no external service sends webhooks to the NullProvider, this
        returns a no-op event. This method exists to satisfy the ABC contract
        and can be useful in testing scenarios where webhook processing
        pipelines need a provider that always returns a valid event.

        Args:
            headers: HTTP headers from the webhook request (ignored).
            body: Raw request body bytes (ignored).

        Returns:
            WebhookEvent with event_type='null.no_op' indicating no action needed.
        """
        logger.info(
            "NullProvider.handle_webhook: received webhook (no-op), body_length=%d",
            len(body),
        )
        return WebhookEvent(
            event_type="null.no_op",
            provider_name="null",
            provider_event_id=self._generate_id("evt"),
            entity_type=None,
            entity_id=None,
            data={"message": "NullProvider webhook — no action taken"},
        )
