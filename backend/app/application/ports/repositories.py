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
    async def get_by_id_only(self, invoice_id: uuid.UUID) -> Invoice | None: ...
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
    async def list_low_stock(
        self, company_id: uuid.UUID, *, threshold: Decimal, limit: int = 50
    ) -> list[Product]: ...


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
    async def get_by_reference(
        self, company_id: uuid.UUID, reference: str
    ) -> "PaymentRecord | None": ...
    async def list_by_invoice(self, invoice_id: uuid.UUID) -> list["PaymentRecord"]: ...
    async def list_by_customer(
        self, company_id: uuid.UUID, customer_id: uuid.UUID
    ) -> list["PaymentRecord"]: ...
    async def list_recent(
        self, company_id: uuid.UUID, *, limit: int, from_date: "date | None" = None
    ) -> list["PaymentRecord"]: ...
    async def sum_collected(
        self, company_id: uuid.UUID, from_date: "date", to_date: "date"
    ) -> "Decimal": ...
    async def aggregate_by_method(
        self, company_id: uuid.UUID, from_date: "date", to_date: "date"
    ) -> list[dict]: ...
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
    async def find_owner_by_whatsapp_phone(self, phone: str) -> "UserRecord | None": ...
    async def update_whatsapp_phone(self, user_id: uuid.UUID, phone: str | None) -> "UserRecord": ...


class SubscriptionRepository(Protocol):
    async def get_by_user_id(self, user_id: uuid.UUID) -> "SubscriptionRecord | None": ...
    async def get_by_order_id(self, order_id: str) -> "SubscriptionRecord | None": ...
    async def list_active_past_period_end(self, as_of: datetime) -> list["SubscriptionRecord"]: ...
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
        msme_segment: str | None = None,
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
        self.msme_segment = msme_segment


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
        whatsapp_phone: str | None = None,
    ):
        self.id = id
        self.company_id = company_id
        self.email = email
        self.full_name = full_name
        self.role = role
        self.entra_oid = entra_oid
        self.google_sub = google_sub
        self.whatsapp_phone = whatsapp_phone


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


class CaClientAssignmentRepository(Protocol):
    async def create(self, record: "CaClientAssignmentRecord") -> "CaClientAssignmentRecord": ...
    async def get_by_id(self, assignment_id: uuid.UUID) -> "CaClientAssignmentRecord | None": ...
    async def get_by_ca_and_company(
        self, ca_user_id: uuid.UUID, company_id: uuid.UUID
    ) -> "CaClientAssignmentRecord | None": ...
    async def list_for_ca(self, ca_user_id: uuid.UUID) -> list["CaClientAssignmentRecord"]: ...
    async def list_active_for_ca(self, ca_user_id: uuid.UUID) -> list["CaClientAssignmentRecord"]: ...
    async def list_for_company(self, company_id: uuid.UUID) -> list["CaClientAssignmentRecord"]: ...
    async def update(self, record: "CaClientAssignmentRecord") -> "CaClientAssignmentRecord": ...


