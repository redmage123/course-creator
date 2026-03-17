"""
Payment Service Domain Enums

Business Context:
Defines all status and type enumerations for the payment domain. These enums
provide type-safe status tracking for payments, subscriptions, invoices, and
related entities across the payment lifecycle.

Technical Rationale:
Using str-based Enums enables JSON serialization compatibility with FastAPI
and PostgreSQL text columns while maintaining type safety in Python code.
"""

from enum import Enum


class PaymentStatus(str, Enum):
    """
    Tracks the lifecycle of a payment transaction.

    PENDING → PROCESSING → COMPLETED (happy path)
    PENDING → PROCESSING → FAILED (provider rejection)
    COMPLETED → REFUNDED | PARTIALLY_REFUNDED (post-completion)
    Any → CANCELLED (manual cancellation)
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    CANCELLED = "cancelled"


class SubscriptionStatus(str, Enum):
    """
    Tracks subscription lifecycle from trial through expiry.

    TRIAL → ACTIVE → CANCELLED | EXPIRED
    ACTIVE → PAST_DUE → ACTIVE (payment retry success)
    ACTIVE → PAST_DUE → CANCELLED (payment retry exhausted)
    ACTIVE → PAUSED → ACTIVE (manual resume)
    """
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAUSED = "paused"


class InvoiceStatus(str, Enum):
    """
    Tracks invoice lifecycle from creation through payment.

    DRAFT → ISSUED → PAID (happy path)
    ISSUED → OVERDUE → PAID (late payment)
    DRAFT | ISSUED → CANCELLED (before payment)
    PAID → VOID (post-payment reversal)
    """
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    VOID = "void"


class PaymentMethodType(str, Enum):
    """
    Types of payment instruments supported by the platform.
    PLATFORM_CREDIT is used by the NullProvider for free/trial plans.
    """
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    ACH = "ach"
    WIRE = "wire"
    PLATFORM_CREDIT = "platform_credit"


class BillingInterval(str, Enum):
    """Subscription billing frequency."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class Currency(str, Enum):
    """Supported currencies (ISO 4217)."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
