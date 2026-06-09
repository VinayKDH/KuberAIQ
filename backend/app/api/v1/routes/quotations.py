"""Quotation routes."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import Response

from app.api.deps import AuthContext, get_client_ip, get_container, get_tenant_context, require_roles
from app.api.schemas.common import PaginatedResponse
from app.api.schemas.invoice import InvoiceResponse, PdfResponse
from app.api.schemas.quotation import (
    ConvertQuotationResponse,
    CreateQuotationRequest,
    QuotationCustomerSummary,
    QuotationItemResponse,
    QuotationResponse,
    UpdateQuotationRequest,
)
from app.application.services.quotation_service import CreateQuotationInput, QuotationItemInput, UpdateQuotationInput
from app.core.container import Container
from app.domain.enums import QuotationStatus, UserRole

router = APIRouter(prefix="/quotations", tags=["quotations"])


def _to_response(quotation, *, customer_name: str | None = None) -> QuotationResponse:
    customer = None
    if customer_name is not None:
        customer = QuotationCustomerSummary(id=str(quotation.customer_id), name=customer_name)
    return QuotationResponse(
        id=str(quotation.id),
        quotation_number=quotation.quotation_number,
        status=quotation.status,
        customer_id=str(quotation.customer_id),
        customer=customer,
        issue_date=quotation.issue_date,
        valid_until=quotation.valid_until,
        items=[
            QuotationItemResponse(
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
                product_id=str(i.product_id) if i.product_id else None,
            )
            for i in quotation.items
        ],
        taxable_amount=quotation.taxable_amount.amount,
        cgst_amount=quotation.cgst_amount.amount,
        sgst_amount=quotation.sgst_amount.amount,
        igst_amount=quotation.igst_amount.amount,
        total_tax=quotation.total_tax.amount,
        round_off=quotation.round_off.amount,
        grand_total=quotation.grand_total.amount,
        place_of_supply=quotation.place_of_supply,
        pdf_blob_path=quotation.pdf_blob_path,
        converted_invoice_id=str(quotation.converted_invoice_id)
        if quotation.converted_invoice_id
        else None,
    )


def _items_from_request(items) -> list[QuotationItemInput]:
    return [
        QuotationItemInput(
            description=i.description,
            quantity=i.quantity,
            unit_price=i.unit_price,
            gst_rate=i.gst_rate,
            hsn_sac=i.hsn_sac,
            unit=i.unit,
            product_id=uuid.UUID(i.product_id) if i.product_id else None,
        )
        for i in items
    ]


@router.post("", response_model=QuotationResponse, status_code=status.HTTP_201_CREATED)
async def create_quotation(
    body: CreateQuotationRequest,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> QuotationResponse:
    quotation = await container.quotation_service.create(
        company_id=auth.company_id,
        actor_id=auth.user_id,
        data=CreateQuotationInput(
            customer_id=uuid.UUID(body.customer_id),
            issue_date=body.issue_date,
            valid_until=body.valid_until,
            items=_items_from_request(body.items),
        ),
        ip=get_client_ip(request),
    )
    async with container.uow_factory() as uow:
        customer = await uow.customers.get_by_id(auth.company_id, quotation.customer_id)
    return _to_response(quotation, customer_name=customer.name if customer else "Unknown")


@router.get("", response_model=PaginatedResponse[QuotationResponse])
async def list_quotations(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    status: QuotationStatus | None = None,
    customer_id: uuid.UUID | None = None,
) -> PaginatedResponse[QuotationResponse]:
    items, total = await container.quotation_service.search(
        auth.company_id, q=q, status=status, customer_id=customer_id, page=page, page_size=page_size
    )
    async with container.uow_factory() as uow:
        names = {}
        for qtn in items:
            if qtn.customer_id not in names:
                customer = await uow.customers.get_by_id(auth.company_id, qtn.customer_id)
                names[qtn.customer_id] = customer.name if customer else "Unknown"
    return PaginatedResponse(
        items=[_to_response(q, customer_name=names.get(q.customer_id)) for q in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{quotation_id}", response_model=QuotationResponse)
async def get_quotation(
    quotation_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> QuotationResponse:
    quotation = await container.quotation_service.get(auth.company_id, quotation_id)
    async with container.uow_factory() as uow:
        customer = await uow.customers.get_by_id(auth.company_id, quotation.customer_id)
    return _to_response(quotation, customer_name=customer.name if customer else "Unknown")


@router.patch("/{quotation_id}", response_model=QuotationResponse)
async def update_quotation(
    quotation_id: uuid.UUID,
    body: UpdateQuotationRequest,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> QuotationResponse:
    payload = body.model_dump(exclude_unset=True)
    if "customer_id" in payload and payload["customer_id"]:
        payload["customer_id"] = uuid.UUID(payload["customer_id"])
    if "items" in payload and payload["items"] is not None:
        payload["items"] = _items_from_request(body.items)
    quotation = await container.quotation_service.update(
        company_id=auth.company_id,
        quotation_id=quotation_id,
        actor_id=auth.user_id,
        data=UpdateQuotationInput(**payload),
        ip=get_client_ip(request),
    )
    async with container.uow_factory() as uow:
        customer = await uow.customers.get_by_id(auth.company_id, quotation.customer_id)
    return _to_response(quotation, customer_name=customer.name if customer else "Unknown")


@router.post("/{quotation_id}:send", response_model=QuotationResponse)
async def send_quotation(
    quotation_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> QuotationResponse:
    quotation = await container.quotation_service.send(
        company_id=auth.company_id,
        quotation_id=quotation_id,
        actor_id=auth.user_id,
        ip=get_client_ip(request),
    )
    async with container.uow_factory() as uow:
        customer = await uow.customers.get_by_id(auth.company_id, quotation.customer_id)
    return _to_response(quotation, customer_name=customer.name if customer else "Unknown")


@router.post("/{quotation_id}:convert", response_model=ConvertQuotationResponse)
async def convert_quotation(
    quotation_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER, UserRole.STAFF))],
    container: Annotated[Container, Depends(get_container)],
    request: Request,
) -> ConvertQuotationResponse:
    quotation, invoice = await container.quotation_service.convert_to_invoice(
        company_id=auth.company_id,
        quotation_id=quotation_id,
        actor_id=auth.user_id,
        ip=get_client_ip(request),
    )
    async with container.uow_factory() as uow:
        customer = await uow.customers.get_by_id(auth.company_id, quotation.customer_id)
    return ConvertQuotationResponse(
        quotation=_to_response(quotation, customer_name=customer.name if customer else "Unknown"),
        invoice_id=str(invoice.id),
    )


@router.get("/{quotation_id}/pdf", response_model=PdfResponse)
async def quotation_pdf(
    quotation_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> PdfResponse:
    path, url = await container.quotation_service.generate_pdf(auth.company_id, quotation_id)
    return PdfResponse(path=path, signed_url=url)


@router.get("/{quotation_id}/pdf/download")
async def quotation_pdf_download(
    quotation_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> Response:
    path, _ = await container.quotation_service.generate_pdf(auth.company_id, quotation_id)
    data = await container.storage.download(path)
    quotation = await container.quotation_service.get(auth.company_id, quotation_id)
    filename = f"{quotation.quotation_number or quotation_id}.pdf"
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
