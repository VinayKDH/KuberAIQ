"""Collections routes."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.deps import AuthContext, get_auth_context, get_client_ip, get_container, require_roles
from app.api.schemas.collection import (
    BulkPreviewResponse,
    CollectionsDashboardResponse,
    OverdueInvoiceResponse,
    ReminderResponse,
    SendReminderRequest,
)
from app.application.services.collection_service import SendReminderInput
from app.core.container import Container
from app.domain.enums import UserRole

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("/overdue", response_model=list[OverdueInvoiceResponse])
async def list_overdue(
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> list[OverdueInvoiceResponse]:
    items = await container.collection_service.list_overdue(auth.company_id)
    return [
        OverdueInvoiceResponse(
            invoice_id=str(r["invoice"].id),
            invoice_number=r["invoice"].invoice_number,
            customer_name=r["customer_name"],
            amount_due=r["invoice"].amount_due.amount,
            days_overdue=r["days_overdue"],
            due_date=str(r["invoice"].due_date),
        )
        for r in items
    ]


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
    auth: Annotated[AuthContext, Depends(get_auth_context)],
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
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> CollectionsDashboardResponse:
    items = await container.collection_service.list_overdue(auth.company_id)
    total = sum((r["invoice"].amount_due.amount for r in items), start=0)
    return CollectionsDashboardResponse(
        overdue_count=len(items),
        total_outstanding=total,
        invoices=[
            OverdueInvoiceResponse(
                invoice_id=str(r["invoice"].id),
                invoice_number=r["invoice"].invoice_number,
                customer_name=r["customer_name"],
                amount_due=r["invoice"].amount_due.amount,
                days_overdue=r["days_overdue"],
                due_date=str(r["invoice"].due_date),
            )
            for r in items
        ],
    )
