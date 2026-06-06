"""SQLAlchemy implementation of AuditRepository."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

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
