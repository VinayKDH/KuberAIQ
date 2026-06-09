"""Scheduled background jobs."""
from __future__ import annotations

import structlog

from app.core.container import build_container

logger = structlog.get_logger(__name__)


async def mark_overdue_all_companies() -> None:
    """Mark past-due invoices as OVERDUE for every active company."""
    container = build_container()
    async with container.uow_factory() as uow:
        company_ids = await uow.companies.list_active_ids()

    total = 0
    for company_id in company_ids:
        count = await container.collection_service.mark_overdue(company_id)
        total += count

    if total:
        logger.info("overdue_job_completed", companies=len(company_ids), invoices_marked=total)


async def send_scheduled_reminders_all_companies() -> None:
    """Send milestone payment reminders for all companies with automation enabled."""
    container = build_container()
    async with container.uow_factory() as uow:
        company_ids = await uow.companies.list_active_ids()

    total = 0
    for company_id in company_ids:
        count = await container.collection_service.send_scheduled_reminders(company_id)
        total += count

    if total:
        logger.info(
            "scheduled_reminders_completed",
            companies=len(company_ids),
            reminders_sent=total,
        )


async def send_compliance_alerts_all_companies() -> None:
    """Send compliance deadline reminders for companies with automation enabled."""
    container = build_container()
    total = await container.compliance_service.send_scheduled_alerts_all_companies()
    if total:
        logger.info("compliance_alerts_completed", alerts_sent=total)


async def expire_quotations_all_companies() -> None:
    """Mark past-validity quotations as EXPIRED."""
    container = build_container()
    async with container.uow_factory() as uow:
        company_ids = await uow.companies.list_active_ids()
    total = 0
    for company_id in company_ids:
        total += await container.quotation_service.expire_overdue(company_id)
    if total:
        logger.info("quotation_expiry_completed", quotations_expired=total)
