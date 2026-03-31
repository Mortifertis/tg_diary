from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from app.models import User
from app.services.greetings import (
    build_reminder_greeting,
    resolve_display_name,
)


def test_resolve_display_name_uses_default_for_empty_name() -> None:
    user = User(
        telegram_id=1,
        timezone="UTC",
        daily_time="09:00",
        weekly_day=1,
        weekly_time="20:00",
        monthly_day=1,
        monthly_time="20:00",
        display_name="   ",
    )

    assert resolve_display_name(user) == "друг"


def test_build_reminder_greeting_uses_time_bucket_and_name() -> None:
    user = User(
        telegram_id=2,
        timezone="UTC",
        daily_time="09:00",
        weekly_day=1,
        weekly_time="20:00",
        monthly_day=1,
        monthly_time="20:00",
        display_name="Аня",
    )

    with patch("app.services.greetings.random.choice") as choice_mock:
        choice_mock.side_effect = ["Доброе утро", "Пора писать! ✍️"]
        greeting = build_reminder_greeting(user, datetime(2024, 1, 1, 9, 0))

    assert greeting == "Доброе утро, Аня! Пора писать! ✍️"
