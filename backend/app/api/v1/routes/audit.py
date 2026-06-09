"""Audit log routes."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import AuthContext, get_container, get_tenant_context
from app.api.schemas.audit import AuditLogItem, AuditLogListResponse
from app.core.constants import DEFAULT_PAGE_SIZE
from app.core.container import Container

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100),
) -> AuditLogListResponse:
    async with container.uow_factory() as uow:
        rows, total = await uow.audit.list_for_company(
            auth.company_id,
            page=page,
            page_size=page_size,
        )
    return AuditLogListResponse(
        items=[
            AuditLogItem(
                id=str(row.id),
                entity_type=row.entity_type,
                entity_id=str(row.entity_id) if row.entity_id else None,
                action=row.action,
                actor_user_id=str(row.actor_user_id) if row.actor_user_id else None,
                ip_address=row.ip_address,
                created_at=row.created_at.isoformat(),
            )
            for row in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
