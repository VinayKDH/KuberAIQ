"""Track B & C: products, quotations, credit notes, invoice extensions."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "007_track_b_c"
down_revision = "006_google_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("hsn_sac", sa.String(length=10), nullable=True),
        sa.Column("unit", sa.String(length=20), nullable=False, server_default="NOS"),
        sa.Column("default_price", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("gst_rate", sa.Numeric(5, 2), nullable=False, server_default="18"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_company_id", "products", ["company_id"])

    op.create_table(
        "quotations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("quotation_number", sa.String(length=40), nullable=True),
        sa.Column("financial_year", sa.String(length=7), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=False),
        sa.Column("taxable_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("cgst_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("sgst_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("igst_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("total_tax", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("round_off", sa.Numeric(6, 2), nullable=False, server_default="0"),
        sa.Column("grand_total", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("place_of_supply", sa.String(length=2), nullable=True),
        sa.Column("pdf_blob_path", sa.String(length=400), nullable=True),
        sa.Column("converted_invoice_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["converted_invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quotations_company_id", "quotations", ["company_id"])
    op.create_index("ix_quotations_customer_id", "quotations", ["customer_id"])

    op.create_table(
        "quotation_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("quotation_id", sa.Uuid(), nullable=False),
        sa.Column("line_no", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=False),
        sa.Column("hsn_sac", sa.String(length=10), nullable=True),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False, server_default="NOS"),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("gst_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("taxable_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("cgst_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("sgst_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("igst_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quotation_items_quotation_id", "quotation_items", ["quotation_id"])

    op.add_column(
        "invoices",
        sa.Column(
            "document_type",
            sa.String(length=20),
            nullable=False,
            server_default="INVOICE",
        ),
    )
    op.add_column("invoices", sa.Column("original_invoice_id", sa.Uuid(), nullable=True))
    op.add_column("invoices", sa.Column("credit_reason", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_invoices_original_invoice_id",
        "invoices",
        "invoices",
        ["original_invoice_id"],
        ["id"],
    )
    op.create_index("ix_invoices_document_type", "invoices", ["document_type"])

    op.add_column("invoice_items", sa.Column("product_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_invoice_items_product_id",
        "invoice_items",
        "products",
        ["product_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_invoice_items_product_id", "invoice_items", type_="foreignkey")
    op.drop_column("invoice_items", "product_id")
    op.drop_index("ix_invoices_document_type", table_name="invoices")
    op.drop_constraint("fk_invoices_original_invoice_id", "invoices", type_="foreignkey")
    op.drop_column("invoices", "credit_reason")
    op.drop_column("invoices", "original_invoice_id")
    op.drop_column("invoices", "document_type")
    op.drop_table("quotation_items")
    op.drop_table("quotations")
    op.drop_table("products")
