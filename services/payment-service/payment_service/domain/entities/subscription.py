"""
Subscription Entity - Organization-to-plan binding.

Business Context:
A subscription represents the active relationship between an organization and a plan.
It tracks billing periods, trial status, and lifecycle events. Each organization
has exactly one active subscription at a time.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from payment_service.domain.enums import SubscriptionStatus


@dataclass
class Subscription:
    """
    Subscription entity binding an organization to a plan.

    The provider_subscription_id links to the external payment provider's record
    (e.g., Stripe subscription ID). For NullProvider, this is a generated placeholder.
    """
    id: UUID = None
    organization_id: UUID = None
    plan_id: UUID = None
    status: SubscriptionStatus = SubscriptionStatus.TRIAL
    provider_name: str = "null"
    provider_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.id is None:
            self.id = uuid4()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def is_active(self) -> bool:
        """Whether the subscription is in a usable state."""
        return self.status in (
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIAL,
            SubscriptionStatus.PAST_DUE,
        )

    def is_trialing(self) -> bool:
        """Whether the subscription is in trial period."""
        return self.status == SubscriptionStatus.TRIAL

    def cancel(self, reason: Optional[str] = None):
        """Mark subscription as cancelled."""
        self.status = SubscriptionStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.cancel_reason = reason
        self.updated_at = datetime.utcnow()

    def activate(self):
        """Transition from trial/past_due to active."""
        self.status = SubscriptionStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def mark_past_due(self):
        """Flag subscription when payment fails."""
        self.status = SubscriptionStatus.PAST_DUE
        self.updated_at = datetime.utcnow()

    def pause(self):
        """Temporarily pause the subscription."""
        self.status = SubscriptionStatus.PAUSED
        self.updated_at = datetime.utcnow()
