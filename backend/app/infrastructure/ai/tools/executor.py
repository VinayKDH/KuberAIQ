"""Typed tool executor — validates and calls application services."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from app.application.services.customer_service import CreateCustomerInput
from app.application.services.invoice_service import CreateInvoiceInput, InvoiceItemInput
from app.domain.enums import InvoiceStatus


class ToolExecutor:
    def __init__(self, services: dict) -> None:
        self._services = services

    async def find_customer(self, company_id: uuid.UUID, query: str) -> list:
        customer_svc = self._services["customer"]
        return (await customer_svc.search(company_id, query, 1, 5))[0]

    async def create_invoice(
        self, company_id: uuid.UUID, user_id: uuid.UUID, preview: dict
    ) -> dict:
        invoice_svc = self._services["invoice"]
        items = [
            InvoiceItemInput(
                description=i["description"],
                quantity=i["quantity"] if isinstance(i["quantity"], Decimal) else Decimal(str(i["quantity"])),
                unit_price=i["unit_price"] if isinstance(i["unit_price"], Decimal) else Decimal(str(i["unit_price"])),
                gst_rate=i["gst_rate"] if isinstance(i["gst_rate"], Decimal) else Decimal(str(i["gst_rate"])),
                hsn_sac=i.get("hsn_sac"),
                unit=i.get("unit", "NOS"),
            )
            for i in preview["items"]
        ]
        status = InvoiceStatus(preview.get("status", "ISSUED"))
        invoice = await invoice_svc.create(
            company_id=company_id,
            actor_id=user_id,
            data=CreateInvoiceInput(
                customer_id=uuid.UUID(preview["customer_id"]),
                issue_date=preview["issue_date"] if isinstance(preview["issue_date"], date) else date.fromisoformat(str(preview["issue_date"])),
                due_date=preview["due_date"] if isinstance(preview["due_date"], date) else date.fromisoformat(str(preview["due_date"])),
                items=items,
                status=status,
            ),
        )
        return {
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "grand_total": float(invoice.grand_total.amount),
        }

    async def create_customer(
        self, company_id: uuid.UUID, user_id: uuid.UUID, data: dict
    ) -> dict:
        customer_svc = self._services["customer"]
        customer = await customer_svc.create(
            company_id=company_id,
            actor_id=user_id,
            data=CreateCustomerInput(
                name=data["name"],
                phone=data["phone"],
                gstin=data.get("gstin"),
                billing_address=data.get("billing_address"),
            ),
        )
        return {"customer_id": str(customer.id), "name": customer.name}
