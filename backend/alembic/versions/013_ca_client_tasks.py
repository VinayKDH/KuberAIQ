"""CA client tasks for MSME follow-ups."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "013_ca_client_tasks"
down_revision = "012_msme_segment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ca_client_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("ca_user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["assignment_id"], ["ca_client_assignments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ca_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ca_client_tasks_assignment_id", "ca_client_tasks", ["assignment_id"])
    op.create_index("ix_ca_client_tasks_company_id", "ca_client_tasks", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_ca_client_tasks_company_id", table_name="ca_client_tasks")
    op.drop_index("ix_ca_client_tasks_assignment_id", table_name="ca_client_tasks")
    op.drop_table("ca_client_tasks")
