"""
Stripe Payment Provider Implementation

Business Context:
Integrates with Stripe's API for real payment processing — checkout sessions,
subscriptions, refunds, and webhook handling. Used by organizations that have
configured Stripe as their payment provider.

Technical Rationale:
Uses the stripe Python SDK for all API interactions. Webhook signature
verification ensures that incoming events are authentic. All operations
return the standardized ProviderResult/WebhookEvent types so the orchestrator
remains provider-agnostic.
"""

import logging
from typing import Dict, Any, Optional

import stripe
from stripe import StripeError, SignatureVerificationError

from payment_service.infrastructure.providers.base import (
    PaymentProvider,
    ProviderResult,
    WebhookEvent,
)

logger = logging.getLogger(__name__)


class StripeProvider(PaymentProvider):
    """
    Stripe payment provider using the stripe Python SDK.

    Expects config with:
        secret_key: Stripe secret key (sk_test_... or sk_live_...)
        publishable_key: Stripe publishable key (pk_test_... or pk_live_...)
        webhook_secret: Stripe webhook endpoint signing secret (whsec_...)
    """

    def __init__(self, config: Dict[str, Any]):
        self._config = config or {}
        self._secret_key = self._config.get("secret_key", "")
        self._publishable_key = self._config.get("publishable_key", "")
        self._webhook_secret = self._config.get("webhook_secret", "")

        if not self._secret_key:
            logger.warning("StripeProvider initialized without secret_key — API calls will fail")

        stripe.api_key = self._secret_key
        logger.info("StripeProvider initialized (test=%s)", self._secret_key.startswith("sk_test_"))

    async def get_provider_name(self) -> str:
        return "stripe"

    async def create_checkout_session(
        self,
        amount_cents: int,
        currency: str,
        metadata: Dict[str, Any],
    ) -> ProviderResult:
        """Create a Stripe Checkout Session for one-time payment."""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": currency,
                        "unit_amount": amount_cents,
                        "product_data": {
                            "name": metadata.get("description", "Payment"),
                        },
                    },
                    "quantity": 1,
                }],
                mode="payment",
                metadata=_sanitize_metadata(metadata),
                success_url=metadata.get("success_url", "https://courses.techuni.ai/payment/success"),
                cancel_url=metadata.get("cancel_url", "https://courses.techuni.ai/payment/cancel"),
            )
            logger.info("Stripe checkout session created: %s", session.id)
            return ProviderResult(
                success=True,
                provider_id=session.id,
                provider_name="stripe",
                data={
                    "checkout_url": session.url,
                    "session_id": session.id,
                    "publishable_key": self._publishable_key,
                    "status": session.status,
                },
                raw_response=dict(session),
            )
        except StripeError as e:
            logger.error("Stripe create_checkout_session failed: %s", e.user_message or str(e))
            return ProviderResult(
                success=False,
                provider_name="stripe",
                error_message=e.user_message or str(e),
                error_code=e.code,
            )

    async def capture_payment(self, provider_payment_id: str) -> ProviderResult:
        """Capture a previously authorized payment intent."""
        try:
            intent = stripe.PaymentIntent.capture(provider_payment_id)
            logger.info("Stripe payment captured: %s", intent.id)
            return ProviderResult(
                success=True,
                provider_id=intent.id,
                provider_name="stripe",
                data={"status": intent.status},
                raw_response=dict(intent),
            )
        except StripeError as e:
            logger.error("Stripe capture_payment failed: %s", e.user_message or str(e))
            return ProviderResult(
                success=False,
                provider_name="stripe",
                error_message=e.user_message or str(e),
                error_code=e.code,
            )

    async def refund_payment(
        self,
        provider_payment_id: str,
        amount_cents: Optional[int] = None,
    ) -> ProviderResult:
        """Refund a Stripe payment — full or partial."""
        try:
            params: Dict[str, Any] = {"payment_intent": provider_payment_id}
            if amount_cents is not None:
                params["amount"] = amount_cents
            refund = stripe.Refund.create(**params)
            logger.info("Stripe refund created: %s (amount=%s)", refund.id, amount_cents)
            return ProviderResult(
                success=True,
                provider_id=refund.id,
                provider_name="stripe",
                data={
                    "status": refund.status,
                    "amount": refund.amount,
                    "currency": refund.currency,
                },
                raw_response=dict(refund),
            )
        except StripeError as e:
            logger.error("Stripe refund_payment failed: %s", e.user_message or str(e))
            return ProviderResult(
                success=False,
                provider_name="stripe",
                error_message=e.user_message or str(e),
                error_code=e.code,
            )

    async def create_subscription(
        self,
        plan_external_id: str,
        customer_id: str,
        metadata: Dict[str, Any],
    ) -> ProviderResult:
        """Create a Stripe subscription for a customer."""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": plan_external_id}],
                metadata=_sanitize_metadata(metadata),
            )
            logger.info("Stripe subscription created: %s", subscription.id)
            return ProviderResult(
                success=True,
                provider_id=subscription.id,
                provider_name="stripe",
                data={
                    "status": subscription.status,
                    "current_period_end": subscription.current_period_end,
                },
                raw_response=dict(subscription),
            )
        except StripeError as e:
            logger.error("Stripe create_subscription failed: %s", e.user_message or str(e))
            return ProviderResult(
                success=False,
                provider_name="stripe",
                error_message=e.user_message or str(e),
                error_code=e.code,
            )

    async def cancel_subscription(self, provider_subscription_id: str) -> ProviderResult:
        """Cancel a Stripe subscription at period end."""
        try:
            subscription = stripe.Subscription.modify(
                provider_subscription_id,
                cancel_at_period_end=True,
            )
            logger.info("Stripe subscription cancelled: %s", subscription.id)
            return ProviderResult(
                success=True,
                provider_id=subscription.id,
                provider_name="stripe",
                data={
                    "status": subscription.status,
                    "cancel_at_period_end": subscription.cancel_at_period_end,
                },
                raw_response=dict(subscription),
            )
        except StripeError as e:
            logger.error("Stripe cancel_subscription failed: %s", e.user_message or str(e))
            return ProviderResult(
                success=False,
                provider_name="stripe",
                error_message=e.user_message or str(e),
                error_code=e.code,
            )

    async def update_subscription(
        self,
        provider_subscription_id: str,
        new_plan_external_id: str,
    ) -> ProviderResult:
        """Change subscription plan (upgrade/downgrade) with proration."""
        try:
            subscription = stripe.Subscription.retrieve(provider_subscription_id)
            updated = stripe.Subscription.modify(
                provider_subscription_id,
                items=[{
                    "id": subscription["items"]["data"][0].id,
                    "price": new_plan_external_id,
                }],
                proration_behavior="create_prorations",
            )
            logger.info("Stripe subscription updated: %s → %s", updated.id, new_plan_external_id)
            return ProviderResult(
                success=True,
                provider_id=updated.id,
                provider_name="stripe",
                data={
                    "status": updated.status,
                    "new_plan": new_plan_external_id,
                },
                raw_response=dict(updated),
            )
        except StripeError as e:
            logger.error("Stripe update_subscription failed: %s", e.user_message or str(e))
            return ProviderResult(
                success=False,
                provider_name="stripe",
                error_message=e.user_message or str(e),
                error_code=e.code,
            )

    async def tokenize_payment_method(self, raw_data: Dict[str, Any]) -> ProviderResult:
        """Attach a payment method to a Stripe customer."""
        try:
            customer_id = raw_data.get("customer_id")
            payment_method_id = raw_data.get("payment_method_id")
            if not customer_id or not payment_method_id:
                return ProviderResult(
                    success=False,
                    provider_name="stripe",
                    error_message="customer_id and payment_method_id are required",
                )
            pm = stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
            logger.info("Stripe payment method attached: %s → customer %s", pm.id, customer_id)
            return ProviderResult(
                success=True,
                provider_id=pm.id,
                provider_name="stripe",
                data={"type": pm.type, "customer": customer_id},
                raw_response=dict(pm),
            )
        except StripeError as e:
            logger.error("Stripe tokenize_payment_method failed: %s", e.user_message or str(e))
            return ProviderResult(
                success=False,
                provider_name="stripe",
                error_message=e.user_message or str(e),
                error_code=e.code,
            )

    async def delete_payment_method(self, provider_token: str) -> ProviderResult:
        """Detach a payment method from its customer."""
        try:
            pm = stripe.PaymentMethod.detach(provider_token)
            logger.info("Stripe payment method detached: %s", pm.id)
            return ProviderResult(
                success=True,
                provider_id=pm.id,
                provider_name="stripe",
                data={"status": "detached"},
                raw_response=dict(pm),
            )
        except StripeError as e:
            logger.error("Stripe delete_payment_method failed: %s", e.user_message or str(e))
            return ProviderResult(
                success=False,
                provider_name="stripe",
                error_message=e.user_message or str(e),
                error_code=e.code,
            )

    async def handle_webhook(self, headers: Dict[str, str], body: bytes) -> WebhookEvent:
        """Verify and parse a Stripe webhook event."""
        sig_header = headers.get("stripe-signature", "")

        if self._webhook_secret and sig_header:
            try:
                event = stripe.Webhook.construct_event(body, sig_header, self._webhook_secret)
            except SignatureVerificationError as e:
                logger.error("Stripe webhook signature verification failed: %s", str(e))
                raise
            except ValueError:
                logger.error("Stripe webhook invalid payload")
                raise
        else:
            # No webhook secret configured — parse without verification (dev/test only)
            import json
            event = json.loads(body)
            logger.warning("Stripe webhook parsed WITHOUT signature verification (no webhook_secret)")

        event_type = event.get("type", "unknown")
        event_id = event.get("id", "")
        obj = event.get("data", {}).get("object", {})

        # Map Stripe event types to entity types
        entity_type = None
        entity_id = None
        if "payment_intent" in event_type:
            entity_type = "payment"
            entity_id = obj.get("id")
        elif "subscription" in event_type:
            entity_type = "subscription"
            entity_id = obj.get("id")
        elif "invoice" in event_type:
            entity_type = "invoice"
            entity_id = obj.get("id")
        elif "checkout.session" in event_type:
            entity_type = "checkout"
            entity_id = obj.get("id")

        logger.info("Stripe webhook received: type=%s entity=%s/%s", event_type, entity_type, entity_id)

        return WebhookEvent(
            event_type=event_type,
            provider_name="stripe",
            provider_event_id=event_id,
            entity_type=entity_type,
            entity_id=entity_id,
            data=obj if isinstance(obj, dict) else {},
        )


def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, str]:
    """Stripe metadata values must be strings, max 500 chars each."""
    return {
        str(k): str(v)[:500]
        for k, v in metadata.items()
        if k not in ("success_url", "cancel_url", "description")
    }
