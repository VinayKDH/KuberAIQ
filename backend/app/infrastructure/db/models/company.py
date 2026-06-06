"""Company and invoice counter ORM models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DEFAULT_INVOICE_PREFIX
from app.infrastructure.db.base import Base


class CompanyModel(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    legal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    gstin: Mapped[str | None] = mapped_column(String(15), unique=True)
    state_code: Mapped[str] = mapped_column(String(2), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    invoice_prefix: Mapped[str] = mapped_column(String(10), nullable=False, default=DEFAULT_INVOICE_PREFIX)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    users: Mapped[list["UserModel"]] = relationship(back_populates="company")  # noqa: F821


class InvoiceCounterModel(Base):
    __tablename__ = "invoice_counters"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True
    )
    financial_year: Mapped[str] = mapped_column(String(7), primary_key=True)
    last_value: Mapped[int] = mapped_column(default=0)