class CaClientAssignmentRecord:
    def __init__(
        self,
        *,
        id: uuid.UUID,
        ca_user_id: uuid.UUID,
        company_id: uuid.UUID,
        status: "CaAssignmentStatus",
        invited_by: uuid.UUID,
        ca_firm_name: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = id
        self.ca_user_id = ca_user_id
        self.company_id = company_id
        self.status = status
        self.invited_by = invited_by
        self.ca_firm_name = ca_firm_name
        self.created_at = created_at
        self.updated_at = updated_at


class CaClientTaskRepository(Protocol):
    async def create(self, record: "CaClientTaskRecord") -> "CaClientTaskRecord": ...
    async def get_by_id(self, task_id: uuid.UUID) -> "CaClientTaskRecord | None": ...
    async def list_for_company(
        self, company_id: uuid.UUID, *, ca_user_id: uuid.UUID | None = None
    ) -> list["CaClientTaskRecord"]: ...
    async def update(self, record: "CaClientTaskRecord") -> "CaClientTaskRecord": ...
    async def delete(self, task_id: uuid.UUID) -> None: ...


class CaClientTaskRecord:
    def __init__(
        self,
        *,
        id: uuid.UUID,
        assignment_id: uuid.UUID,
        company_id: uuid.UUID,
        ca_user_id: uuid.UUID,
        title: str,
        description: str | None = None,
        due_date: date | None = None,
        status: str = "pending",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = id
        self.assignment_id = assignment_id
        self.company_id = company_id
        self.ca_user_id = ca_user_id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at


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


class AiSessionRepository(Protocol):
    async def get_session(
        self, session_id: str, company_id: uuid.UUID
    ) -> "AiSessionRecord | None": ...
    async def create_or_touch_session(
        self, session_id: str, company_id: uuid.UUID, user_id: uuid.UUID
    ) -> "AiSessionRecord": ...
    async def set_pending_action(
        self, session_id: str, company_id: uuid.UUID, pending_action: dict | None
    ) -> None: ...
    async def append_turn(
        self,
        session_id: str,
        company_id: uuid.UUID,
        user_message: str,
        assistant_payload: dict,
    ) -> None: ...
    async def list_recent_turns(
        self, session_id: str, company_id: uuid.UUID, limit: int
    ) -> list[dict]: ...


class StaffInvitationRepository(Protocol):
    async def create(self, record: "StaffInvitationRecord") -> "StaffInvitationRecord": ...
    async def list_for_company(self, company_id: uuid.UUID) -> list["StaffInvitationRecord"]: ...
    async def get_by_id(self, invitation_id: uuid.UUID) -> "StaffInvitationRecord | None": ...
    async def update(self, record: "StaffInvitationRecord") -> "StaffInvitationRecord": ...
    async def find_active_by_email(
        self, company_id: uuid.UUID, email: str
    ) -> "StaffInvitationRecord | None": ...


class RecurringInvoiceTemplateRepository(Protocol):
    async def create(self, record: "RecurringInvoiceTemplateRecord") -> "RecurringInvoiceTemplateRecord": ...
    async def list_for_company(self, company_id: uuid.UUID) -> list["RecurringInvoiceTemplateRecord"]: ...
    async def get_by_id(
        self, company_id: uuid.UUID, template_id: uuid.UUID
    ) -> "RecurringInvoiceTemplateRecord | None": ...
    async def list_due_templates(self, as_of: date) -> list["RecurringInvoiceTemplateRecord"]: ...
    async def update(self, record: "RecurringInvoiceTemplateRecord") -> "RecurringInvoiceTemplateRecord": ...


class ExpenseRepository(Protocol):
    async def create(self, record: "ExpenseRecord") -> "ExpenseRecord": ...
    async def list_for_company(self, company_id: uuid.UUID, page: int, page_size: int) -> tuple[list["ExpenseRecord"], int]: ...
    async def get_by_id(self, company_id: uuid.UUID, expense_id: uuid.UUID) -> "ExpenseRecord | None": ...
    async def update(self, record: "ExpenseRecord") -> "ExpenseRecord": ...
    async def soft_delete(self, company_id: uuid.UUID, expense_id: uuid.UUID) -> None: ...


class AiUsageLogRepository(Protocol):
    async def add_usage(
        self,
        *,
        company_id: uuid.UUID,
        session_id: str | None,
        model_name: str,
        tokens_in: int,
        tokens_out: int,
        total_tokens: int,
    ) -> None: ...
    async def total_tokens_this_month(self, company_id: uuid.UUID) -> int: ...


class AiSessionRecord:
    def __init__(
        self,
        *,
        id: str,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        pending_action: dict | None = None,
    ):
        self.id = id
        self.company_id = company_id
        self.user_id = user_id
        self.pending_action = pending_action


class StaffInvitationRecord:
    def __init__(
        self,
        *,
        id: uuid.UUID,
        company_id: uuid.UUID,
        invited_by: uuid.UUID,
        email: str,
        role: str,
        status: str,
        expires_at: datetime | None = None,
        accepted_at: datetime | None = None,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.company_id = company_id
        self.invited_by = invited_by
        self.email = email
        self.role = role
        self.status = status
        self.expires_at = expires_at
        self.accepted_at = accepted_at
        self.created_at = created_at


class RecurringInvoiceTemplateRecord:
    def __init__(
        self,
        *,
        id: uuid.UUID,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        name: str,
        items_json: list[dict],
        frequency: str,
        next_run_date: date,
        last_run_at: datetime | None = None,
        is_active: bool = True,
        created_by: uuid.UUID | None = None,
    ):
        self.id = id
        self.company_id = company_id
        self.customer_id = customer_id
        self.name = name
        self.items_json = items_json
        self.frequency = frequency
        self.next_run_date = next_run_date
        self.last_run_at = last_run_at
        self.is_active = is_active
        self.created_by = created_by


class ExpenseRecord:
    def __init__(
        self,
        *,
        id: uuid.UUID,
        company_id: uuid.UUID,
        expense_date: date,
        category: str,
        amount: "Decimal",
        vendor_name: str | None = None,
        note: str | None = None,
        created_by: uuid.UUID | None = None,
    ):
        self.id = id
        self.company_id = company_id
        self.expense_date = expense_date
        self.category = category
        self.amount = amount
        self.vendor_name = vendor_name
        self.note = note
        self.created_by = created_by


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
    ca_assignments: CaClientAssignmentRepository
    ca_tasks: CaClientTaskRepository
    ai_sessions: AiSessionRepository
    staff_invitations: StaffInvitationRepository
    recurring_templates: RecurringInvoiceTemplateRepository
    expenses: ExpenseRepository
    ai_usage: AiUsageLogRepository

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork": ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
