"""Invoice routes."""
from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import Response

from app.api.deps import (
    AuthContext,
    get_client_ip,
    get_container,
    get_tenant_context,
    require_msme_roles,
    require_tenant_read_roles,
)
from app.api.schemas.common import PaginatedResponse
from app.api.schemas.gstr import Gstr1ReportResponse, Gstr3bReportResponse
from app.api.schemas.invoice import (
    CancelInvoiceRequest,
    CreateCreditNoteRequest,
    CreateInvoiceRequest,
    CreditNoteResponse,
    GstReportResponse,
    InvoiceCustomerSummary,
    InvoiceItemResponse,
    InvoiceResponse,
    PdfResponse,
    RegisterIrnRequest,
    UpdateInvoiceRequest,
)
from app.application.services.invoice_service import (
    CreateCreditNoteInput,
    CreateInvoiceInput,
    InvoiceItemInput,
    UpdateInvoiceInput,
)
from app.core.container import Container
from app.domain.enums import DocumentType, InvoiceStatus, UserRole

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _to_response(invoice, *, customer_name: str | None = None) -> InvoiceResponse:
    customer = None
    if customer_name is not None:
        customer = InvoiceCustomerSummary(id=str(invoice.customer_id), name=customer_name)
    return InvoiceResponse(
        id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        status=invoice.status,
        customer_id=str(invoice.customer_id),
        customer=customer,
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
        irn=invoice.irn,
        irn_generated_at=invoice.irn_generated_at,
        document_type=invoice.document_type,
        original_invoice_id=str(invoice.original_invoice_id) if invoice.original_invoice_id else None,
        credit_reason=invoice.credit_reason,
    )


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    body: CreateInvoiceRequest,
    auth: Annotated[AuthContext, Depends(require_msme_roles(UserRole.OWNER, UserRole.STAFF))],
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
    async with container.uow_factory() as uow:
        customer = await uow.customers.get_by_id(auth.company_id, invoice.customer_id)
    return _to_response(invoice, customer_name=customer.name if customer else "Unknown")


