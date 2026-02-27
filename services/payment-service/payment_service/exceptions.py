"""
Payment Service Exception Hierarchy

Business Context:
Provides structured exception handling for all payment-related operations.
Each exception carries an error code, contextual details, and optional
original exception for tracing. This hierarchy enables precise error mapping
to HTTP status codes in the error handling middleware.

Technical Rationale:
Inherits from the platform-wide CourseCreatorBaseException pattern to ensure
consistent error serialization across all microservices.
"""

from typing import Dict, Any, Optional
from datetime import datetime


class PaymentBaseException(Exception):
    """
    Base exception for all payment service errors.

    Follows the platform-wide exception pattern with error codes,
    contextual details, and exception chaining.
    """

    def __init__(
        self,
        message: str,
        error_code: str = None,
        details: Dict[str, Any] = None,
        original_exception: Exception = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.details = details or {}
        self.original_exception = original_exception
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for API responses and structured logging."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "original_error": str(self.original_exception) if self.original_exception else None
        }


# --- Validation Exceptions ---

class PaymentValidationException(PaymentBaseException):
    """Invalid input data for a payment operation."""

    def __init__(
        self,
        message: str,
        validation_errors: Dict[str, str] = None,
        **kwargs
    ):
        super().__init__(message, error_code="PAYMENT_VALIDATION_ERROR", **kwargs)
        self.validation_errors = validation_errors or {}
        self.details["validation_errors"] = self.validation_errors


# --- Not Found Exceptions ---

class PlanNotFoundException(PaymentBaseException):
    """Requested subscription plan does not exist."""

    def __init__(self, plan_id: str, **kwargs):
        super().__init__(
            message=f"Subscription plan not found: {plan_id}",
            error_code="PLAN_NOT_FOUND",
            details={"plan_id": plan_id},
            **kwargs
        )


class SubscriptionNotFoundException(PaymentBaseException):
    """Requested subscription does not exist."""

    def __init__(self, identifier: str, **kwargs):
        super().__init__(
            message=f"Subscription not found: {identifier}",
            error_code="SUBSCRIPTION_NOT_FOUND",
            details={"identifier": identifier},
            **kwargs
        )


class InvoiceNotFoundException(PaymentBaseException):
    """Requested invoice does not exist."""

    def __init__(self, invoice_id: str, **kwargs):
        super().__init__(
            message=f"Invoice not found: {invoice_id}",
            error_code="INVOICE_NOT_FOUND",
            details={"invoice_id": invoice_id},
            **kwargs
        )


class PaymentNotFoundException(PaymentBaseException):
    """Requested payment/transaction does not exist."""

    def __init__(self, payment_id: str, **kwargs):
        super().__init__(
            message=f"Payment not found: {payment_id}",
            error_code="PAYMENT_NOT_FOUND",
            details={"payment_id": payment_id},
            **kwargs
        )


class PaymentMethodNotFoundException(PaymentBaseException):
    """Requested payment method does not exist."""

    def __init__(self, method_id: str, **kwargs):
        super().__init__(
            message=f"Payment method not found: {method_id}",
            error_code="PAYMENT_METHOD_NOT_FOUND",
            details={"method_id": method_id},
            **kwargs
        )


# --- Provider Exceptions ---

class PaymentProviderException(PaymentBaseException):
    """Base exception for payment provider errors."""

    def __init__(self, provider_name: str, message: str, **kwargs):
        super().__init__(
            message=f"Provider '{provider_name}' error: {message}",
            error_code="PAYMENT_PROVIDER_ERROR",
            details={"provider": provider_name},
            **kwargs
        )


class PaymentProviderNotFoundError(PaymentBaseException):
    """Requested payment provider is not registered."""

    def __init__(self, provider_name: str, **kwargs):
        super().__init__(
            message=f"Payment provider not registered: {provider_name}",
            error_code="PROVIDER_NOT_FOUND",
            details={"provider": provider_name},
            **kwargs
        )


class PaymentProviderConfigError(PaymentBaseException):
    """Payment provider configuration is invalid or missing."""

    def __init__(self, provider_name: str, reason: str, **kwargs):
        super().__init__(
            message=f"Provider '{provider_name}' config error: {reason}",
            error_code="PROVIDER_CONFIG_ERROR",
            details={"provider": provider_name, "reason": reason},
            **kwargs
        )


# --- Business Logic Exceptions ---

class SubscriptionAlreadyExistsException(PaymentBaseException):
    """Organization already has an active subscription."""

    def __init__(self, organization_id: str, **kwargs):
        super().__init__(
            message=f"Organization already has an active subscription: {organization_id}",
            error_code="SUBSCRIPTION_EXISTS",
            details={"organization_id": organization_id},
            **kwargs
        )


class SubscriptionStateException(PaymentBaseException):
    """Subscription cannot transition to the requested state."""

    def __init__(self, subscription_id: str, current_status: str, requested_action: str, **kwargs):
        super().__init__(
            message=f"Cannot {requested_action} subscription {subscription_id} in status '{current_status}'",
            error_code="SUBSCRIPTION_STATE_ERROR",
            details={
                "subscription_id": subscription_id,
                "current_status": current_status,
                "requested_action": requested_action,
            },
            **kwargs
        )


class PaymentFailedException(PaymentBaseException):
    """Payment processing was declined or failed."""

    def __init__(self, reason: str, provider_name: str = None, **kwargs):
        super().__init__(
            message=f"Payment failed: {reason}",
            error_code="PAYMENT_FAILED",
            details={"reason": reason, "provider": provider_name},
            **kwargs
        )


class RefundException(PaymentBaseException):
    """Refund could not be processed."""

    def __init__(self, payment_id: str, reason: str, **kwargs):
        super().__init__(
            message=f"Refund failed for payment {payment_id}: {reason}",
            error_code="REFUND_FAILED",
            details={"payment_id": payment_id, "reason": reason},
            **kwargs
        )


class InvoiceStateException(PaymentBaseException):
    """Invoice cannot transition to the requested state."""

    def __init__(self, invoice_id: str, current_status: str, requested_action: str, **kwargs):
        super().__init__(
            message=f"Cannot {requested_action} invoice {invoice_id} in status '{current_status}'",
            error_code="INVOICE_STATE_ERROR",
            details={
                "invoice_id": invoice_id,
                "current_status": current_status,
                "requested_action": requested_action,
            },
            **kwargs
        )


# --- Database Exceptions ---

class PaymentDatabaseException(PaymentBaseException):
    """Database operation failed in the payment service."""

    def __init__(self, message: str, operation: str = None, **kwargs):
        super().__init__(
            message=f"Payment database error: {message}",
            error_code="PAYMENT_DB_ERROR",
            details={"operation": operation} if operation else {},
            **kwargs
        )


# --- Authorization Exceptions ---

class PaymentAuthorizationException(PaymentBaseException):
    """User lacks permission for the requested payment operation."""

    def __init__(self, message: str = "Insufficient permissions for this payment operation", **kwargs):
        super().__init__(
            message=message,
            error_code="PAYMENT_AUTHORIZATION_ERROR",
            **kwargs
        )


# --- Webhook Exceptions ---

class WebhookVerificationException(PaymentBaseException):
    """Webhook signature verification failed."""

    def __init__(self, provider_name: str, reason: str = "Invalid signature", **kwargs):
        super().__init__(
            message=f"Webhook verification failed for {provider_name}: {reason}",
            error_code="WEBHOOK_VERIFICATION_FAILED",
            details={"provider": provider_name, "reason": reason},
            **kwargs
        )
