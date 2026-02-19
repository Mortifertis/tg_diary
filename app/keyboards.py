from __future__ import annotations

from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

from app.constants import (EXPORT_INDEX_CALLBACK, MANAGE_DELETE_PREFIX,
                           MANAGE_EDIT_PREFIX, MANAGE_ENTRIES_DELETE,
                           MANAGE_ENTRIES_EDIT, MANAGE_ENTRIES_MORE,
                           MANAGE_SHOW_MORE_PREFIX, MOOD_BAD_LABEL,
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


def language_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGUAGE_FLAGS["ru"]),
             KeyboardButton(text=LANGUAGE_FLAGS["en"])],
            [KeyboardButton(text=LANGUAGE_FLAGS["fr"]),
             KeyboardButton(text=LANGUAGE_FLAGS["de"])],
            [KeyboardButton(text=tr(language, "menu_back"))],
        ],
        resize_keyboard=True,
    )


def questions_settings_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=tr(language, "menu_questions_add"))],
            [KeyboardButton(text=tr(language, "menu_questions_delete"))],
            [KeyboardButton(text=tr(language, "menu_questions_pause"))],
            [KeyboardButton(text=tr(language, "menu_questions_resume"))],
            [KeyboardButton(text=tr(language, "menu_questions_reset"))],
            [KeyboardButton(text=tr(language, "menu_back"))],
        ],
        resize_keyboard=True,
    )


def export_entries_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=tr(language, "export_week"),
                    callback_data="export:week",
                )
            ],
            [
                InlineKeyboardButton(
                    text=tr(language, "export_month"),
                    callback_data="export:month",
                )
            ],
            [
                InlineKeyboardButton(
                    text=tr(language, "export_3months"),
                    callback_data="export:3months",
                )
            ],
            [
                InlineKeyboardButton(
                    text=tr(language, "export_year"),
                    callback_data="export:year",
                )
            ],
            [
                InlineKeyboardButton(
                    text=tr(language, "export_all"),
                    callback_data="export:all",
                )
            ],
            [
                InlineKeyboardButton(
                    text=tr(language, "export_view_by_index"),
                    callback_data=EXPORT_INDEX_CALLBACK,
                )
            ],
            [
                InlineKeyboardButton(
                    text=tr(language, "export_back"),
                    callback_data="export:back",
                )
            ],
        ]
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


QUESTIONS_SETTINGS_KEYBOARD = questions_settings_keyboard("ru")

EXPORT_ENTRIES_KEYBOARD = export_entries_keyboard("ru")

MAIN_MENU_KEYBOARD = main_menu_keyboard("ru")
REMINDER_SETTINGS_KEYBOARD = reminder_settings_keyboard("ru")
