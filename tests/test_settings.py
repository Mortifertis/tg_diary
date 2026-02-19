from types import SimpleNamespace

from app.handlers.settings import _is_valid_time, _menu_text


def test_is_valid_time_accepts_hh_mm() -> None:
    assert _is_valid_time("13:38") is True


def test_is_valid_time_rejects_invalid_values() -> None:
    assert _is_valid_time("13:99") is False
    assert _is_valid_time("9:00") is False
    assert _is_valid_time("13-38") is False


def test_settings_menu_text_accepts_icon_prefix() -> None:
    message = SimpleNamespace(text="⚙️ Настройки")

    assert _menu_text(message, "menu_settings")
