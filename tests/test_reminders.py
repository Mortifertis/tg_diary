from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.models import Entry, EntryType
from app.services.reminders import (
    due_daily_reminders,
    due_monthly_reminder,
    due_weekly_reminder,
    list_due_user_candidates,
    next_due_at,
)


def test_due_daily_reminders_progresses_stages(session, user):
    reminder_evening_hour = 20
    day = date(2024, 1, 10)

    now = datetime.combine(day, time(9, 30), tzinfo=ZoneInfo("UTC"))
    due = due_daily_reminders(session, user, now, reminder_evening_hour)
    assert [item.entry_type for item in due] == [EntryType.daily]
    assert user.daily_reminder_stage == 1
    assert due[0].due_at.time() == time(9, 0)

    later = datetime.combine(day, time(10, 30), tzinfo=ZoneInfo("UTC"))
    due = due_daily_reminders(session, user, later, reminder_evening_hour)
    assert [item.entry_type for item in due] == [EntryType.daily]
    assert user.daily_reminder_stage == 2
    assert due[0].due_at.time() == time(10, 0)

    evening = datetime.combine(day, time(20, 0), tzinfo=ZoneInfo("UTC"))
    due = due_daily_reminders(session, user, evening, reminder_evening_hour)
    assert [item.entry_type for item in due] == [EntryType.daily]
    assert user.daily_reminder_stage == 3
    assert due[0].due_at.time() == time(20, 0)


def test_due_daily_reminders_respects_pause(session, user):
    user.pause_until = date(2024, 1, 12)
    now = datetime(2024, 1, 10, 10, 0, tzinfo=ZoneInfo("UTC"))
    due = due_daily_reminders(session, user, now, reminder_evening_hour=20)
    assert due == []


def test_weekly_and_monthly_reminders(session, user):
    weekly_date = date(2024, 1, 7)
    user.weekly_day = weekly_date.weekday()
    weekly_now = datetime.combine(
        weekly_date, time(21, 0), tzinfo=ZoneInfo("UTC")
    )
    weekly_due = due_weekly_reminder(session, user, weekly_now)
    assert [item.entry_type for item in weekly_due] == [EntryType.weekly]

    monthly_date = date(2024, 2, 1)
    user.monthly_day = monthly_date.day
    monthly_now = datetime.combine(
        monthly_date, time(21, 0), tzinfo=ZoneInfo("UTC")
    )
    monthly_due = due_monthly_reminder(session, user, monthly_now)
    assert [item.entry_type for item in monthly_due] == [EntryType.monthly]


def test_weekly_reminder_waits_for_time(session, user):
    weekly_date = date(2024, 1, 7)
    user.weekly_day = weekly_date.weekday()
    user.weekly_time = "20:00"

    early_now = datetime.combine(
        weekly_date, time(19, 0), tzinfo=ZoneInfo("UTC")
    )
    assert due_weekly_reminder(session, user, early_now) == []

    on_time = datetime.combine(
        weekly_date, time(20, 0), tzinfo=ZoneInfo("UTC")
    )
    due = due_weekly_reminder(session, user, on_time)
    assert [item.entry_type for item in due] == [EntryType.weekly]


def test_weekly_and_monthly_respect_pause(session, user):
    paused_date = date(2024, 1, 7)
    user.pause_until = paused_date
    user.weekly_day = paused_date.weekday()
    weekly_now = datetime.combine(
        paused_date, time(21, 0), tzinfo=ZoneInfo("UTC")
    )
    assert due_weekly_reminder(session, user, weekly_now) == []

    monthly_date = date(2024, 2, 1)
    user.monthly_day = monthly_date.day
    user.pause_until = monthly_date
    monthly_now = datetime.combine(
        monthly_date, time(21, 0), tzinfo=ZoneInfo("UTC")
    )
    assert due_monthly_reminder(session, user, monthly_now) == []


def test_monthly_reminder_waits_for_time(session, user):
    monthly_date = date(2024, 2, 1)
    user.monthly_day = monthly_date.day
    user.monthly_time = "20:00"

    early_now = datetime.combine(
        monthly_date, time(19, 0), tzinfo=ZoneInfo("UTC")
    )
    assert due_monthly_reminder(session, user, early_now) == []

    on_time = datetime.combine(
        monthly_date, time(20, 0), tzinfo=ZoneInfo("UTC")
    )
    due = due_monthly_reminder(session, user, on_time)
    assert [item.entry_type for item in due] == [EntryType.monthly]


def test_daily_reminder_ignores_user_entries(session, user):
    day = date(2024, 1, 10)
    session.add(
        Entry(
            user_id=user.id,
            entry_type=EntryType.user,
            entry_date=day,
            entry_index="u1",
            text="manual",
        )
    )
    session.commit()

    now = datetime.combine(day, time(9, 30), tzinfo=ZoneInfo("UTC"))
    due = due_daily_reminders(session, user, now, reminder_evening_hour=20)

    assert [item.entry_type for item in due] == [EntryType.daily]


def test_next_due_at_returns_future_utc_datetime(session, user):
    now = datetime(2024, 1, 10, 8, 0, tzinfo=ZoneInfo("UTC"))

    due_at = next_due_at(
        session,
        user,
        now,
        reminder_evening_hour=20,
    )

    assert due_at.tzinfo is not None
    assert due_at >= now


def test_list_due_user_candidates_filters_by_next_due_at(session, user):
    now = datetime(2024, 1, 10, 8, 0, tzinfo=ZoneInfo("UTC"))
    user.next_due_at = datetime(2024, 1, 10, 9, 0, tzinfo=ZoneInfo("UTC"))
    session.commit()

    assert list_due_user_candidates(session, now) == []

    user.next_due_at = datetime(2024, 1, 10, 7, 0, tzinfo=ZoneInfo("UTC"))
    session.commit()

    due_users = list_due_user_candidates(session, now)
    assert [item.id for item in due_users] == [user.id]
