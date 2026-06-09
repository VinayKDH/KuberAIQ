"""SQLAlchemy implementation of AuditRepository."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import AuditLogRecord
from app.infrastructure.db.models.audit import AuditLogModel


class SqlAlchemyAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log(
        self,
        *,
        company_id: uuid.UUID,
        actor_user_id: uuid.UUID | None,
        entity_type: str,
        entity_id: uuid.UUID | None,
        action: str,
        before: dict | None,
        after: dict | None,
        ip_address: str | None = None,
    ) -> None:
        entry = AuditLogModel(
            company_id=company_id,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            before=before,
            after=after,
            ip_address=ip_address,
        )
        self._session.add(entry)
        await self._session.flush()

    async def list_for_company(
        self,
        company_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLogRecord], int]:
        base = select(AuditLogModel).where(AuditLogModel.company_id == company_id)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = int((await self._session.execute(count_stmt)).scalar_one())
        stmt = (
            base.order_by(AuditLogModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._to_record(row) for row in rows], total

    @staticmethod
    def _to_record(model: AuditLogModel) -> AuditLogRecord:
        return AuditLogRecord(
            id=model.id,
            company_id=model.company_id,
            actor_user_id=model.actor_user_id,
            entity_type=model.entity_type,
            entity_id=model.entity_id,
            action=model.action,
            before=model.before,
            after=model.after,
            ip_address=model.ip_address,
            created_at=model.created_at,
        )
