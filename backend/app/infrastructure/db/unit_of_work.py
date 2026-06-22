"""SQLAlchemy Unit of Work — coordinates repositories and transaction boundaries."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import UnitOfWork
from app.infrastructure.db.repositories.audit_repository import SqlAlchemyAuditRepository
from app.infrastructure.db.repositories.ai_session_repository import SqlAlchemyAiSessionRepository
from app.infrastructure.db.repositories.ai_usage_repository import SqlAlchemyAiUsageLogRepository
from app.infrastructure.db.repositories.admin_repository import SqlAlchemyAdminRepository
from app.infrastructure.db.repositories.ca_client_assignment_repository import (
    SqlAlchemyCaClientAssignmentRepository,
)
from app.infrastructure.db.repositories.ca_client_task_repository import (
    SqlAlchemyCaClientTaskRepository,
)
from app.infrastructure.db.repositories.compliance_repository import SqlAlchemyComplianceRepository
from app.infrastructure.db.repositories.company_repository import SqlAlchemyCompanyRepository
from app.infrastructure.db.repositories.customer_repository import SqlAlchemyCustomerRepository
from app.infrastructure.db.repositories.expense_repository import SqlAlchemyExpenseRepository
from app.infrastructure.db.repositories.invoice_repository import SqlAlchemyInvoiceRepository
from app.infrastructure.db.repositories.payment_repository import SqlAlchemyPaymentRepository
from app.infrastructure.db.repositories.product_repository import SqlAlchemyProductRepository
from app.infrastructure.db.repositories.stock_movement_repository import SqlAlchemyStockMovementRepository
from app.infrastructure.db.repositories.quotation_repository import SqlAlchemyQuotationRepository
from app.infrastructure.db.repositories.recurring_invoice_repository import (
    SqlAlchemyRecurringInvoiceTemplateRepository,
)
from app.infrastructure.db.repositories.reminder_repository import SqlAlchemyReminderRepository
from app.infrastructure.db.repositories.staff_invitation_repository import (
    SqlAlchemyStaffInvitationRepository,
)
from app.infrastructure.db.repositories.subscription_repository import SqlAlchemySubscriptionRepository
from app.infrastructure.db.repositories.user_repository import SqlAlchemyUserRepository


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.customers = SqlAlchemyCustomerRepository(session)
        self.invoices = SqlAlchemyInvoiceRepository(session)
        self.products = SqlAlchemyProductRepository(session)
        self.stock_movements = SqlAlchemyStockMovementRepository(session)
        self.quotations = SqlAlchemyQuotationRepository(session)
        self.payments = SqlAlchemyPaymentRepository(session)
        self.reminders = SqlAlchemyReminderRepository(session)
        self.audit = SqlAlchemyAuditRepository(session)
        self.companies = SqlAlchemyCompanyRepository(session)
        self.users = SqlAlchemyUserRepository(session)
        self.subscriptions = SqlAlchemySubscriptionRepository(session)
        self.compliance = SqlAlchemyComplianceRepository(session)
        self.ca_assignments = SqlAlchemyCaClientAssignmentRepository(session)
        self.ca_tasks = SqlAlchemyCaClientTaskRepository(session)
        self.ai_sessions = SqlAlchemyAiSessionRepository(session)
        self.staff_invitations = SqlAlchemyStaffInvitationRepository(session)
        self.recurring_templates = SqlAlchemyRecurringInvoiceTemplateRepository(session)
        self.expenses = SqlAlchemyExpenseRepository(session)
        self.ai_usage = SqlAlchemyAiUsageLogRepository(session)
        self.admin = SqlAlchemyAdminRepository(session)

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type:
                await self.rollback()
            else:
                await self.commit()
        finally:
            await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
