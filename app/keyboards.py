from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

MOOD_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 Хорошо", callback_data="mood:good"),
            InlineKeyboardButton(text="🟡 Нормально", callback_data="mood:neutral"),
            InlineKeyboardButton(text="🔴 Плохо", callback_data="mood:bad"),
        ]
    ]
)
