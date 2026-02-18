from __future__ import annotations

from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

from app.constants import (EXPORT_3_MONTHS, EXPORT_ALL, EXPORT_BACK,
                           EXPORT_MONTH, EXPORT_WEEK, EXPORT_YEAR, MENU_BACK,
                           MENU_CREATE_ENTRY, MENU_DAILY, MENU_MONTHLY,
                           MENU_PAUSE, MENU_RESUME, MENU_SET_REMINDERS,
                           MENU_VIEW_ENTRIES, MENU_WEEKLY, MOOD_BAD_LABEL,
                           MOOD_GOOD_LABEL, MOOD_NEUTRAL_LABEL)

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


EXPORT_ENTRIES_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=EXPORT_WEEK, callback_data="export:week")],
        [InlineKeyboardButton(text=EXPORT_MONTH, callback_data="export:month")],
        [InlineKeyboardButton(text=EXPORT_3_MONTHS, callback_data="export:3months")],
        [InlineKeyboardButton(text=EXPORT_YEAR, callback_data="export:year")],
        [InlineKeyboardButton(text=EXPORT_ALL, callback_data="export:all")],
        [InlineKeyboardButton(text=EXPORT_BACK, callback_data="export:back")],
    ]
)
