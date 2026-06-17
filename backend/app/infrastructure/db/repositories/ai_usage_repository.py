"""AI usage token repository."""
from __future__ import annotations

import uuid

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.ai_usage_log import AiUsageLogModel


class SqlAlchemyAiUsageLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_usage(
        self,
        *,
        company_id: uuid.UUID,
        session_id: str | None,
        model_name: str,
        tokens_in: int,
        tokens_out: int,
        total_tokens: int,
    ) -> None:
        self._session.add(
            AiUsageLogModel(
                company_id=company_id,
                session_id=session_id,
                model_name=model_name,
                tokens_in=max(tokens_in, 0),
                tokens_out=max(tokens_out, 0),
                total_tokens=max(total_tokens, 0),
            )
        )
        await self._session.flush()

    async def total_tokens_this_month(self, company_id: uuid.UUID) -> int:
        stmt = select(func.coalesce(func.sum(AiUsageLogModel.total_tokens), 0)).where(
            AiUsageLogModel.company_id == company_id,
            extract("year", AiUsageLogModel.created_at) == extract("year", func.now()),
            extract("month", AiUsageLogModel.created_at) == extract("month", func.now()),
        )
        return int((await self._session.execute(stmt)).scalar_one())
