"""Initial schema — companies, users, customers, invoices, payments, reminders, audit.

Revision ID: 001_initial
Revises:
Create Date: 2026-06-06
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None

user_role = postgresql.ENUM("OWNER", "STAFF", "VIEWER", name="user_role", create_type=False)
invoice_status = postgresql.ENUM(
    "DRAFT", "ISSUED", "PARTIALLY_PAID", "PAID", "OVERDUE", "CANCELLED",
    name="invoice_status", create_type=False,
)
payment_method = postgresql.ENUM(
    "CASH", "UPI", "BANK_TRANSFER", "CHEQUE", "CARD", "OTHER",
    name="payment_method", create_type=False,
)
reminder_channel = postgresql.ENUM("WHATSAPP", "SMS", "EMAIL", name="reminder_channel", create_type=False)
reminder_status = postgresql.ENUM(
    "PENDING", "SENT", "FAILED", "SKIPPED", name="reminder_status", create_type=False,
)


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    user_role.create(op.get_bind(), checkfirst=True)
    invoice_status.create(op.get_bind(), checkfirst=True)
    payment_method.create(op.get_bind(), checkfirst=True)
    reminder_channel.create(op.get_bind(), checkfirst=True)
    reminder_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("legal_name", sa.String(200), nullable=False),
        sa.Column("gstin", sa.String(15), unique=True),
        sa.Column("state_code", sa.String(2), nullable=False),
        sa.Column("address", sa.Text()),
        sa.Column("invoice_prefix", sa.String(10), nullable=False, server_default="INV"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("entra_oid", sa.String(64), unique=True),
        sa.Column("email", sa.String(200), nullable=False),
        sa.Column("full_name", sa.String(150)),
        sa.Column("role", user_role, nullable=False, server_default="STAFF"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("company_id", "email", name="uq_users_company_email"),
    )
    op.create_index("ix_users_company", "users", ["company_id"])

    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(200)),
        sa.Column("gstin", sa.String(15)),
        sa.Column("state_code", sa.String(2)),
        sa.Column("billing_address", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_customers_company", "customers", ["company_id"])
    op.create_index("ix_customers_company_phone", "customers", ["company_id", "phone"])

    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("invoice_number", sa.String(40)),
        sa.Column("financial_year", sa.String(7)),
        sa.Column("status", invoice_status, nullable=False, server_default="DRAFT"),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("taxable_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("cgst_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("sgst_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("igst_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("total_tax", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("round_off", sa.Numeric(6, 2), nullable=False, server_default="0"),
        sa.Column("grand_total", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("amount_paid", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("amount_due", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("place_of_supply", sa.String(2)),
        sa.Column("cancel_reason", sa.Text()),
        sa.Column("pdf_blob_path", sa.String(400)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("company_id", "invoice_number", name="uq_invoice_number"),
        sa.CheckConstraint("due_date >= issue_date", name="ck_due_after_issue"),
        sa.CheckConstraint("amount_due = grand_total - amount_paid", name="ck_amount_due"),
    )
    op.create_index("ix_invoices_company_status", "invoices", ["company_id", "status"])
    op.create_index("ix_invoices_customer", "invoices", ["customer_id"])
    op.create_index("ix_invoices_issue_date", "invoices", ["company_id", "issue_date"])

    op.create_table(
        "invoice_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("line_no", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("hsn_sac", sa.String(10)),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False, server_default="NOS"),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("gst_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("taxable_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("cgst_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("sgst_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("igst_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Numeric(14, 2), nullable=False),
        sa.UniqueConstraint("invoice_id", "line_no", name="uq_invoice_line"),
    )
    op.create_index("ix_invoice_items_invoice", "invoice_items", ["invoice_id"])

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("paid_on", sa.Date(), nullable=False),
        sa.Column("method", payment_method, nullable=False, server_default="CASH"),
        sa.Column("reference", sa.String(120)),
        sa.Column("note", sa.Text()),
        sa.Column("recorded_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_payments_invoice", "payments", ["invoice_id"])
    op.create_index("ix_payments_company", "payments", ["company_id", "paid_on"])

    op.create_table(
        "reminders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("channel", reminder_channel, nullable=False, server_default="WHATSAPP"),
        sa.Column("status", reminder_status, nullable=False, server_default="PENDING"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("provider_message_id", sa.String(120)),
        sa.Column("error", sa.Text()),
        sa.Column("sent_by", postgresql.UUID(as_uuid=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_reminders_invoice", "reminders", ["invoice_id"])
    op.create_index("ix_reminders_company", "reminders", ["company_id", "created_at"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("before", postgresql.JSONB()),
        sa.Column("after", postgresql.JSONB()),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_company_entity", "audit_logs", ["company_id", "entity_type", "entity_id"])
    op.create_index("ix_audit_created", "audit_logs", ["created_at"])

    op.create_table(
        "invoice_counters",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("financial_year", sa.String(7), primary_key=True),
        sa.Column("last_value", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("invoice_counters")
    op.drop_table("audit_logs")
    op.drop_table("reminders")
    op.drop_table("payments")
    op.drop_table("invoice_items")
    op.drop_table("invoices")
    op.drop_table("customers")
    op.drop_table("users")
    op.drop_table("companies")
    reminder_status.drop(op.get_bind(), checkfirst=True)
    reminder_channel.drop(op.get_bind(), checkfirst=True)
    payment_method.drop(op.get_bind(), checkfirst=True)
    invoice_status.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
