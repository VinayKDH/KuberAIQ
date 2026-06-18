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

    async def find_product(self, company_id: uuid.UUID, query: str):
        product_svc = self._services.get("product")
        if not product_svc or not query:
            return None
        products, _ = await product_svc.search(company_id, query, 1, 1)
        return products[0] if products else None

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

    async def create_customer_and_invoice(
        self, company_id: uuid.UUID, user_id: uuid.UUID, preview: dict
    ) -> dict:
        customer_data = preview["customer"]
        customer = await self.create_customer(company_id, user_id, customer_data)
        invoice_preview = {
            "customer_id": customer["customer_id"],
            "customer_name": customer["name"],
            **preview["invoice"],
        }
        invoice = await self.create_invoice(company_id, user_id, invoice_preview)
        return {
            "customer_id": customer["customer_id"],
            "customer_name": customer["name"],
            "invoice_id": invoice["invoice_id"],
            "invoice_number": invoice["invoice_number"],
            "grand_total": invoice["grand_total"],
        }

    async def list_overdue(self, company_id: uuid.UUID) -> list[dict]:
        collection = self._services["collection"]
        return await collection.list_overdue(company_id)

    async def bulk_reminder_preview(self, company_id: uuid.UUID) -> dict:
        collection = self._services["collection"]
        preview = await collection.bulk_preview(company_id)
        return {
            "count": preview["count"],
            "total_outstanding": float(preview["total_outstanding"]),
        }

    async def bulk_send_reminders(
        self, company_id: uuid.UUID, user_id: uuid.UUID
    ) -> list:
        collection = self._services["collection"]
        return await collection.bulk_send(
            company_id=company_id,
            actor_id=user_id,
        )

    async def get_dashboard_summary(self, company_id: uuid.UUID) -> dict:
        from datetime import date

        dashboard = self._services["dashboard"]
        today = date.today()
        from_date = date(today.year, 4, 1) if today.month >= 4 else date(today.year - 1, 4, 1)
        return await dashboard.summary(company_id, from_date, today)
