"""Payment API schemas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.domain.enums import PaymentMethod


class RecordPaymentRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    paid_on: date
    method: PaymentMethod = PaymentMethod.CASH
    reference: str | None = None
    note: str | None = None


class PaymentResponse(BaseModel):
    id: str
    invoice_id: str
    amount: Decimal
    paid_on: date
    method: PaymentMethod
    reference: str | None = None
    note: str | None = None


class RecentPaymentSummary(BaseModel):
    id: str
    invoice_id: str
    invoice_number: str | None = None
    amount: float
    paid_on: str
    method: str


class CollectionSummaryResponse(BaseModel):
    collected_today: float
    recent_payments: list[RecentPaymentSummary]


class PaymentMethodBreakdown(BaseModel):
    method: str
    amount: float


class PaymentAnalyticsResponse(BaseModel):
    collected_week: float
    collected_month: float
    method_breakdown: list[PaymentMethodBreakdown]


class CsvMatchApplyItem(BaseModel):
    invoice_id: str
    amount: Decimal = Field(gt=0)
    paid_on: date | None = None
    method: PaymentMethod = PaymentMethod.BANK_TRANSFER
    reference: str | None = None


class ApplyCsvMatchesRequest(BaseModel):
    items: list[CsvMatchApplyItem]


class UpiStubResponse(BaseModel):
    invoice_id: str
    amount: float
    note: str
    prompt_record: bool = True
