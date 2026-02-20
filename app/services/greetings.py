from __future__ import annotations

import random
from datetime import datetime

from app.models import User

DEFAULT_NAME = "друг"

TIME_GREETINGS = {
    "night": ("Доброй ночи", "Ночная смена мыслей"),
    "morning": ("Доброе утро", "С бодрым утром"),
    "day": ("Добрый день", "Отличного дня"),
    "evening": ("Добрый вечер", "Уютного вечера"),
}

REMINDER_PHRASES = (
    "Пора поделиться своими мыслями! ✍️😊",
    "Самое время сделать новую запись! 📝✨",
    "Лови момент и запиши пару строк! 🌟📔",
    "Открой дневник — мысли уже ждут! 💭💫",
    "Небольшая заметка сейчас = ясная голова позже! 😄🧠",
)


def _time_bucket(hour: int) -> str:
    if 6 <= hour <= 11:
        return "morning"
    if 12 <= hour <= 17:
        return "day"
    if 18 <= hour <= 23:
        return "evening"
    return "night"


def resolve_display_name(user: User) -> str:
    raw_name = (user.display_name or "").strip()
    return raw_name or DEFAULT_NAME


def build_reminder_greeting(user: User, reminder_time: datetime) -> str:
    bucket = _time_bucket(reminder_time.hour)
    welcome = random.choice(TIME_GREETINGS[bucket])
    phrase = random.choice(REMINDER_PHRASES)
    name = resolve_display_name(user)
    return f"{welcome}, {name}! {phrase}"
