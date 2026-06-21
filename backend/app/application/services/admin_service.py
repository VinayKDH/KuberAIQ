"""Admin portal business logic — platform metrics and tenant control."""
from __future__ import annotations

import uuid

from app.core.config import settings
from app.core.constants import ADMIN_DEMO_RESET_ALLOWED_ENVIRONMENTS
from app.core.errors import ForbiddenError, NotFoundError
from app.domain.enums import UserRole
from app.startup.seed import seed_demo_data


class AdminService:
    def __init__(self, uow_factory) -> None:
        self._uow_factory = uow_factory

    async def verify_auth(self) -> dict:
        return {"ok": True, "environment": settings.environment}

    async def get_dashboard_metrics(self):
        async with self._uow_factory() as uow:
            return await uow.admin.get_dashboard_metrics()

    async def list_tenants(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        active_only: bool | None = None,
    ):
        async with self._uow_factory() as uow:
            return await uow.admin.list_tenants(
                page=page,
                page_size=page_size,
                search=search,
                active_only=active_only,
            )

    async def get_tenant_detail(self, company_id: uuid.UUID):
        async with self._uow_factory() as uow:
            company = await uow.admin.get_tenant(company_id)
            if not company:
                raise NotFoundError("Tenant not found")
            users = await uow.admin.list_users_for_company(company_id)
            invoices = await uow.admin.list_recent_invoices(company_id)
            invoice_count = await uow.admin.count_invoices(company_id)
            overdue = await uow.admin.count_compliance_overdue(company_id)
            sub_status, plan_code = await uow.admin.get_owner_subscription(company_id)
            tokens, sessions = await uow.admin.ai_usage_for_company(company_id)
            owner_email = next((u.email for u in users if u.role == UserRole.OWNER), None)
            return {
                "company": company,
                "users": users,
                "recent_invoices": invoices,
                "invoice_count": invoice_count,
                "compliance_overdue_count": overdue,
                "subscription_status": sub_status,
                "plan_code": plan_code,
                "owner_email": owner_email,
                "ai_tokens_this_month": tokens,
                "ai_sessions_count": sessions,
            }

    async def set_tenant_status(self, company_id: uuid.UUID, *, is_active: bool):
        async with self._uow_factory() as uow:
            company = await uow.admin.set_tenant_active(company_id, is_active=is_active)
            if not company:
                raise NotFoundError("Tenant not found")
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=None,
                entity_type="company",
                entity_id=company_id,
                action="activate" if is_active else "suspend",
                before=None,
                after={"is_active": is_active},
            )
            await uow.commit()
            return company

    async def list_users(self, *, page: int, page_size: int, search: str | None = None):
        async with self._uow_factory() as uow:
            return await uow.admin.list_users(page=page, page_size=page_size, search=search)

    async def get_ai_usage(self):
        async with self._uow_factory() as uow:
            return await uow.admin.get_ai_usage_summary()

    async def list_audit_logs(
        self,
        *,
        page: int,
        page_size: int,
        company_id: uuid.UUID | None = None,
    ):
        async with self._uow_factory() as uow:
            return await uow.admin.list_audit_logs(
                page=page,
                page_size=page_size,
                company_id=company_id,
            )

    def get_system_health(self) -> dict:
        return {
            "environment": settings.environment,
            "auth_mode": "mock" if settings.use_mock_auth else "oauth",
            "llm_mode": "mock" if settings.use_mock_llm else "azure_openai",
            "blob_mode": "mock" if settings.use_mock_blob else "azure",
            "whatsapp_mode": "mock" if settings.use_mock_whatsapp else "live",
            "billing_mode": "mock" if settings.use_mock_billing else "razorpay",
            "google_oauth_configured": bool(settings.google_client_id),
            "entra_oauth_configured": bool(settings.entra_client_id),
            "azure_openai_configured": bool(
                settings.azure_openai_endpoint and settings.azure_openai_api_key
            ),
            "azure_blob_configured": bool(settings.azure_blob_connection_string),
            "whatsapp_configured": bool(
                settings.whatsapp_phone_number_id and settings.whatsapp_access_token
            ),
            "razorpay_configured": bool(settings.razorpay_key_id and settings.razorpay_key_secret),
            "razorpay_webhook_configured": bool(settings.razorpay_webhook_secret),
            "admin_api_key_configured": bool(settings.admin_api_key),
        }

    async def reset_demo_data(self) -> dict:
        if settings.environment not in ADMIN_DEMO_RESET_ALLOWED_ENVIRONMENTS:
            raise ForbiddenError("Demo reset is only allowed in local/dev environments")
        if not settings.use_mock_auth:
            raise ForbiddenError("Demo reset requires mock auth mode")
        await seed_demo_data()
        return {"ok": True, "message": "Demo data re-seeded"}
