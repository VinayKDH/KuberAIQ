"""Add is_active flag to companies for admin tenant control."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "014_company_is_active"
down_revision = "013_ca_client_tasks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("companies", "is_active")
