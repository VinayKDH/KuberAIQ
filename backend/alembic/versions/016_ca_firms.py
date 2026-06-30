"""CA firm multi-advisor support."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "016_ca_firms"
down_revision = "015_stock_movements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ca_firms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("users", sa.Column("ca_firm_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_users_ca_firm_id",
        "users",
        "ca_firms",
        ["ca_firm_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_users_ca_firm_id", "users", ["ca_firm_id"])

    op.add_column(
        "ca_client_assignments",
        sa.Column("assigned_advisor_user_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_ca_assignments_assigned_advisor",
        "ca_client_assignments",
        "users",
        ["assigned_advisor_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_ca_assignments_assigned_advisor",
        "ca_client_assignments",
        ["assigned_advisor_user_id"],
    )
    op.execute(
        "UPDATE ca_client_assignments SET assigned_advisor_user_id = ca_user_id "
        "WHERE assigned_advisor_user_id IS NULL"
    )


def downgrade() -> None:
    op.drop_index("ix_ca_assignments_assigned_advisor", table_name="ca_client_assignments")
    op.drop_constraint(
        "fk_ca_assignments_assigned_advisor", "ca_client_assignments", type_="foreignkey"
    )
    op.drop_column("ca_client_assignments", "assigned_advisor_user_id")
    op.drop_index("ix_users_ca_firm_id", table_name="users")
    op.drop_constraint("fk_users_ca_firm_id", "users", type_="foreignkey")
    op.drop_column("users", "ca_firm_id")
    op.drop_table("ca_firms")
