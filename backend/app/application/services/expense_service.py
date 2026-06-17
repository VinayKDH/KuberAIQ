"""Expense service."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.application.ports.repositories import ExpenseRecord
from app.core.errors import NotFoundError


@dataclass
class CreateExpenseInput:
    expense_date: date
    category: str
    amount: Decimal
    vendor_name: str | None = None
    note: str | None = None


@dataclass
class UpdateExpenseInput:
    expense_date: date | None = None
    category: str | None = None
    amount: Decimal | None = None
    vendor_name: str | None = None
    note: str | None = None


class ExpenseService:
    def __init__(self, uow_factory) -> None:
        self._uow_factory = uow_factory

    async def create(
        self, *, company_id: uuid.UUID, actor_id: uuid.UUID, data: CreateExpenseInput
    ) -> ExpenseRecord:
        async with self._uow_factory() as uow:
            return await uow.expenses.create(
                ExpenseRecord(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    expense_date=data.expense_date,
                    category=data.category.strip(),
                    amount=data.amount,
                    vendor_name=data.vendor_name,
                    note=data.note,
                    created_by=actor_id,
                )
            )

    async def list(self, company_id: uuid.UUID, page: int, page_size: int) -> tuple[list[ExpenseRecord], int]:
        async with self._uow_factory() as uow:
            return await uow.expenses.list_for_company(company_id, page, page_size)

    async def update(
        self, *, company_id: uuid.UUID, expense_id: uuid.UUID, data: UpdateExpenseInput
    ) -> ExpenseRecord:
        async with self._uow_factory() as uow:
            expense = await uow.expenses.get_by_id(company_id, expense_id)
            if not expense:
                raise NotFoundError("Expense not found")
            if data.expense_date is not None:
                expense.expense_date = data.expense_date
            if data.category is not None:
                expense.category = data.category
            if data.amount is not None:
                expense.amount = data.amount
            if data.vendor_name is not None:
                expense.vendor_name = data.vendor_name
            if data.note is not None:
                expense.note = data.note
            return await uow.expenses.update(expense)

    async def delete(self, company_id: uuid.UUID, expense_id: uuid.UUID) -> None:
        async with self._uow_factory() as uow:
            await uow.expenses.soft_delete(company_id, expense_id)
