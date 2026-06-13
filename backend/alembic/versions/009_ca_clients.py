"""CA client assignments — multi-client access for chartered accountants."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "009_ca_clients"
down_revision = "008_subscriptions"
branch_labels = None
depends_on = None

ca_assignment_status = postgresql.ENUM(
    "PENDING", "ACTIVE", "REVOKED", name="ca_assignment_status", create_type=False
)


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'CA'")

    ca_assignment_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "ca_client_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ca_user_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("status", ca_assignment_status, nullable=False, server_default="PENDING"),
        sa.Column("invited_by", sa.Uuid(), nullable=False),
        sa.Column("ca_firm_name", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["ca_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ca_user_id", "company_id", name="uq_ca_client_assignments_ca_company"),
    )
    op.create_index("ix_ca_client_assignments_ca_user_id", "ca_client_assignments", ["ca_user_id"])
    op.create_index("ix_ca_client_assignments_company_id", "ca_client_assignments", ["company_id"])
    op.create_index("ix_ca_client_assignments_status", "ca_client_assignments", ["status"])


def downgrade() -> None:
    op.drop_index("ix_ca_client_assignments_status", table_name="ca_client_assignments")
    op.drop_index("ix_ca_client_assignments_company_id", table_name="ca_client_assignments")
    op.drop_index("ix_ca_client_assignments_ca_user_id", table_name="ca_client_assignments")
    op.drop_table("ca_client_assignments")
    ca_assignment_status.drop(op.get_bind(), checkfirst=True)
