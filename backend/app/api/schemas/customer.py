"""Customer API schemas."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CreateCustomerRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone: str
    email: str | None = None
    gstin: str | None = None
    billing_address: str | None = None
    notes: str | None = None


class UpdateCustomerRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = None
    email: str | None = None
    gstin: str | None = None
    billing_address: str | None = None
    notes: str | None = None


class CustomerResponse(BaseModel):
    id: str
    name: str
    phone: str
    email: str | None = None
    gstin: str | None = None
    state_code: str | None = None
    billing_address: str | None = None
    notes: str | None = None
    created_at: datetime | None = None


class CustomerHistoryResponse(BaseModel):
    customer: CustomerResponse
    total_billed: Decimal
    total_paid: Decimal
    outstanding: Decimal
    aging: dict[str, Decimal]
