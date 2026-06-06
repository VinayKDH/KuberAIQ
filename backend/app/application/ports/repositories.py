"""Repository port interfaces (Dependency Inversion)."""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import date
from typing import Protocol

from app.domain.entities.customer import Customer
from app.domain.entities.invoice import Invoice
from app.domain.enums import InvoiceStatus


class CustomerRepository(Protocol):
    async def create(self, customer: Customer) -> Customer: ...
    async def get_by_id(self, company_id: uuid.UUID, customer_id: uuid.UUID) -> Customer | None: ...
    async def update(self, customer: Customer) -> Customer: ...
    async def soft_delete(self, company_id: uuid.UUID, customer_id: uuid.UUID) -> None: ...
    async def search(
        self, company_id: uuid.UUID, q: str | None, page: int, page_size: int
    ) -> tuple[list[Customer], int]: ...
    async def find_by_name(self, company_id: uuid.UUID, name: str) -> list[Customer]: ...


class InvoiceRepository(Protocol):
    async def create(self, invoice: Invoice) -> Invoice: ...
    async def get_by_id(self, company_id: uuid.UUID, invoice_id: uuid.UUID) -> Invoice | None: ...
    async def get_by_number(
        self, company_id: uuid.UUID, invoice_number: str
    ) -> Invoice | None: ...
    async def update(self, invoice: Invoice) -> Invoice: ...
    async def search(
        self,
        company_id: uuid.UUID,
        *,
        q: str | None = None,
        status: InvoiceStatus | None = None,
        customer_id: uuid.UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Invoice], int]: ...
    async def list_overdue(self, company_id: uuid.UUID) -> list[Invoice]: ...
    async def allocate_number(
        self, company_id: uuid.UUID, financial_year: str, prefix: str
    ) -> str: ...


class PaymentRepository(Protocol):
    async def create(self, payment: "PaymentRecord") -> "PaymentRecord": ...
    async def list_by_invoice(self, invoice_id: uuid.UUID) -> list["PaymentRecord"]: ...
    async def list_by_customer(
        self, company_id: uuid.UUID, customer_id: uuid.UUID
    ) -> list["PaymentRecord"]: ...


class ReminderRepository(Protocol):
    async def create(self, reminder: "ReminderRecord") -> "ReminderRecord": ...
    async def list_by_invoice(self, invoice_id: uuid.UUID) -> list["ReminderRecord"]: ...


class AuditRepository(Protocol):
    async def log(
        self,
        *,
        company_id: uuid.UUID,
        actor_user_id: uuid.UUID | None,
        entity_type: str,
        entity_id: uuid.UUID | None,
        action: str,
        before: dict | None,
        after: dict | None,
        ip_address: str | None = None,
    ) -> None: ...


class CompanyRepository(Protocol):
    async def get_by_id(self, company_id: uuid.UUID) -> "CompanyRecord | None": ...
    async def get_state_code(self, company_id: uuid.UUID) -> str: ...


class UserRepository(Protocol):
    async def get_by_id(self, user_id: uuid.UUID) -> "UserRecord | None": ...
    async def get_by_email(self, email: str) -> "UserRecord | None": ...


# Lightweight DTOs for repos that don't need full domain aggregates
class PaymentRecord:
    def __init__(
        self,
        *,
        id: uuid.UUID | None = None,
        company_id: uuid.UUID,
        invoice_id: uuid.UUID,
        amount: "Decimal",
        paid_on: date,
        method: "PaymentMethod",
        reference: str | None = None,
        note: str | None = None,
        recorded_by: uuid.UUID | None = None,
    ):
        import uuid as _uuid
        from decimal import Decimal
        from app.domain.enums import PaymentMethod

        self.id = id or _uuid.uuid4()
        self.company_id = company_id
        self.invoice_id = invoice_id
        self.amount = amount
        self.paid_on = paid_on
        self.method = method
        self.reference = reference
        self.note = note
        self.recorded_by = recorded_by


class ReminderRecord:
    def __init__(
        self,
        *,
        id: uuid.UUID | None = None,
        company_id: uuid.UUID,
        invoice_id: uuid.UUID,
        customer_id: uuid.UUID,
        channel: "ReminderChannel",
        message: str,
        sent_by: uuid.UUID | None = None,
    ):
        import uuid as _uuid
        from app.domain.enums import ReminderChannel, ReminderStatus

        self.id = id or _uuid.uuid4()
        self.company_id = company_id
        self.invoice_id = invoice_id
        self.customer_id = customer_id
        self.channel = channel
        self.status = ReminderStatus.PENDING
        self.message = message
        self.provider_message_id: str | None = None
        self.error: str | None = None
        self.sent_by = sent_by
        self.sent_at = None


class CompanyRecord:
    def __init__(
        self,
        *,
        id: uuid.UUID,
        legal_name: str,
        gstin: str | None,
        state_code: str,
        invoice_prefix: str,
    ):
        self.id = id
        self.legal_name = legal_name
        self.gstin = gstin
        self.state_code = state_code
        self.invoice_prefix = invoice_prefix


class UserRecord:
    def __init__(
        self,
        *,
        id: uuid.UUID,
        company_id: uuid.UUID,
        email: str,
        full_name: str | None,
        role: "UserRole",
    ):
        self.id = id
        self.company_id = company_id
        self.email = email
        self.full_name = full_name
        self.role = role


class UnitOfWork(ABC):
    customers: CustomerRepository
    invoices: InvoiceRepository
    payments: PaymentRepository
    reminders: ReminderRepository
    audit: AuditRepository
    companies: CompanyRepository
    users: UserRepository

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork": ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
