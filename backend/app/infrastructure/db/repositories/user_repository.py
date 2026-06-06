"""SQLAlchemy implementation of UserRepository."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import UserRecord
from app.domain.enums import UserRole
from app.infrastructure.db.models.user import UserModel


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> UserRecord | None:
        stmt = select(UserModel).where(
            UserModel.id == user_id,
            UserModel.deleted_at.is_(None),
            UserModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_record(model) if model else None

    async def get_by_email(self, email: str) -> UserRecord | None:
        stmt = select(UserModel).where(
            UserModel.email == email.lower(),
            UserModel.deleted_at.is_(None),
            UserModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_record(model) if model else None

    async def create(self, record: UserRecord) -> UserRecord:
        model = UserModel(
            id=record.id,
            company_id=record.company_id,
            email=record.email.lower(),
            full_name=record.full_name,
            role=record.role,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_record(model)

    @staticmethod
    def _to_record(model: UserModel) -> UserRecord:
        return UserRecord(
            id=model.id,
            company_id=model.company_id,
            email=model.email,
            full_name=model.full_name,
            role=UserRole(model.role),
        )
