"""CA API schemas."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class CaClientItem(BaseModel):
    id: str
    ca_user_id: str
    company_id: str
    status: str
    invited_by: str
    ca_firm_name: str | None = None
    created_at: str | None = None
    company_name: str | None = None
    gstin: str | None = None
    ca_email: str | None = None
    ca_full_name: str | None = None


class CaClientsResponse(BaseModel):
    items: list[CaClientItem]


class CaUpcomingFiling(BaseModel):
    title: str | None = None
    due_date: str | None = None
    status: str | None = None
    obligation_id: str | None = None


class CaFilingChecklistItem(BaseModel):
    obligation_id: str
    title: str
    due_date: str | None = None
    status: str
    period_key: str | None = None


class CaFirmAdvisorItem(BaseModel):
    id: str
    email: str
    full_name: str | None = None


class CaDashboardClient(BaseModel):
    company_id: str
    company_name: str
    gstin: str | None = None
    assigned_advisor_user_id: str | None = None
    upcoming_filings: list[CaUpcomingFiling]
    filing_checklist: list[CaFilingChecklistItem] = []
    health_score: int | None = None
    overdue_total: float | int | None = None
    profile_complete: bool = True
    filings_due_soon: int = 0
    compliance_overdue: int = 0
    compliance_due_this_week: int = 0
    risk_level: str = "low"


class CaPortfolioSummary(BaseModel):
    avg_health_score: int | None = None
    clients_at_risk: int = 0
    total_overdue: float | int = 0
    filings_due_soon: int = 0


class CaDashboardResponse(BaseModel):
    clients: list[CaDashboardClient]
    client_count: int
    portfolio: CaPortfolioSummary | None = None
    filings_due_this_month: int = 0
    firm_advisors: list[CaFirmAdvisorItem] = []


class CaFilingActionRequest(BaseModel):
    period_key: str | None = None


class CaFilingActionResponse(BaseModel):
    obligation_id: str
    period_key: str
    status: str
    completed_at: str | None = None


class CaSwitchContextRequest(BaseModel):
    company_id: str = Field(..., description="Client company to act on behalf of")


class CaBulkGstrResponse(BaseModel):
    from_date: str = Field(alias="from")
    to_date: str = Field(alias="to")
    items: list[dict]


class InviteAdvisorRequest(BaseModel):
    email: str
    ca_firm_name: str | None = None


class AdvisorItem(BaseModel):
    id: str
    ca_user_id: str
    company_id: str
    status: str
    invited_by: str
    ca_firm_name: str | None = None
    created_at: str | None = None
    ca_email: str | None = None
    ca_full_name: str | None = None


class AdvisorsResponse(BaseModel):
    items: list[AdvisorItem]


class CaBulkFilingRequest(BaseModel):
    company_ids: list[str]
    obligation_ids: list[str]
    period_key: str | None = None


class CaBulkFilingResponse(BaseModel):
    completed: int


class CaClientTaskItem(BaseModel):
    id: str
    company_id: str
    title: str
    description: str | None = None
    due_date: str | None = None
    status: str
    created_at: str | None = None


class CaClientTasksResponse(BaseModel):
    items: list[CaClientTaskItem]


class CaCreateTaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    due_date: date | None = None


class CaUpdateTaskRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    due_date: date | None = None
    status: str | None = None
