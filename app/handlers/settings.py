from __future__ import annotations

from datetime import UTC, date, datetime
from datetime import time as dt_time
from datetime import timedelta
from typing import cast

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import load_config
from app.constants import (DAILY_TIME_UPDATED_TEMPLATE, MENU_PAUSE,
                           MENU_RESUME, MONTHLY_TIME_UPDATED_TEMPLATE,
                           MONTHLY_USAGE_MESSAGE, NEED_START_MESSAGE,
                           PAUSE_DISABLED_MESSAGE, PAUSE_ENABLED_TEMPLATE,
                           QUESTIONS_ADD_PROMPT, QUESTIONS_ADDED_MESSAGE,
                           QUESTIONS_DELETE_PROMPT, QUESTIONS_DELETED_MESSAGE,
                           QUESTIONS_DUPLICATE_MESSAGE,
                           QUESTIONS_EMPTY_MESSAGE,
                           QUESTIONS_EMPTY_TEXT_MESSAGE,
                           QUESTIONS_INVALID_ID_MESSAGE, QUESTIONS_LIST_HEADER,
                           QUESTIONS_NOT_FOUND_MESSAGE, QUESTIONS_PAUSE_PROMPT,
                           QUESTIONS_PAUSED_MESSAGE,
                           QUESTIONS_RESET_DEFAULTS_MESSAGE,
                           QUESTIONS_RESUME_PROMPT, QUESTIONS_RESUMED_MESSAGE,
                           QUESTIONS_STATUS_ACTIVE, QUESTIONS_STATUS_PAUSED,
                           SETTINGS_DAILY_PROMPT, SETTINGS_MONTHLY_PROMPT,
                           SETTINGS_QUESTIONS_MENU_MESSAGE,
                           SETTINGS_WEEKLY_PROMPT, TIME_USAGE_MESSAGE,
                           WEEKLY_TIME_UPDATED_TEMPLATE, WEEKLY_USAGE_MESSAGE)
from app.i18n import LANGUAGE_FLAGS, menu_variants, tr
from app.keyboards import (appearance_settings_keyboard,
                           daily_questions_settings_keyboard,
                           entries_page_size_keyboard, language_keyboard,
                           questions_settings_keyboard,
                           reminder_time_settings_keyboard,
                           settings_toggle_options_keyboard,
                           settings_voice_recognition_keyboard)
from app.models import User
from app.services.questions import (add_daily_question, delete_daily_question,
                                    list_daily_questions,
                                    reset_daily_questions_to_default,
                                    set_daily_question_active)
from app.services.reminders import next_due_at
from app.services.users import get_user_by_telegram_id
from app.states import SettingsState
from app.storage import get_session

router = Router()


def _telegram_user_id(message: Message) -> int | None:
    from_user = message.from_user
    if from_user is None:
        return None
    return cast(int, from_user.id)


def _recalculate_next_due_at(session, user: User) -> None:
    config = load_config()
    user.next_due_at = next_due_at(
        session,
        user,
        datetime.now(UTC),
        config.reminder_evening_hour,
    )


def _menu_text(message: Message, key: str) -> bool:
    text = (message.text or "").strip()
    variants = menu_variants(key)
    if text in variants:
        return True
    parts = text.split(maxsplit=1)
    if len(parts) == 2 and parts[1] in variants:
        return True
    return False


def _flag_to_language(flag: str | None) -> str | None:
    if not flag:
        return None
    for language, value in cast(dict[str, str], LANGUAGE_FLAGS).items():
        if value == flag:
            return language
    return None


def _is_valid_time(value: str) -> bool:
    try:
        dt_time.fromisoformat(value)
    except ValueError:
        return False
    return len(value) == 5


def _parse_daily_time(raw_value: str) -> str | None:
    time_value = raw_value.strip()
    if not _is_valid_time(time_value):
        return None
    return time_value


def _parse_weekly(raw_value: str) -> tuple[int, str] | None:
    args = raw_value.split(maxsplit=1)
    if len(args) != 2:
        return None
    try:
        day = int(args[0])
    except ValueError:
        return None
    if day < 0 or day > 6:
        return None
    time_value = args[1].strip()
    if not _is_valid_time(time_value):
        return None
    return day, time_value


def _parse_monthly(raw_value: str) -> tuple[int, str] | None:
    args = raw_value.split(maxsplit=1)
    if len(args) != 2:
        return None
    try:
        day = int(args[0])
    except ValueError:
        return None
    if day < 1 or day > 31:
        return None
    time_value = args[1].strip()
    if not _is_valid_time(time_value):
        return None
    return day, time_value


