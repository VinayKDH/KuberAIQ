"""GSTR export API schemas."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class GstrReportMetadata(BaseModel):
    disclaimer: str
    invoice_count: int


class Gstr1ReportResponse(BaseModel):
    from_date: str
    to_date: str
    metadata: GstrReportMetadata
    b2b: list[dict]
    b2c_large: list[dict]
    b2c_small: list[dict]
    hsn_summary: list[dict]


class Gstr3bMetadata(BaseModel):
    disclaimer: str
    invoice_count: int
    credit_note_count: int
    includes_itc: bool


class Gstr3bReportResponse(BaseModel):
    from_date: str
    to_date: str
    metadata: Gstr3bMetadata
    outward_taxable: Decimal
    outward_cgst: Decimal
    outward_sgst: Decimal
    outward_igst: Decimal
    total_outward_tax: Decimal


class ComplianceAlertsPreviewResponse(BaseModel):
    count: int
    alerts: list[dict]
    due_soon_days: int
