"""Staff invitation and company staff management."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta

from app.application.ports.repositories import StaffInvitationRecord, UserRecord
from app.core.datetime_utils import utc_now
from app.core.errors import ConflictError, NotFoundError
from app.domain.enums import UserRole


@dataclass
class InviteStaffInput:
    email: str
    role: UserRole = UserRole.STAFF


class StaffService:
    def __init__(self, uow_factory) -> None:
        self._uow_factory = uow_factory

    async def list_staff(self, company_id: uuid.UUID) -> dict:
        async with self._uow_factory() as uow:
            invitations = await uow.staff_invitations.list_for_company(company_id)
            users = []
            for role in (UserRole.OWNER, UserRole.STAFF, UserRole.VIEWER):
                users.extend(await self._list_users_by_role(uow, company_id, role))
        return {
            "users": users,
            "invitations": [self._invitation_dict(row) for row in invitations],
        }

    async def invite(
        self, *, company_id: uuid.UUID, invited_by: uuid.UUID, data: InviteStaffInput
    ) -> dict:
        email = data.email.strip().lower()
        async with self._uow_factory() as uow:
            existing = await uow.staff_invitations.find_active_by_email(company_id, email)
            if existing:
                raise ConflictError("Staff invitation already pending")
            invite = await uow.staff_invitations.create(
                StaffInvitationRecord(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    invited_by=invited_by,
                    email=email,
                    role=data.role.value,
                    status="PENDING",
                    expires_at=utc_now() + timedelta(days=7),
                )
            )
            return self._invitation_dict(invite)

    async def revoke(self, *, company_id: uuid.UUID, invitation_id: uuid.UUID) -> None:
        async with self._uow_factory() as uow:
            invite = await uow.staff_invitations.get_by_id(invitation_id)
            if not invite or invite.company_id != company_id:
                raise NotFoundError("Invitation not found")
            invite.status = "REVOKED"
            await uow.staff_invitations.update(invite)

    @staticmethod
    async def _list_users_by_role(uow, company_id: uuid.UUID, role: UserRole) -> list[dict]:
        from sqlalchemy import select

        from app.infrastructure.db.models.user import UserModel

        result = await uow._session.execute(  # noqa: SLF001
            select(UserModel).where(
                UserModel.company_id == company_id,
                UserModel.role == role,
                UserModel.deleted_at.is_(None),
                UserModel.is_active.is_(True),
            )
        )
        rows = result.scalars().all()
        return [
            {
                "id": str(row.id),
                "email": row.email,
                "full_name": row.full_name,
                "role": row.role.value if hasattr(row.role, "value") else str(row.role),
            }
            for row in rows
        ]

    @staticmethod
    def _invitation_dict(row: StaffInvitationRecord) -> dict:
        return {
            "id": str(row.id),
            "company_id": str(row.company_id),
            "email": row.email,
            "role": row.role,
            "status": row.status,
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
            "accepted_at": row.accepted_at.isoformat() if row.accepted_at else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
