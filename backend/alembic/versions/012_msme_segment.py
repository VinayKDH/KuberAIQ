"""Add msme_segment to company profile."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "012_msme_segment"
down_revision = "011_kuberaiq_tiers_1_5_mvp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("msme_segment", sa.String(length=30), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "msme_segment")
