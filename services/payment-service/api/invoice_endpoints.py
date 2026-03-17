"""
Invoice Endpoints

Business Context:
Invoices represent billing documents generated for organizations. Org admins
can view their invoice history and individual invoice details. Invoice creation
is typically handled by the subscription service during billing cycles.
"""

import logging
from typing import Dict, Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app_dependencies import (
    get_current_user,
    get_invoice_service,
    verify_org_access,
)
from payment_service.application.services.invoice_service import InvoiceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payment/invoices", tags=["invoices"])


@router.get("/{org_id}")
async def list_invoices(
    org_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    invoice_service: InvoiceService = Depends(get_invoice_service),
) -> List[Dict[str, Any]]:
    """List invoices for an organization."""
    verify_org_access(current_user, org_id)
    return await invoice_service.list_invoices(org_id, limit=limit, offset=offset)


@router.get("/detail/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    invoice_service: InvoiceService = Depends(get_invoice_service),
) -> Dict[str, Any]:
    """Get a single invoice with line items."""
    invoice = await invoice_service.get_invoice(invoice_id)
    verify_org_access(current_user, str(invoice["organization_id"]))
    return invoice
