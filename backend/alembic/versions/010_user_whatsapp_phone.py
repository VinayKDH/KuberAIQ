"""Link owner WhatsApp phone for inbound AI copilot."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "010_user_whatsapp_phone"
down_revision = "009_ca_clients"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("whatsapp_phone", sa.String(length=20), nullable=True))
    op.create_index("ix_users_whatsapp_phone", "users", ["whatsapp_phone"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_whatsapp_phone", table_name="users")
    op.drop_column("users", "whatsapp_phone")
