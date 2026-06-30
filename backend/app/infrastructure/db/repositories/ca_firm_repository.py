"""CA firm repository."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.ca_firm import CaFirmModel


class SqlAlchemyCaFirmRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, firm_id: uuid.UUID) -> CaFirmModel | None:
        return await self._session.get(CaFirmModel, firm_id)

    async def get_by_name(self, name: str) -> CaFirmModel | None:
        stmt = select(CaFirmModel).where(CaFirmModel.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, *, name: str) -> CaFirmModel:
        model = CaFirmModel(id=uuid.uuid4(), name=name)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model

    async def list_members(self, firm_id: uuid.UUID) -> list:
        from app.infrastructure.db.models.user import UserModel

        stmt = select(UserModel).where(UserModel.ca_firm_id == firm_id, UserModel.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
