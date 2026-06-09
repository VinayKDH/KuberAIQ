"""E-invoice IRN tracking on invoices."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "003_research_enhancements"
down_revision = "002_onboarding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("invoices", sa.Column("irn", sa.String(length=64), nullable=True))
    op.add_column(
        "invoices",
        sa.Column("irn_generated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("invoices", "irn_generated_at")
    op.drop_column("invoices", "irn")
