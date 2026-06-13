"""CA persona — multi-client assignments, invites, context switching."""
from __future__ import annotations

import uuid

from app.application.ports.repositories import CaClientAssignmentRecord, UserRecord
from app.core.constants import CA_INVITE_ALREADY_EXISTS, CA_INVITE_NOT_FOUND, CA_NOT_ASSIGNED
from app.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.domain.enums import CaAssignmentStatus, UserRole
from app.infrastructure.auth.token_service import TokenService


class CaService:
    def __init__(self, uow_factory, tokens: TokenService | None = None) -> None:
        self._uow_factory = uow_factory
        self._tokens = tokens or TokenService()

    async def list_clients_for_ca(self, ca_user_id: uuid.UUID) -> list[dict]:
        async with self._uow_factory() as uow:
            assignments = await uow.ca_assignments.list_for_ca(ca_user_id)
            results: list[dict] = []
            for assignment in assignments:
                company = await uow.companies.get_by_id(assignment.company_id)
                if not company:
                    continue
                results.append(self._assignment_dict(assignment, company.legal_name, company.gstin))
            return results

    async def list_advisors_for_company(self, company_id: uuid.UUID) -> list[dict]:
        async with self._uow_factory() as uow:
            assignments = await uow.ca_assignments.list_for_company(company_id)
            results: list[dict] = []
            for assignment in assignments:
                ca_user = await uow.users.get_by_id(assignment.ca_user_id)
                if not ca_user:
                    continue
                row = self._assignment_dict(assignment)
                row["ca_email"] = ca_user.email
                row["ca_full_name"] = ca_user.full_name
                results.append(row)
            return results

    async def invite_advisor(
        self,
        *,
        company_id: uuid.UUID,
        invited_by: uuid.UUID,
        email: str,
        ca_firm_name: str | None = None,
    ) -> dict:
        email = email.strip().lower()
        if not email:
            raise ValidationAppError("Advisor email is required")

        async with self._uow_factory() as uow:
            ca_user = await uow.users.get_by_email(email)
            if not ca_user:
                local_part = email.split("@", 1)[0]
                ca_user = await uow.users.create(
                    UserRecord(
                        id=uuid.uuid4(),
                        company_id=None,
                        email=email,
                        full_name=local_part.replace(".", " ").title() or "CA Advisor",
                        role=UserRole.CA,
                    )
                )

            if ca_user.role != UserRole.CA:
                raise ValidationAppError("Invited user is not a CA account")

            existing = await uow.ca_assignments.get_by_ca_and_company(ca_user.id, company_id)
            if existing:
                if existing.status == CaAssignmentStatus.REVOKED:
                    existing.status = CaAssignmentStatus.PENDING
                    existing.invited_by = invited_by
                    existing.ca_firm_name = ca_firm_name
                    assignment = await uow.ca_assignments.update(existing)
                else:
                    raise ConflictError(CA_INVITE_ALREADY_EXISTS)
            else:
                assignment = await uow.ca_assignments.create(
                    CaClientAssignmentRecord(
                        id=uuid.uuid4(),
                        ca_user_id=ca_user.id,
                        company_id=company_id,
                        status=CaAssignmentStatus.PENDING,
                        invited_by=invited_by,
                        ca_firm_name=ca_firm_name,
                    )
                )
            await uow.commit()

        return self._assignment_dict(assignment, ca_email=ca_user.email, ca_full_name=ca_user.full_name)

    async def accept_invite(self, ca_user_id: uuid.UUID, assignment_id: uuid.UUID) -> dict:
        async with self._uow_factory() as uow:
            assignment = await uow.ca_assignments.get_by_id(assignment_id)
            if not assignment or assignment.ca_user_id != ca_user_id:
                raise NotFoundError(CA_INVITE_NOT_FOUND)
            if assignment.status != CaAssignmentStatus.PENDING:
                raise ConflictError("Invitation is not pending")

            assignment.status = CaAssignmentStatus.ACTIVE
            updated = await uow.ca_assignments.update(assignment)
            await uow.commit()

        return self._assignment_dict(updated)

    async def revoke(
        self,
        *,
        company_id: uuid.UUID,
        assignment_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> None:
        async with self._uow_factory() as uow:
            assignment = await uow.ca_assignments.get_by_id(assignment_id)
            if not assignment or assignment.company_id != company_id:
                raise NotFoundError(CA_INVITE_NOT_FOUND)
            if assignment.status == CaAssignmentStatus.REVOKED:
                return

            assignment.status = CaAssignmentStatus.REVOKED
            await uow.ca_assignments.update(assignment)
            await uow.commit()

    async def switch_context(
        self,
        user: UserRecord,
        company_id: uuid.UUID | None,
    ) -> dict:
        if user.role != UserRole.CA:
            raise ForbiddenError("Only CA users can switch client context")

        if company_id is not None:
            if not await self.verify_assignment(user.id, company_id):
                raise ForbiddenError(CA_NOT_ASSIGNED)

        context_user = UserRecord(
            id=user.id,
            company_id=company_id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            entra_oid=user.entra_oid,
            google_sub=user.google_sub,
        )
        return self._tokens.issue_tokens(context_user, subscription_active=True)

    async def verify_assignment(self, ca_user_id: uuid.UUID, company_id: uuid.UUID) -> bool:
        async with self._uow_factory() as uow:
            assignment = await uow.ca_assignments.get_by_ca_and_company(ca_user_id, company_id)
            return assignment is not None and assignment.status == CaAssignmentStatus.ACTIVE

    async def ca_dashboard(self, ca_user_id: uuid.UUID) -> dict:
        from app.application.services.compliance_service import ComplianceService

        compliance = ComplianceService(self._uow_factory)
        async with self._uow_factory() as uow:
            assignments = await uow.ca_assignments.list_active_for_ca(ca_user_id)

        clients: list[dict] = []
        for assignment in assignments:
            async with self._uow_factory() as uow:
                company = await uow.companies.get_by_id(assignment.company_id)
            if not company:
                continue
            obligations = await compliance.obligations(assignment.company_id)
            rows = obligations.get("obligations", [])
            upcoming = sorted(
                [
                    {
                        "title": row.get("title"),
                        "due_date": row.get("due_date"),
                        "status": row.get("status"),
                        "obligation_id": row.get("obligation_id"),
                    }
                    for row in rows
                    if row.get("status") not in ("COMPLETED", "NOT_APPLICABLE")
                ],
                key=lambda r: r.get("due_date") or "",
            )[:5]
            clients.append(
                {
                    "company_id": str(assignment.company_id),
                    "company_name": company.legal_name,
                    "gstin": company.gstin,
                    "upcoming_filings": upcoming,
                    "health_score": obligations.get("summary", {}).get("health_score"),
                }
            )

        return {"clients": clients, "client_count": len(clients)}

    @staticmethod
    def _assignment_dict(
        assignment: CaClientAssignmentRecord,
        company_name: str | None = None,
        gstin: str | None = None,
        *,
        ca_email: str | None = None,
        ca_full_name: str | None = None,
    ) -> dict:
        row = {
            "id": str(assignment.id),
            "ca_user_id": str(assignment.ca_user_id),
            "company_id": str(assignment.company_id),
            "status": assignment.status.value,
            "invited_by": str(assignment.invited_by),
            "ca_firm_name": assignment.ca_firm_name,
            "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
        }
        if company_name is not None:
            row["company_name"] = company_name
        if gstin is not None:
            row["gstin"] = gstin
        if ca_email is not None:
            row["ca_email"] = ca_email
        if ca_full_name is not None:
            row["ca_full_name"] = ca_full_name
        return row
