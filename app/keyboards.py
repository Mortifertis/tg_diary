from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.constants import MOOD_BAD_LABEL, MOOD_GOOD_LABEL, MOOD_NEUTRAL_LABEL

MOOD_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text=MOOD_GOOD_LABEL, callback_data="mood:good"),
            InlineKeyboardButton(text=MOOD_NEUTRAL_LABEL, callback_data="mood:neutral"),
            InlineKeyboardButton(text=MOOD_BAD_LABEL, callback_data="mood:bad"),
        ]
    ]
)
