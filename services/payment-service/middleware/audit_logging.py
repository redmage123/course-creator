"""
Payment Audit Logging Middleware

Business Context:
Logs all payment API requests for compliance and debugging. Financial operations
require detailed audit trails. This middleware captures request metadata (method,
path, user, org) without logging sensitive data (card numbers, tokens).
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("payment.audit")


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Logs payment API request metadata for audit compliance."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        method = request.method
        path = request.url.path

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000
        status_code = response.status_code

        log_data = {
            "method": method,
            "path": path,
            "status": status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": request.client.host if request.client else "unknown",
        }

        if status_code >= 500:
            logger.error("Payment API request failed", extra=log_data)
        elif status_code >= 400:
            logger.warning("Payment API client error", extra=log_data)
        else:
            logger.info("Payment API request", extra=log_data)

        return response
