"""Repository port interfaces (Dependency Inversion)."""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Protocol

from app.domain.entities.customer import Customer
from app.domain.entities.invoice import Invoice
from app.domain.entities.product import Product
from app.domain.entities.quotation import Quotation
from app.domain.enums import DocumentType, InvoiceStatus, QuotationStatus


class CustomerRepository(Protocol):
    async def create(self, customer: Customer) -> Customer: ...
    async def get_by_id(self, company_id: uuid.UUID, customer_id: uuid.UUID) -> Customer | None: ...
    async def update(self, customer: Customer) -> Customer: ...
    async def soft_delete(self, company_id: uuid.UUID, customer_id: uuid.UUID) -> None: ...
    async def search(
        self, company_id: uuid.UUID, q: str | None, page: int, page_size: int
    ) -> tuple[list[Customer], int]: ...
    async def find_by_name(self, company_id: uuid.UUID, name: str) -> list[Customer]: ...
    async def find_by_phone(self, company_id: uuid.UUID, phone: str) -> Customer | None: ...


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
        document_type: DocumentType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Invoice], int]: ...
    async def list_overdue(self, company_id: uuid.UUID) -> list[Invoice]: ...
    async def list_collectible(self, company_id: uuid.UUID) -> list[Invoice]: ...
    async def list_issued_in_period(
        self, company_id: uuid.UUID, from_date: date, to_date: date
    ) -> list[Invoice]: ...
    async def list_credit_notes_for_invoice(
        self, company_id: uuid.UUID, invoice_id: uuid.UUID
    ) -> list[Invoice]: ...
    async def allocate_number(
        self, company_id: uuid.UUID, financial_year: str, prefix: str
    ) -> str: ...


class ProductRepository(Protocol):
    async def create(self, product: Product) -> Product: ...
    async def get_by_id(self, company_id: uuid.UUID, product_id: uuid.UUID) -> Product | None: ...
    async def update(self, product: Product) -> Product: ...
    async def soft_delete(self, company_id: uuid.UUID, product_id: uuid.UUID) -> None: ...
    async def search(
        self,
        company_id: uuid.UUID,
        *,
        q: str | None = None,
        active_only: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Product], int]: ...


class QuotationRepository(Protocol):
    async def create(self, quotation: Quotation) -> Quotation: ...
    async def get_by_id(
        self, company_id: uuid.UUID, quotation_id: uuid.UUID
    ) -> Quotation | None: ...
    async def update(self, quotation: Quotation) -> Quotation: ...
    async def search(
        self,
        company_id: uuid.UUID,
        *,
        q: str | None = None,
        status: QuotationStatus | None = None,
        customer_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Quotation], int]: ...
    async def list_expired_candidates(self, company_id: uuid.UUID, today: date) -> list[Quotation]: ...
    async def allocate_number(
        self, company_id: uuid.UUID, financial_year: str, prefix: str
    ) -> str: ...


class PaymentRepository(Protocol):
    async def create(self, payment: "PaymentRecord") -> "PaymentRecord": ...
    async def get_by_id(
        self, company_id: uuid.UUID, payment_id: uuid.UUID
    ) -> "PaymentRecord | None": ...
    async def list_by_invoice(self, invoice_id: uuid.UUID) -> list["PaymentRecord"]: ...
    async def list_by_customer(
        self, company_id: uuid.UUID, customer_id: uuid.UUID
    ) -> list["PaymentRecord"]: ...
    async def soft_delete(self, payment_id: uuid.UUID) -> None: ...


class ReminderRepository(Protocol):
    async def create(self, reminder: "ReminderRecord") -> "ReminderRecord": ...
    async def list_by_invoice(self, invoice_id: uuid.UUID) -> list["ReminderRecord"]: ...
    async def last_sent_for_invoice(self, invoice_id: uuid.UUID) -> "ReminderRecord | None": ...
    async def has_sent_trigger(self, invoice_id: uuid.UUID, trigger: str) -> bool: ...


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

    async def list_for_company(
        self,
        company_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list["AuditLogRecord"], int]: ...


class AuditLogRecord:
    def __init__(
        self,
        *,
        id: uuid.UUID,
        company_id: uuid.UUID,
        actor_user_id: uuid.UUID | None,
        entity_type: str,
        entity_id: uuid.UUID | None,
        action: str,
        before: dict | None,
        after: dict | None,
        ip_address: str | None,
        created_at,
    ):
        self.id = id
        self.company_id = company_id
        self.actor_user_id = actor_user_id
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.action = action
        self.before = before
        self.after = after
        self.ip_address = ip_address
        self.created_at = created_at


class CompanyRepository(Protocol):
    async def get_by_id(self, company_id: uuid.UUID) -> "CompanyRecord | None": ...
    async def get_by_gstin(self, gstin: str) -> "CompanyRecord | None": ...
    async def get_state_code(self, company_id: uuid.UUID) -> str: ...
    async def list_active_ids(self) -> list[uuid.UUID]: ...
    async def create(self, record: "CompanyRecord") -> "CompanyRecord": ...
    async def update(self, record: "CompanyRecord") -> "CompanyRecord": ...


