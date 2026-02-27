"""
Invoice Entity - Billing documents for organizations.

Business Context:
Invoices represent billable events — generated from subscription cycles or one-time
charges. Each invoice contains line items and tracks payment status. Invoices provide
the audit trail for all financial transactions on the platform.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from payment_service.domain.enums import InvoiceStatus, Currency


@dataclass
class InvoiceLineItem:
    """Single charge line on an invoice."""
    id: UUID = None
    invoice_id: UUID = None
    description: str = ""
    quantity: int = 1
    unit_price_cents: int = 0
    amount_cents: int = 0

    def __post_init__(self):
        if self.id is None:
            self.id = uuid4()
        if self.amount_cents == 0 and self.unit_price_cents > 0:
            self.amount_cents = self.quantity * self.unit_price_cents


@dataclass
class Invoice:
    """
    Invoice entity for billing an organization.

    Invoices are generated automatically from subscription billing cycles
    or created manually for one-time charges. The provider_invoice_id links
    to the external provider's invoice record.
    """
    id: UUID = None
    organization_id: UUID = None
    subscription_id: Optional[UUID] = None
    invoice_number: Optional[str] = None
    amount_cents: int = 0
    currency: Currency = Currency.USD
    status: InvoiceStatus = InvoiceStatus.DRAFT
    line_items: List[Dict[str, Any]] = field(default_factory=list)
    provider_invoice_id: Optional[str] = None
    issued_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
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

    def issue(self):
        """Transition from draft to issued."""
        self.status = InvoiceStatus.ISSUED
        self.issued_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_paid(self):
        """Record payment received."""
        self.status = InvoiceStatus.PAID
        self.paid_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_overdue(self):
        """Flag invoice as past due date."""
        self.status = InvoiceStatus.OVERDUE
        self.updated_at = datetime.utcnow()

    def void(self):
        """Void a paid invoice (e.g., after full refund)."""
        self.status = InvoiceStatus.VOID
        self.updated_at = datetime.utcnow()
