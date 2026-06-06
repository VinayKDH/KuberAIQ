"""Invoice API schemas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.domain.enums import InvoiceStatus


class InvoiceItemRequest(BaseModel):
    description: str = Field(min_length=1, max_length=300)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    gst_rate: Decimal = Field(ge=0, le=28)
    hsn_sac: str | None = None
    unit: str = "NOS"


class CreateInvoiceRequest(BaseModel):
    customer_id: str
    issue_date: date
    due_date: date
    status: InvoiceStatus = InvoiceStatus.DRAFT
    items: list[InvoiceItemRequest] = Field(min_length=1)


class UpdateInvoiceRequest(BaseModel):
    customer_id: str | None = None
    issue_date: date | None = None
    due_date: date | None = None
    items: list[InvoiceItemRequest] | None = None


class InvoiceItemResponse(BaseModel):
    line_no: int
    description: str
    hsn_sac: str | None = None
    quantity: Decimal
    unit: str
    unit_price: Decimal
    gst_rate: Decimal
    taxable_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    line_total: Decimal


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str | None = None
    status: InvoiceStatus
    customer_id: str
    issue_date: date
    due_date: date
    items: list[InvoiceItemResponse]
    taxable_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    total_tax: Decimal
    round_off: Decimal
    grand_total: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    place_of_supply: str | None = None
    pdf_blob_path: str | None = None


class CancelInvoiceRequest(BaseModel):
    reason: str = Field(min_length=1)


class PdfResponse(BaseModel):
    path: str
    signed_url: str


class GstReportResponse(BaseModel):
    taxable_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    total_tax: Decimal
    grand_total: Decimal
    invoice_count: int
