"""Recurring invoice template service."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.application.ports.repositories import RecurringInvoiceTemplateRecord
from app.application.services.invoice_service import CreateInvoiceInput, InvoiceItemInput
from app.core.constants import RECURRING_INVOICE_FREQUENCIES
from app.core.errors import NotFoundError
from app.domain.enums import InvoiceStatus


@dataclass
class CreateRecurringTemplateInput:
    customer_id: uuid.UUID
    name: str
    items: list[dict]
    frequency: str = "MONTHLY"
    next_run_date: date | None = None


class RecurringInvoiceService:
    def __init__(self, uow_factory, invoice_service) -> None:
        self._uow_factory = uow_factory
        self._invoice_service = invoice_service

    async def create_template(
        self,
        *,
        company_id: uuid.UUID,
        actor_id: uuid.UUID,
        data: CreateRecurringTemplateInput,
    ) -> dict:
        async with self._uow_factory() as uow:
            customer = await uow.customers.get_by_id(company_id, data.customer_id)
            if not customer:
                raise NotFoundError("Customer not found")
            record = await uow.recurring_templates.create(
                RecurringInvoiceTemplateRecord(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    customer_id=data.customer_id,
                    name=data.name.strip(),
                    items_json=self._normalize_items(data.items),
                    frequency=data.frequency,
                    next_run_date=data.next_run_date or date.today(),
                    created_by=actor_id,
                )
            )
        return self._to_dict(record)

    async def list_templates(self, company_id: uuid.UUID) -> list[dict]:
        async with self._uow_factory() as uow:
            records = await uow.recurring_templates.list_for_company(company_id)
        return [self._to_dict(record) for record in records]

    async def update_template(
        self,
        *,
        company_id: uuid.UUID,
        template_id: uuid.UUID,
        name: str | None = None,
        frequency: str | None = None,
        next_run_date: date | None = None,
        is_active: bool | None = None,
        items: list[dict] | None = None,
    ) -> dict:
        if frequency is not None and frequency not in RECURRING_INVOICE_FREQUENCIES:
            raise ValueError("Invalid frequency")
        async with self._uow_factory() as uow:
            record = await uow.recurring_templates.get_by_id(company_id, template_id)
            if not record:
                raise NotFoundError("Recurring template not found")
            if name is not None:
                record.name = name.strip()
            if frequency is not None:
                record.frequency = frequency
            if next_run_date is not None:
                record.next_run_date = next_run_date
            if is_active is not None:
                record.is_active = is_active
            if items is not None:
                record.items_json = self._normalize_items(items)
            updated = await uow.recurring_templates.update(record)
            await uow.commit()
        return self._to_dict(updated)

    async def run_due_templates(self) -> int:
        today = date.today()
        async with self._uow_factory() as uow:
            templates = await uow.recurring_templates.list_due_templates(today)
        created = 0
        for template in templates:
            items = [
                InvoiceItemInput(
                    description=str(item.get("description", "")),
                    quantity=item.get("quantity", 1),
                    unit_price=item.get("unit_price", 0),
                    gst_rate=item.get("gst_rate", 18),
                    hsn_sac=item.get("hsn_sac"),
                    unit=item.get("unit", "NOS"),
                    product_id=uuid.UUID(item["product_id"]) if item.get("product_id") else None,
                )
                for item in template.items_json
            ]
            await self._invoice_service.create(
                company_id=template.company_id,
                actor_id=template.created_by or template.company_id,
                data=CreateInvoiceInput(
                    customer_id=template.customer_id,
                    issue_date=today,
                    due_date=today + timedelta(days=15),
                    items=items,
                    status=InvoiceStatus.DRAFT,
                ),
            )
            template.last_run_at = datetime.utcnow()
            template.next_run_date = self._next_date(today, template.frequency)
            async with self._uow_factory() as uow:
                await uow.recurring_templates.update(template)
            created += 1
        return created

    @staticmethod
    def _next_date(current: date, frequency: str) -> date:
        if frequency == "WEEKLY":
            return current + timedelta(days=7)
        if frequency == "DAILY":
            return current + timedelta(days=1)
        return current + timedelta(days=30)

    @staticmethod
    def _normalize_items(items: list[dict]) -> list[dict]:
        normalized: list[dict] = []
        for item in items:
            row = dict(item)
            for key in ("quantity", "unit_price", "gst_rate"):
                if key in row and row[key] is not None:
                    row[key] = float(row[key])
            normalized.append(row)
        return normalized

    @staticmethod
    def _to_dict(record: RecurringInvoiceTemplateRecord) -> dict:
        return {
            "id": str(record.id),
            "company_id": str(record.company_id),
            "customer_id": str(record.customer_id),
            "name": record.name,
            "items": record.items_json,
            "frequency": record.frequency,
            "next_run_date": record.next_run_date.isoformat(),
            "is_active": record.is_active,
        }