class UserRepository(Protocol):
    async def get_by_id(self, user_id: uuid.UUID) -> "UserRecord | None": ...
    async def get_by_email(self, email: str) -> "UserRecord | None": ...
    async def get_by_entra_oid(self, entra_oid: str) -> "UserRecord | None": ...
    async def get_by_google_sub(self, google_sub: str) -> "UserRecord | None": ...
    async def create(self, record: "UserRecord") -> "UserRecord": ...
    async def link_google_sub(self, user_id: uuid.UUID, google_sub: str) -> "UserRecord": ...
    async def assign_company(self, user_id: uuid.UUID, company_id: uuid.UUID) -> "UserRecord": ...


class SubscriptionRepository(Protocol):
    async def get_by_user_id(self, user_id: uuid.UUID) -> "SubscriptionRecord | None": ...
    async def get_by_order_id(self, order_id: str) -> "SubscriptionRecord | None": ...
    async def create(self, record: "SubscriptionRecord") -> "SubscriptionRecord": ...
    async def update(self, record: "SubscriptionRecord") -> "SubscriptionRecord": ...


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
        trigger: str | None = None,
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
        self.trigger = trigger


class CompanyRecord:
    def __init__(
        self,
        *,
        id: uuid.UUID,
        legal_name: str,
        gstin: str | None,
        state_code: str,
        invoice_prefix: str,
        address: str | None = None,
        upi_id: str | None = None,
        upi_payee_name: str | None = None,
        auto_reminders_enabled: bool = True,
        default_reminder_language: str = "en",
        entity_type: str = "PROPRIETORSHIP",
        turnover_band: str | None = None,
        gstr1_filing_frequency: str = "MONTHLY",
        employee_count: int | None = None,
        udyam_number: str | None = None,
        has_tds_applicable: bool = False,
    ):
        self.id = id
        self.legal_name = legal_name
        self.gstin = gstin
        self.state_code = state_code
        self.invoice_prefix = invoice_prefix
        self.address = address
        self.upi_id = upi_id
        self.upi_payee_name = upi_payee_name
        self.auto_reminders_enabled = auto_reminders_enabled
        self.default_reminder_language = default_reminder_language
        self.entity_type = entity_type
        self.turnover_band = turnover_band
        self.gstr1_filing_frequency = gstr1_filing_frequency
        self.employee_count = employee_count
        self.udyam_number = udyam_number
        self.has_tds_applicable = has_tds_applicable


class UserRecord:
    def __init__(
        self,
        *,
        id: uuid.UUID,
        company_id: uuid.UUID | None,
        email: str,
        full_name: str | None,
        role: "UserRole",
        entra_oid: str | None = None,
        google_sub: str | None = None,
    ):
        self.id = id
        self.company_id = company_id
        self.email = email
        self.full_name = full_name
        self.role = role
        self.entra_oid = entra_oid
        self.google_sub = google_sub


class SubscriptionRecord:
    def __init__(
        self,
        *,
        id: uuid.UUID,
        user_id: uuid.UUID,
        status: "SubscriptionStatus",
        plan_code: str,
        amount_paise: int,
        razorpay_order_id: str | None = None,
        razorpay_payment_id: str | None = None,
        paid_at: datetime | None = None,
        current_period_end: datetime | None = None,
    ):
        self.id = id
        self.user_id = user_id
        self.status = status
        self.plan_code = plan_code
        self.amount_paise = amount_paise
        self.razorpay_order_id = razorpay_order_id
        self.razorpay_payment_id = razorpay_payment_id
        self.paid_at = paid_at
        self.current_period_end = current_period_end


class ComplianceRepository(Protocol):
    async def ensure_catalog_seeded(self) -> None: ...
    async def get_status(
        self, company_id: uuid.UUID, obligation_id: str, period_key: str
    ) -> "ComplianceStatusRecord | None": ...
    async def list_for_company(self, company_id: uuid.UUID) -> list["ComplianceStatusRecord"]: ...
    async def upsert_status(self, record: "ComplianceStatusRecord") -> "ComplianceStatusRecord": ...
    async def list_completion_history(
        self, company_id: uuid.UUID, obligation_id: str, *, limit: int = 12
    ) -> list["ComplianceStatusRecord"]: ...


class ComplianceStatusRecord:
    def __init__(
        self,
        *,
        id: uuid.UUID | None = None,
        company_id: uuid.UUID,
        obligation_id: str,
        period_key: str,
        status: str,
        due_date: date,
        completed_at: datetime | None = None,
        completed_by: uuid.UUID | None = None,
        notes: str | None = None,
    ):
        import uuid as _uuid

        self.id = id or _uuid.uuid4()
        self.company_id = company_id
        self.obligation_id = obligation_id
        self.period_key = period_key
        self.status = status
        self.due_date = due_date
        self.completed_at = completed_at
        self.completed_by = completed_by
        self.notes = notes


class UnitOfWork(ABC):
    customers: CustomerRepository
    invoices: InvoiceRepository
    products: ProductRepository
    quotations: QuotationRepository
    payments: PaymentRepository
    reminders: ReminderRepository
    audit: AuditRepository
    companies: CompanyRepository
    users: UserRepository
    subscriptions: SubscriptionRepository
    compliance: ComplianceRepository

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork": ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