@router.get("", response_model=PaginatedResponse[InvoiceResponse])
async def list_invoices(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
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
    customer_names: dict[str, str] = {}
    async with container.uow_factory() as uow:
        for invoice in items:
            cid = str(invoice.customer_id)
            if cid not in customer_names:
                customer = await uow.customers.get_by_id(auth.company_id, invoice.customer_id)
                customer_names[cid] = customer.name if customer else "Unknown"
    return PaginatedResponse(
        items=[
            _to_response(i, customer_name=customer_names[str(i.customer_id)]) for i in items
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/reports/gst", response_model=GstReportResponse)
async def gst_report(
    auth: Annotated[AuthContext, Depends(require_tenant_read_roles)],
    container: Annotated[Container, Depends(get_container)],
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
) -> GstReportResponse:
    report = await container.invoice_service.gst_report(auth.company_id, from_date, to_date)
    return GstReportResponse(**report)


@router.get("/reports/gst.csv")
async def gst_report_csv(
    auth: Annotated[AuthContext, Depends(require_tenant_read_roles)],
    container: Annotated[Container, Depends(get_container)],
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
) -> Response:
    report = await container.invoice_service.gst_report(auth.company_id, from_date, to_date)
    csv_lines = [
        "field,value",
        f"from,{from_date.isoformat()}",
        f"to,{to_date.isoformat()}",
        f"invoice_count,{report['invoice_count']}",
        f"taxable_amount,{report['taxable_amount']}",
        f"cgst_amount,{report['cgst_amount']}",
        f"sgst_amount,{report['sgst_amount']}",
        f"igst_amount,{report['igst_amount']}",
        f"total_tax,{report['total_tax']}",
        f"grand_total,{report['grand_total']}",
    ]
    return Response(
        content="\n".join(csv_lines),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="gst-report-{from_date}_{to_date}.csv"'},
    )


@router.get("/reports/gstr1", response_model=Gstr1ReportResponse)
async def gstr1_report(
    auth: Annotated[AuthContext, Depends(require_tenant_read_roles)],
    container: Annotated[Container, Depends(get_container)],
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
) -> Gstr1ReportResponse:
    report = await container.gstr_report_service.gstr1_report(
        auth.company_id, from_date, to_date
    )
    return Gstr1ReportResponse(**report)


@router.get("/reports/gstr1.csv")
async def gstr1_report_csv(
    auth: Annotated[AuthContext, Depends(require_tenant_read_roles)],
    container: Annotated[Container, Depends(get_container)],
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
) -> Response:
    report = await container.gstr_report_service.gstr1_report(
        auth.company_id, from_date, to_date
    )
    lines = ["section,field,value"]
    for row in report["b2b"]:
        for key, value in row.items():
            lines.append(f"b2b,{key},{value}")
    for row in report["b2c_large"]:
        for key, value in row.items():
            lines.append(f"b2c_large,{key},{value}")
    for row in report["b2c_small"]:
        for key, value in row.items():
            lines.append(f"b2c_small,{key},{value}")
    for row in report["hsn_summary"]:
        for key, value in row.items():
            lines.append(f"hsn,{key},{value}")
    return Response(
        content="\n".join(lines),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="gstr1-{from_date}_{to_date}.csv"'},
    )


@router.get("/reports/gstr3b", response_model=Gstr3bReportResponse)
async def gstr3b_report(
    auth: Annotated[AuthContext, Depends(require_tenant_read_roles)],
    container: Annotated[Container, Depends(get_container)],
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
) -> Gstr3bReportResponse:
    report = await container.gstr_report_service.gstr3b_report(
        auth.company_id, from_date, to_date
    )
    return Gstr3bReportResponse(**report)


@router.get("/reports/gstr3b.csv")
async def gstr3b_report_csv(
    auth: Annotated[AuthContext, Depends(require_tenant_read_roles)],
    container: Annotated[Container, Depends(get_container)],
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
) -> Response:
    report = await container.gstr_report_service.gstr3b_report(
        auth.company_id, from_date, to_date
    )
    csv_lines = [
        "field,value",
        f"from,{from_date.isoformat()}",
        f"to,{to_date.isoformat()}",
        f"outward_taxable,{report['outward_taxable']}",
        f"outward_cgst,{report['outward_cgst']}",
        f"outward_sgst,{report['outward_sgst']}",
        f"outward_igst,{report['outward_igst']}",
        f"total_outward_tax,{report['total_outward_tax']}",
    ]
    return Response(
        content="\n".join(csv_lines),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="gstr3b-{from_date}_{to_date}.csv"'},
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> InvoiceResponse:
    invoice = await container.invoice_service.get(auth.company_id, invoice_id)
    async with container.uow_factory() as uow:
        customer = await uow.customers.get_by_id(auth.company_id, invoice.customer_id)
    return _to_response(invoice, customer_name=customer.name if customer else "Unknown")


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: uuid.UUID,
    body: UpdateInvoiceRequest,
    auth: Annotated[AuthContext, Depends(require_msme_roles(UserRole.OWNER, UserRole.STAFF))],
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
    auth: Annotated[AuthContext, Depends(require_msme_roles(UserRole.OWNER, UserRole.STAFF))],
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
    auth: Annotated[AuthContext, Depends(require_msme_roles(UserRole.OWNER, UserRole.STAFF))],
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


@router.post("/{invoice_id}/irn", response_model=InvoiceResponse)
async def register_invoice_irn(
    invoice_id: uuid.UUID,
    body: RegisterIrnRequest,
    auth: Annotated[AuthContext, Depends(require_msme_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> InvoiceResponse:
    invoice = await container.invoice_service.register_irn(
        company_id=auth.company_id,
        invoice_id=invoice_id,
        irn=body.irn,
        actor_id=auth.user_id,
        ip=get_client_ip(request),
    )
    return _to_response(invoice)


@router.post("/{invoice_id}/credit-notes", response_model=CreditNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_credit_note(
    invoice_id: uuid.UUID,
    body: CreateCreditNoteRequest,
    auth: Annotated[AuthContext, Depends(require_msme_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> CreditNoteResponse:
    items = [InvoiceItemInput(**i.model_dump()) for i in body.items] if body.items else None
    credit_note = await container.invoice_service.create_credit_note(
        company_id=auth.company_id,
        invoice_id=invoice_id,
        actor_id=auth.user_id,
        data=CreateCreditNoteInput(reason=body.reason, items=items),
        ip=get_client_ip(request),
    )
    return CreditNoteResponse(
        id=str(credit_note.id),
        invoice_number=credit_note.invoice_number,
        status=credit_note.status,
        issue_date=credit_note.issue_date,
        grand_total=credit_note.grand_total.amount,
        credit_reason=credit_note.credit_reason,
        original_invoice_id=str(invoice_id),
    )


@router.get("/{invoice_id}/credit-notes", response_model=list[CreditNoteResponse])
async def list_credit_notes(
    invoice_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> list[CreditNoteResponse]:
    notes = await container.invoice_service.list_credit_notes(auth.company_id, invoice_id)
    return [
        CreditNoteResponse(
            id=str(note.id),
            invoice_number=note.invoice_number,
            status=note.status,
            issue_date=note.issue_date,
            grand_total=note.grand_total.amount,
            credit_reason=note.credit_reason,
            original_invoice_id=str(invoice_id),
        )
        for note in notes
    ]


@router.get("/{invoice_id}/pdf", response_model=PdfResponse)
async def get_invoice_pdf(
    invoice_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> PdfResponse:
    path, url = await container.invoice_service.generate_pdf(auth.company_id, invoice_id)
    return PdfResponse(path=path, signed_url=url)


@router.get("/{invoice_id}/pdf/download")
async def download_invoice_pdf(
    invoice_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> Response:
    data, filename = await container.invoice_service.download_pdf_bytes(
        auth.company_id, invoice_id
    )
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{invoice_id}:share-whatsapp")
async def share_invoice_whatsapp(
    invoice_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(require_msme_roles(UserRole.OWNER, UserRole.STAFF))],
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
