from app.i18n import LANGUAGE_FLAGS, menu_variants, tr


def test_menu_variants_contains_all_languages() -> None:
    variants = menu_variants("menu_settings")
    assert len(variants) == 4


def test_translation_returns_english_text() -> None:
    assert tr("en", "settings_language") == "Language"


def test_language_flags_contains_supported_languages() -> None:
    assert set(LANGUAGE_FLAGS) == {"ru", "en", "fr", "de"}


def test_back_translation_is_not_main_menu() -> None:
    assert tr("en", "menu_back") == "Back"
