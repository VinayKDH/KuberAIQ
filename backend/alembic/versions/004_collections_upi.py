"""Company UPI/payment settings, automated reminders, reminder triggers."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "004_collections_upi"
down_revision = "003_research_enhancements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("upi_id", sa.String(length=100), nullable=True))
    op.add_column("companies", sa.Column("upi_payee_name", sa.String(length=200), nullable=True))
    op.add_column(
        "companies",
        sa.Column("auto_reminders_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "companies",
        sa.Column("default_reminder_language", sa.String(length=2), nullable=False, server_default="en"),
    )
    op.add_column("reminders", sa.Column("trigger", sa.String(length=30), nullable=True))


def downgrade() -> None:
    op.drop_column("reminders", "trigger")
    op.drop_column("companies", "default_reminder_language")
    op.drop_column("companies", "auto_reminders_enabled")
    op.drop_column("companies", "upi_payee_name")
    op.drop_column("companies", "upi_id")
