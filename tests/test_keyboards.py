from __future__ import annotations

from app.constants import (EXPORT_VIEW_BY_INDEX, MENU_CREATE_ENTRY,
                           MENU_MANAGE_ENTRIES, MENU_QUESTIONS_RESET,
                           MENU_SETTINGS, MENU_VIEW_ENTRIES)
from app.i18n import tr
from app.keyboards import (EXPORT_ENTRIES_KEYBOARD, MAIN_MENU_KEYBOARD,
                           QUESTIONS_SETTINGS_KEYBOARD, language_keyboard,
                           main_menu_keyboard,
                           settings_toggle_options_keyboard)


def test_main_menu_contains_new_structure() -> None:
    keyboard = main_menu_keyboard("ru", use_icons=False)
    texts = [button.text for row in keyboard.keyboard for button in row]

    assert texts == [
        MENU_CREATE_ENTRY,
        MENU_SETTINGS,
        MENU_VIEW_ENTRIES,
        MENU_MANAGE_ENTRIES,
    ]

    icon_texts = [
        button.text
        for row in MAIN_MENU_KEYBOARD.keyboard
        for button in row
    ]
    assert icon_texts[0].startswith("📝")


def test_questions_menu_contains_reset_button() -> None:
    texts = [
        button.text
        for row in QUESTIONS_SETTINGS_KEYBOARD.keyboard
        for button in row
    ]

    assert MENU_QUESTIONS_RESET in texts


def test_questions_menu_contains_back_button() -> None:
    texts = [
        button.text
        for row in QUESTIONS_SETTINGS_KEYBOARD.keyboard
        for button in row
    ]

    assert any(text.endswith(tr("ru", "menu_back")) for text in texts)


def test_language_menu_contains_back_button() -> None:
    keyboard = language_keyboard("en")
    texts = [button.text for row in keyboard.keyboard for button in row]

    assert any(text.endswith(tr("en", "menu_back")) for text in texts)


def test_export_menu_contains_entry_index_button() -> None:
    texts = [
        button.text
        for row in EXPORT_ENTRIES_KEYBOARD.inline_keyboard
        for button in row
    ]

    assert EXPORT_VIEW_BY_INDEX in texts


def test_toggle_options_keyboard_contains_enable_disable() -> None:
    keyboard = settings_toggle_options_keyboard("ru", use_icons=False)
    texts = [button.text for row in keyboard.keyboard for button in row]

    assert tr("ru", "toggle_enable") in texts
    assert tr("ru", "toggle_disable") in texts
