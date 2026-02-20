from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

from app.constants import (EXPORT_INDEX_CALLBACK, MANAGE_DELETE_PREFIX,
                           MANAGE_EDIT_PREFIX, MANAGE_SHOW_MORE_PREFIX,
                           MOOD_BAD_LABEL, MOOD_GOOD_LABEL, MOOD_NEUTRAL_LABEL,
                           VIEW_ACTION_BACK, VIEW_ACTION_BACKUP,
                           VIEW_ACTION_CALLBACK_PREFIX, VIEW_ACTION_EXPORT,
                           VIEW_ACTION_FIND_BY_ID, VIEW_SHOW_MORE_PREFIX)
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

MENU_ICONS = {
    "menu_create": "📝",
    "menu_settings": "⚙️",
    "menu_view": "📚",
    "menu_manage": "🛠️",
    "settings_reminder_times": "⏰",
    "menu_questions": "❓",
    "settings_language": "🌐",
    "settings_appearance": "🎨",
    "menu_daily": "☀️",
    "menu_weekly": "📅",
    "menu_monthly": "🗓️",
    "menu_questions_change": "✏️",
    "menu_questions_count": "🔢",
    "settings_toggle_icons": "✨",
    "settings_voice_recognition": "🎙️",
    "toggle_enable": "✅",
    "toggle_disable": "🚫",
    "menu_back": "↩️",
}


@dataclass(frozen=True)
class ToggleOptionMenu:
    setting_key: str
    enable_key: str = "toggle_enable"
    disable_key: str = "toggle_disable"

    def keyboard(
        self,
        language: str,
        use_icons: bool = True,
    ) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text=_button_text(
                            language,
                            self.enable_key,
                            use_icons,
                        ),
                    ),
                    KeyboardButton(
                        text=_button_text(
                            language,
                            self.disable_key,
                            use_icons,
                        ),
                    ),
                ],
                [
                    KeyboardButton(
                        text=_button_text(language, "menu_back", use_icons),
                    )
                ],
            ],
            resize_keyboard=True,
        )


MENU_ICONS_TOGGLE_MENU = ToggleOptionMenu(setting_key="settings_toggle_icons")
VOICE_CONFIRMATION_MENU = ToggleOptionMenu(
    setting_key="voice_convert_confirmation",
    enable_key="toggle_yes",
    disable_key="toggle_no",
)
VOICE_RECOGNITION_AUTO_MENU = ToggleOptionMenu(
    setting_key="settings_voice_recognition_auto",
)
VOICE_RECOGNITION_CONFIRM_MENU = ToggleOptionMenu(
    setting_key="settings_voice_recognition_confirm",
)
VOICE_RECOGNITION_OFF_MENU = ToggleOptionMenu(
    setting_key="settings_voice_recognition_off",
)


def _button_text(language: str, key: str, use_icons: bool) -> str:
    text = tr(language, key)
    if not use_icons:
        return text
    icon = MENU_ICONS.get(key)
    if not icon:
        return text
    return f"{icon} {text}"


def main_menu_keyboard(
    language: str,
    use_icons: bool = True,
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=_button_text(language, "menu_create", use_icons),
                ),
                KeyboardButton(
                    text=_button_text(language, "menu_settings", use_icons),
                ),
            ],
            [
                KeyboardButton(
                    text=_button_text(language, "menu_view", use_icons),
                ),
                KeyboardButton(
                    text=_button_text(language, "menu_manage", use_icons),
                ),
            ],
        ],
        resize_keyboard=True,
    )


def reminder_settings_keyboard(
    language: str,
    use_icons: bool = True,
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=_button_text(
                        language,
                        "settings_reminder_times",
                        use_icons,
                    )
                ),
                KeyboardButton(
                    text=_button_text(language, "menu_questions", use_icons),
                ),
            ],
            [
                KeyboardButton(
                    text=_button_text(
                        language,
                        "settings_language",
                        use_icons,
                    ),
                ),
                KeyboardButton(
                    text=_button_text(
                        language,
                        "settings_appearance",
                        use_icons,
                    ),
                ),
            ],
            [
                KeyboardButton(
                    text=_button_text(language, "menu_back", use_icons),
                )
            ],
        ],
        resize_keyboard=True,
    )


def reminder_time_settings_keyboard(
    language: str,
    use_icons: bool = True,
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=_button_text(language, "menu_daily", use_icons),
                ),
                KeyboardButton(
                    text=_button_text(language, "menu_weekly", use_icons),
                ),
            ],
            [
                KeyboardButton(
                    text=_button_text(language, "menu_monthly", use_icons),
                ),
                KeyboardButton(
                    text=_button_text(language, "menu_back", use_icons),
                ),
            ],
        ],
        resize_keyboard=True,
    )


def daily_questions_settings_keyboard(
    language: str,
    use_icons: bool = True,
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=_button_text(
                        language,
                        "menu_questions_change",
                        use_icons,
                    ),
                ),
                KeyboardButton(
                    text=_button_text(
                        language,
                        "menu_questions_count",
                        use_icons,
                    ),
                ),
            ],
            [
                KeyboardButton(
                    text=_button_text(language, "menu_back", use_icons),
                )
            ],
        ],
        resize_keyboard=True,
    )


