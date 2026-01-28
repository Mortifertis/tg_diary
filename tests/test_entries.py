from __future__ import annotations

from datetime import date, timedelta

from app.models import EntryType
from app.services.entries import create_entry, update_streak


def test_update_streak_tracks_consecutive_days(user):
    today = date.today()
    update_streak(user, today)
    assert user.streak == 1
    assert user.last_entry_date == today

    next_day = today + timedelta(days=1)
    update_streak(user, next_day)
    assert user.streak == 2
    assert user.last_entry_date == next_day

    skipped_day = today + timedelta(days=3)
    update_streak(user, skipped_day)
    assert user.streak == 1
    assert user.last_entry_date == skipped_day


def test_create_entry_resets_daily_reminders(session, user):
    user.daily_reminder_date = date(2024, 1, 1)
    user.daily_reminder_stage = 2

    entry = create_entry(
        session=session,
        user=user,
        entry_type=EntryType.daily,
        entry_date=date(2024, 1, 2),
        text="Запись",
        mood="good",
        question="Вопрос",
    )
    session.commit()

    assert entry.user_id == user.id
    assert user.daily_reminder_date == date(2024, 1, 2)
    assert user.daily_reminder_stage == 0
