"""Expense schemas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class CreateExpenseRequest(BaseModel):
    expense_date: date
    category: str = Field(min_length=1, max_length=80)
    amount: Decimal = Field(gt=0)
    vendor_name: str | None = Field(default=None, max_length=200)
    note: str | None = None


class UpdateExpenseRequest(BaseModel):
    expense_date: date | None = None
    category: str | None = Field(default=None, min_length=1, max_length=80)
    amount: Decimal | None = Field(default=None, gt=0)
    vendor_name: str | None = Field(default=None, max_length=200)
    note: str | None = None


class ExpenseResponse(BaseModel):
    id: str
    expense_date: date
    category: str
    amount: Decimal
    vendor_name: str | None = None
    note: str | None = None
