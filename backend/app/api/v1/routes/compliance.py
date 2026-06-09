"""Compliance routes."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import AuthContext, get_container, get_tenant_context, require_roles
from app.api.schemas.compliance import (
    CompleteObligationRequest,
    CompleteObligationResponse,
    ComplianceCalendarResponse,
    ComplianceDashboardResponse,
    ComplianceObligationsResponse,
    UpdateComplianceProfileRequest,
)
from app.api.schemas.gstr import ComplianceAlertsPreviewResponse
from app.api.schemas.company import CompanyResponse
from app.application.services.company_service import UpdateCompanyInput
from app.core.container import Container
from app.domain.enums import UserRole

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/dashboard", response_model=ComplianceDashboardResponse)
async def compliance_dashboard(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> ComplianceDashboardResponse:
    data = await container.compliance_service.dashboard(auth.company_id)
    return ComplianceDashboardResponse(**data)


@router.get("/obligations", response_model=ComplianceObligationsResponse)
async def compliance_obligations(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> ComplianceObligationsResponse:
    data = await container.compliance_service.obligations(auth.company_id)
    return ComplianceObligationsResponse(**data)


@router.get("/calendar", response_model=ComplianceCalendarResponse)
async def compliance_calendar(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
    days: Annotated[int, Query(ge=7, le=365)] = 90,
) -> ComplianceCalendarResponse:
    data = await container.compliance_service.calendar(auth.company_id, days=days)
    return ComplianceCalendarResponse(**data)


@router.post("/obligations/{obligation_id}/complete", response_model=CompleteObligationResponse)
async def complete_compliance_obligation(
    obligation_id: str,
    body: CompleteObligationRequest,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER))],
    container: Annotated[Container, Depends(get_container)],
) -> CompleteObligationResponse:
    try:
        data = await container.compliance_service.complete_obligation(
            company_id=auth.company_id,
            actor_id=auth.user_id,
            obligation_id=obligation_id,
            period_key=body.period_key,
            notes=body.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CompleteObligationResponse(**data)


@router.patch("/profile", response_model=CompanyResponse)
async def update_compliance_profile(
    body: UpdateComplianceProfileRequest,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER))],
    container: Annotated[Container, Depends(get_container)],
) -> CompanyResponse:
    from app.api.v1.routes.companies import _company_response

    company = await container.company_service.update_profile(
        company_id=auth.company_id,
        actor_id=auth.user_id,
        data=UpdateCompanyInput(
            entity_type=body.entity_type,
            turnover_band=body.turnover_band,
            gstr1_filing_frequency=body.gstr1_filing_frequency,
            employee_count=body.employee_count,
            udyam_number=body.udyam_number,
            has_tds_applicable=body.has_tds_applicable,
        ),
    )
    return _company_response(company)


@router.get("/alerts/preview", response_model=ComplianceAlertsPreviewResponse)
async def preview_compliance_alerts(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> ComplianceAlertsPreviewResponse:
    data = await container.compliance_service.preview_alerts(auth.company_id)
    return ComplianceAlertsPreviewResponse(**data)
