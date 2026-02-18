from __future__ import annotations

from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

from app.constants import (EXPORT_3_MONTHS, EXPORT_ALL, EXPORT_BACK,
                           EXPORT_INDEX_CALLBACK, EXPORT_MONTH,
                           EXPORT_VIEW_BY_INDEX, EXPORT_WEEK, EXPORT_YEAR,
                           MANAGE_DELETE_PREFIX, MANAGE_EDIT_PREFIX,
                           MANAGE_ENTRIES_DELETE, MANAGE_ENTRIES_EDIT,
                           MANAGE_ENTRIES_MORE, MANAGE_SHOW_MORE_PREFIX,
                           MENU_BACK, MENU_CREATE_ENTRY, MENU_DAILY,
                           MENU_DAILY_QUESTIONS, MENU_MANAGE_ENTRIES,
                           MENU_MONTHLY, MENU_QUESTIONS_ADD,
                           MENU_QUESTIONS_DELETE, MENU_QUESTIONS_PAUSE,
                           MENU_QUESTIONS_RESET, MENU_QUESTIONS_RESUME,
                           MENU_SETTINGS, MENU_VIEW_ENTRIES, MENU_WEEKLY,
                           MOOD_BAD_LABEL, MOOD_GOOD_LABEL, MOOD_NEUTRAL_LABEL)

MOOD_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=MOOD_GOOD_LABEL, callback_data="mood:good"
            ),
            InlineKeyboardButton(
                text=MOOD_NEUTRAL_LABEL,
                callback_data="mood:neutral",
            ),
            InlineKeyboardButton(
                text=MOOD_BAD_LABEL, callback_data="mood:bad"
            ),
        ]
    ]
)

MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MENU_CREATE_ENTRY)],
        [KeyboardButton(text=MENU_SETTINGS)],
        [KeyboardButton(text=MENU_VIEW_ENTRIES)],
        [KeyboardButton(text=MENU_MANAGE_ENTRIES)],
    ],
    resize_keyboard=True,
)


def manage_entries_page_keyboard(offset: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=MANAGE_ENTRIES_MORE,
                    callback_data=f"{MANAGE_SHOW_MORE_PREFIX}{offset}",
                )
            ]
        ]
    )


def manage_entries_actions_keyboard(entry_index: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=MANAGE_ENTRIES_EDIT,
                    callback_data=f"{MANAGE_EDIT_PREFIX}{entry_index}",
                ),
                InlineKeyboardButton(
                    text=MANAGE_ENTRIES_DELETE,
                    callback_data=f"{MANAGE_DELETE_PREFIX}{entry_index}",
                ),
            ]
        ]
    )


REMINDER_SETTINGS_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MENU_DAILY), KeyboardButton(text=MENU_WEEKLY)],
        [KeyboardButton(text=MENU_MONTHLY)],
        [KeyboardButton(text=MENU_DAILY_QUESTIONS)],
        [KeyboardButton(text=MENU_BACK)],
    ],
    resize_keyboard=True,
)


QUESTIONS_SETTINGS_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MENU_QUESTIONS_ADD)],
        [KeyboardButton(text=MENU_QUESTIONS_DELETE)],
        [KeyboardButton(text=MENU_QUESTIONS_PAUSE)],
        [KeyboardButton(text=MENU_QUESTIONS_RESUME)],
        [KeyboardButton(text=MENU_QUESTIONS_RESET)],
        [KeyboardButton(text=MENU_BACK)],
    ],
    resize_keyboard=True,
)


EXPORT_ENTRIES_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=EXPORT_WEEK, callback_data="export:week")],
        [
            InlineKeyboardButton(
                text=EXPORT_MONTH, callback_data="export:month"
            )
        ],
        [
            InlineKeyboardButton(
                text=EXPORT_3_MONTHS, callback_data="export:3months"
            )
        ],
        [InlineKeyboardButton(text=EXPORT_YEAR, callback_data="export:year")],
        [InlineKeyboardButton(text=EXPORT_ALL, callback_data="export:all")],
        [
            InlineKeyboardButton(
                text=EXPORT_VIEW_BY_INDEX,
                callback_data=EXPORT_INDEX_CALLBACK,
            )
        ],
        [InlineKeyboardButton(text=EXPORT_BACK, callback_data="export:back")],
    ]
)
