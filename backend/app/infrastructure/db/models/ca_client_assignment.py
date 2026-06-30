"""CA client assignment ORM model."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import CaAssignmentStatus
from app.infrastructure.db.base import Base


class CaClientAssignmentModel(Base):
    __tablename__ = "ca_client_assignments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ca_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[CaAssignmentStatus] = mapped_column(
        Enum(CaAssignmentStatus, name="ca_assignment_status", native_enum=False),
        nullable=False,
        default=CaAssignmentStatus.PENDING,
        index=True,
    )
    invited_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    ca_firm_name: Mapped[str | None] = mapped_column(String(200))
    assigned_advisor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    ca_user: Mapped["UserModel"] = relationship(foreign_keys=[ca_user_id])  # noqa: F821
    company: Mapped["CompanyModel"] = relationship(foreign_keys=[company_id])  # noqa: F821
