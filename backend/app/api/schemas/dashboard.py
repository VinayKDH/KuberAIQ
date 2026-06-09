"""Dashboard API schemas."""
from __future__ import annotations

from pydantic import BaseModel

from app.api.schemas.compliance import ComplianceAlert


class AgingBucket(BaseModel):
    bucket: str
    invoices: int
    outstanding: float


class CashflowPeriod(BaseModel):
    period: str
    expected_inflow: float


class CashflowForecastDay(BaseModel):
    date: str
    expected_inflow: float
    cumulative_balance: float


class CashflowAlert(BaseModel):
    triggered: bool
    projected_minimum: float
    buffer: float
    shortfall_date: str | None = None
    message: str


class TopCustomer(BaseModel):
    customer_id: str
    name: str
    revenue: float


class TopProduct(BaseModel):
    description: str
    revenue: float
    share_pct: float


class DashboardResponse(BaseModel):
    revenue: float
    pending: float
    overdue: float
    aging: list[AgingBucket]
    cashflow: list[CashflowPeriod]
    cashflow_forecast: list[CashflowForecastDay]
    cashflow_alert: CashflowAlert
    compliance_alert: ComplianceAlert | None = None
    top_customers: list[TopCustomer]
    top_products: list[TopProduct]
