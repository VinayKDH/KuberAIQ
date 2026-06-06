"""Dashboard API schemas."""
from __future__ import annotations

from pydantic import BaseModel


class AgingBucket(BaseModel):
    bucket: str
    invoices: int
    outstanding: float


class CashflowPeriod(BaseModel):
    period: str
    expected_inflow: float


class TopCustomer(BaseModel):
    customer_id: str
    name: str
    revenue: float


class DashboardResponse(BaseModel):
    revenue: float
    pending: float
    overdue: float
    aging: list[AgingBucket]
    cashflow: list[CashflowPeriod]
    top_customers: list[TopCustomer]
