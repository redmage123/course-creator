"""
Subscription Lifecycle Endpoints

Business Context:
Organizations subscribe to plans to access platform features. These endpoints
handle creating, upgrading, downgrading, and cancelling subscriptions. Each
organization can have at most one active subscription.
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app_dependencies import (
    get_current_user,
    require_org_admin,
    get_subscription_service,
    verify_org_access,
)
from payment_service.application.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payment/subscriptions", tags=["subscriptions"])


class SubscriptionCreateRequest(BaseModel):
    organization_id: str
    plan_id: str


class SubscriptionUpgradeRequest(BaseModel):
    new_plan_id: str


class SubscriptionCancelRequest(BaseModel):
    reason: Optional[str] = None


@router.post("", status_code=201)
async def create_subscription(
    request: SubscriptionCreateRequest,
    current_user: Dict[str, Any] = Depends(require_org_admin),
    sub_service: SubscriptionService = Depends(get_subscription_service),
) -> Dict[str, Any]:
    """Create a subscription for an organization (org admin)."""
    verify_org_access(current_user, request.organization_id)
    return await sub_service.create_subscription(
        organization_id=request.organization_id,
        plan_id=request.plan_id,
        actor_id=current_user.get("user_id"),
    )


@router.get("/{org_id}")
async def get_org_subscription(
    org_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    sub_service: SubscriptionService = Depends(get_subscription_service),
) -> Dict[str, Any]:
    """Get the active subscription for an organization."""
    verify_org_access(current_user, org_id)
    subscription = await sub_service.get_org_subscription(org_id)
    if not subscription:
        return {"organization_id": org_id, "subscription": None, "message": "No active subscription"}
    return subscription


@router.get("/{org_id}/history")
async def list_org_subscriptions(
    org_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    sub_service: SubscriptionService = Depends(get_subscription_service),
) -> list:
    """List all subscriptions (including historical) for an organization."""
    verify_org_access(current_user, org_id)
    return await sub_service.list_subscriptions(org_id)


@router.put("/{subscription_id}/upgrade")
async def upgrade_subscription(
    subscription_id: str,
    request: SubscriptionUpgradeRequest,
    current_user: Dict[str, Any] = Depends(require_org_admin),
    sub_service: SubscriptionService = Depends(get_subscription_service),
) -> Dict[str, Any]:
    """Upgrade or downgrade a subscription to a different plan."""
    return await sub_service.upgrade_subscription(
        subscription_id=subscription_id,
        new_plan_id=request.new_plan_id,
        actor_id=current_user.get("user_id"),
    )


@router.delete("/{subscription_id}")
async def cancel_subscription(
    subscription_id: str,
    request: Optional[SubscriptionCancelRequest] = None,
    current_user: Dict[str, Any] = Depends(require_org_admin),
    sub_service: SubscriptionService = Depends(get_subscription_service),
) -> Dict[str, Any]:
    """Cancel an active subscription."""
    reason = request.reason if request else None
    return await sub_service.cancel_subscription(
        subscription_id=subscription_id,
        reason=reason,
        actor_id=current_user.get("user_id"),
    )
