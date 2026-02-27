"""
FastAPI Dependencies for Payment Service

Business Context:
Provides dependency injection functions for FastAPI endpoints. All service
instances are resolved through the DI container. Authentication dependencies
follow the platform-wide pattern (HTTPBearer + user-management validation).
"""

import logging
from typing import Dict, Any, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from payment_service.infrastructure.container import get_container
from payment_service.application.services.payment_orchestrator import PaymentOrchestrator
from payment_service.application.services.subscription_service import SubscriptionService
from payment_service.application.services.invoice_service import InvoiceService
from payment_service.application.services.billing_service import BillingService
from payment_service.data_access.payment_dao import PaymentDAO
from auth.jwt_auth import JWTAuthenticator

logger = logging.getLogger(__name__)

security = HTTPBearer()


def get_config():
    """Get current Hydra configuration."""
    from main import current_config
    return current_config


# --- Authentication Dependencies ---

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Validate JWT and return the authenticated user."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    config = get_config()
    authenticator = JWTAuthenticator(config)
    return await authenticator.validate_token(credentials.credentials)


async def get_optional_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Return the authenticated user if a token is present, otherwise None."""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    try:
        config = get_config()
        authenticator = JWTAuthenticator(config)
        return await authenticator.validate_token(token)
    except Exception:
        return None


# --- Authorization Dependencies ---

async def require_site_admin(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Require site admin role (for plan management)."""
    role = current_user.get("role") or current_user.get("role_type")
    username = current_user.get("username")
    if role == "site_admin" or username == "admin":
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Site administrator access required",
    )


async def require_org_admin(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Require organization admin role or higher."""
    username = current_user.get("username")
    if username == "admin":
        return current_user
    user_roles = current_user.get("roles", [])
    allowed_roles = ["org_admin", "organization_admin", "admin", "site_admin"]
    if any(role in allowed_roles for role in user_roles):
        return current_user
    role = current_user.get("role", "")
    if role in allowed_roles:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Organization administrator access required",
    )


def verify_org_access(user: Dict[str, Any], organization_id: str) -> bool:
    """Check that the user can access the specified organization."""
    if user.get("username") == "admin":
        return True
    user_org = user.get("organization_id") or user.get("organization")
    if str(user_org) == str(organization_id):
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied for this organization",
    )


# --- Service Dependencies ---

async def get_payment_orchestrator() -> PaymentOrchestrator:
    """Get payment orchestrator service."""
    container = get_container()
    return await container.get_payment_orchestrator()


async def get_subscription_service() -> SubscriptionService:
    """Get subscription service."""
    container = get_container()
    return await container.get_subscription_service()


async def get_invoice_service() -> InvoiceService:
    """Get invoice service."""
    container = get_container()
    return await container.get_invoice_service()


async def get_billing_service() -> BillingService:
    """Get billing service."""
    container = get_container()
    return await container.get_billing_service()


async def get_dao() -> PaymentDAO:
    """Get payment DAO for direct data access."""
    container = get_container()
    return await container.get_dao()
