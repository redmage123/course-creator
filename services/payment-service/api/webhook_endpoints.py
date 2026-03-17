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

from fastapi import APIRouter, Request, HTTPException

from payment_service.infrastructure.providers.registry import get_provider
from payment_service.exceptions import (
    PaymentProviderNotFoundError,
    WebhookVerificationException,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payment/webhooks", tags=["webhooks"])


@router.post("/{provider_name}")
async def handle_webhook(
    provider_name: str,
    request: Request,
) -> Dict[str, Any]:
    """
    Receive and process a webhook from a payment provider.

    No authentication required — webhooks are verified by the provider's
    own signature mechanism (e.g., Stripe-Signature header).
    """
    try:
        provider = get_provider(provider_name)
    except PaymentProviderNotFoundError:
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

    return {
        "status": "received",
        "event_type": event.event_type,
        "provider": provider_name,
    }
