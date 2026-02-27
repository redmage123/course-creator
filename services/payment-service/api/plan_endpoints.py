"""
Subscription Plan Management Endpoints (Site Admin)

Business Context:
Site administrators manage the available subscription plans (Free, Pro, Enterprise).
Plans define pricing, features, and billing intervals. Changes to plans do not
retroactively affect existing subscriptions.
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app_dependencies import (
    require_site_admin,
    get_dao,
    get_billing_service,
)
from payment_service.data_access.payment_dao import PaymentDAO
from payment_service.application.services.billing_service import BillingService
from payment_service.exceptions import PlanNotFoundException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payment/plans", tags=["plans"])


class PlanCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=1000)
    price_cents: int = Field(0, ge=0)
    currency: str = Field("USD", pattern=r"^[A-Z]{3}$")
    billing_interval: str = Field("monthly")
    features: Dict[str, Any] = Field(default_factory=dict)
    trial_days: int = Field(0, ge=0)
    sort_order: int = Field(0, ge=0)


class PlanUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    price_cents: Optional[int] = Field(None, ge=0)
    currency: Optional[str] = Field(None, pattern=r"^[A-Z]{3}$")
    billing_interval: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
    trial_days: Optional[int] = Field(None, ge=0)
    sort_order: Optional[int] = Field(None, ge=0)


@router.get("")
async def list_plans(
    billing_service: BillingService = Depends(get_billing_service),
) -> List[Dict[str, Any]]:
    """List all active subscription plans (public)."""
    return await billing_service.get_available_plans()


@router.get("/{plan_id}")
async def get_plan(
    plan_id: UUID,
    dao: PaymentDAO = Depends(get_dao),
) -> Dict[str, Any]:
    """Get a specific plan by ID."""
    plan = await dao.get_plan_by_id(str(plan_id))
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("", status_code=201)
async def create_plan(
    request: PlanCreateRequest,
    current_user: Dict[str, Any] = Depends(require_site_admin),
    dao: PaymentDAO = Depends(get_dao),
) -> Dict[str, Any]:
    """Create a new subscription plan (site admin only)."""
    plan_data = {
        "id": str(uuid4()),
        "name": request.name,
        "description": request.description,
        "price_cents": request.price_cents,
        "currency": request.currency,
        "billing_interval": request.billing_interval,
        "features": request.features,
        "trial_days": request.trial_days,
        "sort_order": request.sort_order,
        "provider_name": "null",
    }
    plan_id = await dao.create_plan(plan_data)
    return await dao.get_plan_by_id(plan_id)


@router.put("/{plan_id}")
async def update_plan(
    plan_id: UUID,
    request: PlanUpdateRequest,
    current_user: Dict[str, Any] = Depends(require_site_admin),
    dao: PaymentDAO = Depends(get_dao),
) -> Dict[str, Any]:
    """Update an existing plan (site admin only)."""
    existing = await dao.get_plan_by_id(str(plan_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Plan not found")

    updates = {k: v for k, v in request.dict(exclude_unset=True).items() if v is not None}
    if not updates:
        return existing

    return await dao.update_plan(str(plan_id), updates)


@router.delete("/{plan_id}", status_code=204)
async def deactivate_plan(
    plan_id: UUID,
    current_user: Dict[str, Any] = Depends(require_site_admin),
    dao: PaymentDAO = Depends(get_dao),
):
    """Deactivate a plan (site admin only). Existing subscriptions continue."""
    existing = await dao.get_plan_by_id(str(plan_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Plan not found")
    await dao.deactivate_plan(str(plan_id))
