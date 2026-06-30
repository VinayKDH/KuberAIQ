"""CA persona routes — client list, dashboard, invites, context switching."""
from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import AuthContext, get_container, get_verified_auth_context
from app.api.schemas.auth import TokenResponse
from app.api.schemas.ca import (
    CaBulkFilingRequest,
    CaBulkFilingResponse,
    CaBulkGstrResponse,
    CaClientTasksResponse,
    CaClientsResponse,
    CaCreateTaskRequest,
    CaDashboardResponse,
    CaFilingActionRequest,
    CaFilingActionResponse,
    CaSwitchContextRequest,
    CaUpdateTaskRequest,
)
from app.core.container import Container
from app.core.errors import ForbiddenError
from app.domain.enums import UserRole
from fastapi.responses import PlainTextResponse, Response

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
    advisor_id: uuid.UUID | None = Query(None),
) -> CaDashboardResponse:
    _require_ca(auth)
    data = await container.ca_service.ca_dashboard(auth.user_id, advisor_id=advisor_id)
    return CaDashboardResponse(**data)


@router.get("/firm/advisors")
async def list_firm_advisors(
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> dict:
    _require_ca(auth)
    advisors = await container.ca_service.list_firm_advisors(auth.user_id)
    return {"items": advisors}


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


@router.get("/reports/gstr1/bulk", response_model=CaBulkGstrResponse)
async def ca_bulk_gstr1(
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    company_ids: list[uuid.UUID] | None = Query(default=None),
) -> CaBulkGstrResponse:
    _require_ca(auth)
    data = await container.ca_service.gstr1_bulk(
        auth.user_id, from_date, to_date, company_ids=company_ids
    )
    return CaBulkGstrResponse(**data)


@router.get("/reports/gstr3b/bulk", response_model=CaBulkGstrResponse)
async def ca_bulk_gstr3b(
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    company_ids: list[uuid.UUID] | None = Query(default=None),
) -> CaBulkGstrResponse:
    _require_ca(auth)
    data = await container.ca_service.gstr3b_bulk(
        auth.user_id, from_date, to_date, company_ids=company_ids
    )
    return CaBulkGstrResponse(**data)


@router.post(
    "/clients/{company_id}/filing/{obligation_id}/complete",
    response_model=CaFilingActionResponse,
)
async def ca_complete_client_filing(
    company_id: uuid.UUID,
    obligation_id: str,
    body: CaFilingActionRequest,
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> CaFilingActionResponse:
    _require_ca(auth)
    try:
        data = await container.ca_service.complete_client_filing(
            auth.user_id,
            company_id,
            obligation_id,
            period_key=body.period_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CaFilingActionResponse(**data)


@router.post(
    "/clients/{company_id}/filing/{obligation_id}/skip",
    response_model=CaFilingActionResponse,
)
async def ca_skip_client_filing(
    company_id: uuid.UUID,
    obligation_id: str,
    body: CaFilingActionRequest,
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> CaFilingActionResponse:
    _require_ca(auth)
    try:
        data = await container.ca_service.skip_client_filing(
            auth.user_id,
            company_id,
            obligation_id,
            period_key=body.period_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CaFilingActionResponse(**data)


@router.post("/filing/bulk-complete", response_model=CaBulkFilingResponse)
async def ca_bulk_complete_filings(
    body: CaBulkFilingRequest,
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> CaBulkFilingResponse:
    _require_ca(auth)
    data = await container.ca_service.bulk_complete_filings(
        auth.user_id,
        company_ids=[uuid.UUID(cid) for cid in body.company_ids],
        obligation_ids=body.obligation_ids,
        period_key=body.period_key,
    )
    return CaBulkFilingResponse(**data)


@router.get("/filing/export.csv")
async def ca_export_filing_csv(
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
    due_before: date | None = Query(default=None),
    due_after: date | None = Query(default=None),
) -> PlainTextResponse:
    _require_ca(auth)
    csv_text = await container.ca_service.export_filing_status_csv(
        auth.user_id, due_before=due_before, due_after=due_after
    )
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="filing-status.csv"'},
    )


@router.get("/clients/{company_id}/tasks", response_model=CaClientTasksResponse)
async def list_ca_client_tasks(
    company_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> CaClientTasksResponse:
    _require_ca(auth)
    items = await container.ca_service.list_client_tasks(auth.user_id, company_id)
    return CaClientTasksResponse(items=items)


@router.post("/clients/{company_id}/tasks", response_model=CaClientTasksResponse)
async def create_ca_client_task(
    company_id: uuid.UUID,
    body: CaCreateTaskRequest,
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> CaClientTasksResponse:
    _require_ca(auth)
    await container.ca_service.create_client_task(
        auth.user_id,
        company_id,
        title=body.title,
        description=body.description,
        due_date=body.due_date,
    )
    items = await container.ca_service.list_client_tasks(auth.user_id, company_id)
    return CaClientTasksResponse(items=items)


@router.patch("/clients/{company_id}/tasks/{task_id}", response_model=CaClientTasksResponse)
async def update_ca_client_task(
    company_id: uuid.UUID,
    task_id: uuid.UUID,
    body: CaUpdateTaskRequest,
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> CaClientTasksResponse:
    _require_ca(auth)
    await container.ca_service.update_client_task(
        auth.user_id,
        company_id,
        task_id,
        title=body.title,
        description=body.description,
        due_date=body.due_date,
        status=body.status,
    )
    items = await container.ca_service.list_client_tasks(auth.user_id, company_id)
    return CaClientTasksResponse(items=items)


@router.delete("/clients/{company_id}/tasks/{task_id}", status_code=204, response_class=Response)
async def delete_ca_client_task(
    company_id: uuid.UUID,
    task_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> Response:
    _require_ca(auth)
    await container.ca_service.delete_client_task(auth.user_id, company_id, task_id)
    return Response(status_code=204)


@router.get("/clients/{company_id}/compliance-pack")
async def ca_compliance_pack(
    company_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
) -> dict:
    _require_ca(auth)
    return await container.ca_service.compliance_pack(
        auth.user_id, company_id, from_date=from_date, to_date=to_date
    )
