"""MSME compliance tracking tables and company profile extensions."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from app.infrastructure.db.seeds.compliance_catalog import compliance_catalog_rows

revision = "005_compliance_tracking"
down_revision = "004_collections_upi"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "compliance_obligations",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("frequency", sa.String(length=20), nullable=False),
        sa.Column("priority", sa.String(length=10), nullable=False),
        sa.Column("action_route", sa.String(length=200), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    obligations = sa.table(
        "compliance_obligations",
        sa.column("id", sa.String),
        sa.column("category", sa.String),
        sa.column("title", sa.String),
        sa.column("description", sa.Text),
        sa.column("frequency", sa.String),
        sa.column("priority", sa.String),
        sa.column("action_route", sa.String),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(obligations, compliance_catalog_rows())

    op.create_table(
        "company_compliance_status",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("obligation_id", sa.String(length=50), nullable=False),
        sa.Column("period_key", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_by", sa.Uuid(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["completed_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["obligation_id"], ["compliance_obligations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "obligation_id", "period_key", name="uq_company_compliance_period"),
    )
    op.create_index("ix_company_compliance_status_company_id", "company_compliance_status", ["company_id"])

    op.add_column(
        "companies",
        sa.Column("entity_type", sa.String(length=30), nullable=False, server_default="PROPRIETORSHIP"),
    )
    op.add_column("companies", sa.Column("turnover_band", sa.String(length=20), nullable=True))
    op.add_column(
        "companies",
        sa.Column("gstr1_filing_frequency", sa.String(length=10), nullable=False, server_default="MONTHLY"),
    )
    op.add_column("companies", sa.Column("employee_count", sa.Integer(), nullable=True))
    op.add_column("companies", sa.Column("udyam_number", sa.String(length=20), nullable=True))
    op.add_column(
        "companies",
        sa.Column("has_tds_applicable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("companies", "has_tds_applicable")
    op.drop_column("companies", "udyam_number")
    op.drop_column("companies", "employee_count")
    op.drop_column("companies", "gstr1_filing_frequency")
    op.drop_column("companies", "turnover_band")
    op.drop_column("companies", "entity_type")
    op.drop_index("ix_company_compliance_status_company_id", table_name="company_compliance_status")
    op.drop_table("company_compliance_status")
    op.drop_table("compliance_obligations")