def _parse_question_id(raw_value: str | None) -> int | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value.isdigit():
        return None
    return int(value)


def _update_daily_time(message: Message, time_value: str) -> str:
    telegram_user_id = _telegram_user_id(message)
    if telegram_user_id is None:
        return cast(str, NEED_START_MESSAGE)
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, telegram_user_id)
        if not user:
            return cast(str, NEED_START_MESSAGE)
        user.daily_time = time_value
        user.daily_reminder_date = None
        user.daily_reminder_stage = 0
        _recalculate_next_due_at(session, user)
    return cast(
        str,
        DAILY_TIME_UPDATED_TEMPLATE.format(time_value=time_value),
    )


def _update_weekly_time(message: Message, day: int, time_value: str) -> str:
    telegram_user_id = _telegram_user_id(message)
    if telegram_user_id is None:
        return cast(str, NEED_START_MESSAGE)
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, telegram_user_id)
        if not user:
            return cast(str, NEED_START_MESSAGE)
        user.weekly_day = day
        user.weekly_time = time_value
        _recalculate_next_due_at(session, user)
    return cast(
        str,
        WEEKLY_TIME_UPDATED_TEMPLATE.format(day=day, time_value=time_value),
    )


def _update_monthly_time(message: Message, day: int, time_value: str) -> str:
    telegram_user_id = _telegram_user_id(message)
    if telegram_user_id is None:
        return cast(str, NEED_START_MESSAGE)
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, telegram_user_id)
        if not user:
            return cast(str, NEED_START_MESSAGE)
        user.monthly_day = day
        user.monthly_time = time_value
        _recalculate_next_due_at(session, user)
    return cast(
        str,
        MONTHLY_TIME_UPDATED_TEMPLATE.format(day=day, time_value=time_value),
    )


def _build_daily_questions_list(message: Message) -> str:
    telegram_user_id = _telegram_user_id(message)
    if telegram_user_id is None:
        return cast(str, NEED_START_MESSAGE)
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, telegram_user_id)
        if not user:
            return cast(str, NEED_START_MESSAGE)
        questions = list_daily_questions(session, user)

    if not questions:
        return cast(str, QUESTIONS_EMPTY_MESSAGE)

    lines = [cast(str, QUESTIONS_LIST_HEADER)]
    for question in questions:
        status = (
            QUESTIONS_STATUS_ACTIVE
            if question.is_active
            else QUESTIONS_STATUS_PAUSED
        )
        lines.append(f"{question.id}. [{status}] {question.text}")
    return "\n".join(lines)


async def _show_daily_questions_menu(message: Message) -> None:
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
    language = user.language if user else "ru"
    use_icons = bool(user.enable_menu_icons) if user else True

    await message.answer(
        _build_daily_questions_list(message),
        reply_markup=questions_settings_keyboard(language, use_icons),
    )
    await message.answer(SETTINGS_QUESTIONS_MENU_MESSAGE)


