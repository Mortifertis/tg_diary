from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.constants import (
    MANAGE_DELETE_PREFIX,
    MANAGE_EDIT_PREFIX,
    MANAGE_SHOW_MORE_PREFIX,
    MOOD_BAD_LABEL,
    MOOD_GOOD_LABEL,
    MOOD_NEUTRAL_LABEL,
    VIEW_SHOW_MORE_PREFIX,
)
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
    "view_find_by_id": "🔎",
    "view_export": "📤",
    "view_import": "📥",
    "view_backup": "🗄️",
    "settings_entries_page_size": "📄",
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


def _reply_keyboard(
    language: str,
    rows: list[list[str]],
    use_icons: bool,
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_button_text(language, key, use_icons))
                for key in row
            ]
            for row in rows
        ],
        resize_keyboard=True,
    )


def _two_columns_with_back(
    language: str,
    keys: list[str],
    use_icons: bool,
) -> ReplyKeyboardMarkup:
    rows: list[list[str]] = []
    for index in range(0, len(keys), 2):
        rows.append(keys[index : index + 2])
    rows.append(["menu_back"])
    return _reply_keyboard(language, rows, use_icons)


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
    return _reply_keyboard(
        language,
        [["menu_create", "menu_settings"], ["menu_view", "menu_manage"]],
        use_icons,
    )


def reminder_settings_keyboard(
    language: str,
    use_icons: bool = True,
) -> ReplyKeyboardMarkup:
    return _reply_keyboard(
        language,
        [
            ["settings_reminder_times", "menu_questions"],
            ["settings_language", "settings_appearance"],
            ["settings_entries_page_size"],
            ["menu_back"],
        ],
        use_icons,
    )


def view_entries_actions_keyboard(
    language: str,
    use_icons: bool = True,
) -> ReplyKeyboardMarkup:
    return _two_columns_with_back(
        language,
        ["view_find_by_id", "view_export", "view_import", "view_backup"],
        use_icons,
    )


def export_entries_keyboard(
    language: str,
    use_icons: bool = True,
) -> ReplyKeyboardMarkup:
    return _two_columns_with_back(
        language,
        [
            "export_week",
            "export_month",
            "export_3months",
            "export_year",
            "export_all",
        ],
        use_icons,
    )


def entries_page_size_keyboard(
    language: str,
    use_icons: bool = True,
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="5"), KeyboardButton(text="10")],
            [KeyboardButton(text="15"), KeyboardButton(text="20")],
            [KeyboardButton(text="25")],
            [
                KeyboardButton(
                    text=_button_text(language, "menu_back", use_icons)
                )
            ],
        ],
        resize_keyboard=True,
    )


def reminder_time_settings_keyboard(
    language: str,
    use_icons: bool = True,
) -> ReplyKeyboardMarkup:
    return _two_columns_with_back(
        language,
        ["menu_daily", "menu_weekly", "menu_monthly"],
        use_icons,
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
    return _two_columns_with_back(
        language,
        ["settings_toggle_icons", "settings_voice_recognition"],
        use_icons,
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
    return _two_columns_with_back(
        language,
        [
            "settings_voice_recognition_auto",
            "settings_voice_recognition_confirm",
            "settings_voice_recognition_off",
        ],
        use_icons,
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
    return _two_columns_with_back(
        language,
        [
            "menu_questions_add",
            "menu_questions_delete",
            "menu_questions_pause",
            "menu_questions_resume",
            "menu_questions_reset",
        ],
        use_icons,
    )


def view_entries_page_keyboard(
    language: str,
    offset: int,
    page_size: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=tr(language, "view_more", count=page_size),
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
