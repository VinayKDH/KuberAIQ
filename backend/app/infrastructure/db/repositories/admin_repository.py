"""Admin portal data access — platform-wide metrics and tenant control."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import extract, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import COMPLIANCE_OBLIGATION_STATUS_OVERDUE
from app.domain.enums import UserRole
from app.infrastructure.db.models.ai_session import AiSessionModel
from app.infrastructure.db.models.ai_usage_log import AiUsageLogModel
from app.infrastructure.db.models.audit import AuditLogModel
from app.infrastructure.db.models.company import CompanyModel
from app.infrastructure.db.models.compliance import CompanyComplianceStatusModel
from app.infrastructure.db.models.invoice import InvoiceModel
from app.infrastructure.db.models.payment import PaymentModel
from app.infrastructure.db.models.subscription import SubscriptionModel
from app.infrastructure.db.models.user import UserModel


@dataclass
class AdminDashboardData:
    total_tenants: int
    active_tenants: int
    suspended_tenants: int
    active_users: int
    invoices_this_month: int
    ai_sessions_total: int
    ai_tokens_this_month: int
    collections_volume_this_month: float
    subscription_breakdown: dict[str, int]


@dataclass
class AdminTenantRow:
    company: CompanyModel
    user_count: int
    invoice_count: int
    last_activity_at: datetime | None
    owner_email: str | None
    subscription_status: str


class SqlAlchemyAdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_dashboard_metrics(self) -> AdminDashboardData:
        now = datetime.now(timezone.utc)
        tenant_base = select(CompanyModel).where(CompanyModel.deleted_at.is_(None))
        total_tenants = int(
            (await self._session.execute(select(func.count()).select_from(tenant_base.subquery()))).scalar_one()
        )
        active_tenants = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(
                        tenant_base.where(CompanyModel.is_active.is_(True)).subquery()
                    )
                )
            ).scalar_one()
        )
        suspended_tenants = total_tenants - active_tenants

        active_users = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(
                        select(UserModel)
                        .where(UserModel.deleted_at.is_(None), UserModel.is_active.is_(True))
                        .subquery()
                    )
                )
            ).scalar_one()
        )

        invoices_this_month = int(
            (
                await self._session.execute(
                    select(func.count()).where(
                        extract("year", InvoiceModel.created_at) == now.year,
                        extract("month", InvoiceModel.created_at) == now.month,
                    )
                )
            ).scalar_one()
        )

        ai_sessions_total = int(
            (await self._session.execute(select(func.count()).select_from(AiSessionModel))).scalar_one()
        )

        ai_tokens_this_month = int(
            (
                await self._session.execute(
                    select(func.coalesce(func.sum(AiUsageLogModel.total_tokens), 0)).where(
                        extract("year", AiUsageLogModel.created_at) == now.year,
                        extract("month", AiUsageLogModel.created_at) == now.month,
                    )
                )
            ).scalar_one()
        )

        collections_volume = (
            await self._session.execute(
                select(func.coalesce(func.sum(PaymentModel.amount), 0)).where(
                    extract("year", PaymentModel.created_at) == now.year,
                    extract("month", PaymentModel.created_at) == now.month,
                )
            )
        ).scalar_one()

        sub_rows = (
            await self._session.execute(
                select(SubscriptionModel.status, func.count())
                .group_by(SubscriptionModel.status)
            )
        ).all()
        subscription_breakdown = {status: int(count) for status, count in sub_rows}

        return AdminDashboardData(
            total_tenants=total_tenants,
            active_tenants=active_tenants,
            suspended_tenants=suspended_tenants,
            active_users=active_users,
            invoices_this_month=invoices_this_month,
            ai_sessions_total=ai_sessions_total,
            ai_tokens_this_month=ai_tokens_this_month,
            collections_volume_this_month=float(collections_volume or 0),
            subscription_breakdown=subscription_breakdown,
        )

    async def list_tenants(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        active_only: bool | None = None,
    ) -> tuple[list[AdminTenantRow], int]:
        user_count_sq = (
            select(func.count(UserModel.id))
            .where(UserModel.company_id == CompanyModel.id, UserModel.deleted_at.is_(None))
            .correlate(CompanyModel)
            .scalar_subquery()
        )
        invoice_count_sq = (
            select(func.count(InvoiceModel.id))
            .where(InvoiceModel.company_id == CompanyModel.id)
            .correlate(CompanyModel)
            .scalar_subquery()
        )
        last_invoice_sq = (
            select(func.max(InvoiceModel.created_at))
            .where(InvoiceModel.company_id == CompanyModel.id)
            .correlate(CompanyModel)
            .scalar_subquery()
        )
        last_audit_sq = (
            select(func.max(AuditLogModel.created_at))
            .where(AuditLogModel.company_id == CompanyModel.id)
            .correlate(CompanyModel)
            .scalar_subquery()
        )
        owner_email_sq = (
            select(UserModel.email)
            .where(
                UserModel.company_id == CompanyModel.id,
                UserModel.role == UserRole.OWNER,
                UserModel.deleted_at.is_(None),
            )
            .order_by(UserModel.created_at.asc())
            .limit(1)
            .correlate(CompanyModel)
            .scalar_subquery()
        )
        subscription_status_sq = (
            select(SubscriptionModel.status)
            .join(UserModel, SubscriptionModel.user_id == UserModel.id)
            .where(
                UserModel.company_id == CompanyModel.id,
                UserModel.role == UserRole.OWNER,
                UserModel.deleted_at.is_(None),
            )
            .order_by(SubscriptionModel.created_at.desc())
            .limit(1)
            .correlate(CompanyModel)
            .scalar_subquery()
        )

        base = select(
            CompanyModel,
            user_count_sq.label("user_count"),
            invoice_count_sq.label("invoice_count"),
            func.coalesce(
                last_invoice_sq,
                last_audit_sq,
                CompanyModel.updated_at,
            ).label("last_activity_at"),
            owner_email_sq.label("owner_email"),
            func.coalesce(subscription_status_sq, "NONE").label("subscription_status"),
        ).where(CompanyModel.deleted_at.is_(None))

        if search:
            pattern = f"%{search.strip()}%"
            base = base.where(
                or_(
                    CompanyModel.legal_name.ilike(pattern),
                    CompanyModel.gstin.ilike(pattern),
                )
            )
        if active_only is True:
            base = base.where(CompanyModel.is_active.is_(True))
        elif active_only is False:
            base = base.where(CompanyModel.is_active.is_(False))

        count_stmt = select(func.count()).select_from(base.subquery())
        total = int((await self._session.execute(count_stmt)).scalar_one())

        stmt = (
            base.order_by(CompanyModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self._session.execute(stmt)).all()
        items = [
            AdminTenantRow(
                company=row[0],
                user_count=int(row.user_count or 0),
                invoice_count=int(row.invoice_count or 0),
                last_activity_at=row.last_activity_at,
                owner_email=row.owner_email,
                subscription_status=str(row.subscription_status),
            )
            for row in rows
        ]
        return items, total

    async def get_tenant(self, company_id: uuid.UUID) -> CompanyModel | None:
        stmt = select(CompanyModel).where(
            CompanyModel.id == company_id,
            CompanyModel.deleted_at.is_(None),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def set_tenant_active(self, company_id: uuid.UUID, *, is_active: bool) -> CompanyModel | None:
        company = await self.get_tenant(company_id)
        if not company:
            return None
        company.is_active = is_active
        await self._session.flush()
        return company

    async def list_users_for_company(self, company_id: uuid.UUID) -> list[UserModel]:
        stmt = (
            select(UserModel)
            .where(UserModel.company_id == company_id, UserModel.deleted_at.is_(None))
            .order_by(UserModel.created_at.asc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_recent_invoices(self, company_id: uuid.UUID, *, limit: int = 10) -> list[InvoiceModel]:
        stmt = (
            select(InvoiceModel)
            .where(InvoiceModel.company_id == company_id)
            .order_by(InvoiceModel.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def count_invoices(self, company_id: uuid.UUID) -> int:
        stmt = select(func.count()).where(InvoiceModel.company_id == company_id)
        return int((await self._session.execute(stmt)).scalar_one())

    async def count_compliance_overdue(self, company_id: uuid.UUID) -> int:
        stmt = select(func.count()).where(
            CompanyComplianceStatusModel.company_id == company_id,
            CompanyComplianceStatusModel.status == COMPLIANCE_OBLIGATION_STATUS_OVERDUE,
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def get_owner_subscription(
        self, company_id: uuid.UUID
    ) -> tuple[str, str | None]:
        stmt = (
            select(SubscriptionModel.status, SubscriptionModel.plan_code)
            .join(UserModel, SubscriptionModel.user_id == UserModel.id)
            .where(
                UserModel.company_id == company_id,
                UserModel.role == UserRole.OWNER,
                UserModel.deleted_at.is_(None),
            )
            .order_by(SubscriptionModel.created_at.desc())
            .limit(1)
        )
        row = (await self._session.execute(stmt)).first()
        if not row:
            return "NONE", None
        return str(row.status), row.plan_code

    async def ai_usage_for_company(self, company_id: uuid.UUID) -> tuple[int, int]:
        now = datetime.now(timezone.utc)
        tokens_stmt = select(func.coalesce(func.sum(AiUsageLogModel.total_tokens), 0)).where(
            AiUsageLogModel.company_id == company_id,
            extract("year", AiUsageLogModel.created_at) == now.year,
            extract("month", AiUsageLogModel.created_at) == now.month,
        )
        tokens = int((await self._session.execute(tokens_stmt)).scalar_one())
        sessions_stmt = select(func.count()).where(AiSessionModel.company_id == company_id)
        sessions = int((await self._session.execute(sessions_stmt)).scalar_one())
        return tokens, sessions

    async def list_users(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
    ) -> tuple[list[tuple[UserModel, str | None]], int]:
        company_name_sq = (
            select(CompanyModel.legal_name)
            .where(CompanyModel.id == UserModel.company_id)
            .correlate(UserModel)
            .scalar_subquery()
        )
        base = select(UserModel, company_name_sq.label("company_name")).where(
            UserModel.deleted_at.is_(None)
        )
        if search:
            pattern = f"%{search.strip()}%"
            base = base.where(
                or_(
                    UserModel.email.ilike(pattern),
                    UserModel.full_name.ilike(pattern),
                )
            )
        count_stmt = select(func.count()).select_from(base.subquery())
        total = int((await self._session.execute(count_stmt)).scalar_one())
        stmt = (
            base.order_by(UserModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self._session.execute(stmt)).all()
        return [(row[0], row.company_name) for row in rows], total

    async def get_ai_usage_summary(self) -> tuple[int, int, int, list[dict]]:
        now = datetime.now(timezone.utc)
        tokens_month_stmt = select(func.coalesce(func.sum(AiUsageLogModel.total_tokens), 0)).where(
            extract("year", AiUsageLogModel.created_at) == now.year,
            extract("month", AiUsageLogModel.created_at) == now.month,
        )
        tokens_total_stmt = select(func.coalesce(func.sum(AiUsageLogModel.total_tokens), 0))
        sessions_stmt = select(func.count()).select_from(AiSessionModel)

        tokens_month = int((await self._session.execute(tokens_month_stmt)).scalar_one())
        tokens_total = int((await self._session.execute(tokens_total_stmt)).scalar_one())
        sessions_total = int((await self._session.execute(sessions_stmt)).scalar_one())

        month_tokens_sq = (
            select(func.coalesce(func.sum(AiUsageLogModel.total_tokens), 0))
            .where(
                AiUsageLogModel.company_id == CompanyModel.id,
                extract("year", AiUsageLogModel.created_at) == now.year,
                extract("month", AiUsageLogModel.created_at) == now.month,
            )
            .correlate(CompanyModel)
            .scalar_subquery()
        )
        total_tokens_sq = (
            select(func.coalesce(func.sum(AiUsageLogModel.total_tokens), 0))
            .where(AiUsageLogModel.company_id == CompanyModel.id)
            .correlate(CompanyModel)
            .scalar_subquery()
        )
        sessions_sq = (
            select(func.count(AiSessionModel.id))
            .where(AiSessionModel.company_id == CompanyModel.id)
            .correlate(CompanyModel)
            .scalar_subquery()
        )

        tenant_stmt = (
            select(
                CompanyModel.id,
                CompanyModel.legal_name,
                month_tokens_sq.label("tokens_this_month"),
                total_tokens_sq.label("tokens_total"),
                sessions_sq.label("sessions_count"),
            )
            .where(CompanyModel.deleted_at.is_(None))
            .order_by(month_tokens_sq.desc())
            .limit(20)
        )
        tenant_rows = (await self._session.execute(tenant_stmt)).all()
        by_tenant = [
            {
                "company_id": str(row.id),
                "company_name": row.legal_name,
                "tokens_this_month": int(row.tokens_this_month or 0),
                "tokens_total": int(row.tokens_total or 0),
                "sessions_count": int(row.sessions_count or 0),
            }
            for row in tenant_rows
        ]
        return tokens_month, tokens_total, sessions_total, by_tenant

    async def list_audit_logs(
        self,
        *,
        page: int,
        page_size: int,
        company_id: uuid.UUID | None = None,
    ) -> tuple[list[tuple[AuditLogModel, str | None]], int]:
        company_name_sq = (
            select(CompanyModel.legal_name)
            .where(CompanyModel.id == AuditLogModel.company_id)
            .correlate(AuditLogModel)
            .scalar_subquery()
        )
        base = select(AuditLogModel, company_name_sq.label("company_name"))
        if company_id:
            base = base.where(AuditLogModel.company_id == company_id)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = int((await self._session.execute(count_stmt)).scalar_one())
        stmt = (
            base.order_by(AuditLogModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self._session.execute(stmt)).all()
        return [(row[0], row.company_name) for row in rows], total
