"""
Payment Error Handling Middleware

Business Context:
Maps payment exception types to appropriate HTTP status codes and structured
error responses. This ensures consistent error formatting across all payment
endpoints without duplicating error handling logic in each endpoint.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from payment_service.exceptions import (
    PaymentBaseException,
    PaymentValidationException,
    PaymentAuthorizationException,
    PlanNotFoundException,
    SubscriptionNotFoundException,
    InvoiceNotFoundException,
    PaymentNotFoundException,
    PaymentMethodNotFoundException,
    PaymentProviderException,
    PaymentProviderNotFoundError,
    PaymentProviderConfigError,
    SubscriptionAlreadyExistsException,
    SubscriptionStateException,
    InvoiceStateException,
    PaymentFailedException,
    RefundException,
    PaymentDatabaseException,
    WebhookVerificationException,
)

EXCEPTION_STATUS_MAPPING = {
    PaymentValidationException: 400,
    PaymentAuthorizationException: 403,
    PlanNotFoundException: 404,
    SubscriptionNotFoundException: 404,
    InvoiceNotFoundException: 404,
    PaymentNotFoundException: 404,
    PaymentMethodNotFoundException: 404,
    SubscriptionAlreadyExistsException: 409,
    SubscriptionStateException: 409,
    InvoiceStateException: 409,
    PaymentFailedException: 402,
    RefundException: 422,
    PaymentProviderNotFoundError: 404,
    PaymentProviderConfigError: 500,
    PaymentProviderException: 502,
    WebhookVerificationException: 400,
    PaymentDatabaseException: 500,
}


async def payment_exception_handler(request: Request, exc: PaymentBaseException) -> JSONResponse:
    """Map PaymentBaseException subclasses to HTTP error responses."""
    status_code = next(
        (code for exc_type, code in EXCEPTION_STATUS_MAPPING.items() if isinstance(exc, exc_type)),
        500,
    )
    response_data = exc.to_dict()
    response_data["path"] = str(request.url)
    return JSONResponse(status_code=status_code, content=response_data)
