"""KuberAIQ tiers 1-5 MVP schema additions."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "011_kuberaiq_tiers_1_5_mvp"
down_revision = "010_user_whatsapp_phone"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_sessions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("pending_action", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_sessions_company_id", "ai_sessions", ["company_id"], unique=False)

    op.create_table(
        "ai_session_turns",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("session_id", sa.String(length=64), sa.ForeignKey("ai_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("turn_index", sa.Integer(), nullable=False),
        sa.Column("user_message", sa.Text(), nullable=False),
        sa.Column("assistant_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_session_turns_session_id", "ai_session_turns", ["session_id"], unique=False)
    op.create_index(
        "ix_ai_session_turns_session_turn_index",
        "ai_session_turns",
        ["session_id", "turn_index"],
        unique=True,
    )

    op.create_table(
        "staff_invitations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("invited_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("email", sa.String(length=200), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="STAFF"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_staff_invitations_company_email",
        "staff_invitations",
        ["company_id", "email"],
        unique=False,
    )

    op.create_table(
        "recurring_invoice_templates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("customer_id", sa.Uuid(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("items_json", sa.JSON(), nullable=False),
        sa.Column("frequency", sa.String(length=20), nullable=False, server_default="MONTHLY"),
        sa.Column("next_run_date", sa.Date(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_recurring_invoice_templates_company_next_run",
        "recurring_invoice_templates",
        ["company_id", "next_run_date"],
        unique=False,
    )

    op.create_table(
        "expenses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("vendor_name", sa.String(length=200), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_expenses_company_id", "expenses", ["company_id"], unique=False)

    op.create_table(
        "ai_usage_log",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=True),
        sa.Column("model_name", sa.String(length=80), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_ai_usage_log_company_created_at",
        "ai_usage_log",
        ["company_id", "created_at"],
        unique=False,
    )

    op.add_column(
        "products",
        sa.Column("stock_qty", sa.Numeric(14, 3), nullable=False, server_default="0"),
    )
    op.add_column(
        "invoices",
        sa.Column("payment_link_url", sa.String(length=400), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("invoices", "payment_link_url")
    op.drop_column("products", "stock_qty")

    op.drop_index("ix_ai_usage_log_company_created_at", table_name="ai_usage_log")
    op.drop_table("ai_usage_log")

    op.drop_index("ix_expenses_company_id", table_name="expenses")
    op.drop_table("expenses")

    op.drop_index(
        "ix_recurring_invoice_templates_company_next_run",
        table_name="recurring_invoice_templates",
    )
    op.drop_table("recurring_invoice_templates")

    op.drop_index("ix_staff_invitations_company_email", table_name="staff_invitations")
    op.drop_table("staff_invitations")

    op.drop_index("ix_ai_session_turns_session_turn_index", table_name="ai_session_turns")
    op.drop_index("ix_ai_session_turns_session_id", table_name="ai_session_turns")
    op.drop_table("ai_session_turns")
    op.drop_index("ix_ai_sessions_company_id", table_name="ai_sessions")
    op.drop_table("ai_sessions")
