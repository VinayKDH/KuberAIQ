"""Add stock_movements audit table."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "015_stock_movements"
down_revision = "014_company_is_active"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("delta", sa.Numeric(14, 3), nullable=False),
        sa.Column("qty_after", sa.Numeric(14, 3), nullable=False),
        sa.Column("reason", sa.String(100), nullable=False),
        sa.Column("reference_type", sa.String(40)),
        sa.Column("reference_id", sa.Uuid()),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stock_movements_company_id", "stock_movements", ["company_id"])
    op.create_index("ix_stock_movements_product_id", "stock_movements", ["product_id"])
    op.create_index("ix_stock_movements_created_at", "stock_movements", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_stock_movements_created_at", table_name="stock_movements")
    op.drop_index("ix_stock_movements_product_id", table_name="stock_movements")
    op.drop_index("ix_stock_movements_company_id", table_name="stock_movements")
    op.drop_table("stock_movements")
