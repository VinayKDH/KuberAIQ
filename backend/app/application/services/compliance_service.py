"""Compliance dashboard — GST deadlines, e-invoice readiness, obligation tracking."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.core.constants import (
    AuditAction,
    COMPLIANCE_ALERT_FALLBACK_PHONE,
    COMPLIANCE_ALERT_MESSAGE_PREFIX,
    COMPLIANCE_CALENDAR_DEFAULT_DAYS,
    COMPLIANCE_DEADLINE_LOOKAHEAD_DAYS,
    COMPLIANCE_DISCLAIMER,
    COMPLIANCE_DUE_SOON_DAYS,
    COMPLIANCE_HEALTH_SCORE_COMPLETE,
    COMPLIANCE_HEALTH_SCORE_DUE_SOON_PENALTY,
    COMPLIANCE_HEALTH_SCORE_OVERDUE_PENALTY,
    COMPLIANCE_OBLIGATION_STATUS_COMPLETED,
    COMPLIANCE_OBLIGATION_STATUS_NOT_APPLICABLE,
    COMPLIANCE_OBLIGATION_STATUS_OVERDUE,
    COMPLIANCE_OBLIGATION_STATUS_PENDING,
    COMPLIANCE_OBLIGATION_STATUS_SKIPPED,
    COMPLIANCE_STATUS_DUE_SOON,
    COMPLIANCE_STATUS_OVERDUE,
    COMPLIANCE_STATUS_UPCOMING,
    EntityType,
    E_INVOICE_IRN_MAX_AGE_DAYS,
    E_INVOICE_TURNOVER_THRESHOLD,
    FINANCIAL_YEAR_START_MONTH,
)
from app.application.ports.repositories import ComplianceStatusRecord
from app.domain.compliance.catalog import CATALOG_BY_ID, COMPLIANCE_CATALOG
from app.domain.enums import InvoiceStatus, ReminderChannel
from app.domain.services.compliance_applicability import (
    applicable_obligations,
    default_profile_from_company,
    evaluate_applicability,
    profile_is_complete,
)
from app.domain.services.compliance_dates import (
    due_date_for_obligation,
    gstr1_due_for_period,
    gstr3b_due_for_period,
    tds_deposit_due_for_period,
    upcoming_gst_periods,
)


class ComplianceService:
    def __init__(self, uow_factory, notifier=None) -> None:
        self._uow_factory = uow_factory
        self._notifier = notifier

    async def preview_alerts(self, company_id: uuid.UUID) -> dict:
        today = date.today()
        alerts = await self._due_soon_obligations(company_id, today)
        return {
            "count": len(alerts),
            "alerts": alerts,
            "due_soon_days": COMPLIANCE_DUE_SOON_DAYS,
        }

    async def send_scheduled_alerts(self, company_id: uuid.UUID) -> int:
        today = date.today()
        async with self._uow_factory() as uow:
            company = await uow.companies.get_by_id(company_id)
            if not company or not company.auto_reminders_enabled:
                return 0
            if not company.turnover_band:
                return 0

        alerts = await self._due_soon_obligations(company_id, today)
        if not alerts or not self._notifier:
            return 0

        lines = [
            f"• {row['title']} due {row['due_date']} ({row['days_until_due']} days)"
            for row in alerts
        ]
        message = f"{COMPLIANCE_ALERT_MESSAGE_PREFIX}\n" + "\n".join(lines)
        await self._notifier.send_message(
            channel=ReminderChannel.WHATSAPP,
            to=COMPLIANCE_ALERT_FALLBACK_PHONE,
            message=message,
            template_name="compliance_reminder",
        )
        async with self._uow_factory() as uow:
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=None,
                entity_type=EntityType.COMPANY,
                entity_id=company_id,
                action=AuditAction.COMPLIANCE_ALERT_SENT,
                before=None,
                after={"count": len(alerts), "obligations": [a["id"] for a in alerts]},
                ip_address=None,
            )
        return len(alerts)

    async def _due_soon_obligations(self, company_id: uuid.UUID, today: date) -> list[dict]:
        data = await self.obligations(company_id)
        if not data.get("profile_complete"):
            return []
        alerts: list[dict] = []
        for row in data.get("obligations", []):
            if row["status"] in {
                COMPLIANCE_OBLIGATION_STATUS_COMPLETED,
                COMPLIANCE_OBLIGATION_STATUS_NOT_APPLICABLE,
            }:
                continue
            due = date.fromisoformat(row["due_date"])
            days_until = (due - today).days
            if 0 <= days_until <= COMPLIANCE_DUE_SOON_DAYS:
                alerts.append(
                    {
                        "id": row["id"],
                        "title": row["title"],
                        "due_date": row["due_date"],
                        "days_until_due": days_until,
                        "status": row["status"],
                        "category": row["category"],
                    }
                )
        alerts.sort(key=lambda item: item["due_date"])
        return alerts

    async def compliance_alert(self, company_id: uuid.UUID) -> dict:
        today = date.today()
        async with self._uow_factory() as uow:
            ytd_turnover = await self._load_ytd_turnover(uow, company_id, today)
            summary = await self._obligations_summary(uow, company_id, today, ytd_turnover)
            return summary["alert"]

    async def dashboard(self, company_id: uuid.UUID) -> dict:
        today = date.today()
        async with self._uow_factory() as uow:
            invoices, _ = await uow.invoices.search(
                company_id, page=1, page_size=10000
            )
            active = [
                inv
                for inv in invoices
                if inv.status not in {InvoiceStatus.CANCELLED, InvoiceStatus.DRAFT}
            ]
            ytd_turnover = self._financial_year_turnover(active, today)
            requires_e_invoice = ytd_turnover >= E_INVOICE_TURNOVER_THRESHOLD
            pending_e_invoices = self._pending_e_invoices(active, today, requires_e_invoice)
            summary = await self._obligations_summary(uow, company_id, today, ytd_turnover)

            return {
                "disclaimer": COMPLIANCE_DISCLAIMER,
                "deadlines": self._build_deadlines(today),
                "e_invoice": {
                    "threshold": float(E_INVOICE_TURNOVER_THRESHOLD),
                    "ytd_turnover": float(ytd_turnover),
                    "requires_e_invoice": requires_e_invoice,
                    "pending_count": len(pending_e_invoices),
                    "pending_invoices": pending_e_invoices[:10],
                },
                "checklist": self._build_checklist(
                    requires_e_invoice=requires_e_invoice,
                    pending_count=len(pending_e_invoices),
                    overdue_receivables=self._overdue_total(active, today),
                ),
                "compliance_alert": summary["alert"],
            }

    async def obligations(self, company_id: uuid.UUID) -> dict:
        today = date.today()
        async with self._uow_factory() as uow:
            await uow.compliance.ensure_catalog_seeded()
            company = await uow.companies.get_by_id(company_id)
            if not company:
                return self._empty_obligations_response()

            ytd_turnover = await self._load_ytd_turnover(uow, company_id, today)
            profile = default_profile_from_company(
                gstin=company.gstin,
                state_code=company.state_code,
                entity_type=company.entity_type,
                turnover_band=company.turnover_band,
                gstr1_filing_frequency=company.gstr1_filing_frequency,
                employee_count=company.employee_count,
                has_tds_applicable=company.has_tds_applicable,
                udyam_number=company.udyam_number,
                ytd_turnover=ytd_turnover,
            )

            if not profile_is_complete(profile):
                return {
                    "profile_complete": False,
                    "disclaimer": COMPLIANCE_DISCLAIMER,
                    "summary": self._zero_summary(),
                    "obligations": [],
                    "not_applicable": [],
                    "profile": self._profile_payload(profile),
                }

            applicable_rows: list[dict] = []
            not_applicable_rows: list[dict] = []
            for item in COMPLIANCE_CATALOG:
                result = evaluate_applicability(item, profile)
                if not result.applies:
                    not_applicable_rows.append(self._not_applicable_payload(result))
                    continue
                row = await self._resolve_obligation_row(
                    uow,
                    company_id=company_id,
                    obligation_id=item.id,
                    frequency=result.effective_frequency,
                    today=today,
                )
                applicable_rows.append(row)

            summary = self._compute_summary(applicable_rows)
            grouped = self._group_by_category(applicable_rows)
            return {
                "profile_complete": True,
                "disclaimer": COMPLIANCE_DISCLAIMER,
                "summary": summary,
                "obligations": applicable_rows,
                "obligations_by_category": grouped,
                "not_applicable": not_applicable_rows,
                "profile": self._profile_payload(profile),
            }

    async def calendar(
        self,
        company_id: uuid.UUID,
        *,
        days: int = COMPLIANCE_CALENDAR_DEFAULT_DAYS,
    ) -> dict:
        obligations_data = await self.obligations(company_id)
        if not obligations_data.get("profile_complete"):
            return {"days": days, "events": [], "profile_complete": False}

        today = date.today()
        horizon = today + timedelta(days=days)
        events: list[dict] = []
        for row in obligations_data["obligations"]:
            if row["status"] == COMPLIANCE_OBLIGATION_STATUS_COMPLETED:
                continue
            due = date.fromisoformat(row["due_date"])
            if due < today - timedelta(days=7) or due > horizon:
                continue
            events.append(
                {
                    "obligation_id": row["id"],
                    "title": row["title"],
                    "category": row["category"],
                    "due_date": row["due_date"],
                    "status": row["status"],
                    "period_key": row["period_key"],
                    "priority": row["priority"],
                }
            )
        events.sort(key=lambda item: item["due_date"])
        return {"days": days, "events": events, "profile_complete": True}

    async def complete_obligation(
        self,
        *,
        company_id: uuid.UUID,
        actor_id: uuid.UUID,
        obligation_id: str,
        period_key: str | None = None,
        notes: str | None = None,
    ) -> dict:
        if obligation_id not in CATALOG_BY_ID:
            raise ValueError("Unknown obligation")

        today = date.today()
        async with self._uow_factory() as uow:
            await uow.compliance.ensure_catalog_seeded()
            company = await uow.companies.get_by_id(company_id)
            if not company:
                raise ValueError("Company not found")

            ytd_turnover = await self._load_ytd_turnover(uow, company_id, today)
            profile = default_profile_from_company(
                gstin=company.gstin,
                state_code=company.state_code,
                entity_type=company.entity_type,
                turnover_band=company.turnover_band,
                gstr1_filing_frequency=company.gstr1_filing_frequency,
                employee_count=company.employee_count,
                has_tds_applicable=company.has_tds_applicable,
                udyam_number=company.udyam_number,
                ytd_turnover=ytd_turnover,
            )
            result = evaluate_applicability(CATALOG_BY_ID[obligation_id], profile)
            if not result.applies:
                raise ValueError("Obligation does not apply to this company")

            key, due = due_date_for_obligation(
                obligation_id,
                today=today,
                frequency=result.effective_frequency,
            )
            resolved_period = period_key or key
            existing = await uow.compliance.get_status(company_id, obligation_id, resolved_period)
            record = ComplianceStatusRecord(
                id=existing.id if existing else uuid.uuid4(),
                company_id=company_id,
                obligation_id=obligation_id,
                period_key=resolved_period,
                status=COMPLIANCE_OBLIGATION_STATUS_COMPLETED,
                due_date=existing.due_date if existing else due,
                completed_at=datetime.now(timezone.utc),
                completed_by=actor_id,
                notes=notes,
            )
            saved = await uow.compliance.upsert_status(record)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.COMPANY,
                entity_id=company_id,
                action=AuditAction.UPDATE,
                before={"obligation_id": obligation_id, "period_key": resolved_period},
                after={"status": COMPLIANCE_OBLIGATION_STATUS_COMPLETED},
            )
            await uow.commit()
            history = await uow.compliance.list_completion_history(company_id, obligation_id)
            return {
                "obligation_id": obligation_id,
                "period_key": saved.period_key,
                "status": saved.status,
                "completed_at": saved.completed_at.isoformat() if saved.completed_at else None,
                "history": [
                    {
                        "period_key": row.period_key,
                        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                        "notes": row.notes,
                    }
                    for row in history
                ],
            }

    async def _obligations_summary(self, uow, company_id: uuid.UUID, today: date, ytd_turnover: Decimal) -> dict:
        company = await uow.companies.get_by_id(company_id)
        if not company or not company.turnover_band:
            return {"alert": self._default_alert(False, 0, 0, 0)}

        profile = default_profile_from_company(
            gstin=company.gstin,
            state_code=company.state_code,
            entity_type=company.entity_type,
            turnover_band=company.turnover_band,
            gstr1_filing_frequency=company.gstr1_filing_frequency,
            employee_count=company.employee_count,
            has_tds_applicable=company.has_tds_applicable,
            udyam_number=company.udyam_number,
            ytd_turnover=ytd_turnover,
        )
        rows: list[dict] = []
        for item in COMPLIANCE_CATALOG:
            result = evaluate_applicability(item, profile)
            if not result.applies:
                continue
            rows.append(
                await self._resolve_obligation_row(
                    uow,
                    company_id=company_id,
                    obligation_id=item.id,
                    frequency=result.effective_frequency,
                    today=today,
                )
            )
        summary = self._compute_summary(rows)
        return {"alert": self._default_alert(True, summary["overdue"], summary["due_this_week"], summary["health_score"])}

    async def _resolve_obligation_row(
        self,
        uow,
        *,
        company_id: uuid.UUID,
        obligation_id: str,
        frequency: str,
        today: date,
    ) -> dict:
        item = CATALOG_BY_ID[obligation_id]
        period_key, due = due_date_for_obligation(obligation_id, today=today, frequency=frequency)
        stored = await uow.compliance.get_status(company_id, obligation_id, period_key)
        status = self._derive_status(today, due, stored)
        if stored is None and status != COMPLIANCE_OBLIGATION_STATUS_NOT_APPLICABLE:
            stored = await uow.compliance.upsert_status(
                ComplianceStatusRecord(
                    company_id=company_id,
                    obligation_id=obligation_id,
                    period_key=period_key,
                    status=status,
                    due_date=due,
                )
            )
        elif stored and stored.status not in (
            COMPLIANCE_OBLIGATION_STATUS_COMPLETED,
            COMPLIANCE_OBLIGATION_STATUS_SKIPPED,
        ):
            if stored.status != status:
                stored = await uow.compliance.upsert_status(
                    ComplianceStatusRecord(
                        id=stored.id,
                        company_id=company_id,
                        obligation_id=obligation_id,
                        period_key=period_key,
                        status=status,
                        due_date=due,
                        completed_at=stored.completed_at,
                        completed_by=stored.completed_by,
                        notes=stored.notes,
                    )
                )

        effective_status = stored.status if stored else status
        return {
            "id": item.id,
            "category": item.category,
            "title": item.title,
            "description": item.description,
            "frequency": frequency,
            "priority": item.priority,
            "action_route": item.action_route,
            "period_key": period_key,
            "due_date": due.isoformat(),
            "status": effective_status,
            "completed_at": stored.completed_at.isoformat() if stored and stored.completed_at else None,
        }

    def _derive_status(self, today: date, due: date, stored: ComplianceStatusRecord | None) -> str:
        if stored and stored.status == COMPLIANCE_OBLIGATION_STATUS_COMPLETED:
            return COMPLIANCE_OBLIGATION_STATUS_COMPLETED
        if stored and stored.status == COMPLIANCE_OBLIGATION_STATUS_SKIPPED:
            return COMPLIANCE_OBLIGATION_STATUS_SKIPPED
        if due < today:
            return COMPLIANCE_OBLIGATION_STATUS_OVERDUE
        return COMPLIANCE_OBLIGATION_STATUS_PENDING

    async def skip_obligation(
        self,
        *,
        company_id: uuid.UUID,
        actor_id: uuid.UUID,
        obligation_id: str,
        period_key: str | None = None,
        notes: str | None = None,
    ) -> dict:
        if obligation_id not in CATALOG_BY_ID:
            raise ValueError("Unknown obligation")

        today = date.today()
        async with self._uow_factory() as uow:
            await uow.compliance.ensure_catalog_seeded()
            company = await uow.companies.get_by_id(company_id)
            if not company:
                raise ValueError("Company not found")

            ytd_turnover = await self._load_ytd_turnover(uow, company_id, today)
            profile = default_profile_from_company(
                gstin=company.gstin,
                state_code=company.state_code,
                entity_type=company.entity_type,
                turnover_band=company.turnover_band,
                gstr1_filing_frequency=company.gstr1_filing_frequency,
                employee_count=company.employee_count,
                has_tds_applicable=company.has_tds_applicable,
                udyam_number=company.udyam_number,
                ytd_turnover=ytd_turnover,
            )
            result = evaluate_applicability(CATALOG_BY_ID[obligation_id], profile)
            if not result.applies:
                raise ValueError("Obligation does not apply to this company")

            key, due = due_date_for_obligation(
                obligation_id,
                today=today,
                frequency=result.effective_frequency,
            )
            resolved_period = period_key or key
            existing = await uow.compliance.get_status(company_id, obligation_id, resolved_period)
            record = ComplianceStatusRecord(
                id=existing.id if existing else uuid.uuid4(),
                company_id=company_id,
                obligation_id=obligation_id,
                period_key=resolved_period,
                status=COMPLIANCE_OBLIGATION_STATUS_SKIPPED,
                due_date=existing.due_date if existing else due,
                completed_at=datetime.now(timezone.utc),
                completed_by=actor_id,
                notes=notes or "Skipped by advisor",
            )
            saved = await uow.compliance.upsert_status(record)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.COMPANY,
                entity_id=company_id,
                action=AuditAction.UPDATE,
                before={"obligation_id": obligation_id, "period_key": resolved_period},
                after={"status": COMPLIANCE_OBLIGATION_STATUS_SKIPPED},
            )
            await uow.commit()
            return {
                "obligation_id": obligation_id,
                "period_key": saved.period_key,
                "status": saved.status,
                "completed_at": saved.completed_at.isoformat() if saved.completed_at else None,
            }

    def _compute_summary(self, rows: list[dict]) -> dict:
        active_rows = [
            row for row in rows if row["status"] != COMPLIANCE_OBLIGATION_STATUS_SKIPPED
        ]
        overdue = sum(1 for row in active_rows if row["status"] == COMPLIANCE_OBLIGATION_STATUS_OVERDUE)
        due_this_week = sum(
            1
            for row in active_rows
            if row["status"] == COMPLIANCE_OBLIGATION_STATUS_PENDING
            and 0 <= (date.fromisoformat(row["due_date"]) - date.today()).days <= COMPLIANCE_DUE_SOON_DAYS
        )
        pending = sum(1 for row in active_rows if row["status"] == COMPLIANCE_OBLIGATION_STATUS_PENDING)
        completed = sum(1 for row in active_rows if row["status"] == COMPLIANCE_OBLIGATION_STATUS_COMPLETED)
        total = len(active_rows) or 1
        health = COMPLIANCE_HEALTH_SCORE_COMPLETE
        health -= overdue * COMPLIANCE_HEALTH_SCORE_OVERDUE_PENALTY
        health -= due_this_week * COMPLIANCE_HEALTH_SCORE_DUE_SOON_PENALTY
        health = max(0, min(COMPLIANCE_HEALTH_SCORE_COMPLETE, health))
        return {
            "total_applicable": len(rows),
            "pending": pending,
            "completed": completed,
            "overdue": overdue,
            "due_this_week": due_this_week,
            "health_score": health,
        }

    def _zero_summary(self) -> dict:
        return {
            "total_applicable": 0,
            "pending": 0,
            "completed": 0,
            "overdue": 0,
            "due_this_week": 0,
            "health_score": 0,
        }

    def _group_by_category(self, rows: list[dict]) -> dict[str, list[dict]]:
        grouped: dict[str, list[dict]] = {}
        for row in rows:
            grouped.setdefault(row["category"], []).append(row)
        return grouped

    def _not_applicable_payload(self, result) -> dict:
        item = result.obligation
        return {
            "id": item.id,
            "category": item.category,
            "title": item.title,
            "reason": result.reason,
        }

    def _profile_payload(self, profile) -> dict:
        return {
            "entity_type": profile.entity_type,
            "turnover_band": profile.turnover_band,
            "gstr1_filing_frequency": profile.gstr1_filing_frequency,
            "employee_count": profile.employee_count,
            "has_tds_applicable": profile.has_tds_applicable,
            "udyam_number": profile.udyam_number,
            "has_gstin": bool(profile.gstin),
        }

    def _empty_obligations_response(self) -> dict:
        return {
            "profile_complete": False,
            "disclaimer": COMPLIANCE_DISCLAIMER,
            "summary": self._zero_summary(),
            "obligations": [],
            "not_applicable": [],
            "profile": {},
        }

    def _default_alert(
        self, profile_complete: bool, overdue: int, due_this_week: int, health_score: int
    ) -> dict:
        triggered = profile_complete and (overdue > 0 or due_this_week > 0)
        if not profile_complete:
            message = "Complete your business profile to see applicable compliances."
        elif overdue > 0:
            message = f"{overdue} compliance obligation(s) overdue. Review the Compliance Center."
        elif due_this_week > 0:
            message = f"{due_this_week} compliance deadline(s) due this week."
        else:
            message = "All tracked compliances are on schedule."
        return {
            "triggered": triggered,
            "overdue_count": overdue,
            "due_this_week_count": due_this_week,
            "health_score": health_score,
            "message": message,
        }

    async def _load_ytd_turnover(self, uow, company_id: uuid.UUID, today: date) -> Decimal:
        invoices, _ = await uow.invoices.search(company_id, page=1, page_size=10000)
        active = [
            inv
            for inv in invoices
            if inv.status not in {InvoiceStatus.CANCELLED, InvoiceStatus.DRAFT}
        ]
        return self._financial_year_turnover(active, today)

    def _financial_year_turnover(self, invoices, today: date) -> Decimal:
        if today.month >= FINANCIAL_YEAR_START_MONTH:
            fy_start = date(today.year, FINANCIAL_YEAR_START_MONTH, 1)
        else:
            fy_start = date(today.year - 1, FINANCIAL_YEAR_START_MONTH, 1)
        total = Decimal("0")
        for inv in invoices:
            if inv.issue_date >= fy_start:
                total += inv.grand_total.amount
        return total

    def _pending_e_invoices(
        self, invoices, today: date, requires_e_invoice: bool
    ) -> list[dict]:
        if not requires_e_invoice:
            return []
        pending: list[dict] = []
        for inv in invoices:
            if inv.status not in {
                InvoiceStatus.ISSUED,
                InvoiceStatus.PARTIALLY_PAID,
                InvoiceStatus.PAID,
                InvoiceStatus.OVERDUE,
            }:
                continue
            if inv.irn:
                continue
            days_since_issue = (today - inv.issue_date).days
            pending.append(
                {
                    "invoice_id": str(inv.id),
                    "invoice_number": inv.invoice_number,
                    "issue_date": inv.issue_date.isoformat(),
                    "grand_total": float(inv.grand_total.amount),
                    "days_since_issue": days_since_issue,
                    "urgency": (
                        COMPLIANCE_STATUS_OVERDUE
                        if days_since_issue > E_INVOICE_IRN_MAX_AGE_DAYS
                        else COMPLIANCE_STATUS_DUE_SOON
                        if days_since_issue > E_INVOICE_IRN_MAX_AGE_DAYS - 7
                        else COMPLIANCE_STATUS_UPCOMING
                    ),
                }
            )
        pending.sort(key=lambda row: row["days_since_issue"], reverse=True)
        return pending

    def _overdue_total(self, invoices, today: date) -> float:
        total = Decimal("0")
        for inv in invoices:
            if inv.status in {InvoiceStatus.OVERDUE, InvoiceStatus.PARTIALLY_PAID}:
                if inv.due_date < today and inv.amount_due.amount > 0:
                    total += inv.amount_due.amount
        return float(total)

    def _build_deadlines(self, today: date) -> list[dict]:
        deadlines: list[dict] = []
        for label, _start, period_end in upcoming_gst_periods(today, count=2):
            for filing_type, due_fn, title in (
                ("GSTR1", gstr1_due_for_period, f"GSTR-1 — {label}"),
                ("GSTR3B", gstr3b_due_for_period, f"GSTR-3B — {label}"),
                ("TDS", tds_deposit_due_for_period, f"TDS deposit — {label}"),
            ):
                due = due_fn(period_end)
                if due < today - timedelta(days=30):
                    continue
                if due > today + timedelta(days=COMPLIANCE_DEADLINE_LOOKAHEAD_DAYS):
                    continue
                deadlines.append(
                    {
                        "type": filing_type,
                        "title": title,
                        "due_date": due.isoformat(),
                        "status": self._deadline_status(today, due),
                        "description": self._deadline_description(filing_type, label),
                    }
                )
        deadlines.sort(key=lambda row: row["due_date"])
        return deadlines

    def _deadline_status(self, today: date, due: date) -> str:
        if due < today:
            return COMPLIANCE_STATUS_OVERDUE
        if (due - today).days <= 7:
            return COMPLIANCE_STATUS_DUE_SOON
        return COMPLIANCE_STATUS_UPCOMING

    def _deadline_description(self, filing_type: str, period_label: str) -> str:
        descriptions = {
            "GSTR1": f"Outward supplies return for {period_label}. File on GST portal.",
            "GSTR3B": f"Summary return and tax payment for {period_label}.",
            "TDS": f"Deposit TDS deducted during {period_label} (if applicable).",
        }
        return descriptions.get(filing_type, "")

    def _build_checklist(
        self,
        *,
        requires_e_invoice: bool,
        pending_count: int,
        overdue_receivables: float,
    ) -> list[dict]:
        items = [
            {
                "id": "gstin_valid",
                "title": "Verify GSTIN on company profile",
                "description": "Ensure legal name and address match your GST registration.",
                "priority": "HIGH",
            },
            {
                "id": "gstr_export",
                "title": "Export GST summary before filing",
                "description": "Download the GST CSV from Settings → Reports and reconcile with books.",
                "priority": "MEDIUM",
            },
            {
                "id": "payment_reminders",
                "title": "Send payment reminders for overdue invoices",
                "description": "Use Collections to nudge customers via WhatsApp before month-end.",
                "priority": "MEDIUM" if overdue_receivables > 0 else "LOW",
            },
        ]
        if requires_e_invoice:
            items.insert(
                0,
                {
                    "id": "e_invoice_irn",
                    "title": "Register IRN for issued B2B invoices",
                    "description": (
                        f"{pending_count} invoice(s) need e-invoice IRN. "
                        "Generate on IRP and record IRN in KuberAIQ within 30 days."
                    ),
                    "priority": "HIGH" if pending_count else "MEDIUM",
                },
            )
        else:
            items.append(
                {
                    "id": "e_invoice_threshold",
                    "title": "Monitor e-invoice turnover threshold",
                    "description": (
                        "E-invoicing is mandatory when annual turnover crosses ₹10 lakh. "
                        "KuberAIQ tracks your FY turnover automatically."
                    ),
                    "priority": "LOW",
                }
            )
        return items

    async def send_scheduled_alerts_all_companies(self) -> int:
        """Send compliance reminders for every company with automation enabled."""
        async with self._uow_factory() as uow:
            company_ids = await uow.companies.list_active_ids()
        total = 0
        for company_id in company_ids:
            total += await self.send_scheduled_alerts(company_id)
        return total
