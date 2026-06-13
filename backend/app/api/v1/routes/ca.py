"""CA persona routes — client list, dashboard, invites, context switching."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import AuthContext, get_container, get_verified_auth_context
from app.api.schemas.auth import TokenResponse
from app.api.schemas.ca import (
    CaClientsResponse,
    CaDashboardResponse,
    CaSwitchContextRequest,
)
from app.core.container import Container
from app.core.errors import ForbiddenError
from app.domain.enums import UserRole

router = APIRouter(prefix="/ca", tags=["ca"])


def _require_ca(auth: AuthContext) -> AuthContext:
    if auth.role != UserRole.CA:
        raise ForbiddenError("CA access only")
    return auth


@router.get("/clients", response_model=CaClientsResponse)
async def list_ca_clients(
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> CaClientsResponse:
    _require_ca(auth)
    items = await container.ca_service.list_clients_for_ca(auth.user_id)
    return CaClientsResponse(items=items)


@router.get("/dashboard", response_model=CaDashboardResponse)
async def ca_dashboard(
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> CaDashboardResponse:
    _require_ca(auth)
    data = await container.ca_service.ca_dashboard(auth.user_id)
    return CaDashboardResponse(**data)


@router.post("/invitations/{assignment_id}/accept", response_model=CaClientsResponse)
async def accept_ca_invitation(
    assignment_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> CaClientsResponse:
    _require_ca(auth)
    await container.ca_service.accept_invite(auth.user_id, assignment_id)
    items = await container.ca_service.list_clients_for_ca(auth.user_id)
    return CaClientsResponse(items=items)


@router.post("/context", response_model=TokenResponse)
async def switch_ca_context(
    body: CaSwitchContextRequest,
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> TokenResponse:
    _require_ca(auth)
    async with container.uow_factory() as uow:
        user = await uow.users.get_by_id(auth.user_id)
    if not user:
        raise ForbiddenError("User not found")
    result = await container.ca_service.switch_context(user, uuid.UUID(body.company_id))
    return TokenResponse(**result)


@router.post("/context/clear", response_model=TokenResponse)
async def clear_ca_context(
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> TokenResponse:
    _require_ca(auth)
    async with container.uow_factory() as uow:
        user = await uow.users.get_by_id(auth.user_id)
    if not user:
        raise ForbiddenError("User not found")
    result = await container.ca_service.switch_context(user, None)
    return TokenResponse(**result)
