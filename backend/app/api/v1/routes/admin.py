"""Admin routes protected by ADMIN_API_KEY."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_container, require_admin_key
from app.api.schemas.admin import (
    AdminAiUsageResponse,
    AdminAiUsageTenantItem,
    AdminAuditLogItem,
    AdminAuditLogListResponse,
    AdminAuthVerifyResponse,
    AdminDashboardMetrics,
    AdminDemoResetResponse,
    AdminSystemHealthResponse,
    AdminTenantAiUsage,
    AdminTenantDetail,
    AdminTenantInvoiceItem,
    AdminTenantListItem,
    AdminTenantListResponse,
    AdminTenantStatusResponse,
    AdminTenantStatusUpdate,
    AdminTenantUserItem,
    AdminUserListItem,
    AdminUserListResponse,
)
from app.application.services.admin_service import AdminService
from app.core.config import settings
from app.core.constants import DEFAULT_PAGE_SIZE
from app.core.container import Container

router = APIRouter(prefix="/admin", tags=["admin"])


def _admin_service(container: Container) -> AdminService:
    return AdminService(container.uow_factory)


@router.post("/auth/verify", response_model=AdminAuthVerifyResponse)
async def verify_admin_auth(
    _: Annotated[None, Depends(require_admin_key)],
) -> AdminAuthVerifyResponse:
    return AdminAuthVerifyResponse(ok=True, environment=settings.environment)


@router.get("/dashboard", response_model=AdminDashboardMetrics)
async def admin_dashboard(
    _: Annotated[None, Depends(require_admin_key)],
    container: Annotated[Container, Depends(get_container)],
) -> AdminDashboardMetrics:
    data = await _admin_service(container).get_dashboard_metrics()
    return AdminDashboardMetrics(
        total_tenants=data.total_tenants,
        active_tenants=data.active_tenants,
        suspended_tenants=data.suspended_tenants,
        active_users=data.active_users,
        invoices_this_month=data.invoices_this_month,
        ai_sessions_total=data.ai_sessions_total,
        ai_tokens_this_month=data.ai_tokens_this_month,
        collections_volume_this_month=data.collections_volume_this_month,
        subscription_breakdown=data.subscription_breakdown,
    )


@router.get("/tenants", response_model=AdminTenantListResponse)
async def list_tenants(
    _: Annotated[None, Depends(require_admin_key)],
    container: Annotated[Container, Depends(get_container)],
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100),
    search: str | None = None,
    active_only: bool | None = None,
) -> AdminTenantListResponse:
    rows, total = await _admin_service(container).list_tenants(
        page=page,
        page_size=page_size,
        search=search,
        active_only=active_only,
    )
    return AdminTenantListResponse(
        items=[
            AdminTenantListItem(
                company_id=str(row.company.id),
                legal_name=row.company.legal_name,
                gstin=row.company.gstin,
                msme_segment=row.company.msme_segment,
                is_active=row.company.is_active,
                created_at=row.company.created_at.isoformat(),
                user_count=row.user_count,
                invoice_count=row.invoice_count,
                last_activity_at=row.last_activity_at.isoformat() if row.last_activity_at else None,
                owner_email=row.owner_email,
                subscription_status=row.subscription_status,
            )
            for row in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/tenants/{company_id}", response_model=AdminTenantDetail)
async def get_tenant_detail(
    company_id: uuid.UUID,
    _: Annotated[None, Depends(require_admin_key)],
    container: Annotated[Container, Depends(get_container)],
) -> AdminTenantDetail:
    detail = await _admin_service(container).get_tenant_detail(company_id)
    company = detail["company"]
    return AdminTenantDetail(
        company_id=str(company.id),
        legal_name=company.legal_name,
        gstin=company.gstin,
        state_code=company.state_code,
        address=company.address,
        msme_segment=company.msme_segment,
        is_active=company.is_active,
        created_at=company.created_at.isoformat(),
        updated_at=company.updated_at.isoformat(),
        owner_email=detail["owner_email"],
        subscription_status=detail["subscription_status"],
        plan_code=detail["plan_code"],
        user_count=len(detail["users"]),
        invoice_count=detail["invoice_count"],
        compliance_overdue_count=detail["compliance_overdue_count"],
        users=[
            AdminTenantUserItem(
                id=str(u.id),
                email=u.email,
                full_name=u.full_name,
                role=u.role.value if hasattr(u.role, "value") else str(u.role),
                is_active=u.is_active,
            )
            for u in detail["users"]
        ],
        recent_invoices=[
            AdminTenantInvoiceItem(
                id=str(inv.id),
                invoice_number=inv.invoice_number,
                status=inv.status.value if hasattr(inv.status, "value") else str(inv.status),
                grand_total=float(inv.grand_total),
                issue_date=inv.issue_date.isoformat(),
            )
            for inv in detail["recent_invoices"]
        ],
        ai_usage=AdminTenantAiUsage(
            tokens_this_month=detail["ai_tokens_this_month"],
            sessions_count=detail["ai_sessions_count"],
        ),
    )


@router.patch("/tenants/{company_id}/status", response_model=AdminTenantStatusResponse)
async def update_tenant_status(
    company_id: uuid.UUID,
    body: AdminTenantStatusUpdate,
    _: Annotated[None, Depends(require_admin_key)],
    container: Annotated[Container, Depends(get_container)],
) -> AdminTenantStatusResponse:
    company = await _admin_service(container).set_tenant_status(company_id, is_active=body.is_active)
    return AdminTenantStatusResponse(company_id=str(company.id), is_active=company.is_active)


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    _: Annotated[None, Depends(require_admin_key)],
    container: Annotated[Container, Depends(get_container)],
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100),
    search: str | None = None,
) -> AdminUserListResponse:
    rows, total = await _admin_service(container).list_users(
        page=page,
        page_size=page_size,
        search=search,
    )
    return AdminUserListResponse(
        items=[
            AdminUserListItem(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                role=user.role.value if hasattr(user.role, "value") else str(user.role),
                company_id=str(user.company_id) if user.company_id else None,
                company_name=company_name,
                is_active=user.is_active,
                created_at=user.created_at.isoformat(),
            )
            for user, company_name in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/ai-usage", response_model=AdminAiUsageResponse)
async def get_ai_usage(
    _: Annotated[None, Depends(require_admin_key)],
    container: Annotated[Container, Depends(get_container)],
) -> AdminAiUsageResponse:
    tokens_month, tokens_total, sessions_total, by_tenant = await _admin_service(
        container
    ).get_ai_usage()
    return AdminAiUsageResponse(
        tokens_this_month=tokens_month,
        tokens_total=tokens_total,
        sessions_total=sessions_total,
        by_tenant=[AdminAiUsageTenantItem(**row) for row in by_tenant],
    )


@router.get("/system-health", response_model=AdminSystemHealthResponse)
async def get_system_health(
    _: Annotated[None, Depends(require_admin_key)],
    container: Annotated[Container, Depends(get_container)],
) -> AdminSystemHealthResponse:
    return AdminSystemHealthResponse(**_admin_service(container).get_system_health())


@router.get("/audit-logs", response_model=AdminAuditLogListResponse)
async def list_audit_logs(
    _: Annotated[None, Depends(require_admin_key)],
    container: Annotated[Container, Depends(get_container)],
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100),
    company_id: uuid.UUID | None = None,
) -> AdminAuditLogListResponse:
    rows, total = await _admin_service(container).list_audit_logs(
        page=page,
        page_size=page_size,
        company_id=company_id,
    )
    return AdminAuditLogListResponse(
        items=[
            AdminAuditLogItem(
                id=str(log.id),
                company_id=str(log.company_id),
                company_name=company_name,
                entity_type=log.entity_type,
                entity_id=str(log.entity_id) if log.entity_id else None,
                action=log.action,
                actor_user_id=str(log.actor_user_id) if log.actor_user_id else None,
                ip_address=log.ip_address,
                created_at=log.created_at.isoformat(),
            )
            for log, company_name in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/demo/reset", response_model=AdminDemoResetResponse)
async def reset_demo_data(
    _: Annotated[None, Depends(require_admin_key)],
    container: Annotated[Container, Depends(get_container)],
) -> AdminDemoResetResponse:
    result = await _admin_service(container).reset_demo_data()
    return AdminDemoResetResponse(**result)
