"""Company advisor (CA) management routes."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import AuthContext, get_container, get_tenant_context, require_roles
from app.api.schemas.ca import AdvisorItem, AdvisorsResponse, InviteAdvisorRequest
from app.core.container import Container
from app.domain.enums import UserRole

router = APIRouter(prefix="/companies/me/advisors", tags=["advisors"])


@router.get("", response_model=AdvisorsResponse)
async def list_advisors(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> AdvisorsResponse:
    items = await container.ca_service.list_advisors_for_company(auth.company_id)
    return AdvisorsResponse(items=items)


@router.post("", response_model=AdvisorItem, status_code=201)
async def invite_advisor(
    body: InviteAdvisorRequest,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER))],
    container: Annotated[Container, Depends(get_container)],
) -> AdvisorItem:
    item = await container.ca_service.invite_advisor(
        company_id=auth.company_id,
        invited_by=auth.user_id,
        email=body.email,
        ca_firm_name=body.ca_firm_name,
    )
    return AdvisorItem(**item)


@router.delete("/{assignment_id}", status_code=204, response_class=Response)
async def revoke_advisor(
    assignment_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(require_roles(UserRole.OWNER))],
    container: Annotated[Container, Depends(get_container)],
) -> Response:
    await container.ca_service.revoke(
        company_id=auth.company_id,
        assignment_id=assignment_id,
        actor_id=auth.user_id,
    )
    return Response(status_code=204)