@router.message(Command("time"))
async def set_daily_time(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(TIME_USAGE_MESSAGE)
        return
    time_value = _parse_daily_time(args[1])
    if not time_value:
        await message.answer(TIME_USAGE_MESSAGE)
        return
    await message.answer(_update_daily_time(message, time_value))


@router.message(Command("weekly"))
async def set_weekly_time(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(WEEKLY_USAGE_MESSAGE)
        return
    parsed = _parse_weekly(args[1])
    if not parsed:
        await message.answer(WEEKLY_USAGE_MESSAGE)
        return
    day, time_value = parsed
    await message.answer(_update_weekly_time(message, day, time_value))


@router.message(Command("monthly"))
async def set_monthly_time(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(MONTHLY_USAGE_MESSAGE)
        return
    parsed = _parse_monthly(args[1])
    if not parsed:
        await message.answer(MONTHLY_USAGE_MESSAGE)
        return
    day, time_value = parsed
    await message.answer(_update_monthly_time(message, day, time_value))


@router.message(lambda message: _menu_text(message, "menu_daily"))
async def menu_set_daily_time(message: Message, state: FSMContext) -> None:
    await state.set_state(SettingsState.waiting_daily_time)
    await message.answer(SETTINGS_DAILY_PROMPT)


@router.message(lambda message: _menu_text(message, "menu_weekly"))
async def menu_set_weekly_time(message: Message, state: FSMContext) -> None:
    await state.set_state(SettingsState.waiting_weekly_time)
    await message.answer(SETTINGS_WEEKLY_PROMPT)


@router.message(lambda message: _menu_text(message, "menu_monthly"))
async def menu_set_monthly_time(message: Message, state: FSMContext) -> None:
    await state.set_state(SettingsState.waiting_monthly_time)
    await message.answer(SETTINGS_MONTHLY_PROMPT)


@router.message(lambda message: _menu_text(message, "menu_questions"))
async def daily_questions_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(SettingsState.in_daily_questions_settings)
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
    language = user.language if user else "ru"
    use_icons = bool(user.enable_menu_icons) if user else True
    await message.answer(
        tr(language, "settings_questions_menu"),
        reply_markup=daily_questions_settings_keyboard(language, use_icons),
    )


@router.message(lambda message: _menu_text(message, "menu_questions_change"))
async def change_daily_questions_menu(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(SettingsState.in_questions_menu)
    await _show_daily_questions_menu(message)


@router.message(lambda message: _menu_text(message, "menu_questions_count"))
async def set_daily_questions_count_menu(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(SettingsState.waiting_daily_questions_count)
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
    language = user.language if user else "ru"
    await message.answer(tr(language, "settings_questions_count_prompt"))


@router.message(
    lambda message: _menu_text(message, "settings_entries_page_size")
)
async def set_entries_page_size_menu(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(SettingsState.waiting_entries_page_size)
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
    language = user.language if user else "ru"
    use_icons = bool(user.enable_menu_icons) if user else True
    await message.answer(
        tr(language, "settings_entries_page_size_prompt"),
        reply_markup=entries_page_size_keyboard(language, use_icons),
    )


@router.message(lambda message: _menu_text(message, "settings_reminder_times"))
async def reminder_times_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(SettingsState.in_reminder_times_settings)
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
    language = user.language if user else "ru"
    use_icons = bool(user.enable_menu_icons) if user else True
    await message.answer(
        tr(language, "settings_reminder_times_menu"),
        reply_markup=reminder_time_settings_keyboard(language, use_icons),
    )


@router.message(lambda message: _menu_text(message, "settings_appearance"))
async def appearance_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(SettingsState.in_appearance_settings)
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
    language = user.language if user else "ru"
    use_icons = bool(user.enable_menu_icons) if user else True
    await message.answer(
        tr(language, "settings_appearance"),
        reply_markup=appearance_settings_keyboard(language, use_icons),
    )


async def _show_toggle_icons_menu(
    message: Message,
    language: str,
    use_icons: bool,
) -> None:
    await message.answer(
        tr(language, "settings_toggle_icons_prompt"),
        reply_markup=settings_toggle_options_keyboard(language, use_icons),
    )


@router.message(
    lambda message: _menu_text(message, "settings_voice_recognition")
)
async def voice_recognition_menu(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(SettingsState.waiting_voice_recognition_mode)
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
    language = user.language if user else "ru"
    use_icons = bool(user.enable_menu_icons) if user else True
    await message.answer(
        tr(language, "settings_voice_recognition_prompt"),
        reply_markup=settings_voice_recognition_keyboard(language, use_icons),
    )


@router.message(SettingsState.waiting_voice_recognition_mode)
async def save_voice_recognition_mode(
    message: Message,
    state: FSMContext,
) -> None:
    mode = None
    if _menu_text(message, "settings_voice_recognition_auto"):
        mode = "auto"
    if _menu_text(message, "settings_voice_recognition_confirm"):
        mode = "confirm"
    if _menu_text(message, "settings_voice_recognition_off"):
        mode = "off"

    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(tr("ru", "need_start"))
            return
        language = user.language
        use_icons = bool(user.enable_menu_icons)
        if mode is None:
            await message.answer(
                tr(language, "settings_voice_recognition_prompt"),
                reply_markup=settings_voice_recognition_keyboard(
                    language,
                    use_icons,
                ),
            )
            return
        user.voice_recognition_mode = mode

    await state.clear()
    mode_key = {
        "auto": "settings_voice_recognition_mode_auto",
        "confirm": "settings_voice_recognition_mode_confirm",
        "off": "settings_voice_recognition_mode_off",
    }[mode]
    await message.answer(
        tr(language, mode_key),
        reply_markup=appearance_settings_keyboard(language, use_icons),
    )


@router.message(lambda message: _menu_text(message, "settings_language"))
async def settings_language_menu(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(SettingsState.waiting_language)
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
    language = user.language if user else "ru"
    use_icons = bool(user.enable_menu_icons) if user else True
    await message.answer(
        tr(language, "settings_language_prompt"),
        reply_markup=language_keyboard(language, use_icons),
    )


@router.message(SettingsState.waiting_language)
async def save_language(message: Message, state: FSMContext) -> None:
    selected = _flag_to_language(message.text)
    if not selected:
        with get_session(message.bot) as session:
            user = get_user_by_telegram_id(session, message.from_user.id)
        language = user.language if user else "ru"
        use_icons = bool(user.enable_menu_icons) if user else True
        await message.answer(
            tr(language, "settings_language_prompt"),
            reply_markup=language_keyboard(language, use_icons),
        )
        return

    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(tr("ru", "need_start"))
            return
        user.language = selected

    await state.clear()
    await message.answer(
        tr(selected, "language_updated"),
    )


@router.message(lambda message: _menu_text(message, "settings_toggle_icons"))
async def toggle_icons(message: Message, state: FSMContext) -> None:
    await state.set_state(SettingsState.waiting_toggle_icons_value)
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(tr("ru", "need_start"))
            return
        language = user.language
        use_icons = bool(user.enable_menu_icons)

    await _show_toggle_icons_menu(message, language, use_icons)


@router.message(SettingsState.waiting_toggle_icons_value)
async def save_toggle_icons(message: Message, state: FSMContext) -> None:
    selected_enable = _menu_text(message, "toggle_enable")
    selected_disable = _menu_text(message, "toggle_disable")
    if not (selected_enable or selected_disable):
        with get_session(message.bot) as session:
            user = get_user_by_telegram_id(session, message.from_user.id)
        language = user.language if user else "ru"
        use_icons = bool(user.enable_menu_icons) if user else True
        await _show_toggle_icons_menu(message, language, use_icons)
        return

    use_icons = selected_enable
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(tr("ru", "need_start"))
            return
        user.enable_menu_icons = use_icons
        language = user.language

    key = "settings_icons_enabled" if use_icons else "settings_icons_disabled"
    await state.clear()
    await message.answer(
        tr(language, key),
        reply_markup=appearance_settings_keyboard(language, use_icons),
    )


@router.message(lambda message: _menu_text(message, "menu_questions_add"))
async def prompt_add_daily_question(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(SettingsState.waiting_new_daily_question)
    await message.answer(QUESTIONS_ADD_PROMPT)


@router.message(lambda message: _menu_text(message, "menu_questions_delete"))
async def prompt_delete_daily_question(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(SettingsState.waiting_delete_daily_question_id)
    await message.answer(QUESTIONS_DELETE_PROMPT)


@router.message(lambda message: _menu_text(message, "menu_questions_pause"))
async def prompt_pause_daily_question(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(SettingsState.waiting_pause_daily_question_id)
    await message.answer(QUESTIONS_PAUSE_PROMPT)


@router.message(lambda message: _menu_text(message, "menu_questions_resume"))
async def prompt_resume_daily_question(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(SettingsState.waiting_resume_daily_question_id)
    await message.answer(QUESTIONS_RESUME_PROMPT)


@router.message(lambda message: _menu_text(message, "menu_questions_reset"))
async def reset_daily_questions(message: Message, state: FSMContext) -> None:
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        reset_daily_questions_to_default(session, user)

    await message.answer(QUESTIONS_RESET_DEFAULTS_MESSAGE)
    await state.set_state(SettingsState.in_questions_menu)
    await _show_daily_questions_menu(message)


@router.message(SettingsState.waiting_daily_questions_count)
async def save_daily_questions_count(
    message: Message,
    state: FSMContext,
) -> None:
    value = (message.text or "").strip()
    if not value.isdigit():
        with get_session(message.bot) as session:
            user = get_user_by_telegram_id(session, message.from_user.id)
        language = user.language if user else "ru"
        await message.answer(tr(language, "settings_questions_count_invalid"))
        return

    count = int(value)
    if count < 1 or count > 10:
        with get_session(message.bot) as session:
            user = get_user_by_telegram_id(session, message.from_user.id)
        language = user.language if user else "ru"
        await message.answer(tr(language, "settings_questions_count_invalid"))
        return

    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        user.daily_questions_count = count
        language = user.language

    await state.clear()
    await message.answer(
        tr(language, "settings_questions_count_updated", count=count)
    )


@router.message(SettingsState.waiting_entries_page_size)
async def save_entries_page_size(
    message: Message,
    state: FSMContext,
) -> None:
    value = (message.text or "").strip()
    if not value.isdigit():
        with get_session(message.bot) as session:
            user = get_user_by_telegram_id(session, message.from_user.id)
        language = user.language if user else "ru"
        await message.answer(
            tr(language, "settings_entries_page_size_invalid")
        )
        return

    count = int(value)
    if count < 1 or count > 25:
        with get_session(message.bot) as session:
            user = get_user_by_telegram_id(session, message.from_user.id)
        language = user.language if user else "ru"
        await message.answer(
            tr(language, "settings_entries_page_size_invalid")
        )
        return

    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        user.entries_page_size = count
        language = user.language

    await state.clear()
    await message.answer(
        tr(language, "settings_entries_page_size_updated", count=count)
    )


@router.message(SettingsState.waiting_new_daily_question)
async def save_new_daily_question(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer(QUESTIONS_EMPTY_TEXT_MESSAGE)
        return

    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        added = add_daily_question(session, user, text)

    await state.clear()
    if not added:
        await message.answer(QUESTIONS_DUPLICATE_MESSAGE)
        return
    await message.answer(QUESTIONS_ADDED_MESSAGE)
    await state.set_state(SettingsState.in_questions_menu)
    await _show_daily_questions_menu(message)


@router.message(SettingsState.waiting_delete_daily_question_id)
async def delete_daily_question_from_menu(
    message: Message,
    state: FSMContext,
) -> None:
    question_id = _parse_question_id(message.text)
    if question_id is None:
        await message.answer(QUESTIONS_INVALID_ID_MESSAGE)
        return

    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        deleted = delete_daily_question(session, user, question_id)

    await state.clear()
    if not deleted:
        await message.answer(QUESTIONS_NOT_FOUND_MESSAGE)
        return
    await message.answer(QUESTIONS_DELETED_MESSAGE)
    await state.set_state(SettingsState.in_questions_menu)
    await _show_daily_questions_menu(message)


@router.message(SettingsState.waiting_pause_daily_question_id)
async def pause_daily_question_from_menu(
    message: Message,
    state: FSMContext,
) -> None:
    question_id = _parse_question_id(message.text)
    if question_id is None:
        await message.answer(QUESTIONS_INVALID_ID_MESSAGE)
        return

    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        updated = set_daily_question_active(session, user, question_id, False)

    await state.clear()
    if not updated:
        await message.answer(QUESTIONS_NOT_FOUND_MESSAGE)
        return
    await message.answer(QUESTIONS_PAUSED_MESSAGE)
    await state.set_state(SettingsState.in_questions_menu)
    await _show_daily_questions_menu(message)


@router.message(SettingsState.waiting_resume_daily_question_id)
async def resume_daily_question_from_menu(
    message: Message,
    state: FSMContext,
) -> None:
    question_id = _parse_question_id(message.text)
    if question_id is None:
        await message.answer(QUESTIONS_INVALID_ID_MESSAGE)
        return

    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        updated = set_daily_question_active(session, user, question_id, True)

    await state.clear()
    if not updated:
        await message.answer(QUESTIONS_NOT_FOUND_MESSAGE)
        return
    await message.answer(QUESTIONS_RESUMED_MESSAGE)
    await state.set_state(SettingsState.in_questions_menu)
    await _show_daily_questions_menu(message)


@router.message(SettingsState.waiting_daily_time)
async def save_daily_time_from_menu(
    message: Message,
    state: FSMContext,
) -> None:
    time_value = _parse_daily_time(message.text)
    if not time_value:
        await message.answer(TIME_USAGE_MESSAGE)
        return
    await state.clear()
    await message.answer(_update_daily_time(message, time_value))


@router.message(SettingsState.waiting_weekly_time)
async def save_weekly_time_from_menu(
    message: Message,
    state: FSMContext,
) -> None:
    parsed = _parse_weekly(message.text)
    if not parsed:
        await message.answer(WEEKLY_USAGE_MESSAGE)
        return
    await state.clear()
    day, time_value = parsed
    await message.answer(_update_weekly_time(message, day, time_value))


@router.message(SettingsState.waiting_monthly_time)
async def save_monthly_time_from_menu(
    message: Message,
    state: FSMContext,
) -> None:
    parsed = _parse_monthly(message.text)
    if not parsed:
        await message.answer(MONTHLY_USAGE_MESSAGE)
        return
    await state.clear()
    day, time_value = parsed
    await message.answer(_update_monthly_time(message, day, time_value))


@router.message(Command("pause"))
@router.message(lambda message: (message.text or "") == MENU_PAUSE)
async def pause(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    days = int(args[1]) if len(args) > 1 and args[1].isdigit() else 36500
    pause_until = date.today() + timedelta(days=days)
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        user.pause_until = pause_until
        _recalculate_next_due_at(session, user)
    await message.answer(
        PAUSE_ENABLED_TEMPLATE.format(pause_until=pause_until)
    )


@router.message(Command("resume"))
@router.message(lambda message: (message.text or "") == MENU_RESUME)
async def resume(message: Message) -> None:
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        user.pause_until = None
        _recalculate_next_due_at(session, user)
    await message.answer(PAUSE_DISABLED_MESSAGE)
