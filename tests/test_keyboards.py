from __future__ import annotations

from app.constants import (EXPORT_VIEW_BY_INDEX, MENU_CREATE_ENTRY,
                           MENU_QUESTIONS_RESET, MENU_SETTINGS,
                           MENU_VIEW_ENTRIES)
from app.keyboards import (EXPORT_ENTRIES_KEYBOARD, MAIN_MENU_KEYBOARD,
                           QUESTIONS_SETTINGS_KEYBOARD)


def test_main_menu_contains_new_structure() -> None:
    texts = [
        button.text for row in MAIN_MENU_KEYBOARD.keyboard for button in row
    ]

    assert texts == [MENU_CREATE_ENTRY, MENU_SETTINGS, MENU_VIEW_ENTRIES]


def test_questions_menu_contains_reset_button() -> None:
    texts = [
        button.text
        for row in QUESTIONS_SETTINGS_KEYBOARD.keyboard
        for button in row
    ]

    assert MENU_QUESTIONS_RESET in texts


def test_export_menu_contains_entry_index_button() -> None:
    texts = [
        button.text
        for row in EXPORT_ENTRIES_KEYBOARD.inline_keyboard
        for button in row
    ]

    assert EXPORT_VIEW_BY_INDEX in texts
