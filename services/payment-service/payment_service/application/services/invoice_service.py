"""
Invoice Service — generates and manages billing invoices.

Business Context:
Invoices are created either automatically from subscription billing cycles or
manually for one-time charges. Each invoice contains line items describing what
was billed. When a payment succeeds against an invoice, it's marked as paid.
Invoices provide the financial audit trail for organizations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import uuid4

from payment_service.data_access.payment_dao import PaymentDAO
from payment_service.exceptions import (
    InvoiceNotFoundException,
    InvoiceStateException,
    PaymentValidationException,
)

logger = logging.getLogger(__name__)


class InvoiceService:
    """Manages invoice creation, status transitions, and line items."""

    def __init__(self, dao: PaymentDAO):
        self._dao = dao

    async def create_invoice(
        self,
        organization_id: str,
        amount_cents: int,
        currency: str = "USD",
        subscription_id: Optional[str] = None,
        line_items: Optional[List[Dict[str, Any]]] = None,
        due_days: int = 30,
        actor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new invoice for an organization.

        The invoice starts in DRAFT status. Call issue_invoice() to send it.
        Line items are created as separate records linked to the invoice.
        """
        invoice_id = str(uuid4())
        now = datetime.utcnow()
        invoice_number = f"INV-{now.strftime('%Y%m')}-{uuid4().hex[:8].upper()}"

        invoice_data = {
            "id": invoice_id,
            "organization_id": organization_id,
            "subscription_id": subscription_id,
            "invoice_number": invoice_number,
            "amount_cents": amount_cents,
            "currency": currency,
            "status": "draft",
            "due_at": now + timedelta(days=due_days),
        }
        await self._dao.create_invoice(invoice_data)

        if line_items:
            for item in line_items:
                item_data = {
                    "id": str(uuid4()),
                    "invoice_id": invoice_id,
                    "description": item.get("description", ""),
                    "quantity": item.get("quantity", 1),
                    "unit_price_cents": item.get("unit_price_cents", 0),
                    "amount_cents": item.get("amount_cents", item.get("quantity", 1) * item.get("unit_price_cents", 0)),
                }
                await self._dao.create_line_item(item_data)

        await self._dao.create_audit_entry({
            "entity_type": "invoice",
            "entity_id": invoice_id,
            "action": "created",
            "actor_id": actor_id,
            "organization_id": organization_id,
            "new_values": {"invoice_number": invoice_number, "amount_cents": amount_cents},
        })

        logger.info(f"Invoice created: {invoice_number} org={organization_id} amount={amount_cents}")
        return await self._dao.get_invoice_by_id(invoice_id)

    async def issue_invoice(
        self, invoice_id: str, actor_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transition invoice from DRAFT to ISSUED."""
        invoice = await self._dao.get_invoice_by_id(invoice_id)
        if not invoice:
            raise InvoiceNotFoundException(invoice_id)

        if invoice["status"] != "draft":
            raise InvoiceStateException(invoice_id, invoice["status"], "issue")

        now = datetime.utcnow()
        await self._dao.update_invoice_status(invoice_id, "issued")

        await self._dao.create_audit_entry({
            "entity_type": "invoice",
            "entity_id": invoice_id,
            "action": "issued",
            "actor_id": actor_id,
            "organization_id": str(invoice["organization_id"]),
            "old_values": {"status": "draft"},
            "new_values": {"status": "issued", "issued_at": now.isoformat()},
        })

        return await self._dao.get_invoice_by_id(invoice_id)

    async def mark_paid(
        self, invoice_id: str, actor_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mark an invoice as paid."""
        invoice = await self._dao.get_invoice_by_id(invoice_id)
        if not invoice:
            raise InvoiceNotFoundException(invoice_id)

        if invoice["status"] not in ("issued", "overdue"):
            raise InvoiceStateException(invoice_id, invoice["status"], "mark_paid")

        now = datetime.utcnow()
        await self._dao.update_invoice_status(invoice_id, "paid", paid_at=now)

        await self._dao.create_audit_entry({
            "entity_type": "invoice",
            "entity_id": invoice_id,
            "action": "paid",
            "actor_id": actor_id,
            "organization_id": str(invoice["organization_id"]),
            "old_values": {"status": invoice["status"]},
            "new_values": {"status": "paid", "paid_at": now.isoformat()},
        })

        logger.info(f"Invoice paid: {invoice_id}")
        return await self._dao.get_invoice_by_id(invoice_id)

    async def void_invoice(
        self, invoice_id: str, actor_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Void a paid invoice (e.g., after full refund)."""
        invoice = await self._dao.get_invoice_by_id(invoice_id)
        if not invoice:
            raise InvoiceNotFoundException(invoice_id)

        if invoice["status"] != "paid":
            raise InvoiceStateException(invoice_id, invoice["status"], "void")

        await self._dao.update_invoice_status(invoice_id, "void")

        await self._dao.create_audit_entry({
            "entity_type": "invoice",
            "entity_id": invoice_id,
            "action": "voided",
            "actor_id": actor_id,
            "organization_id": str(invoice["organization_id"]),
            "old_values": {"status": "paid"},
            "new_values": {"status": "void"},
        })

        return await self._dao.get_invoice_by_id(invoice_id)

    async def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Retrieve a single invoice with its line items."""
        invoice = await self._dao.get_invoice_by_id(invoice_id)
        if not invoice:
            raise InvoiceNotFoundException(invoice_id)
        invoice["line_items"] = await self._dao.get_line_items_for_invoice(invoice_id)
        return invoice

    async def list_invoices(
        self, organization_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List invoices for an organization."""
        return await self._dao.list_invoices_for_org(organization_id, limit, offset)

    async def generate_subscription_invoice(
        self,
        subscription_id: str,
        organization_id: str,
        plan_name: str,
        amount_cents: int,
        currency: str = "USD",
        actor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate an invoice from a subscription billing cycle.

        Creates the invoice with a single line item for the plan charge,
        then immediately issues it.
        """
        line_items = [
            {
                "description": f"Subscription: {plan_name}",
                "quantity": 1,
                "unit_price_cents": amount_cents,
                "amount_cents": amount_cents,
            }
        ]
        invoice = await self.create_invoice(
            organization_id=organization_id,
            amount_cents=amount_cents,
            currency=currency,
            subscription_id=subscription_id,
            line_items=line_items,
            actor_id=actor_id,
        )
        return await self.issue_invoice(str(invoice["id"]), actor_id=actor_id)
