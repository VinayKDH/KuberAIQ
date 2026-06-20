"""Invoice API schemas."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.domain.enums import DocumentType, InvoiceStatus


class InvoiceItemRequest(BaseModel):
    description: str = Field(min_length=1, max_length=300)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    gst_rate: Decimal = Field(ge=0, le=28)
    hsn_sac: str | None = None
    unit: str = "NOS"
    product_id: str | None = None


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


class InvoiceCustomerSummary(BaseModel):
    id: str
    name: str


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str | None = None
    status: InvoiceStatus
    customer_id: str
    customer: InvoiceCustomerSummary | None = None
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
    payment_link_url: str | None = None
    irn: str | None = None
    irn_generated_at: datetime | None = None
    document_type: DocumentType = DocumentType.INVOICE
    original_invoice_id: str | None = None
    credit_reason: str | None = None


class CreateCreditNoteRequest(BaseModel):
    reason: str = Field(min_length=1)
    items: list[InvoiceItemRequest] | None = None


class CreditNoteResponse(BaseModel):
    id: str
    invoice_number: str | None = None
    status: InvoiceStatus
    issue_date: date
    grand_total: Decimal
    credit_reason: str | None = None
    original_invoice_id: str


class CancelInvoiceRequest(BaseModel):
    reason: str = Field(min_length=1)


class RegisterIrnRequest(BaseModel):
    irn: str = Field(min_length=10, max_length=64)


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


class PaymentLinkResponse(BaseModel):
    url: str | None = None
    provider: str


class CreateRecurringInvoiceTemplateRequest(BaseModel):
    customer_id: str
    name: str = Field(min_length=1, max_length=200)
    items: list[InvoiceItemRequest] = Field(min_length=1)
    frequency: str = Field(default="MONTHLY")
    next_run_date: date | None = None


class UpdateRecurringInvoiceTemplateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    items: list[InvoiceItemRequest] | None = None
    frequency: str | None = None
    next_run_date: date | None = None
    is_active: bool | None = None


class RecurringInvoiceTemplateResponse(BaseModel):
    id: str
    company_id: str
    customer_id: str
    name: str
    items: list[dict]
    frequency: str
    next_run_date: str
    is_active: bool


class RecurringInvoiceTemplateListResponse(BaseModel):
    items: list[RecurringInvoiceTemplateResponse]


class CounterBillRequest(BaseModel):
    product_id: str
    quantity: Decimal = Field(gt=0)
    customer_id: str | None = None
    customer_name: str | None = None


class CounterBillResponse(BaseModel):
    invoice: InvoiceResponse
    customer_name: str
    stock_warning: str | None = None
