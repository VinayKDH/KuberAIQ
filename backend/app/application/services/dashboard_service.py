"""Dashboard use-case orchestration."""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date
from decimal import Decimal

from app.core.constants import AGING_BUCKETS
from app.domain.enums import InvoiceStatus


class DashboardService:
    def __init__(self, uow_factory) -> None:
        self._uow_factory = uow_factory

    async def summary(
        self, company_id: uuid.UUID, from_date: date, to_date: date
    ) -> dict:
        async with self._uow_factory() as uow:
            invoices, _ = await uow.invoices.search(
                company_id, from_date=from_date, to_date=to_date, page=1, page_size=10000
            )
            today = date.today()
            revenue = Decimal("0")
            pending = Decimal("0")
            overdue = Decimal("0")
            aging: dict[str, dict] = {
                b: {"bucket": b, "invoices": 0, "outstanding": Decimal("0")} for b in AGING_BUCKETS
            }
            customer_revenue: dict[uuid.UUID, Decimal] = defaultdict(lambda: Decimal("0"))
            customer_names: dict[uuid.UUID, str] = {}

            for inv in invoices:
                if inv.status == InvoiceStatus.CANCELLED:
                    continue
                if inv.status == InvoiceStatus.PAID:
                    revenue += inv.grand_total.amount
                customer_revenue[inv.customer_id] += inv.amount_paid.amount
                cust = await uow.customers.get_by_id(company_id, inv.customer_id)
                if cust:
                    customer_names[inv.customer_id] = cust.name

                if inv.status == InvoiceStatus.ISSUED and inv.due_date >= today:
                    pending += inv.amount_due.amount
                if inv.status in {InvoiceStatus.OVERDUE, InvoiceStatus.PARTIALLY_PAID} and inv.amount_due.amount > 0:
                    if inv.due_date < today:
                        overdue += inv.amount_due.amount
                    days = (today - inv.due_date).days
                    bucket = "90+" if days > 90 else "61-90" if days > 60 else "31-60" if days > 30 else "0-30"
                    aging[bucket]["invoices"] += 1
                    aging[bucket]["outstanding"] += inv.amount_due.amount

            cashflow = await self._expected_cashflow(uow, company_id)
            top_customers = sorted(
                [
                    {
                        "customer_id": str(cid),
                        "name": customer_names.get(cid, "Unknown"),
                        "revenue": float(amt),
                    }
                    for cid, amt in customer_revenue.items()
                ],
                key=lambda x: x["revenue"],
                reverse=True,
            )[:5]

            return {
                "revenue": float(revenue),
                "pending": float(pending),
                "overdue": float(overdue),
                "aging": [
                    {
                        "bucket": b["bucket"],
                        "invoices": b["invoices"],
                        "outstanding": float(b["outstanding"]),
                    }
                    for b in aging.values()
                ],
                "cashflow": cashflow,
                "top_customers": top_customers,
            }

    async def _expected_cashflow(self, uow, company_id: uuid.UUID) -> list[dict]:
        invoices, _ = await uow.invoices.search(
            company_id,
            status=InvoiceStatus.ISSUED,
            page=1,
            page_size=10000,
        )
        partial, _ = await uow.invoices.search(
            company_id,
            status=InvoiceStatus.PARTIALLY_PAID,
            page=1,
            page_size=10000,
        )
        invoices.extend(partial)
        by_month: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for inv in invoices:
            if inv.amount_due.is_zero:
                continue
            period = inv.due_date.strftime("%Y-%m")
            by_month[period] += inv.amount_due.amount
        return [
            {"period": period, "expected_inflow": float(amount)}
            for period, amount in sorted(by_month.items())
        ]
