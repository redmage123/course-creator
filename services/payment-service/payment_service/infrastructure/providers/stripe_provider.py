"""
Stripe Payment Provider Implementation

Business Context:
Implements the PaymentProvider ABC for Stripe. Handles checkout sessions,
subscriptions, refunds, and webhook verification using Stripe's Python SDK.

Operates in test mode by default (STRIPE_MODE=test). Keys are loaded from
the container environment (STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET).

Technical Rationale:
- Uses stripe.stripe_object async patterns via the synchronous Stripe SDK
  (Stripe's Python SDK is sync; all calls are wrapped to remain non-blocking
  via run_in_executor in a production setting — kept sync here for clarity)
- Webhook signature verification uses stripe.Webhook.construct_event which
  requires the raw request bytes (not parsed JSON)
- Provider config dict keys: secret_key, webhook_secret, publishable_key
"""

import logging
from typing import Dict, Any, Optional

from payment_service.infrastructure.providers.base import (
    PaymentProvider,
    ProviderResult,
    WebhookEvent,
)
from payment_service.exceptions import (
    PaymentProviderConfigError,
    WebhookVerificationException,
)

logger = logging.getLogger(__name__)


class StripeProvider(PaymentProvider):
    """
    Stripe payment provider.

    Required config keys (passed via config.yaml under payment.providers.stripe
    or injected via environment variables loaded by the container):
        secret_key       — Stripe secret key (sk_test_... or sk_live_...)
        webhook_secret   — Stripe webhook signing secret (whsec_...)
        publishable_key  — Stripe publishable key (pk_test_... or pk_live_...)
    """

    def __init__(self, config: Dict[str, Any]):
        try:
            import stripe as _stripe
            self._stripe = _stripe
        except ImportError as e:
            raise PaymentProviderConfigError(
                "stripe",
                "stripe Python package not installed. Run: pip install stripe>=7.0.0",
                original_exception=e,
            )

        self._secret_key = config.get("secret_key", "")
        self._webhook_secret = config.get("webhook_secret", "")
        self._publishable_key = config.get("publishable_key", "")

        if not self._secret_key:
            raise PaymentProviderConfigError(
                "stripe",
                "secret_key is required. Set STRIPE_SECRET_KEY environment variable.",
            )

        self._stripe.api_key = self._secret_key
        logger.info(
            "StripeProvider initialized (mode=%s)",
            "test" if self._secret_key.startswith("sk_test") else "live",
        )

    async def get_provider_name(self) -> str:
        return "stripe"

    async def create_checkout_session(
        self,
        amount_cents: int,
        currency: str,
        metadata: Dict[str, Any],
    ) -> ProviderResult:
        """
        Create a Stripe Checkout Session for a one-time payment.

        Returns a checkout URL the frontend can redirect to.
        """
        try:
            session = self._stripe.checkout.Session.create(
                mode="payment",
                line_items=[
                    {
                        "price_data": {
                            "currency": currency.lower(),
                            "unit_amount": amount_cents,
                            "product_data": {
                                "name": metadata.get("description", "Course Creator Payment"),
                            },
                        },
                        "quantity": 1,
                    }
                ],
                metadata=metadata,
                success_url=metadata.get(
                    "success_url", "https://localhost:3000/billing?status=success"
                ),
                cancel_url=metadata.get(
                    "cancel_url", "https://localhost:3000/billing?status=cancelled"
                ),
            )
            logger.info(
                "Stripe checkout session created: id=%s amount_cents=%d",
                session.id,
                amount_cents,
            )
            return ProviderResult(
                success=True,
                provider_id=session.id,
                provider_name="stripe",
                data={
                    "checkout_url": session.url,
                    "session_id": session.id,
                    "amount_cents": amount_cents,
                    "currency": currency,
                    "status": session.status,
                },
                raw_response={"id": session.id, "url": session.url},
            )
        except self._stripe.error.StripeError as e:
            logger.error("Stripe checkout session failed: %s", e)
            return ProviderResult(
                success=False,
                provider_name="stripe",
                error_message=str(e),
                error_code=e.code if hasattr(e, "code") else "stripe_error",
            )

    async def capture_payment(self, provider_payment_id: str) -> ProviderResult:
        """
        Confirm/capture a PaymentIntent.

        For Checkout Sessions that auto-capture, this is a lookup to verify status.
        """
        try:
            # Retrieve the PaymentIntent linked to the session
            intent = self._stripe.PaymentIntent.retrieve(provider_payment_id)
            status = intent.status
            logger.info(
                "Stripe payment intent status: id=%s status=%s",
                provider_payment_id,
                status,
            )
            return ProviderResult(
                success=status == "succeeded",
                provider_id=intent.id,
                provider_name="stripe",
                data={"status": status},
                error_message=None if status == "succeeded" else f"Intent status: {status}",
            )
        except self._stripe.error.StripeError as e:
            logger.error("Stripe capture failed: %s", e)
            return ProviderResult(
                success=False,
                provider_name="stripe",
                error_message=str(e),
                error_code=getattr(e, "code", "stripe_error"),
            )

    async def refund_payment(
        self,
        provider_payment_id: str,
        amount_cents: Optional[int] = None,
    ) -> ProviderResult:
        """
        Refund a Stripe charge or PaymentIntent (full or partial).
        """
        try:
            params: Dict[str, Any] = {"payment_intent": provider_payment_id}
            if amount_cents is not None:
                params["amount"] = amount_cents

            refund = self._stripe.Refund.create(**params)
            logger.info(
                "Stripe refund created: id=%s amount=%s status=%s",
                refund.id,
                refund.amount,
                refund.status,
            )
            return ProviderResult(
                success=refund.status in ("succeeded", "pending"),
                provider_id=refund.id,
                provider_name="stripe",
                data={
                    "refund_id": refund.id,
                    "amount": refund.amount,
                    "status": refund.status,
                    "currency": refund.currency,
                },
            )
        except self._stripe.error.StripeError as e:
            logger.error("Stripe refund failed: %s", e)
            return ProviderResult(
                success=False,
                provider_name="stripe",
                error_message=str(e),
                error_code=getattr(e, "code", "stripe_error"),
            )

    async def create_subscription(
        self,
        plan_external_id: str,
        customer_id: str,
        metadata: Dict[str, Any],
    ) -> ProviderResult:
        """
        Create a Stripe subscription.

        plan_external_id should be a Stripe Price ID (price_xxx).
        customer_id should be a Stripe Customer ID (cus_xxx).

        If customer_id is not a Stripe Customer ID (e.g. it's an org UUID),
        a Stripe Customer will be created automatically.
        """
        try:
            # Ensure we have a Stripe Customer
            if not customer_id.startswith("cus_"):
                customer = self._stripe.Customer.create(
                    metadata={"organization_id": customer_id, **metadata},
                )
                stripe_customer_id = customer.id
                logger.info(
                    "Created Stripe customer for org %s: %s",
                    customer_id,
                    stripe_customer_id,
                )
            else:
                stripe_customer_id = customer_id

            subscription = self._stripe.Subscription.create(
                customer=stripe_customer_id,
                items=[{"price": plan_external_id}],
                metadata=metadata,
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"],
            )
            logger.info(
                "Stripe subscription created: id=%s status=%s",
                subscription.id,
                subscription.status,
            )
            return ProviderResult(
                success=True,
                provider_id=subscription.id,
                provider_name="stripe",
                data={
                    "subscription_id": subscription.id,
                    "customer_id": stripe_customer_id,
                    "status": subscription.status,
                    "current_period_end": subscription.current_period_end,
                },
            )
        except self._stripe.error.StripeError as e:
            logger.error("Stripe subscription creation failed: %s", e)
            return ProviderResult(
                success=False,
                provider_name="stripe",
                error_message=str(e),
                error_code=getattr(e, "code", "stripe_error"),
            )

    async def cancel_subscription(self, provider_subscription_id: str) -> ProviderResult:
        """Cancel a Stripe subscription at period end."""
        try:
            subscription = self._stripe.Subscription.cancel(provider_subscription_id)
            logger.info(
                "Stripe subscription cancelled: id=%s status=%s",
                subscription.id,
                subscription.status,
            )
            return ProviderResult(
                success=True,
                provider_id=subscription.id,
                provider_name="stripe",
                data={"status": subscription.status},
            )
        except self._stripe.error.StripeError as e:
            logger.error("Stripe cancel subscription failed: %s", e)
            return ProviderResult(
                success=False,
                provider_name="stripe",
                error_message=str(e),
                error_code=getattr(e, "code", "stripe_error"),
            )

    async def update_subscription(
        self,
        provider_subscription_id: str,
        new_plan_external_id: str,
    ) -> ProviderResult:
        """Upgrade or downgrade a Stripe subscription to a new price."""
        try:
            subscription = self._stripe.Subscription.retrieve(provider_subscription_id)
            item_id = subscription["items"]["data"][0]["id"]

            updated = self._stripe.Subscription.modify(
                provider_subscription_id,
                items=[{"id": item_id, "price": new_plan_external_id}],
                proration_behavior="create_prorations",
            )
            logger.info(
                "Stripe subscription updated: id=%s new_price=%s",
                updated.id,
                new_plan_external_id,
            )
            return ProviderResult(
                success=True,
                provider_id=updated.id,
                provider_name="stripe",
                data={"status": updated.status, "new_price": new_plan_external_id},
            )
        except self._stripe.error.StripeError as e:
            logger.error("Stripe update subscription failed: %s", e)
            return ProviderResult(
                success=False,
                provider_name="stripe",
                error_message=str(e),
                error_code=getattr(e, "code", "stripe_error"),
            )

    async def tokenize_payment_method(self, raw_data: Dict[str, Any]) -> ProviderResult:
        """
        Attach a payment method to a Stripe customer.

        raw_data expected keys:
            payment_method_id  — Stripe PaymentMethod ID (pm_xxx)
            customer_id        — Stripe Customer ID (cus_xxx)
        """
        try:
            pm_id = raw_data.get("payment_method_id", "")
            customer_id = raw_data.get("customer_id", "")

            self._stripe.PaymentMethod.attach(pm_id, customer=customer_id)
            logger.info(
                "Stripe payment method attached: pm=%s customer=%s",
                pm_id,
                customer_id,
            )
            return ProviderResult(
                success=True,
                provider_id=pm_id,
                provider_name="stripe",
                data={"payment_method_id": pm_id, "customer_id": customer_id},
            )
        except self._stripe.error.StripeError as e:
            logger.error("Stripe tokenize payment method failed: %s", e)
            return ProviderResult(
                success=False,
                provider_name="stripe",
                error_message=str(e),
                error_code=getattr(e, "code", "stripe_error"),
            )

    async def delete_payment_method(self, provider_token: str) -> ProviderResult:
        """Detach a Stripe payment method from its customer."""
        try:
            pm = self._stripe.PaymentMethod.detach(provider_token)
            logger.info("Stripe payment method detached: pm=%s", pm.id)
            return ProviderResult(
                success=True,
                provider_id=pm.id,
                provider_name="stripe",
                data={"status": "detached"},
            )
        except self._stripe.error.StripeError as e:
            logger.error("Stripe delete payment method failed: %s", e)
            return ProviderResult(
                success=False,
                provider_name="stripe",
                error_message=str(e),
                error_code=getattr(e, "code", "stripe_error"),
            )

    async def handle_webhook(
        self,
        headers: Dict[str, str],
        body: bytes,
    ) -> WebhookEvent:
        """
        Verify and parse an incoming Stripe webhook event.

        Stripe-Signature header is required. The raw body bytes are used
        for HMAC verification — do not parse the body before calling this.

        Raises:
            WebhookVerificationException: If signature is invalid or webhook_secret is missing.
        """
        if not self._webhook_secret:
            raise WebhookVerificationException(
                "stripe",
                "webhook_secret not configured. Set STRIPE_WEBHOOK_SECRET env var.",
            )

        sig_header = headers.get("stripe-signature", headers.get("Stripe-Signature", ""))
        if not sig_header:
            raise WebhookVerificationException(
                "stripe", "Missing Stripe-Signature header"
            )

        try:
            event = self._stripe.Webhook.construct_event(
                payload=body,
                sig_header=sig_header,
                secret=self._webhook_secret,
            )
        except self._stripe.error.SignatureVerificationError as e:
            raise WebhookVerificationException("stripe", str(e))

        # Normalize Stripe event types → platform event types
        event_type_map = {
            "checkout.session.completed": "payment.completed",
            "invoice.payment_succeeded": "invoice.paid",
            "invoice.payment_failed": "invoice.payment_failed",
            "customer.subscription.created": "subscription.created",
            "customer.subscription.updated": "subscription.updated",
            "customer.subscription.deleted": "subscription.cancelled",
            "payment_intent.succeeded": "payment.completed",
            "payment_intent.payment_failed": "payment.failed",
        }

        raw_event_type = event["type"]
        platform_event_type = event_type_map.get(raw_event_type, raw_event_type)

        # Extract entity identifiers
        data_object = event.get("data", {}).get("object", {})
        entity_type = None
        entity_id = None

        if "subscription" in raw_event_type:
            entity_type = "subscription"
            entity_id = data_object.get("id")
        elif "invoice" in raw_event_type:
            entity_type = "invoice"
            entity_id = data_object.get("id")
        elif "payment_intent" in raw_event_type or "checkout" in raw_event_type:
            entity_type = "payment"
            entity_id = data_object.get("payment_intent") or data_object.get("id")

        logger.info(
            "Stripe webhook received: type=%s entity=%s:%s",
            raw_event_type,
            entity_type,
            entity_id,
        )

        return WebhookEvent(
            event_type=platform_event_type,
            provider_name="stripe",
            provider_event_id=event.get("id"),
            entity_type=entity_type,
            entity_id=entity_id,
            data=dict(data_object),
        )
