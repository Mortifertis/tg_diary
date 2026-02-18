from __future__ import annotations

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.models import User

UTC_ZONE = ZoneInfo("UTC")


def _resolve_user_timezone(user: User) -> ZoneInfo:
    try:
        return ZoneInfo(user.timezone)
    except ZoneInfoNotFoundError:
        return UTC_ZONE


def _to_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def local_datetime_for_user(user: User, value: datetime) -> datetime:
    return _to_aware_utc(value).astimezone(_resolve_user_timezone(user))


def local_date_for_user(user: User, value: datetime | None = None) -> date:
    source = value or datetime.now(UTC)
    return local_datetime_for_user(user, source).date()


def format_user_datetime(user: User, value: datetime) -> str:
    local_value = local_datetime_for_user(user, value)
    return local_value.strftime("%Y-%m-%d %H:%M:%S")


def local_day_start_to_utc_naive(user: User, day: date) -> datetime:
    local_tz = _resolve_user_timezone(user)
    local_start = datetime.combine(day, time.min, tzinfo=local_tz)
    return local_start.astimezone(UTC).replace(tzinfo=None)


def message_datetime_to_utc_naive(value: datetime) -> datetime:
    return _to_aware_utc(value).replace(tzinfo=None)
