"""Company profile routes."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import (
    AuthContext,
    get_client_ip,
    get_container,
    get_subscribed_context,
    get_tenant_context,
    require_roles,
)
from app.api.schemas.auth import TokenResponse
from app.api.schemas.company import CompanyResponse, OnboardCompanyRequest, UpdateCompanyRequest
from app.api.schemas.company import CompanyStaffResponse, InviteStaffRequest
from app.application.services.company_service import OnboardCompanyInput, UpdateCompanyInput
from app.core.container import Container
from app.domain.enums import UserRole

router = APIRouter(prefix="/companies", tags=["companies"])


def _company_response(record) -> CompanyResponse:
    return CompanyResponse(
        id=str(record.id),
        legal_name=record.legal_name,
        gstin=record.gstin,
        state_code=record.state_code,
        address=record.address,
        invoice_prefix=record.invoice_prefix,
        upi_id=record.upi_id,
        upi_payee_name=record.upi_payee_name,
        auto_reminders_enabled=record.auto_reminders_enabled,
        default_reminder_language=record.default_reminder_language,
        entity_type=record.entity_type,
        turnover_band=record.turnover_band,
        gstr1_filing_frequency=record.gstr1_filing_frequency,
        employee_count=record.employee_count,
        udyam_number=record.udyam_number,
        has_tds_applicable=record.has_tds_applicable,
        msme_segment=record.msme_segment,
    )


@router.post("/onboard", response_model=TokenResponse)
async def onboard_company(
    body: OnboardCompanyRequest,
    auth: Annotated[AuthContext, Depends(get_subscribed_context)],
    container: Annotated[Container, Depends(get_container)],
    ip: Annotated[str | None, Depends(get_client_ip)],
) -> TokenResponse:
    result = await container.company_service.onboard(
        user_id=auth.user_id,
        data=OnboardCompanyInput(
            legal_name=body.legal_name,
            gstin=body.gstin,
            address=body.address,
            invoice_prefix=body.invoice_prefix,
        ),
        ip=ip,
    )
    return TokenResponse(**result)


@router.get("/me", response_model=CompanyResponse)
async def get_my_company(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> CompanyResponse:
    company = await container.company_service.get_profile(auth.company_id)
    return _company_response(company)


@router.patch("/me", response_model=CompanyResponse)
async def update_my_company(
    body: UpdateCompanyRequest,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER))],
    container: Annotated[Container, Depends(get_container)],
    ip: Annotated[str | None, Depends(get_client_ip)],
) -> CompanyResponse:
    company = await container.company_service.update_profile(
        company_id=auth.company_id,
        actor_id=auth.user_id,
        data=UpdateCompanyInput(**body.model_dump(exclude_unset=True)),
        ip=ip,
    )
    return _company_response(company)


@router.get("/me/staff", response_model=CompanyStaffResponse)
async def list_company_staff(
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER))],
    container: Annotated[Container, Depends(get_container)],
) -> CompanyStaffResponse:
    data = await container.staff_service.list_staff(auth.company_id)
    return CompanyStaffResponse(**data)


@router.post("/me/staff", response_model=dict)
async def invite_company_staff(
    body: InviteStaffRequest,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER))],
    container: Annotated[Container, Depends(get_container)],
) -> dict:
    from app.application.services.staff_service import InviteStaffInput

    invite = await container.staff_service.invite(
        company_id=auth.company_id,
        invited_by=auth.user_id,
        data=InviteStaffInput(email=body.email, role=UserRole(body.role)),
    )
    return invite


@router.delete("/me/staff/{invitation_id}", response_model=dict)
async def revoke_staff_invite(
    invitation_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER))],
    container: Annotated[Container, Depends(get_container)],
) -> dict:
    await container.staff_service.revoke(
        company_id=auth.company_id,
        invitation_id=invitation_id,
    )
    return {"ok": True}
