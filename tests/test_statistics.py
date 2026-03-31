from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.models import EntryType
from app.services.entries import (
    count_entries,
    create_entry,
    has_entry_for_date,
    mood_breakdown,
)
from app.services.reminders import due_daily_reminders


def test_count_entries_and_mood_breakdown(session, user):
    create_entry(
        session=session,
        user=user,
        entry_type=EntryType.daily,
        entry_date=date(2024, 1, 10),
        text="Запись 1",
        mood="good",
        question="Вопрос",
    )
    create_entry(
        session=session,
        user=user,
        entry_type=EntryType.weekly,
        entry_date=date(2024, 1, 14),
        text="Запись 2",
        mood=None,
        question=None,
    )
    create_entry(
        session=session,
        user=user,
        entry_type=EntryType.daily,
        entry_date=date(2024, 1, 11),
        text="Запись 3",
        mood="bad",
        question=None,
    )
    session.commit()

    assert count_entries(session, user) == 3
    assert count_entries(session, user, EntryType.daily) == 2
    assert mood_breakdown(session, user) == {"good": 1, "bad": 1}


def test_has_entry_for_date_and_reminder_skip(session, user):
    entry_date = date(2024, 1, 10)
    create_entry(
        session=session,
        user=user,
        entry_type=EntryType.daily,
        entry_date=entry_date,
        text="Готово",
        mood="good",
        question=None,
    )
    session.commit()

    assert (
        has_entry_for_date(session, user, EntryType.daily, entry_date) is True
    )
    assert (
        has_entry_for_date(session, user, EntryType.daily, date(2024, 1, 11))
        is False
    )

    user.daily_reminder_stage = 2
    user.daily_reminder_date = entry_date
    now = datetime(2024, 1, 10, 12, 0, tzinfo=ZoneInfo("UTC"))
    due = due_daily_reminders(session, user, now, reminder_evening_hour=20)
    assert due == []
    assert user.daily_reminder_stage == 2
