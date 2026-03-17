"""
Payment Provider Abstract Base Class

Business Context:
Defines the contract that all payment providers must implement. This enables
the Strategy Pattern — new providers (Stripe, Square, PayPal) can be added
by implementing this interface without modifying existing code.

Technical Rationale:
By programming against this abstraction, the PaymentOrchestrator and all
upstream services are completely decoupled from any specific payment gateway.
Provider-specific logic (API calls, webhook parsing, authentication) lives
entirely within the concrete implementations, keeping the core domain clean.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4


@dataclass
class ProviderResult:
    """
    Standardized result from any provider operation.

    Every provider method returns this structure, ensuring that the orchestrator
    and domain services never need to understand provider-specific response
    formats. The raw_response field preserves the original provider data for
    debugging and audit purposes without leaking it into the domain layer.
    """
    success: bool
    provider_id: Optional[str] = None      # External ID from the provider
    provider_name: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class WebhookEvent:
    """
    Parsed webhook event from a provider.

    Normalizes the diverse webhook formats from different providers into a
    single structure that the webhook processing pipeline can handle uniformly.
    The entity_type and entity_id fields identify which domain object the event
    relates to (payment, subscription, invoice), enabling targeted event routing.
    """
    event_type: str                        # e.g. 'payment.completed', 'subscription.cancelled'
    provider_name: str
    provider_event_id: Optional[str] = None
    entity_type: Optional[str] = None      # 'payment', 'subscription', 'invoice'
    entity_id: Optional[str] = None        # Provider's entity ID
    data: Dict[str, Any] = field(default_factory=dict)
    received_at: datetime = field(default_factory=datetime.utcnow)


class PaymentProvider(ABC):
    """
    Abstract interface for payment providers.

    All providers (Stripe, Square, NullProvider, etc.) implement these methods.
    The PaymentOrchestrator delegates to the appropriate provider at runtime,
    selected based on the organization's configured provider name.

    To add a new provider:
    1. Create a new module implementing this ABC (e.g., stripe_provider.py)
    2. Register it in the PROVIDER_REGISTRY (see registry.py)
    3. Pass provider-specific configuration through the constructor

    All methods are async to support non-blocking I/O when calling external
    payment gateway APIs.
    """

    @abstractmethod
    async def get_provider_name(self) -> str:
        """Return the registered name of this provider (e.g., 'stripe', 'null')."""

    @abstractmethod
    async def create_checkout_session(
        self,
        amount_cents: int,
        currency: str,
        metadata: Dict[str, Any]
    ) -> ProviderResult:
        """
        Create a checkout/payment session for a one-time payment.

        Args:
            amount_cents: Payment amount in the smallest currency unit (e.g., cents for USD).
            currency: ISO 4217 currency code (e.g., 'usd', 'cad').
            metadata: Arbitrary key-value pairs passed through to the provider
                      (e.g., organization_id, invoice_id, description).

        Returns:
            ProviderResult with provider_id set to the session/payment identifier
            and data containing any redirect URLs or client secrets needed by the frontend.
        """

    @abstractmethod
    async def capture_payment(self, provider_payment_id: str) -> ProviderResult:
        """
        Capture/confirm a previously created payment.

        Some providers use a two-step flow: authorize then capture. This method
        handles the capture step. For providers that capture immediately, this
        may be a no-op that returns success.

        Args:
            provider_payment_id: The provider's identifier for the payment session.

        Returns:
            ProviderResult indicating capture success or failure.
        """

    @abstractmethod
    async def refund_payment(
        self,
        provider_payment_id: str,
        amount_cents: Optional[int] = None
    ) -> ProviderResult:
        """
        Refund a payment — full if amount_cents is None, partial otherwise.

        Args:
            provider_payment_id: The provider's identifier for the original payment.
            amount_cents: Amount to refund in smallest currency unit. None means full refund.

        Returns:
            ProviderResult with provider_id set to the refund identifier.
        """

    @abstractmethod
    async def create_subscription(
        self,
        plan_external_id: str,
        customer_id: str,
        metadata: Dict[str, Any]
    ) -> ProviderResult:
        """
        Create a recurring subscription.

        Args:
            plan_external_id: The provider's identifier for the subscription plan/price.
            customer_id: The provider's customer identifier.
            metadata: Arbitrary key-value pairs (e.g., organization_id, user_id).

        Returns:
            ProviderResult with provider_id set to the subscription identifier.
        """

    @abstractmethod
    async def cancel_subscription(self, provider_subscription_id: str) -> ProviderResult:
        """
        Cancel an active subscription.

        The cancellation policy (immediate vs end-of-period) is determined by
        the provider configuration or the calling service's business logic.

        Args:
            provider_subscription_id: The provider's identifier for the subscription.

        Returns:
            ProviderResult indicating cancellation success or failure.
        """

    @abstractmethod
    async def update_subscription(
        self,
        provider_subscription_id: str,
        new_plan_external_id: str
    ) -> ProviderResult:
        """
        Change a subscription to a different plan (upgrade or downgrade).

        Proration handling is provider-specific and configured at the provider level.

        Args:
            provider_subscription_id: The provider's identifier for the subscription.
            new_plan_external_id: The provider's identifier for the new plan/price.

        Returns:
            ProviderResult indicating update success or failure.
        """

    @abstractmethod
    async def tokenize_payment_method(self, raw_data: Dict[str, Any]) -> ProviderResult:
        """
        Store/tokenize a payment method for future use.

        The raw_data format is provider-specific (e.g., Stripe token, card details).
        The provider returns a reusable token/ID that can be used for future charges.

        Args:
            raw_data: Provider-specific payment method data.

        Returns:
            ProviderResult with provider_id set to the stored payment method token/ID.
        """

    @abstractmethod
    async def delete_payment_method(self, provider_token: str) -> ProviderResult:
        """
        Remove a stored payment method.

        Args:
            provider_token: The token/ID of the payment method to remove.

        Returns:
            ProviderResult indicating deletion success or failure.
        """

    @abstractmethod
    async def handle_webhook(self, headers: Dict[str, str], body: bytes) -> WebhookEvent:
        """
        Parse and verify an incoming webhook from this provider.

        Each provider has its own signature verification mechanism and payload
        format. This method handles both verification and parsing, returning
        a normalized WebhookEvent.

        Args:
            headers: HTTP headers from the webhook request.
            body: Raw request body bytes (needed for signature verification).

        Returns:
            WebhookEvent with the parsed and normalized event data.

        Raises:
            WebhookVerificationException: If signature verification fails.
        """
