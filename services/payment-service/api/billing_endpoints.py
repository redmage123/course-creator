"""
Billing Summary Endpoints

Business Context:
Provides the billing overview for organization admins. The billing summary
powers the account status section of the org admin dashboard, showing current
plan, subscription status, recent invoices, payment history, and stored
payment methods at a glance.
"""

import logging
from typing import Dict, Any, List

from fastapi import APIRouter, Depends

from app_dependencies import (
    get_current_user,
    get_billing_service,
    verify_org_access,
)
from payment_service.application.services.billing_service import BillingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payment/billing", tags=["billing"])


@router.get("/{org_id}/summary")
async def get_billing_summary(
    org_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    billing_service: BillingService = Depends(get_billing_service),
) -> Dict[str, Any]:
    """
    Get the comprehensive billing summary for an organization.

    Returns: current plan, subscription status, recent invoices,
    recent payments, stored payment methods, and account health.
    This is the primary endpoint for the org admin billing dashboard.
    """
    verify_org_access(current_user, org_id)
    return await billing_service.get_billing_summary(org_id)


@router.get("/{org_id}/history")
async def get_payment_history(
    org_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user),
    billing_service: BillingService = Depends(get_billing_service),
) -> List[Dict[str, Any]]:
    """Get the full payment history for an organization."""
    verify_org_access(current_user, org_id)
    return await billing_service.get_payment_history(org_id, limit=limit, offset=offset)
