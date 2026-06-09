"""Collections routes."""
from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import AuthContext, get_tenant_context, get_client_ip, get_container, require_roles
from app.api.schemas.collection import (
    BulkPreviewResponse,
    CallTodayInvoiceResponse,
    CollectionsDashboardResponse,
    OverdueInvoiceResponse,
    ReminderPreviewResponse,
    ReminderResponse,
    SendReminderRequest,
)
from app.api.schemas.common import PaginatedResponse
from app.application.services.collection_service import SendReminderInput
from app.core.container import Container
from app.domain.enums import UserRole

router = APIRouter(prefix="/collections", tags=["collections"])


def _to_overdue_response(row: dict) -> OverdueInvoiceResponse:
    invoice_id = str(row["invoice"].id)
    last = row.get("last_reminder")
    return OverdueInvoiceResponse(
        id=invoice_id,
        invoice_id=invoice_id,
        invoice_number=row["invoice"].invoice_number,
        customer_name=row["customer_name"],
        customer_phone=row.get("customer_phone"),
        amount_due=row["invoice"].amount_due.amount,
        days_overdue=row["days_overdue"],
        due_date=str(row["invoice"].due_date),
        last_reminder_at=last.sent_at.isoformat() if last and last.sent_at else None,
        last_reminder_channel=str(last.channel) if last else None,
    )


def _to_call_today_response(row: dict) -> CallTodayInvoiceResponse:
    invoice_id = str(row["invoice"].id)
    last = row.get("last_reminder")
    return CallTodayInvoiceResponse(
        id=invoice_id,
        invoice_id=invoice_id,
        invoice_number=row["invoice"].invoice_number,
        customer_name=row["customer_name"],
        customer_phone=row.get("customer_phone"),
        amount_due=row["invoice"].amount_due.amount,
        days_overdue=row["days_overdue"],
        days_until_due=row["days_until_due"],
        priority_score=row["priority_score"],
        due_date=str(row["invoice"].due_date),
        last_reminder_at=last.sent_at.isoformat() if last and last.sent_at else None,
        last_reminder_channel=str(last.channel) if last else None,
    )


@router.get("/call-today", response_model=list[CallTodayInvoiceResponse])
async def list_call_today(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> list[CallTodayInvoiceResponse]:
    items = await container.collection_service.list_call_today(auth.company_id)
    return [_to_call_today_response(row) for row in items]


@router.get("/overdue", response_model=PaginatedResponse[OverdueInvoiceResponse])
async def list_overdue(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[OverdueInvoiceResponse]:
    items = await container.collection_service.list_overdue(auth.company_id)
    responses = [_to_overdue_response(r) for r in items]
    start = (page - 1) * page_size
    end = start + page_size
    return PaginatedResponse(
        items=responses[start:end],
        page=page,
        page_size=page_size,
        total=len(responses),
    )


@router.get("/reminders/preview", response_model=ReminderPreviewResponse)
async def preview_reminder(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
    invoice_id: uuid.UUID = Query(...),
    language: str = Query("en"),
) -> ReminderPreviewResponse:
    preview = await container.collection_service.preview_reminder(
        auth.company_id,
        invoice_id,
        language=language,
    )
    return ReminderPreviewResponse(**preview)


@router.post("/reminders", response_model=ReminderResponse)
async def send_reminder(
    body: SendReminderRequest,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> ReminderResponse:
    import uuid

    reminder = await container.collection_service.send_reminder(
        company_id=auth.company_id,
        actor_id=auth.user_id,
        data=SendReminderInput(
            invoice_id=uuid.UUID(body.invoice_id),
            channel=body.channel,
            language=body.language,
        ),
        ip=get_client_ip(request),
    )
    return ReminderResponse(
        reminder_id=str(reminder.id),
        status=reminder.status,
        provider_message_id=reminder.provider_message_id,
    )


@router.post("/reminders/bulk:preview", response_model=BulkPreviewResponse)
async def bulk_preview(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> BulkPreviewResponse:
    preview = await container.collection_service.bulk_preview(auth.company_id)
    return BulkPreviewResponse(
        count=preview["count"],
        total_outstanding=preview["total_outstanding"],
    )


@router.post("/reminders/bulk", response_model=list[ReminderResponse])
async def bulk_send(
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> list[ReminderResponse]:
    reminders = await container.collection_service.bulk_send(
        company_id=auth.company_id,
        actor_id=auth.user_id,
        ip=get_client_ip(request),
    )
    return [
        ReminderResponse(
            reminder_id=str(r.id),
            status=r.status,
            provider_message_id=r.provider_message_id,
        )
        for r in reminders
    ]


@router.get("/dashboard", response_model=CollectionsDashboardResponse)
async def collections_dashboard(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> CollectionsDashboardResponse:
    items = await container.collection_service.list_overdue(auth.company_id)
    responses = [_to_overdue_response(r) for r in items]
    total = sum((r.amount_due for r in responses), start=0)
    reminded_today = sum(
        1
        for r in items
        if r.get("last_reminder")
        and r["last_reminder"].sent_at
        and r["last_reminder"].sent_at.date() == date.today()
    )
    return CollectionsDashboardResponse(
        overdue_count=len(responses),
        total_outstanding=total,
        total_overdue=total,
        reminded_today=reminded_today,
        invoices=responses,
    )
