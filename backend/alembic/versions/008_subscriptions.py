"""Subscription billing — payment required before company onboarding."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "008_subscriptions"
down_revision = "007_track_b_c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("plan_code", sa.String(length=40), nullable=False, server_default="starter_monthly"),
        sa.Column("amount_paise", sa.Integer(), nullable=False, server_default="99900"),
        sa.Column("razorpay_order_id", sa.String(length=64), nullable=True),
        sa.Column("razorpay_payment_id", sa.String(length=64), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_subscriptions_user_id"),
        sa.UniqueConstraint("razorpay_order_id", name="uq_subscriptions_razorpay_order_id"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])

    # Existing onboarded users (e.g. demo) are grandfathered as ACTIVE.
    op.execute(
        """
        INSERT INTO subscriptions (id, user_id, status, plan_code, amount_paise, paid_at, current_period_end)
        SELECT gen_random_uuid(), u.id, 'ACTIVE', 'starter_monthly', 99900, NOW(), NOW() + INTERVAL '30 days'
        FROM users u
        WHERE u.company_id IS NOT NULL
          AND u.deleted_at IS NULL
          AND NOT EXISTS (SELECT 1 FROM subscriptions s WHERE s.user_id = u.id)
        """
    )
    # Registered but not onboarded users start as PENDING (must pay before setup).
    op.execute(
        """
        INSERT INTO subscriptions (id, user_id, status, plan_code, amount_paise)
        SELECT gen_random_uuid(), u.id, 'PENDING', 'starter_monthly', 99900
        FROM users u
        WHERE u.company_id IS NULL
          AND u.deleted_at IS NULL
          AND NOT EXISTS (SELECT 1 FROM subscriptions s WHERE s.user_id = u.id)
        """
    )


def downgrade() -> None:
    op.drop_index("ix_subscriptions_status", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.drop_table("subscriptions")
