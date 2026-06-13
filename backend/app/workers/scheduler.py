"""APScheduler integration for periodic background jobs."""
from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.constants import (
    OVERDUE_JOB_INTERVAL_HOURS,
    SCHEDULED_REMINDER_JOB_HOUR,
    SCHEDULED_REMINDER_JOB_MINUTE,
    SUBSCRIPTION_EXPIRY_JOB_HOUR,
    SUBSCRIPTION_EXPIRY_JOB_MINUTE,
)
from app.workers.jobs import (
    expire_quotations_all_companies,
    expire_subscriptions_past_period,
    mark_overdue_all_companies,
    send_compliance_alerts_all_companies,
    send_scheduled_reminders_all_companies,
)

_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
    _scheduler.add_job(
        mark_overdue_all_companies,
        "interval",
        hours=OVERDUE_JOB_INTERVAL_HOURS,
        id="mark_overdue",
        replace_existing=True,
    )
    _scheduler.add_job(
        send_scheduled_reminders_all_companies,
        CronTrigger(
            hour=SCHEDULED_REMINDER_JOB_HOUR,
            minute=SCHEDULED_REMINDER_JOB_MINUTE,
        ),
        id="scheduled_reminders",
        replace_existing=True,
    )
    _scheduler.add_job(
        send_compliance_alerts_all_companies,
        CronTrigger(
            hour=SCHEDULED_REMINDER_JOB_HOUR,
            minute=SCHEDULED_REMINDER_JOB_MINUTE,
        ),
        id="compliance_alerts",
        replace_existing=True,
    )
    _scheduler.add_job(
        expire_quotations_all_companies,
        CronTrigger(
            hour=SCHEDULED_REMINDER_JOB_HOUR,
            minute=SCHEDULED_REMINDER_JOB_MINUTE,
        ),
        id="quotation_expiry",
        replace_existing=True,
    )
    _scheduler.add_job(
        expire_subscriptions_past_period,
        CronTrigger(
            hour=SUBSCRIPTION_EXPIRY_JOB_HOUR,
            minute=SUBSCRIPTION_EXPIRY_JOB_MINUTE,
        ),
        id="subscription_expiry",
        replace_existing=True,
    )
    _scheduler.start()


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
