from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Config:
    bot_token: str
    database_url: str
    timezone: str
    daily_time_default: str
    weekly_day_default: int
    weekly_time_default: str
    monthly_day_default: int
    monthly_time_default: str
    reminder_evening_hour: int


def load_config() -> Config:
    return Config(
        bot_token=os.getenv("BOT_TOKEN", ""),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./tg_diary.db"),
        timezone=os.getenv("DEFAULT_TIMEZONE", "UTC"),
        daily_time_default=os.getenv("DEFAULT_DAILY_TIME", "09:00"),
        weekly_day_default=int(os.getenv("DEFAULT_WEEKLY_DAY", "6")),
        weekly_time_default=os.getenv("DEFAULT_WEEKLY_TIME", "20:00"),
        monthly_day_default=int(os.getenv("DEFAULT_MONTHLY_DAY", "1")),
        monthly_time_default=os.getenv("DEFAULT_MONTHLY_TIME", "20:00"),
        reminder_evening_hour=int(os.getenv("REMINDER_EVENING_HOUR", "20")),
    )