def appearance_settings_keyboard(
    language: str,
    use_icons: bool = True,
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=_button_text(
                        language,
                        "settings_toggle_icons",
                        use_icons,
                    ),
                )
            ],
            [
                KeyboardButton(
                    text=_button_text(
                        language,
                        "settings_voice_recognition",
                        use_icons,
                    ),
                )
            ],
            [
                KeyboardButton(
                    text=_button_text(language, "menu_back", use_icons),
                )
            ],
        ],
        resize_keyboard=True,
    )


def settings_toggle_options_keyboard(
    language: str,
    use_icons: bool = True,
) -> ReplyKeyboardMarkup:
    return MENU_ICONS_TOGGLE_MENU.keyboard(language, use_icons)


def settings_voice_recognition_keyboard(
    language: str,
    use_icons: bool = True,
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=_button_text(
                        language,
                        "settings_voice_recognition_auto",
                        use_icons,
                    ),
                )
            ],
            [
                KeyboardButton(
                    text=_button_text(
                        language,
                        "settings_voice_recognition_confirm",
                        use_icons,
                    ),
                )
            ],
            [
                KeyboardButton(
                    text=_button_text(
                        language,
                        "settings_voice_recognition_off",
                        use_icons,
                    ),
                )
            ],
            [
                KeyboardButton(
                    text=_button_text(language, "menu_back", use_icons),
                )
            ],
        ],
        resize_keyboard=True,
    )


def voice_confirmation_keyboard(
    language: str,
    use_icons: bool = True,
) -> ReplyKeyboardMarkup:
    return VOICE_CONFIRMATION_MENU.keyboard(language, use_icons)


def language_keyboard(
    language: str,
    use_icons: bool = True,
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=LANGUAGE_FLAGS["ru"]),
                KeyboardButton(text=LANGUAGE_FLAGS["en"]),
            ],
            [
                KeyboardButton(text=LANGUAGE_FLAGS["fr"]),
                KeyboardButton(text=LANGUAGE_FLAGS["de"]),
            ],
            [
                KeyboardButton(
                    text=_button_text(language, "menu_back", use_icons),
                )
            ],
        ],
        resize_keyboard=True,
    )


def questions_settings_keyboard(
    language: str,
    use_icons: bool = True,
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=_button_text(
                        language,
                        "menu_questions_add",
                        use_icons,
                    ),
                ),
                KeyboardButton(
                    text=_button_text(
                        language,
                        "menu_questions_delete",
                        use_icons,
                    ),
                ),
            ],
            [
                KeyboardButton(
                    text=_button_text(
                        language,
                        "menu_questions_pause",
                        use_icons,
                    ),
                ),
                KeyboardButton(
                    text=_button_text(
                        language,
                        "menu_questions_resume",
                        use_icons,
                    ),
                ),
            ],
            [
                KeyboardButton(
                    text=_button_text(
                        language,
                        "menu_questions_reset",
                        use_icons,
                    ),
                ),
                KeyboardButton(
                    text=_button_text(language, "menu_back", use_icons),
                ),
            ],
        ],
        resize_keyboard=True,
    )


def view_entries_actions_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=tr(language, "view_find_by_id"),
                    callback_data=(
                        f"{VIEW_ACTION_CALLBACK_PREFIX}{VIEW_ACTION_FIND_BY_ID}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text=tr(language, "view_export"),
                    callback_data=(
                        f"{VIEW_ACTION_CALLBACK_PREFIX}{VIEW_ACTION_EXPORT}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text=tr(language, "view_backup"),
                    callback_data=(
                        f"{VIEW_ACTION_CALLBACK_PREFIX}{VIEW_ACTION_BACKUP}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text=tr(language, "view_back"),
                    callback_data=(
                        f"{VIEW_ACTION_CALLBACK_PREFIX}{VIEW_ACTION_BACK}"
                    ),
                )
            ],
        ]
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
                    text=tr(language, "export_back"),
                    callback_data="export:back",
                )
            ],
        ]
    )


def view_entries_page_keyboard(language: str, offset: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=tr(language, "view_more"),
                    callback_data=f"{VIEW_SHOW_MORE_PREFIX}{offset}",
                )
            ]
        ]
    )


def manage_entries_page_keyboard(
    offset: int,
    language: str,
    use_icons: bool = True,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=tr(language, "manage_entries_more"),
                    callback_data=f"{MANAGE_SHOW_MORE_PREFIX}{offset}",
                )
            ]
        ]
    )


def manage_entries_actions_keyboard(
    entry_index: str,
    language: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=tr(language, "manage_entries_edit"),
                    callback_data=f"{MANAGE_EDIT_PREFIX}{entry_index}",
                ),
                InlineKeyboardButton(
                    text=tr(language, "manage_entries_delete"),
                    callback_data=f"{MANAGE_DELETE_PREFIX}{entry_index}",
                ),
            ]
        ]
    )


QUESTIONS_SETTINGS_KEYBOARD = questions_settings_keyboard("ru")

EXPORT_ENTRIES_KEYBOARD = export_entries_keyboard("ru")

MAIN_MENU_KEYBOARD = main_menu_keyboard("ru")
REMINDER_SETTINGS_KEYBOARD = reminder_settings_keyboard("ru")
