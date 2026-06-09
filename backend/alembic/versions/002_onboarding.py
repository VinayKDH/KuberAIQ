"""Allow users without a company until onboarding completes."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "002_onboarding"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "company_id", existing_type=sa.Uuid(), nullable=True)


def downgrade() -> None:
    op.alter_column("users", "company_id", existing_type=sa.Uuid(), nullable=False)
