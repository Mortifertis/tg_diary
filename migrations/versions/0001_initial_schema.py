"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-30 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


entry_type_enum = sa.Enum(
    "daily",
    "weekly",
    "monthly",
    "user",
    name="entrytype",
)
attachment_type_enum = sa.Enum(
    "image",
    "file",
    name="attachmenttype",
)


def upgrade() -> None:
    bind = op.get_bind()
    entry_type_enum.create(bind, checkfirst=True)
    attachment_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=True),
        sa.Column("enable_menu_icons", sa.Boolean(), nullable=False),
        sa.Column(
            "voice_recognition_mode",
            sa.String(length=16),
            nullable=False,
        ),
        sa.Column("entries_page_size", sa.Integer(), nullable=False),
        sa.Column("daily_questions_count", sa.Integer(), nullable=False),
        sa.Column("daily_time", sa.String(length=5), nullable=False),
        sa.Column("weekly_day", sa.Integer(), nullable=False),
        sa.Column("weekly_time", sa.String(length=5), nullable=False),
        sa.Column("monthly_day", sa.Integer(), nullable=False),
        sa.Column("monthly_time", sa.String(length=5), nullable=False),
        sa.Column("streak", sa.Integer(), nullable=True),
        sa.Column("last_entry_date", sa.Date(), nullable=True),
        sa.Column("pause_until", sa.Date(), nullable=True),
        sa.Column("daily_reminder_date", sa.Date(), nullable=True),
        sa.Column("daily_reminder_stage", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_table(
        "entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("entry_type", entry_type_enum, nullable=False),
        sa.Column("entry_index", sa.String(length=16), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("question", sa.String(length=255), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("mood", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "entry_index", name="uq_entry_index"),
    )

    op.create_table(
        "entry_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column(
            "attachment_type",
            attachment_type_enum,
            nullable=False,
        ),
        sa.Column("file_id", sa.String(length=255), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("extension", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["entry_id"], ["entries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "user_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("entry_type", entry_type_enum, nullable=False),
        sa.Column("text", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "entry_type",
            "text",
            name="uq_user_question_text",
        ),
    )


def downgrade() -> None:
    op.drop_table("user_questions")
    op.drop_table("entry_attachments")
    op.drop_table("entries")
    op.drop_table("users")

    bind = op.get_bind()
    attachment_type_enum.drop(bind, checkfirst=True)
    entry_type_enum.drop(bind, checkfirst=True)
