"""
Payment Entity - Transaction records for money movements.

Business Context:
A Payment (transaction) records an actual money movement — either a charge to a
customer or a refund back. Payments are linked to invoices and track the provider
that processed them. This is the core financial audit record.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

from payment_service.domain.enums import PaymentStatus, Currency


@dataclass
class Payment:
    """
    Payment transaction entity.

    Each payment records a single money movement processed through a provider.
    The provider_transaction_id links to the external provider's record
    (e.g., Stripe charge ID). For NullProvider, this is a generated placeholder.
    """
    id: UUID = None
    organization_id: UUID = None
    invoice_id: Optional[UUID] = None
    amount_cents: int = 0
    currency: Currency = Currency.USD
    status: PaymentStatus = PaymentStatus.PENDING
    provider_name: str = "null"
    provider_transaction_id: Optional[str] = None
    payment_method_id: Optional[UUID] = None
    refund_amount_cents: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    failure_reason: Optional[str] = None
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
    def amount_dollars(self) -> float:
        return self.amount_cents / 100.0

    @property
    def refund_dollars(self) -> float:
        return self.refund_amount_cents / 100.0

    @property
    def net_amount_cents(self) -> int:
        """Amount after refunds."""
        return self.amount_cents - self.refund_amount_cents

    def complete(self, provider_transaction_id: str):
        """Mark payment as successfully completed."""
        self.status = PaymentStatus.COMPLETED
        self.provider_transaction_id = provider_transaction_id
        self.updated_at = datetime.utcnow()

    def fail(self, reason: str):
        """Record payment failure."""
        self.status = PaymentStatus.FAILED
        self.failure_reason = reason
        self.updated_at = datetime.utcnow()

    def refund(self, amount_cents: int):
        """Apply a refund (partial or full)."""
        self.refund_amount_cents += amount_cents
        if self.refund_amount_cents >= self.amount_cents:
            self.status = PaymentStatus.REFUNDED
        else:
            self.status = PaymentStatus.PARTIALLY_REFUNDED
        self.updated_at = datetime.utcnow()
