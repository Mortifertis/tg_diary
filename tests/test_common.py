from __future__ import annotations

from datetime import date, datetime

from app.handlers.common import (_format_manage_entries_preview,
                                 _format_recent_entries)
from app.models import AttachmentType, Entry, EntryAttachment, EntryType, User


def test_format_recent_entries_shows_local_time_and_attachments() -> None:
    user = User(
        telegram_id=1,
        timezone="Europe/Moscow",
        daily_time="09:00",
        weekly_day=6,
        weekly_time="20:00",
        monthly_day=1,
        monthly_time="20:00",
    )
    entry = Entry(
        entry_type=EntryType.user,
        entry_index="u10",
        entry_date=date(2024, 2, 1),
        text="Текст",
        created_at=datetime(2024, 2, 1, 13, 12, 0),
    )
    entry.attachments = [
        EntryAttachment(
            attachment_type=AttachmentType.file,
            file_id="file-id",
            file_name="entries_week.txt",
            extension=".txt",
        )
    ]

    formatted = _format_recent_entries([entry], user)

    assert "2024-02-01 16:12:00" in formatted
    assert "Вложения: entries_week.txt" in formatted


def test_format_manage_entries_preview_truncates_text() -> None:
    entry = Entry(
        entry_type=EntryType.user,
        entry_index="u11",
        entry_date=date(2024, 2, 1),
        text="a" * 101,
        created_at=datetime(2024, 2, 1, 13, 12, 0),
    )

    formatted = _format_manage_entries_preview([entry])

    assert "[u11]" in formatted
    assert "..." in formatted
