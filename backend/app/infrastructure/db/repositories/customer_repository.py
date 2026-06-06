"""SQLAlchemy implementation of CustomerRepository."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.customer import Customer
from app.domain.enums import InvoiceStatus
from app.infrastructure.db.mappers.customer_mapper import CustomerMapper
from app.infrastructure.db.models.customer import CustomerModel
from app.infrastructure.db.models.invoice import InvoiceModel


class SqlAlchemyCustomerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, customer: Customer) -> Customer:
        model = CustomerMapper.to_model(customer)
        self._session.add(model)
        await self._session.flush()
        return CustomerMapper.to_domain(model)

    async def get_by_id(self, company_id: uuid.UUID, customer_id: uuid.UUID) -> Customer | None:
        stmt = select(CustomerModel).where(
            CustomerModel.company_id == company_id,
            CustomerModel.id == customer_id,
            CustomerModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return CustomerMapper.to_domain(model) if model else None

    async def update(self, customer: Customer) -> Customer:
        stmt = select(CustomerModel).where(
            CustomerModel.id == customer.id,
            CustomerModel.company_id == customer.company_id,
            CustomerModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        CustomerMapper.update_model(model, customer)
        await self._session.flush()
        return CustomerMapper.to_domain(model)

    async def soft_delete(self, company_id: uuid.UUID, customer_id: uuid.UUID) -> None:
        stmt = select(CustomerModel).where(
            CustomerModel.company_id == company_id,
            CustomerModel.id == customer_id,
            CustomerModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.deleted_at = datetime.now(timezone.utc)

    async def search(
        self, company_id: uuid.UUID, q: str | None, page: int, page_size: int
    ) -> tuple[list[Customer], int]:
        base = select(CustomerModel).where(
            CustomerModel.company_id == company_id,
            CustomerModel.deleted_at.is_(None),
        )
        if q:
            pattern = f"%{q.lower()}%"
            base = base.where(
                or_(
                    func.lower(CustomerModel.name).like(pattern),
                    CustomerModel.phone.like(f"%{q}%"),
                )
            )
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = (
            base.order_by(CustomerModel.name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        items = [CustomerMapper.to_domain(m) for m in result.scalars().all()]
        return items, total

    async def find_by_name(self, company_id: uuid.UUID, name: str) -> list[Customer]:
        pattern = f"%{name.lower()}%"
        stmt = select(CustomerModel).where(
            CustomerModel.company_id == company_id,
            CustomerModel.deleted_at.is_(None),
            func.lower(CustomerModel.name).like(pattern),
        )
        result = await self._session.execute(stmt)
        return [CustomerMapper.to_domain(m) for m in result.scalars().all()]

    async def has_active_invoices(self, company_id: uuid.UUID, customer_id: uuid.UUID) -> bool:
        active_statuses = [
            InvoiceStatus.DRAFT,
            InvoiceStatus.ISSUED,
            InvoiceStatus.PARTIALLY_PAID,
            InvoiceStatus.OVERDUE,
            InvoiceStatus.PAID,
        ]
        stmt = select(func.count()).where(
            InvoiceModel.company_id == company_id,
            InvoiceModel.customer_id == customer_id,
            InvoiceModel.status.in_(active_statuses),
            InvoiceModel.deleted_at.is_(None),
        )
        count = (await self._session.execute(stmt)).scalar_one()
        return count > 0

    async def find_by_phone(self, company_id: uuid.UUID, phone: str) -> Customer | None:
        stmt = select(CustomerModel).where(
            CustomerModel.company_id == company_id,
            CustomerModel.phone == phone,
            CustomerModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return CustomerMapper.to_domain(model) if model else None
