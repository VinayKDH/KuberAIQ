"""Dashboard routes."""
from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import AuthContext, get_tenant_context, get_container
from app.api.schemas.dashboard import DashboardResponse
from app.core.container import Container

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
) -> DashboardResponse:
    summary = await container.dashboard_service.summary(auth.company_id, from_date, to_date)
    compliance_alert = await container.compliance_service.compliance_alert(auth.company_id)
    return DashboardResponse(**summary, compliance_alert=compliance_alert)
