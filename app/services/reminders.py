from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import cast
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

    daily_time = cast(str, user.daily_time)
    timezone = cast(str, user.timezone)
    scheduled = _local_datetime(entry_date, daily_time, timezone)
    evening_time = datetime.combine(
        entry_date,
        time(reminder_evening_hour, 0, tzinfo=ZoneInfo(timezone)),
    )
    due = []

    daily_reminder_date = cast(date | None, user.daily_reminder_date)
    daily_reminder_stage = cast(int, user.daily_reminder_stage)

    if daily_reminder_date != entry_date:
        setattr(user, "daily_reminder_date", entry_date)
        setattr(user, "daily_reminder_stage", 0)
        daily_reminder_stage = 0

    if daily_reminder_stage == 0 and now >= scheduled:
        due.append(
            Reminder(user=user, entry_type=EntryType.daily, due_at=scheduled)
        )
        setattr(user, "daily_reminder_stage", 1)
    elif daily_reminder_stage == 1 and now >= scheduled + timedelta(
        hours=1
    ):
        due.append(
            Reminder(
                user=user,
                entry_type=EntryType.daily,
                due_at=scheduled + timedelta(hours=1),
            )
        )
        setattr(user, "daily_reminder_stage", 2)
    elif daily_reminder_stage == 2 and now >= evening_time:
        due.append(
            Reminder(
                user=user, entry_type=EntryType.daily, due_at=evening_time
            )
        )
        setattr(user, "daily_reminder_stage", 3)

    return due


def due_weekly_reminder(
    session: Session, user: User, now: datetime
) -> list[Reminder]:
    if user.pause_until and now.date() <= user.pause_until:
        return []

    local_day = now.weekday()
    weekly_day = cast(int, user.weekly_day)
    if local_day != weekly_day:
        return []

    entry_date = now.date()
    if has_entry_for_date(session, user, EntryType.weekly, entry_date):
        return []

    weekly_time = cast(str, user.weekly_time)
    timezone = cast(str, user.timezone)
    scheduled = _local_datetime(entry_date, weekly_time, timezone)
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

    monthly_day = cast(int, user.monthly_day)
    if now.day != monthly_day:
        return []

    entry_date = now.date()
    if has_entry_for_date(session, user, EntryType.monthly, entry_date):
        return []

    monthly_time = cast(str, user.monthly_time)
    timezone = cast(str, user.timezone)
    scheduled = _local_datetime(entry_date, monthly_time, timezone)
    if now >= scheduled:
        return [
            Reminder(user=user, entry_type=EntryType.monthly, due_at=scheduled)
        ]
    return []
