"""CA persona — multi-client assignments, invites, context switching."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from app.application.ports.repositories import CaClientAssignmentRecord, CaClientTaskRecord, UserRecord
from app.core.constants import (
    CA_FILING_CHECKLIST_IDS,
    CA_FILING_DUE_SOON_DAYS,
    CA_FILING_EXPORT_CSV_HEADERS,
    CA_HEALTH_SCORE_AT_RISK,
    CA_INVITE_ALREADY_EXISTS,
    CA_INVITE_NOT_FOUND,
    CA_NOT_ASSIGNED,
    CA_OVERDUE_ALERT_THRESHOLD,
    CA_TASK_STATUS_DONE,
    CA_TASK_STATUS_PENDING,
)
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
            async with self._uow_factory() as uow:
                collectible = await uow.invoices.list_collectible(assignment.company_id)
            overdue_total = sum(
                (inv.amount_due.amount for inv in collectible if inv.status.value == "OVERDUE"),
                start=0,
            )
            rows = obligations.get("obligations", [])
            summary = obligations.get("summary", {})
            profile_complete = obligations.get("profile_complete", False)
            filing_checklist = self._build_filing_checklist(rows)
            filings_due_soon = self._count_filings_due_soon(filing_checklist)
            upcoming = sorted(
                [
                    {
                        "title": row.get("title"),
                        "due_date": row.get("due_date"),
                        "status": row.get("status"),
                        "obligation_id": row.get("id"),
                    }
                    for row in rows
                    if row.get("status") not in ("COMPLETED", "NOT_APPLICABLE", "SKIPPED")
                ],
                key=lambda r: r.get("due_date") or "",
            )[:5]
            health_score = summary.get("health_score")
            risk_level = self._compute_risk_level(
                gstin=company.gstin,
                overdue_total=overdue_total,
                profile_complete=profile_complete,
                filings_due_soon=filings_due_soon,
                health_score=health_score,
                compliance_overdue=summary.get("overdue", 0),
            )
            clients.append(
                {
                    "company_id": str(assignment.company_id),
                    "company_name": company.legal_name,
                    "gstin": company.gstin,
                    "upcoming_filings": upcoming,
                    "filing_checklist": filing_checklist,
                    "health_score": health_score,
                    "overdue_total": overdue_total,
                    "profile_complete": profile_complete,
                    "filings_due_soon": filings_due_soon,
                    "compliance_overdue": summary.get("overdue", 0),
                    "compliance_due_this_week": summary.get("due_this_week", 0),
                    "risk_level": risk_level,
                }
            )

        clients.sort(key=lambda c: {"high": 0, "medium": 1, "low": 2}.get(c["risk_level"], 3))
        portfolio = self._build_portfolio_summary(clients)
        filings_due_this_month = self._count_filings_due_this_month(clients)
        return {
            "clients": clients,
            "client_count": len(clients),
            "portfolio": portfolio,
            "filings_due_this_month": filings_due_this_month,
        }

    async def complete_client_filing(
        self,
        ca_user_id: uuid.UUID,
        company_id: uuid.UUID,
        obligation_id: str,
        *,
        period_key: str | None = None,
    ) -> dict:
        if obligation_id not in CA_FILING_CHECKLIST_IDS:
            raise ValidationAppError("Invalid filing obligation")
        if not await self.verify_assignment(ca_user_id, company_id):
            raise ForbiddenError(CA_NOT_ASSIGNED)
        from app.application.services.compliance_service import ComplianceService

        compliance = ComplianceService(self._uow_factory)
        return await compliance.complete_obligation(
            company_id=company_id,
            actor_id=ca_user_id,
            obligation_id=obligation_id,
            period_key=period_key,
        )

    async def skip_client_filing(
        self,
        ca_user_id: uuid.UUID,
        company_id: uuid.UUID,
        obligation_id: str,
        *,
        period_key: str | None = None,
    ) -> dict:
        if obligation_id not in CA_FILING_CHECKLIST_IDS:
            raise ValidationAppError("Invalid filing obligation")
        if not await self.verify_assignment(ca_user_id, company_id):
            raise ForbiddenError(CA_NOT_ASSIGNED)
        from app.application.services.compliance_service import ComplianceService

        compliance = ComplianceService(self._uow_factory)
        return await compliance.skip_obligation(
            company_id=company_id,
            actor_id=ca_user_id,
            obligation_id=obligation_id,
            period_key=period_key,
        )

    async def gstr1_bulk(
        self,
        ca_user_id: uuid.UUID,
        from_date,
        to_date,
        *,
        company_ids: list[uuid.UUID] | None = None,
    ) -> dict:
        from app.application.services.gstr_report_service import GstrReportService

        service = GstrReportService(self._uow_factory)
        async with self._uow_factory() as uow:
            assignments = await uow.ca_assignments.list_active_for_ca(ca_user_id)
            if company_ids is not None:
                allowed = {row.company_id for row in assignments}
                company_ids = [cid for cid in company_ids if cid in allowed]
            else:
                company_ids = [row.company_id for row in assignments]
            companies = [await uow.companies.get_by_id(cid) for cid in company_ids]
        items = []
        for company in companies:
            if not company:
                continue
            report = await service.gstr1_report(company.id, from_date, to_date)
            items.append(
                {
                    "company_id": str(company.id),
                    "company_name": company.legal_name,
                    "gstin": company.gstin,
                    "report": report,
                }
            )
        return {"from": from_date.isoformat(), "to": to_date.isoformat(), "items": items}

    async def gstr3b_bulk(
        self,
        ca_user_id: uuid.UUID,
        from_date,
        to_date,
        *,
        company_ids: list[uuid.UUID] | None = None,
    ) -> dict:
        from app.application.services.gstr_report_service import GstrReportService

        service = GstrReportService(self._uow_factory)
        async with self._uow_factory() as uow:
            assignments = await uow.ca_assignments.list_active_for_ca(ca_user_id)
            if company_ids is not None:
                allowed = {row.company_id for row in assignments}
                company_ids = [cid for cid in company_ids if cid in allowed]
            else:
                company_ids = [row.company_id for row in assignments]
            companies = [await uow.companies.get_by_id(cid) for cid in company_ids]
        items = []
        for company in companies:
            if not company:
                continue
            report = await service.gstr3b_report(company.id, from_date, to_date)
            items.append(
                {
                    "company_id": str(company.id),
                    "company_name": company.legal_name,
                    "gstin": company.gstin,
                    "report": report,
                }
            )
        return {"from": from_date.isoformat(), "to": to_date.isoformat(), "items": items}

    async def bulk_complete_filings(
        self,
        ca_user_id: uuid.UUID,
        *,
        company_ids: list[uuid.UUID],
        obligation_ids: list[str],
        period_key: str | None = None,
    ) -> dict:
        completed = 0
        for company_id in company_ids:
            if not await self.verify_assignment(ca_user_id, company_id):
                continue
            for obligation_id in obligation_ids:
                if obligation_id not in CA_FILING_CHECKLIST_IDS:
                    continue
                await self.complete_client_filing(
                    ca_user_id, company_id, obligation_id, period_key=period_key
                )
                completed += 1
        return {"completed": completed}

    async def export_filing_status_csv(
        self,
        ca_user_id: uuid.UUID,
        *,
        due_before: date | None = None,
        due_after: date | None = None,
    ) -> str:
        import csv
        from io import StringIO

        dashboard = await self.ca_dashboard(ca_user_id)
        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(CA_FILING_EXPORT_CSV_HEADERS))
        writer.writeheader()
        for client in dashboard["clients"]:
            for item in client.get("filing_checklist", []):
                due_str = item.get("due_date")
                if due_before and due_str and date.fromisoformat(due_str) > due_before:
                    continue
                if due_after and due_str and date.fromisoformat(due_str) < due_after:
                    continue
                writer.writerow(
                    {
                        "company_name": client["company_name"],
                        "gstin": client.get("gstin") or "",
                        "obligation_id": item["obligation_id"],
                        "title": item["title"],
                        "due_date": due_str or "",
                        "status": item["status"],
                        "period_key": item.get("period_key") or "",
                    }
                )
        return buffer.getvalue()

    async def list_client_tasks(
        self, ca_user_id: uuid.UUID, company_id: uuid.UUID
    ) -> list[dict]:
        if not await self.verify_assignment(ca_user_id, company_id):
            raise ForbiddenError(CA_NOT_ASSIGNED)
        async with self._uow_factory() as uow:
            tasks = await uow.ca_tasks.list_for_company(company_id, ca_user_id=ca_user_id)
        return [self._task_dict(t) for t in tasks]

    async def create_client_task(
        self,
        ca_user_id: uuid.UUID,
        company_id: uuid.UUID,
        *,
        title: str,
        description: str | None = None,
        due_date: date | None = None,
    ) -> dict:
        if not await self.verify_assignment(ca_user_id, company_id):
            raise ForbiddenError(CA_NOT_ASSIGNED)
        title = title.strip()
        if not title:
            raise ValidationAppError("Task title is required")
        async with self._uow_factory() as uow:
            assignment = await uow.ca_assignments.get_by_ca_and_company(ca_user_id, company_id)
            if not assignment:
                raise ForbiddenError(CA_NOT_ASSIGNED)
            task = await uow.ca_tasks.create(
                CaClientTaskRecord(
                    id=uuid.uuid4(),
                    assignment_id=assignment.id,
                    company_id=company_id,
                    ca_user_id=ca_user_id,
                    title=title,
                    description=description,
                    due_date=due_date,
                    status=CA_TASK_STATUS_PENDING,
                )
            )
            await uow.commit()
        return self._task_dict(task)

    async def update_client_task(
        self,
        ca_user_id: uuid.UUID,
        company_id: uuid.UUID,
        task_id: uuid.UUID,
        *,
        title: str | None = None,
        description: str | None = None,
        due_date: date | None = None,
        status: str | None = None,
    ) -> dict:
        if not await self.verify_assignment(ca_user_id, company_id):
            raise ForbiddenError(CA_NOT_ASSIGNED)
        async with self._uow_factory() as uow:
            task = await uow.ca_tasks.get_by_id(task_id)
            if not task or task.company_id != company_id or task.ca_user_id != ca_user_id:
                raise NotFoundError("Task not found")
            if title is not None:
                task.title = title.strip()
            if description is not None:
                task.description = description
            if due_date is not None:
                task.due_date = due_date
            if status is not None:
                task.status = status
            updated = await uow.ca_tasks.update(task)
            await uow.commit()
        return self._task_dict(updated)

    async def delete_client_task(
        self, ca_user_id: uuid.UUID, company_id: uuid.UUID, task_id: uuid.UUID
    ) -> None:
        if not await self.verify_assignment(ca_user_id, company_id):
            raise ForbiddenError(CA_NOT_ASSIGNED)
        async with self._uow_factory() as uow:
            task = await uow.ca_tasks.get_by_id(task_id)
            if not task or task.company_id != company_id or task.ca_user_id != ca_user_id:
                raise NotFoundError("Task not found")
            await uow.ca_tasks.delete(task_id)
            await uow.commit()

    async def compliance_pack(
        self, ca_user_id: uuid.UUID, company_id: uuid.UUID, *, from_date: date, to_date: date
    ) -> dict:
        if not await self.verify_assignment(ca_user_id, company_id):
            raise ForbiddenError(CA_NOT_ASSIGNED)
        from app.application.services.compliance_service import ComplianceService
        from app.application.services.gstr_report_service import GstrReportService

        compliance = ComplianceService(self._uow_factory)
        gstr = GstrReportService(self._uow_factory)
        async with self._uow_factory() as uow:
            company = await uow.companies.get_by_id(company_id)
            collectible = await uow.invoices.list_collectible(company_id)
        obligations = await compliance.obligations(company_id)
        gstr1 = await gstr.gstr1_report(company_id, from_date, to_date)
        overdue_invoices = [
            {
                "invoice_number": inv.invoice_number,
                "amount_due": float(inv.amount_due.amount),
                "due_date": inv.due_date.isoformat(),
                "status": inv.status.value,
            }
            for inv in collectible
            if inv.amount_due.amount > 0 and inv.due_date < date.today()
        ]
        return {
            "company_id": str(company_id),
            "company_name": company.legal_name if company else "",
            "gstin": company.gstin if company else None,
            "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
            "gstr1_summary": gstr1,
            "filing_checklist": self._build_filing_checklist(obligations.get("obligations", [])),
            "overdue_receivables": overdue_invoices,
            "generated_at": date.today().isoformat(),
        }

    @staticmethod
    def _count_filings_due_this_month(clients: list[dict]) -> int:
        today = date.today()
        month_end = (today.replace(day=28) + timedelta(days=4)).replace(day=1) + timedelta(days=32)
        month_end = month_end.replace(day=1) - timedelta(days=1)
        count = 0
        for client in clients:
            for item in client.get("filing_checklist", []):
                if item["status"] in ("COMPLETED", "NOT_APPLICABLE", "SKIPPED"):
                    continue
                due_str = item.get("due_date")
                if not due_str:
                    continue
                due = date.fromisoformat(due_str)
                if today <= due <= month_end:
                    count += 1
        return count

    @staticmethod
    def _task_dict(task: CaClientTaskRecord) -> dict:
        return {
            "id": str(task.id),
            "company_id": str(task.company_id),
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }

    @staticmethod
    def _build_filing_checklist(rows: list[dict]) -> list[dict]:
        by_id = {row.get("id"): row for row in rows}
        checklist: list[dict] = []
        for obligation_id in CA_FILING_CHECKLIST_IDS:
            row = by_id.get(obligation_id)
            if row:
                checklist.append(
                    {
                        "obligation_id": row["id"],
                        "title": row["title"],
                        "due_date": row["due_date"],
                        "status": row["status"],
                        "period_key": row["period_key"],
                    }
                )
            else:
                title = {
                    "gst_gstr1": "GSTR-1 (Outward Supplies)",
                    "gst_gstr3b": "GSTR-3B (Summary Return)",
                    "it_itr": "Income Tax Return (ITR)",
                }.get(obligation_id, obligation_id)
                checklist.append(
                    {
                        "obligation_id": obligation_id,
                        "title": title,
                        "due_date": None,
                        "status": "NOT_APPLICABLE",
                        "period_key": None,
                    }
                )
        return checklist

    @staticmethod
    def _count_filings_due_soon(checklist: list[dict]) -> int:
        cutoff = date.today() + timedelta(days=CA_FILING_DUE_SOON_DAYS)
        count = 0
        for item in checklist:
            if item["status"] in ("COMPLETED", "NOT_APPLICABLE", "SKIPPED"):
                continue
            due_str = item.get("due_date")
            if not due_str:
                continue
            due = date.fromisoformat(due_str)
            if due <= cutoff:
                count += 1
        return count

    @staticmethod
    def _compute_risk_level(
        *,
        gstin: str | None,
        overdue_total: float | int,
        profile_complete: bool,
        filings_due_soon: int,
        health_score: int | None,
        compliance_overdue: int,
    ) -> str:
        if (
            not gstin
            or overdue_total >= CA_OVERDUE_ALERT_THRESHOLD
            or not profile_complete
            or filings_due_soon > 0
            or compliance_overdue > 0
            or (health_score is not None and health_score < CA_HEALTH_SCORE_AT_RISK)
        ):
            return "high"
        if overdue_total > 0 or (health_score is not None and health_score < 85):
            return "medium"
        return "low"

    @staticmethod
    def _build_portfolio_summary(clients: list[dict]) -> dict:
        scores = [c["health_score"] for c in clients if c.get("health_score") is not None]
        avg_health = round(sum(scores) / len(scores)) if scores else None
        return {
            "avg_health_score": avg_health,
            "clients_at_risk": sum(1 for c in clients if c.get("risk_level") == "high"),
            "total_overdue": sum(c.get("overdue_total") or 0 for c in clients),
            "filings_due_soon": sum(c.get("filings_due_soon") or 0 for c in clients),
        }

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
