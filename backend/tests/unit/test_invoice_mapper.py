"""Invoice mapper unit tests."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.entities.invoice import Invoice, InvoiceItem
from app.domain.enums import InvoiceStatus
from app.domain.value_objects.money import Money
from app.infrastructure.db.base import Base
from app.infrastructure.db.mappers.invoice_mapper import InvoiceMapper
from app.infrastructure.db.models.invoice import InvoiceModel
from app.infrastructure.db.repositories.invoice_repository import SqlAlchemyInvoiceRepository


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


def _sample_invoice() -> Invoice:
    item = InvoiceItem(
        line_no=1,
        description="Widget",
        quantity=Decimal("2"),
        unit_price=Money.of(100),
        gst_rate=Decimal("18"),
    )
    item.taxable_amount = Money.of(200)
    item.cgst_amount = Money.of(18)
    item.sgst_amount = Money.of(18)
    inv = Invoice(
        company_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        issue_date=date(2026, 6, 6),
        due_date=date(2026, 6, 21),
        items=[item],
        status=InvoiceStatus.ISSUED,
        invoice_number="INV/2026-27/0001",
        financial_year="2026-27",
        grand_total=Money.of(236),
        amount_paid=Money.zero(),
    )
    inv.taxable_amount = Money.of(200)
    inv.cgst_amount = Money.of(18)
    inv.sgst_amount = Money.of(18)
    inv.total_tax = Money.of(36)
    return inv


@pytest.mark.asyncio
async def test_update_invoice_preserves_line_items(session: AsyncSession) -> None:
    repo = SqlAlchemyInvoiceRepository(session)
    invoice = _sample_invoice()
    created = await repo.create(invoice)

    created.amount_paid = Money.of(100)
    updated = await repo.update(created)

    assert updated.amount_paid.amount == Decimal("100")
    assert len(updated.items) == 1
    assert updated.items[0].line_no == 1

    stmt_count = await session.execute(
        __import__("sqlalchemy").select(__import__("sqlalchemy").func.count()).select_from(InvoiceModel)
    )
    assert stmt_count.scalar_one() == 1
