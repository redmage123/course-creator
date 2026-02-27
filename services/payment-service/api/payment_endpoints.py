"""
Payment/Transaction Endpoints

Business Context:
Handles one-time payments (checkout), refunds, and payment method management.
Payments are processed through the provider resolved for the organization.
Payment methods (credit cards, etc.) are tokenized and stored for future use.
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app_dependencies import (
    get_current_user,
    require_org_admin,
    get_payment_orchestrator,
    get_dao,
    verify_org_access,
)
from payment_service.application.services.payment_orchestrator import PaymentOrchestrator
from payment_service.data_access.payment_dao import PaymentDAO

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payment", tags=["payments"])


# --- Request Models ---

class CheckoutRequest(BaseModel):
    organization_id: str
    amount_cents: int = Field(..., gt=0)
    currency: str = Field("USD", pattern=r"^[A-Z]{3}$")
    invoice_id: Optional[str] = None
    payment_method_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RefundRequest(BaseModel):
    amount_cents: Optional[int] = Field(None, gt=0)


class PaymentMethodCreateRequest(BaseModel):
    organization_id: str
    method_type: str = Field("credit_card")
    provider_token: Optional[str] = None
    label: Optional[str] = None
    last_four: Optional[str] = Field(None, min_length=4, max_length=4)
    expiry_month: Optional[int] = Field(None, ge=1, le=12)
    expiry_year: Optional[int] = Field(None, ge=2024)
    is_default: bool = False


# --- Payment Endpoints ---

@router.post("/payments/checkout", status_code=201)
async def create_payment(
    request: CheckoutRequest,
    current_user: Dict[str, Any] = Depends(require_org_admin),
    orchestrator: PaymentOrchestrator = Depends(get_payment_orchestrator),
) -> Dict[str, Any]:
    """Process a one-time payment for an organization."""
    verify_org_access(current_user, request.organization_id)
    return await orchestrator.create_payment(
        organization_id=request.organization_id,
        amount_cents=request.amount_cents,
        currency=request.currency,
        invoice_id=request.invoice_id,
        payment_method_id=request.payment_method_id,
        metadata=request.metadata,
        actor_id=current_user.get("user_id"),
    )


@router.post("/payments/{transaction_id}/refund")
async def refund_payment(
    transaction_id: str,
    request: Optional[RefundRequest] = None,
    current_user: Dict[str, Any] = Depends(require_org_admin),
    orchestrator: PaymentOrchestrator = Depends(get_payment_orchestrator),
) -> Dict[str, Any]:
    """Refund a completed payment (full or partial)."""
    amount_cents = request.amount_cents if request else None
    return await orchestrator.refund_payment(
        transaction_id=transaction_id,
        amount_cents=amount_cents,
        actor_id=current_user.get("user_id"),
    )


@router.get("/payments/{org_id}")
async def list_payments(
    org_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    orchestrator: PaymentOrchestrator = Depends(get_payment_orchestrator),
) -> List[Dict[str, Any]]:
    """List payment transactions for an organization."""
    verify_org_access(current_user, org_id)
    return await orchestrator.list_transactions(org_id, limit=limit, offset=offset)


@router.get("/payments/detail/{transaction_id}")
async def get_payment(
    transaction_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    orchestrator: PaymentOrchestrator = Depends(get_payment_orchestrator),
) -> Dict[str, Any]:
    """Get details of a specific payment transaction."""
    return await orchestrator.get_transaction(transaction_id)


# --- Payment Method Endpoints ---

@router.post("/payment-methods", status_code=201)
async def create_payment_method(
    request: PaymentMethodCreateRequest,
    current_user: Dict[str, Any] = Depends(require_org_admin),
    dao: PaymentDAO = Depends(get_dao),
) -> Dict[str, Any]:
    """Store a new payment method for an organization."""
    verify_org_access(current_user, request.organization_id)
    method_data = {
        "id": str(uuid4()),
        "organization_id": request.organization_id,
        "method_type": request.method_type,
        "provider_name": "null",
        "provider_token": request.provider_token,
        "label": request.label,
        "last_four": request.last_four,
        "expiry_month": request.expiry_month,
        "expiry_year": request.expiry_year,
        "is_default": request.is_default,
    }
    method_id = await dao.create_payment_method(method_data)
    if request.is_default:
        await dao.set_default_payment_method(request.organization_id, method_id)
    return await dao.get_payment_method_by_id(method_id)


@router.get("/payment-methods/{org_id}")
async def list_payment_methods(
    org_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    dao: PaymentDAO = Depends(get_dao),
) -> List[Dict[str, Any]]:
    """List active payment methods for an organization."""
    verify_org_access(current_user, org_id)
    return await dao.list_payment_methods_for_org(org_id)


@router.delete("/payment-methods/{method_id}", status_code=204)
async def delete_payment_method(
    method_id: str,
    current_user: Dict[str, Any] = Depends(require_org_admin),
    dao: PaymentDAO = Depends(get_dao),
):
    """Deactivate (soft-delete) a payment method."""
    await dao.deactivate_payment_method(method_id)
