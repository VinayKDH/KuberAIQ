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

    async def get_by_entra_oid(self, entra_oid: str) -> UserRecord | None:
        stmt = select(UserModel).where(
            UserModel.entra_oid == entra_oid,
            UserModel.deleted_at.is_(None),
            UserModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_record(model) if model else None

    async def get_by_google_sub(self, google_sub: str) -> UserRecord | None:
        stmt = select(UserModel).where(
            UserModel.google_sub == google_sub,
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
            entra_oid=record.entra_oid,
            google_sub=record.google_sub,
            email=record.email.lower(),
            full_name=record.full_name,
            role=record.role,
            whatsapp_phone=record.whatsapp_phone,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_record(model)

    async def link_google_sub(self, user_id: uuid.UUID, google_sub: str) -> UserRecord:
        stmt = select(UserModel).where(UserModel.id == user_id, UserModel.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.google_sub = google_sub
        await self._session.flush()
        return self._to_record(model)

    async def assign_company(self, user_id: uuid.UUID, company_id: uuid.UUID) -> UserRecord:
        stmt = select(UserModel).where(UserModel.id == user_id, UserModel.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.company_id = company_id
        await self._session.flush()
        return self._to_record(model)

    async def find_owner_by_whatsapp_phone(self, phone: str) -> UserRecord | None:
        stmt = select(UserModel).where(
            UserModel.whatsapp_phone == phone,
            UserModel.role == UserRole.OWNER,
            UserModel.company_id.is_not(None),
            UserModel.deleted_at.is_(None),
            UserModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_record(model) if model else None

    async def update_whatsapp_phone(self, user_id: uuid.UUID, phone: str | None) -> UserRecord:
        stmt = select(UserModel).where(UserModel.id == user_id, UserModel.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.whatsapp_phone = phone
        await self._session.flush()
        return self._to_record(model)

    @staticmethod
    def _to_record(model: UserModel) -> UserRecord:
        return UserRecord(
            id=model.id,
            company_id=model.company_id,
            entra_oid=model.entra_oid,
            google_sub=model.google_sub,
            email=model.email,
            full_name=model.full_name,
            role=UserRole(model.role),
            whatsapp_phone=model.whatsapp_phone,
        )
