from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models import EntryType, User
from app.services.entries import has_entry_for_date


@dataclass(slots=True)
class Reminder:
    user: User
    entry_type: EntryType
    due_at: datetime


def _time_from_string(value: str) -> time:
    hour, minute = value.split(":")
    return time(hour=int(hour), minute=int(minute))


def _local_datetime(
    local_date: date, time_str: str, timezone: str
) -> datetime:
    tz = ZoneInfo(timezone)
    return datetime.combine(local_date, _time_from_string(time_str), tzinfo=tz)


def due_daily_reminders(
    session: Session,
    user: User,
    now: datetime,
    reminder_evening_hour: int,
) -> list[Reminder]:
    if user.pause_until and now.date() <= user.pause_until:
        return []

    entry_date = now.date()
    if has_entry_for_date(session, user, EntryType.daily, entry_date):
        return []

    scheduled = _local_datetime(entry_date, user.daily_time, user.timezone)
    evening_time = datetime.combine(
        entry_date,
        time(reminder_evening_hour, 0, tzinfo=ZoneInfo(user.timezone)),
    )
    due = []

    if user.daily_reminder_date != entry_date:
        user.daily_reminder_date = entry_date
        user.daily_reminder_stage = 0

    if user.daily_reminder_stage == 0 and now >= scheduled:
        due.append(
            Reminder(user=user, entry_type=EntryType.daily, due_at=scheduled)
        )
        user.daily_reminder_stage = 1
    elif user.daily_reminder_stage == 1 and now >= scheduled + timedelta(
        hours=1
    ):
        due.append(
            Reminder(
                user=user,
                entry_type=EntryType.daily,
                due_at=scheduled + timedelta(hours=1),
            )
        )
        user.daily_reminder_stage = 2
    elif user.daily_reminder_stage == 2 and now >= evening_time:
        due.append(
            Reminder(
                user=user, entry_type=EntryType.daily, due_at=evening_time
            )
        )
        user.daily_reminder_stage = 3

    return due


def due_weekly_reminder(
    session: Session, user: User, now: datetime
) -> list[Reminder]:
    if user.pause_until and now.date() <= user.pause_until:
        return []

    local_day = now.weekday()
    if local_day != user.weekly_day:
        return []

    entry_date = now.date()
    if has_entry_for_date(session, user, EntryType.weekly, entry_date):
        return []

    scheduled = _local_datetime(entry_date, user.weekly_time, user.timezone)
    if now >= scheduled:
        return [
            Reminder(user=user, entry_type=EntryType.weekly, due_at=scheduled)
        ]
    return []


def due_monthly_reminder(
    session: Session, user: User, now: datetime
) -> list[Reminder]:
    if user.pause_until and now.date() <= user.pause_until:
        return []

    if now.day != user.monthly_day:
        return []

    entry_date = now.date()
    if has_entry_for_date(session, user, EntryType.monthly, entry_date):
        return []

    scheduled = _local_datetime(entry_date, user.monthly_time, user.timezone)
    if now >= scheduled:
        return [
            Reminder(user=user, entry_type=EntryType.monthly, due_at=scheduled)
        ]
    return []
