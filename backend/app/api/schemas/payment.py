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
