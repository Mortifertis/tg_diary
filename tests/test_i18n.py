from app.i18n import (DEFAULT_LANGUAGE, LANGUAGE_FLAGS, SUPPORTED_LANGUAGES,
                      menu_variants, normalize_language, tr,
                      validate_translations)


def test_menu_variants_contains_all_languages() -> None:
    variants = menu_variants("menu_settings")
    assert len(variants) == 4


def test_translation_returns_english_text() -> None:
    assert tr("en", "settings_language") == "Language"


def test_language_flags_contains_supported_languages() -> None:
    assert set(LANGUAGE_FLAGS) == {"ru", "en", "fr", "de"}


def test_back_translation_is_not_main_menu() -> None:
    assert tr("en", "menu_back") == "Back"


def test_normalize_language_accepts_regional_locale() -> None:
    assert normalize_language("en-US") == "en"


def test_translation_falls_back_to_default_language_by_locale() -> None:
    assert tr("it-IT", "settings_language") == tr(
        DEFAULT_LANGUAGE,
        "settings_language",
    )


def test_validate_translations_has_no_missing_or_extra_keys() -> None:
    report = validate_translations()
    for language in SUPPORTED_LANGUAGES:
        assert report[language]["missing"] == set()
        assert report[language]["extra"] == set()
