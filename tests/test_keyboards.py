from __future__ import annotations

from app.constants import (MENU_CREATE_ENTRY, MENU_MANAGE_ENTRIES,
                           MENU_QUESTIONS_RESET, MENU_SETTINGS,
                           MENU_VIEW_ENTRIES)
from app.i18n import tr
from app.keyboards import (EXPORT_ENTRIES_KEYBOARD, MAIN_MENU_KEYBOARD,
                           QUESTIONS_SETTINGS_KEYBOARD,
                           entries_page_size_keyboard, language_keyboard,
                           main_menu_keyboard,
                           settings_toggle_options_keyboard,
                           settings_voice_recognition_keyboard,
                           view_entries_actions_keyboard,
                           voice_confirmation_keyboard)


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


def test_export_menu_contains_period_buttons() -> None:
    texts = [
        button.text
        for row in EXPORT_ENTRIES_KEYBOARD.keyboard
        for button in row
    ]

    assert tr("ru", "export_week") in texts
    assert tr("ru", "export_all") in texts


def test_view_actions_keyboard_contains_backup_action() -> None:
    keyboard = view_entries_actions_keyboard("ru")
    texts = [button.text for row in keyboard.keyboard for button in row]

    assert any(text.endswith(tr("ru", "view_backup")) for text in texts)


def test_entries_page_size_keyboard_contains_limit() -> None:
    keyboard = entries_page_size_keyboard("ru", use_icons=False)
    texts = [button.text for row in keyboard.keyboard for button in row]

    assert "25" in texts


def test_toggle_options_keyboard_contains_enable_disable() -> None:
    keyboard = settings_toggle_options_keyboard("ru", use_icons=False)
    texts = [button.text for row in keyboard.keyboard for button in row]

    assert tr("ru", "toggle_enable") in texts
    assert tr("ru", "toggle_disable") in texts


def test_voice_recognition_settings_keyboard_contains_all_modes() -> None:
    keyboard = settings_voice_recognition_keyboard("ru", use_icons=False)
    texts = [button.text for row in keyboard.keyboard for button in row]

    assert tr("ru", "settings_voice_recognition_auto") in texts
    assert tr("ru", "settings_voice_recognition_confirm") in texts
    assert tr("ru", "settings_voice_recognition_off") in texts


def test_voice_confirmation_keyboard_contains_yes_no() -> None:
    keyboard = voice_confirmation_keyboard("ru", use_icons=False)
    texts = [button.text for row in keyboard.keyboard for button in row]

    assert tr("ru", "toggle_yes") in texts
    assert tr("ru", "toggle_no") in texts


def test_view_actions_keyboard_has_two_columns_and_back_row() -> None:
    keyboard = view_entries_actions_keyboard("ru", use_icons=False)

    assert len(keyboard.keyboard[0]) == 2
    assert len(keyboard.keyboard[1]) == 2
    assert len(keyboard.keyboard[-1]) == 1
    assert keyboard.keyboard[-1][0].text == tr("ru", "menu_back")


def test_export_keyboard_has_two_columns_and_back_row() -> None:
    keyboard = EXPORT_ENTRIES_KEYBOARD

    assert len(keyboard.keyboard[0]) == 2
    assert len(keyboard.keyboard[1]) == 2
    assert len(keyboard.keyboard[2]) == 1
    assert len(keyboard.keyboard[-1]) == 1
    assert keyboard.keyboard[-1][0].text.endswith(tr("ru", "menu_back"))


def test_questions_keyboard_has_back_on_separate_row() -> None:
    last_row = QUESTIONS_SETTINGS_KEYBOARD.keyboard[-1]

    assert len(last_row) == 1
    assert last_row[0].text.endswith(tr("ru", "menu_back"))
