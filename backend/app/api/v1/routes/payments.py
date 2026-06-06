"""Payment routes."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import AuthContext, get_client_ip, get_container, require_roles
from app.api.schemas.payment import PaymentResponse, RecordPaymentRequest
from app.application.services.payment_service import RecordPaymentInput
from app.core.container import Container
from app.domain.enums import UserRole

router = APIRouter(prefix="/invoices", tags=["payments"])


@router.post("/{invoice_id}/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_payment(
    invoice_id: uuid.UUID,
    body: RecordPaymentRequest,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> PaymentResponse:
    payment = await container.payment_service.record(
        company_id=auth.company_id,
        invoice_id=invoice_id,
        actor_id=auth.user_id,
        data=RecordPaymentInput(**body.model_dump()),
        ip=get_client_ip(request),
    )
    return PaymentResponse(
        id=str(payment.id),
        invoice_id=str(payment.invoice_id),
        amount=payment.amount,
        paid_on=payment.paid_on,
        method=payment.method,
        reference=payment.reference,
        note=payment.note,
    )
