"""
Webhook Ingestion Endpoints

Business Context:
Payment providers (Stripe, Square, etc.) send webhook events to notify us
of asynchronous events like successful payments, subscription renewals,
and payment failures. Each provider has its own webhook URL and signature
verification scheme.

The NullProvider doesn't send real webhooks, but the endpoint exists so
the infrastructure is ready when a real provider is plugged in.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, Depends

from payment_service.infrastructure.container import get_container
from payment_service.application.services.subscription_service import SubscriptionService
from payment_service.data_access.payment_dao import PaymentDAO
from payment_service.exceptions import (
    PaymentProviderNotFoundError,
    WebhookVerificationException,
)
from app_dependencies import get_subscription_service, get_dao

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payment/webhooks", tags=["webhooks"])


@router.post("/{provider_name}")
async def handle_webhook(
    provider_name: str,
    request: Request,
    sub_service: SubscriptionService = Depends(get_subscription_service),
    dao: PaymentDAO = Depends(get_dao),
) -> Dict[str, Any]:
    """
    Receive and process a webhook from a payment provider.

    No authentication required — webhooks are verified by the provider's
    own signature mechanism (e.g., Stripe-Signature header).

    Handles:
    - payment.completed (checkout.session.completed) → activate subscription
    - subscription.created / subscription.updated → sync subscription status
    - subscription.cancelled → mark subscription cancelled
    - invoice.paid → record payment
    - invoice.payment_failed → mark subscription past_due
    """
    # Get provider through the container so it has the correct config/keys
    container = get_container()
    try:
        provider = container.get_provider(provider_name)
    except PaymentProviderNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider_name}")
    except Exception:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider_name}")

    body = await request.body()
    headers = dict(request.headers)

    try:
        event = await provider.handle_webhook(headers, body)
    except WebhookVerificationException as e:
        logger.warning(f"Webhook verification failed for {provider_name}: {e.message}")
        raise HTTPException(status_code=400, detail="Webhook verification failed")

    logger.info(
        f"Webhook received: provider={provider_name} event_type={event.event_type} "
        f"entity={event.entity_type}:{event.entity_id}"
    )

    await _process_event(event, dao)

    return {
        "status": "received",
        "event_type": event.event_type,
        "provider": provider_name,
    }


async def _process_event(event, dao: PaymentDAO):
    """Dispatch webhook events to update local subscription state."""
    event_type = event.event_type
    data = event.data or {}

    try:
        if event_type == "payment.completed":
            # checkout.session.completed — look up subscription by provider reference and activate it
            provider_sub_id = data.get("subscription")
            if provider_sub_id:
                sub = await dao.get_subscription_by_provider_id(provider_sub_id)
                if sub and sub["status"] in ("trial", "past_due"):
                    await dao.update_subscription(str(sub["id"]), {"status": "active"})
                    logger.info(f"Subscription activated via checkout: {sub['id']}")

        elif event_type == "subscription.created":
            # New subscription created in Stripe — may already exist locally; ensure status=active
            provider_sub_id = event.entity_id
            if provider_sub_id:
                sub = await dao.get_subscription_by_provider_id(provider_sub_id)
                if sub and sub["status"] == "trial":
                    # Trial → active on first payment
                    stripe_status = data.get("status", "")
                    if stripe_status == "active":
                        await dao.update_subscription(str(sub["id"]), {"status": "active"})
                        logger.info(f"Subscription status synced to active: {sub['id']}")

        elif event_type == "subscription.updated":
            provider_sub_id = event.entity_id
            if provider_sub_id:
                sub = await dao.get_subscription_by_provider_id(provider_sub_id)
                if sub:
                    stripe_status = data.get("status", "")
                    status_map = {
                        "active": "active",
                        "past_due": "past_due",
                        "canceled": "cancelled",
                        "paused": "paused",
                        "trialing": "trial",
                    }
                    mapped = status_map.get(stripe_status)
                    if mapped and mapped != sub["status"]:
                        await dao.update_subscription(str(sub["id"]), {"status": mapped})
                        logger.info(f"Subscription status updated: {sub['id']} → {mapped}")

        elif event_type == "subscription.cancelled":
            provider_sub_id = event.entity_id
            if provider_sub_id:
                sub = await dao.get_subscription_by_provider_id(provider_sub_id)
                if sub and sub["status"] != "cancelled":
                    from datetime import datetime
                    await dao.update_subscription(str(sub["id"]), {
                        "status": "cancelled",
                        "cancelled_at": datetime.utcnow(),
                        "cancel_reason": "stripe_webhook",
                    })
                    logger.info(f"Subscription cancelled via webhook: {sub['id']}")

        elif event_type == "invoice.payment_failed":
            provider_sub_id = data.get("subscription")
            if provider_sub_id:
                sub = await dao.get_subscription_by_provider_id(provider_sub_id)
                if sub and sub["status"] == "active":
                    await dao.update_subscription(str(sub["id"]), {"status": "past_due"})
                    logger.info(f"Subscription marked past_due: {sub['id']}")

        elif event_type == "invoice.paid":
            # Payment succeeded — ensure subscription is active (recover from past_due)
            provider_sub_id = data.get("subscription")
            if provider_sub_id:
                sub = await dao.get_subscription_by_provider_id(provider_sub_id)
                if sub and sub["status"] == "past_due":
                    await dao.update_subscription(str(sub["id"]), {"status": "active"})
                    logger.info(f"Subscription recovered from past_due: {sub['id']}")

    except Exception as exc:
        # Never let webhook processing errors cause a non-200 response to Stripe
        # (Stripe would retry indefinitely). Log and continue.
        logger.error(f"Error processing webhook event {event_type}: {exc}", exc_info=True)
