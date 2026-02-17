from __future__ import annotations

from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

from app.constants import (MENU_BACK, MENU_CREATE_ENTRY, MENU_DAILY,
                           MENU_MONTHLY, MENU_PAUSE, MENU_RESUME,
                           MENU_SET_REMINDERS, MENU_VIEW_ENTRIES, MENU_WEEKLY,
                           MOOD_BAD_LABEL, MOOD_GOOD_LABEL, MOOD_NEUTRAL_LABEL)

MOOD_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text=MOOD_GOOD_LABEL, callback_data="mood:good"),
            InlineKeyboardButton(
                text=MOOD_NEUTRAL_LABEL,
                callback_data="mood:neutral",
            ),
            InlineKeyboardButton(text=MOOD_BAD_LABEL, callback_data="mood:bad"),
        ]
    ]
)

MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MENU_CREATE_ENTRY)],
        [KeyboardButton(text=MENU_SET_REMINDERS)],
        [KeyboardButton(text=MENU_PAUSE), KeyboardButton(text=MENU_RESUME)],
        [KeyboardButton(text=MENU_VIEW_ENTRIES)],
    ],
    resize_keyboard=True,
)

REMINDER_SETTINGS_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MENU_DAILY), KeyboardButton(text=MENU_WEEKLY)],
        [KeyboardButton(text=MENU_MONTHLY)],
        [KeyboardButton(text=MENU_BACK)],
    ],
    resize_keyboard=True,
)
