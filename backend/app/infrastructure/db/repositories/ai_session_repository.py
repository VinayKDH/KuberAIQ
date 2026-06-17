"""SQLAlchemy AI session repository."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import AiSessionRecord
from app.infrastructure.db.models.ai_session import AiSessionModel, AiSessionTurnModel


class SqlAlchemyAiSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_session(self, session_id: str, company_id: uuid.UUID) -> AiSessionRecord | None:
        stmt = select(AiSessionModel).where(
            AiSessionModel.id == session_id,
            AiSessionModel.company_id == company_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if not model:
            return None
        return AiSessionRecord(
            id=model.id,
            company_id=model.company_id,
            user_id=model.user_id,
            pending_action=model.pending_action,
        )

    async def create_or_touch_session(
        self, session_id: str, company_id: uuid.UUID, user_id: uuid.UUID
    ) -> AiSessionRecord:
        model = (
            await self._session.execute(
                select(AiSessionModel).where(
                    AiSessionModel.id == session_id,
                    AiSessionModel.company_id == company_id,
                )
            )
        ).scalar_one_or_none()
        if not model:
            model = AiSessionModel(id=session_id, company_id=company_id, user_id=user_id)
            self._session.add(model)
            await self._session.flush()
        return AiSessionRecord(
            id=model.id,
            company_id=model.company_id,
            user_id=model.user_id,
            pending_action=model.pending_action,
        )

    async def set_pending_action(
        self, session_id: str, company_id: uuid.UUID, pending_action: dict | None
    ) -> None:
        model = (
            await self._session.execute(
                select(AiSessionModel).where(
                    AiSessionModel.id == session_id,
                    AiSessionModel.company_id == company_id,
                )
            )
        ).scalar_one()
        model.pending_action = pending_action
        await self._session.flush()

    async def append_turn(
        self,
        session_id: str,
        company_id: uuid.UUID,
        user_message: str,
        assistant_payload: dict,
    ) -> None:
        max_turn_stmt = select(func.max(AiSessionTurnModel.turn_index)).where(
            AiSessionTurnModel.session_id == session_id
        )
        max_turn = (await self._session.execute(max_turn_stmt)).scalar_one()
        next_turn = (max_turn or 0) + 1
        turn = AiSessionTurnModel(
            session_id=session_id,
            turn_index=next_turn,
            user_message=user_message,
            assistant_payload=assistant_payload,
        )
        self._session.add(turn)
        await self._session.flush()

    async def list_recent_turns(
        self, session_id: str, company_id: uuid.UUID, limit: int
    ) -> list[dict]:
        stmt = (
            select(AiSessionTurnModel)
            .where(AiSessionTurnModel.session_id == session_id)
            .order_by(AiSessionTurnModel.turn_index.desc())
            .limit(limit)
        )
        rows = list((await self._session.execute(stmt)).scalars().all())
        rows.reverse()
        return [{"user": row.user_message, "assistant": row.assistant_payload} for row in rows]
