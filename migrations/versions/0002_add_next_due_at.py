"""add next_due_at for reminder scheduling

Revision ID: 0002_add_next_due_at
Revises: 0001_initial_schema
Create Date: 2026-03-30 00:20:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_add_next_due_at"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_next_due_at", "users", ["next_due_at"])


def downgrade() -> None:
    op.drop_index("ix_users_next_due_at", table_name="users")
    op.drop_column("users", "next_due_at")