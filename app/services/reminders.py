from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import cast
from zoneinfo import ZoneInfo

from sqlalchemy import or_
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
    local_date: date,
    time_str: str,
    timezone: str,
) -> datetime:
    tz = ZoneInfo(timezone)
    return datetime.combine(local_date, _time_from_string(time_str), tzinfo=tz)


def _to_utc(value: datetime) -> datetime:
    return value.astimezone(UTC)


def _next_weekly_local_due(user: User, now: datetime) -> datetime:
    weekly_day = cast(int, user.weekly_day)
    weekly_time = cast(str, user.weekly_time)
    scheduled_time = _time_from_string(weekly_time)
    for days_ahead in range(0, 8):
        candidate_date = now.date() + timedelta(days=days_ahead)
        if candidate_date.weekday() != weekly_day:
            continue
        candidate = datetime.combine(
            candidate_date,
            scheduled_time,
            tzinfo=now.tzinfo,
        )
        if days_ahead == 0 and candidate <= now:
            continue
        return candidate
    fallback_date = now.date() + timedelta(days=7)
    return datetime.combine(fallback_date, scheduled_time, tzinfo=now.tzinfo)


def _next_monthly_local_due(user: User, now: datetime) -> datetime:
    monthly_day = cast(int, user.monthly_day)
    monthly_time = cast(str, user.monthly_time)
    scheduled_time = _time_from_string(monthly_time)
    year = now.year
    month = now.month
    for _ in range(0, 36):
        _, days_in_month = monthrange(year, month)
        if monthly_day <= days_in_month:
            candidate = datetime(
                year,
                month,
                monthly_day,
                scheduled_time.hour,
                scheduled_time.minute,
                tzinfo=now.tzinfo,
            )
            if candidate > now:
                return candidate
        month += 1
        if month > 12:
            month = 1
            year += 1
    return now + timedelta(days=31)


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
        hours=1,
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
                user=user,
                entry_type=EntryType.daily,
                due_at=evening_time,
            )
        )
        setattr(user, "daily_reminder_stage", 3)

    return due


def due_weekly_reminder(
    session: Session,
    user: User,
    now: datetime,
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
    session: Session,
    user: User,
    now: datetime,
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


def next_due_at(
    session: Session,
    user: User,
    now_utc: datetime,
    reminder_evening_hour: int,
) -> datetime:
    local_now = now_utc.astimezone(ZoneInfo(cast(str, user.timezone)))

    if user.pause_until and local_now.date() <= user.pause_until:
        resume_date = user.pause_until + timedelta(days=1)
        resume_local = datetime.combine(
            resume_date,
            time.min,
            tzinfo=local_now.tzinfo,
        )
        return _to_utc(resume_local)

    candidates: list[datetime] = []
    entry_date = local_now.date()

    daily_time = cast(str, user.daily_time)
    daily_scheduled = _local_datetime(entry_date, daily_time, user.timezone)
    evening_due = datetime.combine(
        entry_date,
        time(reminder_evening_hour, 0, tzinfo=local_now.tzinfo),
    )
    daily_stage = cast(int, user.daily_reminder_stage)
    if cast(date | None, user.daily_reminder_date) != entry_date:
        daily_stage = 0

    has_daily_entry = has_entry_for_date(
        session,
        user,
        EntryType.daily,
        entry_date,
    )
    if not has_daily_entry:
        if daily_stage == 0:
            candidates.append(daily_scheduled)
        elif daily_stage == 1:
            candidates.append(daily_scheduled + timedelta(hours=1))
        elif daily_stage == 2:
            candidates.append(evening_due)

    tomorrow = entry_date + timedelta(days=1)
    candidates.append(_local_datetime(tomorrow, daily_time, user.timezone))

    weekly_today = has_entry_for_date(
        session,
        user,
        EntryType.weekly,
        entry_date,
    )
    weekly_due = _next_weekly_local_due(user, local_now)
    if (
        weekly_today
        and entry_date.weekday() == cast(int, user.weekly_day)
        and weekly_due.date() == entry_date
    ):
        weekly_due += timedelta(days=7)
    candidates.append(weekly_due)

    monthly_today = has_entry_for_date(
        session,
        user,
        EntryType.monthly,
        entry_date,
    )
    monthly_due = _next_monthly_local_due(user, local_now)
    if (
        monthly_today
        and entry_date.day == cast(int, user.monthly_day)
        and monthly_due.date() == entry_date
    ):
        monthly_due = _next_monthly_local_due(
            user,
            local_now + timedelta(days=1),
        )
    candidates.append(monthly_due)

    return min(_to_utc(item) for item in candidates)


def list_due_user_candidates(
    session: Session,
    now_utc: datetime,
) -> list[User]:
    due_users = (
        session.query(User)
        .filter(
            or_(
                User.next_due_at.is_(None),
                User.next_due_at <= now_utc,
            )
        )
        .all()
    )
    return cast(list[User], due_users)
