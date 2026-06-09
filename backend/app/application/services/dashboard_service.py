"""Dashboard use-case orchestration."""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from app.core.constants import (
    AGING_BUCKETS,
    CASHFLOW_BUFFER_DEFAULT,
    CASHFLOW_FORECAST_DAYS,
    TOP_CUSTOMERS_LIMIT,
    TOP_PRODUCTS_LIMIT,
)
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
            product_revenue: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

            for inv in invoices:
                if inv.status == InvoiceStatus.CANCELLED:
                    continue
                if inv.status == InvoiceStatus.PAID:
                    revenue += inv.grand_total.amount
                customer_revenue[inv.customer_id] += inv.amount_paid.amount
                cust = await uow.customers.get_by_id(company_id, inv.customer_id)
                if cust:
                    customer_names[inv.customer_id] = cust.name

                for item in inv.items:
                    product_revenue[item.description] += item.line_total.amount

                if inv.status == InvoiceStatus.ISSUED and inv.due_date >= today:
                    pending += inv.amount_due.amount
                if inv.status in {InvoiceStatus.OVERDUE, InvoiceStatus.PARTIALLY_PAID} and inv.amount_due.amount > 0:
                    if inv.due_date < today:
                        overdue += inv.amount_due.amount
                    days = (today - inv.due_date).days
                    bucket = "90+" if days > 90 else "61-90" if days > 60 else "31-60" if days > 30 else "0-30"
                    aging[bucket]["invoices"] += 1
                    aging[bucket]["outstanding"] += inv.amount_due.amount

            open_invoices = await self._open_receivables(uow, company_id)
            cashflow = self._monthly_cashflow(open_invoices)
            forecast, alert = self._cashflow_forecast(open_invoices, today)

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
            )[:TOP_CUSTOMERS_LIMIT]

            top_products = sorted(
                [
                    {"description": desc, "revenue": float(amt), "share_pct": 0.0}
                    for desc, amt in product_revenue.items()
                ],
                key=lambda x: x["revenue"],
                reverse=True,
            )[:TOP_PRODUCTS_LIMIT]
            product_total = sum(p["revenue"] for p in top_products) or 1.0
            for product in top_products:
                product["share_pct"] = round(product["revenue"] / product_total * 100, 1)

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
                "cashflow_forecast": forecast,
                "cashflow_alert": alert,
                "top_customers": top_customers,
                "top_products": top_products,
            }

    async def _open_receivables(self, uow, company_id: uuid.UUID):
        invoices: list = []
        for status in (
            InvoiceStatus.ISSUED,
            InvoiceStatus.PARTIALLY_PAID,
            InvoiceStatus.OVERDUE,
        ):
            batch, _ = await uow.invoices.search(
                company_id, status=status, page=1, page_size=10000
            )
            invoices.extend(batch)
        return [inv for inv in invoices if not inv.amount_due.is_zero]

    def _monthly_cashflow(self, invoices) -> list[dict]:
        by_month: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for inv in invoices:
            period = inv.due_date.strftime("%Y-%m")
            by_month[period] += inv.amount_due.amount
        return [
            {"period": period, "expected_inflow": float(amount)}
            for period, amount in sorted(by_month.items())
        ]

    def _cashflow_forecast(self, invoices, today: date) -> tuple[list[dict], dict]:
        inflows_by_day: dict[date, Decimal] = defaultdict(lambda: Decimal("0"))
        overdue_total = Decimal("0")
        for inv in invoices:
            if inv.due_date < today:
                overdue_total += inv.amount_due.amount
            elif inv.due_date <= today + timedelta(days=CASHFLOW_FORECAST_DAYS):
                inflows_by_day[inv.due_date] += inv.amount_due.amount

        forecast: list[dict] = []
        running = overdue_total
        min_balance = running
        shortfall_date: date | None = None

        for offset in range(CASHFLOW_FORECAST_DAYS + 1):
            day = today + timedelta(days=offset)
            inflow = inflows_by_day.get(day, Decimal("0"))
            running += inflow
            if running < min_balance:
                min_balance = running
                if min_balance < CASHFLOW_BUFFER_DEFAULT:
                    shortfall_date = day
            forecast.append(
                {
                    "date": day.isoformat(),
                    "expected_inflow": float(inflow),
                    "cumulative_balance": float(running),
                }
            )

        triggered = min_balance < CASHFLOW_BUFFER_DEFAULT
        return forecast, {
            "triggered": triggered,
            "projected_minimum": float(min_balance),
            "buffer": float(CASHFLOW_BUFFER_DEFAULT),
            "shortfall_date": shortfall_date.isoformat() if shortfall_date else None,
            "message": (
                f"Projected receivables may fall below ₹{CASHFLOW_BUFFER_DEFAULT:,.0f} "
                f"around {shortfall_date.strftime('%d %b')}. Review collections."
                if triggered and shortfall_date
                else "Receivables outlook is above your buffer for the next 30 days."
            ),
        }
