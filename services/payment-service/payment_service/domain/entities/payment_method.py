"""
PaymentMethod Entity - Tokenized payment instruments.

Business Context:
Payment methods represent stored payment instruments (credit cards, ACH accounts, etc.)
for an organization. The actual card/account data is stored with the payment provider;
we only keep a tokenized reference and display metadata (last four digits, expiry).
For NullProvider/free plans, a PLATFORM_CREDIT method is auto-created.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from payment_service.domain.enums import PaymentMethodType


@dataclass
class PaymentMethod:
    """
    Tokenized payment instrument for an organization.

    The provider_token is the external reference (e.g., Stripe payment method ID).
    We store only display metadata (last_four, expiry) — never raw card numbers.
    """
    id: UUID = None
    organization_id: UUID = None
    method_type: PaymentMethodType = PaymentMethodType.PLATFORM_CREDIT
    provider_name: str = "null"
    provider_token: Optional[str] = None
    label: Optional[str] = None
    last_four: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    is_default: bool = False
    is_active: bool = True
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
    def display_name(self) -> str:
        """Human-readable label for the payment method."""
        if self.label:
            return self.label
        if self.last_four:
            return f"{self.method_type.value} ending in {self.last_four}"
        return self.method_type.value

    def deactivate(self):
        """Soft-delete the payment method."""
        self.is_active = False
        self.is_default = False
        self.updated_at = datetime.utcnow()

    def set_default(self):
        """Mark as the default payment method for the org."""
        self.is_default = True
        self.updated_at = datetime.utcnow()
