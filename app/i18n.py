from __future__ import annotations

from typing import Any

DEFAULT_LANGUAGE = "ru"
SUPPORTED_LANGUAGES = ("ru", "en", "fr", "de")

LANGUAGE_FLAGS = {
    "ru": "🇷🇺",
    "en": "🇺🇸",
    "fr": "🇫🇷",
    "de": "🇩🇪",
}

TEXTS = {
    "ru": {
        "start": "Я дневник-бот. Буду писать первым и просить короткие заметки.\n"
        "Теперь можно пользоваться меню кнопок ниже.",
        "need_start": "Сначала напишите /start.",
        "settings_menu": "Выберите, что настроить:",
        "settings_language": "Язык",
        "settings_language_prompt": "Выберите язык:",
        "language_updated": "Язык обновлён.",
        "menu_create": "Сделать новую запись",
        "menu_settings": "Настройки",
        "menu_view": "Посмотреть записи",
        "menu_manage": "Редактирование/удаление записей",
        "menu_daily": "Ежедневные напоминания",
        "menu_weekly": "Еженедельные напоминания",
        "menu_monthly": "Ежемесячные напоминания",
        "menu_questions": "Ежедневные вопросы",
        "menu_back": "Назад в главное меню",
    },
    "en": {
        "start": "I am your diary bot. I will message first and ask for short notes.\n"
        "You can use the menu buttons below.",
        "need_start": "Send /start first.",
        "settings_menu": "Choose what to configure:",
        "settings_language": "Language",
        "settings_language_prompt": "Choose a language:",
        "language_updated": "Language updated.",
        "menu_create": "Create a new entry",
        "menu_settings": "Settings",
        "menu_view": "View entries",
        "menu_manage": "Edit/delete entries",
        "menu_daily": "Daily reminders",
        "menu_weekly": "Weekly reminders",
        "menu_monthly": "Monthly reminders",
        "menu_questions": "Daily questions",
        "menu_back": "Back to main menu",
    },
    "fr": {
        "start": "Je suis votre bot-journal. J'écrirai en premier et "
        "demanderai de courtes notes.\nVous pouvez utiliser le menu ci-dessous.",
        "need_start": "Envoyez d'abord /start.",
        "settings_menu": "Choisissez ce que vous voulez configurer :",
        "settings_language": "Langue",
        "settings_language_prompt": "Choisissez une langue :",
        "language_updated": "Langue mise à jour.",
        "menu_create": "Créer une entrée",
        "menu_settings": "Paramètres",
        "menu_view": "Voir les entrées",
        "menu_manage": "Modifier/supprimer des entrées",
        "menu_daily": "Rappels quotidiens",
        "menu_weekly": "Rappels hebdomadaires",
        "menu_monthly": "Rappels mensuels",
        "menu_questions": "Questions quotidiennes",
        "menu_back": "Retour au menu principal",
    },
    "de": {
        "start": "Ich bin dein Tagebuch-Bot. Ich schreibe zuerst und "
        "bitte um kurze Notizen.\nDu kannst die Menütasten unten nutzen.",
        "need_start": "Sende zuerst /start.",
        "settings_menu": "Wähle aus, was konfiguriert werden soll:",
        "settings_language": "Sprache",
        "settings_language_prompt": "Wähle eine Sprache:",
        "language_updated": "Sprache aktualisiert.",
        "menu_create": "Neuen Eintrag erstellen",
        "menu_settings": "Einstellungen",
        "menu_view": "Einträge ansehen",
        "menu_manage": "Einträge bearbeiten/löschen",
        "menu_daily": "Tägliche Erinnerungen",
        "menu_weekly": "Wöchentliche Erinnerungen",
        "menu_monthly": "Monatliche Erinnerungen",
        "menu_questions": "Tägliche Fragen",
        "menu_back": "Zurück zum Hauptmenü",
    },
}


def normalize_language(language: str | None) -> str:
    if language in SUPPORTED_LANGUAGES:
        return language
    return DEFAULT_LANGUAGE


def tr(language: str | None, key: str, **kwargs: Any) -> str:
    normalized = normalize_language(language)
    template = TEXTS[normalized].get(key, TEXTS[DEFAULT_LANGUAGE][key])
    return template.format(**kwargs)


def menu_variants(key: str) -> set[str]:
    return {TEXTS[language][key] for language in SUPPORTED_LANGUAGES}
