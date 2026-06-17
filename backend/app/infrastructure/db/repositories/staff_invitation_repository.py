"""Staff invitation repository."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import StaffInvitationRecord
from app.infrastructure.db.models.staff_invitation import StaffInvitationModel


class SqlAlchemyStaffInvitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: StaffInvitationRecord) -> StaffInvitationRecord:
        model = StaffInvitationModel(
            id=record.id,
            company_id=record.company_id,
            invited_by=record.invited_by,
            email=record.email,
            role=record.role,
            status=record.status,
            expires_at=record.expires_at,
            accepted_at=record.accepted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_record(model)

    async def list_for_company(self, company_id: uuid.UUID) -> list[StaffInvitationRecord]:
        stmt = select(StaffInvitationModel).where(StaffInvitationModel.company_id == company_id)
        models = (await self._session.execute(stmt)).scalars().all()
        return [self._to_record(model) for model in models]

    async def get_by_id(self, invitation_id: uuid.UUID) -> StaffInvitationRecord | None:
        model = (
            await self._session.execute(
                select(StaffInvitationModel).where(StaffInvitationModel.id == invitation_id)
            )
        ).scalar_one_or_none()
        return self._to_record(model) if model else None

    async def update(self, record: StaffInvitationRecord) -> StaffInvitationRecord:
        model = (
            await self._session.execute(
                select(StaffInvitationModel).where(StaffInvitationModel.id == record.id)
            )
        ).scalar_one()
        model.status = record.status
        model.role = record.role
        model.accepted_at = record.accepted_at
        model.expires_at = record.expires_at
        await self._session.flush()
        return self._to_record(model)

    async def find_active_by_email(
        self, company_id: uuid.UUID, email: str
    ) -> StaffInvitationRecord | None:
        model = (
            await self._session.execute(
                select(StaffInvitationModel).where(
                    StaffInvitationModel.company_id == company_id,
                    StaffInvitationModel.email == email.lower().strip(),
                    StaffInvitationModel.status == "PENDING",
                )
            )
        ).scalar_one_or_none()
        return self._to_record(model) if model else None

    @staticmethod
    def _to_record(model: StaffInvitationModel) -> StaffInvitationRecord:
        return StaffInvitationRecord(
            id=model.id,
            company_id=model.company_id,
            invited_by=model.invited_by,
            email=model.email,
            role=model.role,
            status=model.status,
            expires_at=model.expires_at,
            accepted_at=model.accepted_at,
            created_at=model.created_at,
        )
