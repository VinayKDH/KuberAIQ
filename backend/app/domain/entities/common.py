"""Smaller domain entities: Company, User, Payment, Reminder."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime

from app.core.constants import DEFAULT_INVOICE_PREFIX
from app.domain.enums import PaymentMethod, ReminderChannel, ReminderStatus, UserRole
from app.domain.value_objects.money import Money


@dataclass
class Company:
    legal_name: str
    state_code: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    gstin: str | None = None
    address: str | None = None
    invoice_prefix: str = DEFAULT_INVOICE_PREFIX


@dataclass
class User:
    company_id: uuid.UUID
    email: str
    role: UserRole = UserRole.STAFF
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    entra_oid: str | None = None
    full_name: str | None = None
    is_active: bool = True


@dataclass
class Payment:
    company_id: uuid.UUID
    invoice_id: uuid.UUID
    amount: Money
    paid_on: date
    method: PaymentMethod = PaymentMethod.CASH
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    reference: str | None = None
    note: str | None = None
    recorded_by: uuid.UUID | None = None


@dataclass
class Reminder:
    company_id: uuid.UUID
    invoice_id: uuid.UUID
    customer_id: uuid.UUID
    message: str
    channel: ReminderChannel = ReminderChannel.WHATSAPP
    status: ReminderStatus = ReminderStatus.PENDING
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    provider_message_id: str | None = None
    error: str | None = None
    sent_by: uuid.UUID | None = None
    sent_at: datetime | None = None
