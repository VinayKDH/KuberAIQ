"""Invoice routes."""
from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import AuthContext, get_auth_context, get_client_ip, get_container, require_roles
from app.api.schemas.common import PaginatedResponse
from app.api.schemas.invoice import (
    CancelInvoiceRequest,
    CreateInvoiceRequest,
    GstReportResponse,
    InvoiceItemResponse,
    InvoiceResponse,
    PdfResponse,
    UpdateInvoiceRequest,
)
from app.application.services.invoice_service import CreateInvoiceInput, InvoiceItemInput, UpdateInvoiceInput
from app.core.container import Container
from app.domain.enums import InvoiceStatus, UserRole

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _to_response(invoice) -> InvoiceResponse:
    return InvoiceResponse(
        id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        status=invoice.status,
        customer_id=str(invoice.customer_id),
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        items=[
            InvoiceItemResponse(
                line_no=i.line_no,
                description=i.description,
                hsn_sac=i.hsn_sac,
                quantity=i.quantity,
                unit=i.unit,
                unit_price=i.unit_price.amount,
                gst_rate=i.gst_rate,
                taxable_amount=i.taxable_amount.amount,
                cgst_amount=i.cgst_amount.amount,
                sgst_amount=i.sgst_amount.amount,
                igst_amount=i.igst_amount.amount,
                line_total=i.line_total.amount,
            )
            for i in invoice.items
        ],
        taxable_amount=invoice.taxable_amount.amount,
        cgst_amount=invoice.cgst_amount.amount,
        sgst_amount=invoice.sgst_amount.amount,
        igst_amount=invoice.igst_amount.amount,
        total_tax=invoice.total_tax.amount,
        round_off=invoice.round_off.amount,
        grand_total=invoice.grand_total.amount,
        amount_paid=invoice.amount_paid.amount,
        amount_due=invoice.amount_due.amount,
        place_of_supply=invoice.place_of_supply,
        pdf_blob_path=invoice.pdf_blob_path,
    )


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    body: CreateInvoiceRequest,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> InvoiceResponse:
    items = [InvoiceItemInput(**i.model_dump()) for i in body.items]
    invoice = await container.invoice_service.create(
        company_id=auth.company_id,
        actor_id=auth.user_id,
        data=CreateInvoiceInput(
            customer_id=uuid.UUID(body.customer_id),
            issue_date=body.issue_date,
            due_date=body.due_date,
            status=body.status,
            items=items,
        ),
        ip=get_client_ip(request),
    )
    return _to_response(invoice)


@router.get("", response_model=PaginatedResponse[InvoiceResponse])
async def list_invoices(
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    container: Annotated[Container, Depends(get_container)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    status_filter: InvoiceStatus | None = Query(None, alias="status"),
    customer_id: uuid.UUID | None = None,
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
) -> PaginatedResponse[InvoiceResponse]:
    items, total = await container.invoice_service.search(
        auth.company_id,
        q=q,
        status=status_filter,
        customer_id=customer_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[_to_response(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/reports/gst", response_model=GstReportResponse)
async def gst_report(
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    container: Annotated[Container, Depends(get_container)],
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
) -> GstReportResponse:
    report = await container.invoice_service.gst_report(auth.company_id, from_date, to_date)
    return GstReportResponse(**report)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> InvoiceResponse:
    invoice = await container.invoice_service.get(auth.company_id, invoice_id)
    return _to_response(invoice)


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: uuid.UUID,
    body: UpdateInvoiceRequest,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> InvoiceResponse:
    items = [InvoiceItemInput(**i.model_dump()) for i in body.items] if body.items else None
    invoice = await container.invoice_service.update(
        company_id=auth.company_id,
        invoice_id=invoice_id,
        actor_id=auth.user_id,
        data=UpdateInvoiceInput(
            customer_id=uuid.UUID(body.customer_id) if body.customer_id else None,
            issue_date=body.issue_date,
            due_date=body.due_date,
            items=items,
        ),
        ip=get_client_ip(request),
    )
    return _to_response(invoice)


@router.post("/{invoice_id}:issue", response_model=InvoiceResponse)
async def issue_invoice(
    invoice_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> InvoiceResponse:
    invoice = await container.invoice_service.issue(
        company_id=auth.company_id,
        invoice_id=invoice_id,
        actor_id=auth.user_id,
        ip=get_client_ip(request),
    )
    return _to_response(invoice)


@router.post("/{invoice_id}:cancel", response_model=InvoiceResponse)
async def cancel_invoice(
    invoice_id: uuid.UUID,
    body: CancelInvoiceRequest,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> InvoiceResponse:
    invoice = await container.invoice_service.cancel(
        company_id=auth.company_id,
        invoice_id=invoice_id,
        reason=body.reason,
        actor_id=auth.user_id,
        ip=get_client_ip(request),
    )
    return _to_response(invoice)


@router.get("/{invoice_id}/pdf", response_model=PdfResponse)
async def get_invoice_pdf(
    invoice_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> PdfResponse:
    path, url = await container.invoice_service.generate_pdf(auth.company_id, invoice_id)
    return PdfResponse(path=path, signed_url=url)


@router.post("/{invoice_id}:share-whatsapp")
async def share_invoice_whatsapp(
    invoice_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> dict:
    provider_id = await container.invoice_service.share_whatsapp(
        company_id=auth.company_id,
        invoice_id=invoice_id,
        actor_id=auth.user_id,
        ip=get_client_ip(request),
    )
    return {"provider_message_id": provider_id}
