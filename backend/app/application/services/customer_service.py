"""Customer use-case orchestration."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.application.ports.repositories import UnitOfWork
from app.core.constants import AuditAction, EntityType, ErrorCode
from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.domain.entities.customer import Customer
from app.domain.enums import InvoiceStatus
from app.domain.exceptions import DomainError, InvalidGstin, InvalidPhone
from app.domain.value_objects.gstin import Gstin
from app.domain.value_objects.phone import Phone


@dataclass
class CreateCustomerInput:
    name: str
    phone: str
    email: str | None = None
    gstin: str | None = None
    billing_address: str | None = None
    notes: str | None = None


@dataclass
class UpdateCustomerInput:
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    gstin: str | None = None
    billing_address: str | None = None
    notes: str | None = None


class CustomerService:
    def __init__(self, uow_factory) -> None:
        self._uow_factory = uow_factory

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        actor_id: uuid.UUID,
        data: CreateCustomerInput,
        ip: str | None = None,
    ) -> Customer:
        try:
            phone = Phone(data.phone)
            gstin = Gstin.parse_optional(data.gstin)
        except DomainError as exc:
            raise ValidationAppError(str(exc), code=ErrorCode.VALIDATION_ERROR) from exc

        async with self._uow_factory() as uow:
            existing = await uow.customers.find_by_phone(company_id, phone.value)
            if existing:
                raise ConflictError(
                    f"Customer with phone {phone.value} already exists",
                    code=ErrorCode.DUPLICATE,
                )
            customer = Customer(
                company_id=company_id,
                name=data.name.strip(),
                phone=phone,
                email=data.email,
                gstin=gstin,
                billing_address=data.billing_address,
                notes=data.notes,
            )
            saved = await uow.customers.create(customer)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.CUSTOMER,
                entity_id=saved.id,
                action=AuditAction.CREATE,
                before=None,
                after={"name": saved.name, "phone": saved.phone.value},
                ip_address=ip,
            )
            return saved

    async def get(self, company_id: uuid.UUID, customer_id: uuid.UUID) -> Customer:
        async with self._uow_factory() as uow:
            customer = await uow.customers.get_by_id(company_id, customer_id)
            if not customer:
                raise NotFoundError("Customer not found")
            return customer

    async def update(
        self,
        *,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        actor_id: uuid.UUID,
        data: UpdateCustomerInput,
        ip: str | None = None,
    ) -> Customer:
        async with self._uow_factory() as uow:
            customer = await uow.customers.get_by_id(company_id, customer_id)
            if not customer:
                raise NotFoundError("Customer not found")
            before = {"name": customer.name, "phone": customer.phone.value}
            if data.name is not None:
                customer.rename(data.name)
            if data.phone is not None:
                try:
                    customer.phone = Phone(data.phone)
                except InvalidPhone as exc:
                    raise ValidationAppError(str(exc), code=ErrorCode.PHONE_INVALID) from exc
            if data.email is not None:
                customer.email = data.email
            if data.gstin is not None:
                try:
                    customer.gstin = Gstin.parse_optional(data.gstin)
                except InvalidGstin as exc:
                    raise ValidationAppError(str(exc), code=ErrorCode.GSTIN_INVALID) from exc
            if data.billing_address is not None:
                customer.billing_address = data.billing_address
            if data.notes is not None:
                customer.notes = data.notes
            saved = await uow.customers.update(customer)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.CUSTOMER,
                entity_id=saved.id,
                action=AuditAction.UPDATE,
                before=before,
                after={"name": saved.name, "phone": saved.phone.value},
                ip_address=ip,
            )
            return saved

    async def delete(
        self,
        *,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        actor_id: uuid.UUID,
        ip: str | None = None,
    ) -> None:
        async with self._uow_factory() as uow:
            customer = await uow.customers.get_by_id(company_id, customer_id)
            if not customer:
                raise NotFoundError("Customer not found")
            if await uow.customers.has_active_invoices(company_id, customer_id):
                raise ConflictError(
                    "Cannot delete customer with active invoices",
                    code=ErrorCode.CONFLICT,
                )
            await uow.customers.soft_delete(company_id, customer_id)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.CUSTOMER,
                entity_id=customer_id,
                action=AuditAction.DELETE,
                before={"name": customer.name},
                after=None,
                ip_address=ip,
            )

    async def search(
        self, company_id: uuid.UUID, q: str | None, page: int, page_size: int
    ) -> tuple[list[Customer], int]:
        async with self._uow_factory() as uow:
            return await uow.customers.search(company_id, q, page, page_size)

    async def history(self, company_id: uuid.UUID, customer_id: uuid.UUID) -> dict:
        async with self._uow_factory() as uow:
            customer = await uow.customers.get_by_id(company_id, customer_id)
            if not customer:
                raise NotFoundError("Customer not found")
            invoices, _ = await uow.invoices.search(
                company_id, customer_id=customer_id, page=1, page_size=1000
            )
            payments = await uow.payments.list_by_customer(company_id, customer_id)
            total_billed = sum(
                (i.grand_total.amount for i in invoices if i.status != InvoiceStatus.CANCELLED),
                start=Decimal("0"),
            )
            total_paid = sum((p.amount for p in payments), start=Decimal("0"))
            outstanding = sum(
                (i.amount_due.amount for i in invoices if i.status.is_open),
                start=Decimal("0"),
            )
            today = date.today()
            aging: dict[str, Decimal] = {"0-30": Decimal("0"), "31-60": Decimal("0"), "61-90": Decimal("0"), "90+": Decimal("0")}
            for inv in invoices:
                if not inv.status.is_open or inv.amount_due.is_zero:
                    continue
                days = (today - inv.due_date).days
                bucket = "90+" if days > 90 else "61-90" if days > 60 else "31-60" if days > 30 else "0-30"
                aging[bucket] += inv.amount_due.amount
            return {
                "customer": customer,
                "invoices": invoices,
                "payments": payments,
                "total_billed": total_billed,
                "total_paid": total_paid,
                "outstanding": outstanding,
                "aging": aging,
            }
