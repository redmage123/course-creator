"""
Plan Entity - Subscription plan definitions.

Business Context:
Plans define the pricing tiers available to organizations (e.g., Free, Pro, Enterprise).
Each plan specifies its billing interval, price, included features, and optional trial period.
Plans are managed by site admins and referenced by subscriptions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

from payment_service.domain.enums import BillingInterval, Currency


@dataclass
class Plan:
    """
    Subscription plan entity.

    A plan is a template that defines what an organization gets and what it costs.
    The features dict stores plan-specific capabilities (e.g., max_users, max_courses).
    """
    id: UUID = None
    name: str = ""
    description: str = ""
    price_cents: int = 0
    currency: Currency = Currency.USD
    billing_interval: BillingInterval = BillingInterval.MONTHLY
    features: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    trial_days: int = 0
    sort_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.id is None:
            self.id = uuid4()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    @property
    def price_dollars(self) -> float:
        """Price in dollars (from cents storage)."""
        return self.price_cents / 100.0

    def is_free(self) -> bool:
        """Whether this plan has no cost."""
        return self.price_cents == 0

    def has_trial(self) -> bool:
        """Whether this plan offers a trial period."""
        return self.trial_days > 0

    def deactivate(self):
        """Soft-deactivate plan (existing subscriptions continue)."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
