"""Company API schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class CompanyResponse(BaseModel):
    id: str
    legal_name: str
    gstin: str | None
    state_code: str
    address: str | None
    invoice_prefix: str
    upi_id: str | None = None
    upi_payee_name: str | None = None
    auto_reminders_enabled: bool = True
    default_reminder_language: str = "en"
    entity_type: str = "PROPRIETORSHIP"
    turnover_band: str | None = None
    gstr1_filing_frequency: str = "MONTHLY"
    employee_count: int | None = None
    udyam_number: str | None = None
    has_tds_applicable: bool = False


class OnboardCompanyRequest(BaseModel):
    legal_name: str = Field(min_length=2, max_length=200)
    gstin: str = Field(min_length=15, max_length=15)
    address: str = Field(min_length=5, max_length=500)
    invoice_prefix: str = Field(default="INV", min_length=2, max_length=10)


class UpdateCompanyRequest(BaseModel):
    legal_name: str | None = Field(default=None, min_length=2, max_length=200)
    gstin: str | None = Field(default=None, min_length=15, max_length=15)
    address: str | None = Field(default=None, min_length=5, max_length=500)
    invoice_prefix: str | None = Field(default=None, min_length=2, max_length=10)
    upi_id: str | None = Field(default=None, max_length=100)
    upi_payee_name: str | None = Field(default=None, max_length=200)
    auto_reminders_enabled: bool | None = None
    default_reminder_language: str | None = Field(default=None, min_length=2, max_length=2)
    entity_type: str | None = Field(default=None, max_length=30)
    turnover_band: str | None = Field(default=None, max_length=20)
    gstr1_filing_frequency: str | None = Field(default=None, max_length=10)
    employee_count: int | None = Field(default=None, ge=0)
    udyam_number: str | None = Field(default=None, max_length=20)
    has_tds_applicable: bool | None = None
