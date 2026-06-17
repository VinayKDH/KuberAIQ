"""CA API schemas."""
from __future__ import annotations

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


class CaDashboardClient(BaseModel):
    company_id: str
    company_name: str
    gstin: str | None = None
    upcoming_filings: list[CaUpcomingFiling]
    health_score: int | None = None
    overdue_total: float | int | None = None


class CaDashboardResponse(BaseModel):
    clients: list[CaDashboardClient]
    client_count: int


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
