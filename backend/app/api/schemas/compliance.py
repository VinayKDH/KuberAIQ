"""Compliance API schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ComplianceDeadline(BaseModel):
    type: str
    title: str
    due_date: str
    status: str
    description: str


class PendingEInvoice(BaseModel):
    invoice_id: str
    invoice_number: str | None = None
    issue_date: str
    grand_total: float
    days_since_issue: int
    urgency: str


class EInvoiceSummary(BaseModel):
    threshold: float
    ytd_turnover: float
    requires_e_invoice: bool
    pending_count: int
    pending_invoices: list[PendingEInvoice]


class ComplianceChecklistItem(BaseModel):
    id: str
    title: str
    description: str
    priority: str


class ComplianceAlert(BaseModel):
    triggered: bool
    overdue_count: int = 0
    due_this_week_count: int = 0
    health_score: int = 0
    message: str


class ComplianceDashboardResponse(BaseModel):
    disclaimer: str
    deadlines: list[ComplianceDeadline]
    e_invoice: EInvoiceSummary
    checklist: list[ComplianceChecklistItem]
    compliance_alert: ComplianceAlert | None = None


class ComplianceProfile(BaseModel):
    entity_type: str | None = None
    turnover_band: str | None = None
    gstr1_filing_frequency: str | None = None
    employee_count: int | None = None
    has_tds_applicable: bool = False
    udyam_number: str | None = None
    has_gstin: bool = False


class ComplianceSummary(BaseModel):
    total_applicable: int
    pending: int
    completed: int
    overdue: int
    due_this_week: int
    health_score: int


class ComplianceObligationItem(BaseModel):
    id: str
    category: str
    title: str
    description: str
    frequency: str
    priority: str
    action_route: str | None = None
    period_key: str
    due_date: str
    status: str
    completed_at: str | None = None


class ComplianceNotApplicableItem(BaseModel):
    id: str
    category: str
    title: str
    reason: str


class ComplianceObligationsResponse(BaseModel):
    profile_complete: bool
    disclaimer: str
    summary: ComplianceSummary
    obligations: list[ComplianceObligationItem]
    obligations_by_category: dict[str, list[ComplianceObligationItem]] = Field(default_factory=dict)
    not_applicable: list[ComplianceNotApplicableItem]
    profile: ComplianceProfile


class ComplianceCalendarEvent(BaseModel):
    obligation_id: str
    title: str
    category: str
    due_date: str
    status: str
    period_key: str
    priority: str


class ComplianceCalendarResponse(BaseModel):
    days: int
    profile_complete: bool
    events: list[ComplianceCalendarEvent]


class CompleteObligationRequest(BaseModel):
    period_key: str | None = None
    notes: str | None = Field(default=None, max_length=500)


class ComplianceCompletionHistoryItem(BaseModel):
    period_key: str
    completed_at: str | None = None
    notes: str | None = None


class CompleteObligationResponse(BaseModel):
    obligation_id: str
    period_key: str
    status: str
    completed_at: str | None = None
    history: list[ComplianceCompletionHistoryItem]


class UpdateComplianceProfileRequest(BaseModel):
    entity_type: str | None = Field(default=None, max_length=30)
    turnover_band: str | None = Field(default=None, max_length=20)
    gstr1_filing_frequency: str | None = Field(default=None, max_length=10)
    employee_count: int | None = Field(default=None, ge=0)
    udyam_number: str | None = Field(default=None, max_length=20)
    has_tds_applicable: bool | None = None
