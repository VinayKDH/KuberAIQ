"""Quotation API schemas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.domain.enums import QuotationStatus


class QuotationItemRequest(BaseModel):
    description: str = Field(min_length=1, max_length=300)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    gst_rate: Decimal = Field(ge=0, le=28)
    hsn_sac: str | None = None
    unit: str = "NOS"
    product_id: str | None = None


class CreateQuotationRequest(BaseModel):
    customer_id: str
    issue_date: date
    valid_until: date
    items: list[QuotationItemRequest] = Field(min_length=1)


class UpdateQuotationRequest(BaseModel):
    customer_id: str | None = None
    issue_date: date | None = None
    valid_until: date | None = None
    items: list[QuotationItemRequest] | None = None


class QuotationItemResponse(BaseModel):
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
    product_id: str | None = None


class QuotationCustomerSummary(BaseModel):
    id: str
    name: str


class QuotationResponse(BaseModel):
    id: str
    quotation_number: str | None = None
    status: QuotationStatus
    customer_id: str
    customer: QuotationCustomerSummary | None = None
    issue_date: date
    valid_until: date
    items: list[QuotationItemResponse]
    taxable_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    total_tax: Decimal
    round_off: Decimal
    grand_total: Decimal
    place_of_supply: str | None = None
    pdf_blob_path: str | None = None
    converted_invoice_id: str | None = None


class ConvertQuotationResponse(BaseModel):
    quotation: QuotationResponse
    invoice_id: str
