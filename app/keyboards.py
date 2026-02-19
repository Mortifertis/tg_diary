from __future__ import annotations

from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

from app.constants import (EXPORT_3_MONTHS, EXPORT_ALL, EXPORT_BACK,
                           EXPORT_INDEX_CALLBACK, EXPORT_MONTH,
                           EXPORT_VIEW_BY_INDEX, EXPORT_WEEK, EXPORT_YEAR,
                           MANAGE_DELETE_PREFIX, MANAGE_EDIT_PREFIX,
                           MANAGE_ENTRIES_DELETE, MANAGE_ENTRIES_EDIT,
                           MANAGE_ENTRIES_MORE, MANAGE_SHOW_MORE_PREFIX,
                           MENU_QUESTIONS_ADD, MENU_QUESTIONS_DELETE,
                           MENU_QUESTIONS_PAUSE, MENU_QUESTIONS_RESET,
                           MENU_QUESTIONS_RESUME, MOOD_BAD_LABEL,
                           MOOD_GOOD_LABEL, MOOD_NEUTRAL_LABEL)
from app.i18n import LANGUAGE_FLAGS, tr

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


def main_menu_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=tr(language, "menu_create"))],
            [KeyboardButton(text=tr(language, "menu_settings"))],
            [KeyboardButton(text=tr(language, "menu_view"))],
            [KeyboardButton(text=tr(language, "menu_manage"))],
        ],
        resize_keyboard=True,
    )


def reminder_settings_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=tr(language, "menu_daily")),
                KeyboardButton(text=tr(language, "menu_weekly")),
            ],
            [KeyboardButton(text=tr(language, "menu_monthly"))],
            [KeyboardButton(text=tr(language, "menu_questions"))],
            [KeyboardButton(text=tr(language, "settings_language"))],
            [KeyboardButton(text=tr(language, "menu_back"))],
        ],
        resize_keyboard=True,
    )


def language_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGUAGE_FLAGS["ru"]),
             KeyboardButton(text=LANGUAGE_FLAGS["en"])],
            [KeyboardButton(text=LANGUAGE_FLAGS["fr"]),
             KeyboardButton(text=LANGUAGE_FLAGS["de"])],
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


QUESTIONS_SETTINGS_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MENU_QUESTIONS_ADD)],
        [KeyboardButton(text=MENU_QUESTIONS_DELETE)],
        [KeyboardButton(text=MENU_QUESTIONS_PAUSE)],
        [KeyboardButton(text=MENU_QUESTIONS_RESUME)],
        [KeyboardButton(text=MENU_QUESTIONS_RESET)],
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

MAIN_MENU_KEYBOARD = main_menu_keyboard("ru")
REMINDER_SETTINGS_KEYBOARD = reminder_settings_keyboard("ru")
