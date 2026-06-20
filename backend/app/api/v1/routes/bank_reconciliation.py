"""Bank reconciliation and payment summary routes."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile

from app.api.deps import AuthContext, get_client_ip, get_container, require_roles
from app.api.schemas.payment import (
    ApplyCsvMatchesRequest,
    CollectionSummaryResponse,
    PaymentAnalyticsResponse,
    UpiStubResponse,
)
from app.application.services.payment_service import CsvMatchApplyInput
from app.core.container import Container
from app.domain.enums import UserRole

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/import-csv")
async def import_payments_csv(
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    file: UploadFile = File(...),
) -> dict:
    raw = await file.read()
    suggestions = await container.payment_service.suggest_matches_from_csv(
        auth.company_id, raw.decode("utf-8")
    )
    return {"items": suggestions, "count": len(suggestions)}


@router.post("/import-csv/apply")
async def apply_payments_csv_matches(
    body: ApplyCsvMatchesRequest,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> dict:
    matches = [
        CsvMatchApplyInput(
            invoice_id=uuid.UUID(item.invoice_id),
            amount=item.amount,
            paid_on=item.paid_on,
            method=item.method,
            reference=item.reference,
        )
        for item in body.items
    ]
    applied = await container.payment_service.apply_csv_matches(
        company_id=auth.company_id,
        actor_id=auth.user_id,
        matches=matches,
        ip=get_client_ip(request),
    )
    return {"applied": len(applied), "payment_ids": [str(p.id) for p in applied]}


@router.get("/summary", response_model=CollectionSummaryResponse)
async def payment_collection_summary(
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
) -> CollectionSummaryResponse:
    data = await container.payment_service.collection_summary(auth.company_id)
    return CollectionSummaryResponse(**data)


@router.get("/analytics", response_model=PaymentAnalyticsResponse)
async def payment_analytics(
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
) -> PaymentAnalyticsResponse:
    data = await container.payment_service.payment_analytics(auth.company_id)
    return PaymentAnalyticsResponse(**data)


@router.post("/webhooks/razorpay", status_code=204, response_class=Response)
async def razorpay_invoice_webhook(
    request: Request,
    container: Annotated[Container, Depends(get_container)],
) -> Response:
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    await container.payment_service.handle_razorpay_invoice_webhook(body, signature)
    return Response(status_code=204)


@router.post("/invoices/{invoice_id}/upi-stub", response_model=UpiStubResponse)
async def upi_payment_stub(
    invoice_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
) -> UpiStubResponse:
    data = await container.payment_service.record_upi_stub(
        company_id=auth.company_id,
        invoice_id=invoice_id,
        actor_id=auth.user_id,
    )
    return UpiStubResponse(**data)
