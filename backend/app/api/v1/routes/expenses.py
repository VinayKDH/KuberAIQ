"""Expense routes."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import AuthContext, get_container, get_tenant_context, require_msme_roles
from app.api.schemas.common import PaginatedResponse
from app.api.schemas.expense import CreateExpenseRequest, ExpenseResponse, UpdateExpenseRequest
from app.application.services.expense_service import CreateExpenseInput, UpdateExpenseInput
from app.core.container import Container
from app.domain.enums import UserRole

router = APIRouter(prefix="/expenses", tags=["expenses"])


def _to_response(record) -> ExpenseResponse:
    return ExpenseResponse(
        id=str(record.id),
        expense_date=record.expense_date,
        category=record.category,
        amount=record.amount,
        vendor_name=record.vendor_name,
        note=record.note,
    )


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    body: CreateExpenseRequest,
    auth: Annotated[AuthContext, Depends(require_msme_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
) -> ExpenseResponse:
    row = await container.expense_service.create(
        company_id=auth.company_id,
        actor_id=auth.user_id,
        data=CreateExpenseInput(**body.model_dump()),
    )
    return _to_response(row)


@router.get("", response_model=PaginatedResponse[ExpenseResponse])
async def list_expenses(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[ExpenseResponse]:
    rows, total = await container.expense_service.list(auth.company_id, page, page_size)
    return PaginatedResponse(
        items=[_to_response(row) for row in rows],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.patch("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: uuid.UUID,
    body: UpdateExpenseRequest,
    auth: Annotated[AuthContext, Depends(require_msme_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
) -> ExpenseResponse:
    row = await container.expense_service.update(
        company_id=auth.company_id,
        expense_id=expense_id,
        data=UpdateExpenseInput(**body.model_dump(exclude_unset=True)),
    )
    return _to_response(row)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_expense(
    expense_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(require_msme_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
) -> Response:
    await container.expense_service.delete(auth.company_id, expense_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
