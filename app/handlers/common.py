from __future__ import annotations

from datetime import datetime
from typing import cast

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, ForceReply, Message

from app.constants import (DAILY_PROMPT_SUFFIX,
                           ENTRY_DETAILS_ATTACHMENTS_HEADER,
                           ENTRY_DETAILS_HEADER_TEMPLATE,
                           ENTRY_DETAILS_TEXT_TEMPLATE, EXPORT_CALLBACK_PREFIX,
                           EXPORT_DONE_TEMPLATE, EXPORT_INDEX_CALLBACK,
                           EXPORT_MENU_PROMPT, EXPORT_NO_ENTRIES,
                           MANAGE_DELETE_PREFIX, MANAGE_EDIT_PREFIX,
                           MANAGE_ENTRIES_DELETED,
                           MANAGE_ENTRIES_PREVIEW_LIMIT,
                           MANAGE_ENTRIES_PREVIEW_TEXT_LIMIT,
                           MANAGE_ENTRIES_TEXT_EDIT_PLACEHOLDER_MAX,
                           MANAGE_ENTRIES_TEXT_EDIT_PROMPT,
                           MANAGE_ENTRIES_TEXT_EMPTY, MANAGE_ENTRIES_UPDATED,
                           MANAGE_SHOW_MORE_PREFIX, MANUAL_ENTRY_PROMPT,
                           MOOD_BAD_ICON, MOOD_CALLBACK_PREFIX, MOOD_GOOD_ICON,
                           MOOD_NEUTRAL_ICON, MOOD_SAVED_MESSAGE,
                           NEED_START_MESSAGE, STATS_MOOD_TEMPLATE,
                           STATS_STREAK_TEMPLATE, STATS_TOTAL_TEMPLATE,
                           STATUS_DAILY_TEMPLATE, STATUS_HEADER,
                           STATUS_MONTHLY_TEMPLATE,
                           STATUS_PAUSE_ACTIVE_TEMPLATE, STATUS_PAUSE_INACTIVE,
                           STATUS_PAUSE_TEMPLATE, STATUS_WEEKLY_TEMPLATE)
from app.i18n import menu_variants, tr
from app.keyboards import (MOOD_KEYBOARD, export_entries_keyboard,
                           main_menu_keyboard, manage_entries_actions_keyboard,
                           manage_entries_page_keyboard,
                           reminder_settings_keyboard)
from app.models import Entry, EntryType, User
from app.questions import DAILY_QUESTIONS, pick_question
from app.services.entries import (count_entries, delete_entry_by_index,
                                  format_entries_export, get_entry_by_index,
                                  list_entries, mood_breakdown,
                                  resolve_export_start_date, update_entry_text)
from app.services.questions import (ensure_default_daily_questions,
                                    list_active_daily_questions)
from app.services.timezones import (format_user_datetime, local_date_for_user,
                                    local_day_start_to_utc_naive)
from app.services.users import get_user_by_telegram_id
from app.states import EntryState, SettingsState
from app.storage import get_session

router = Router()


def _menu_text(message: Message, key: str) -> bool:
    text = (message.text or "").strip()
    variants = menu_variants(key)
    if text in variants:
        return True
    parts = text.split(maxsplit=1)
    if len(parts) == 2 and parts[1] in variants:
        return True
    return False


async def _handle_menu_interrupt(message: Message, state: FSMContext) -> bool:
    from app.handlers import settings as settings_handlers

    handlers = (
        ("menu_create", lambda: create_entry_from_menu(message, state)),
        ("menu_settings", lambda: reminder_settings_menu(message)),
        ("menu_view", lambda: view_entries(message)),
        ("menu_manage", lambda: manage_entries(message, state)),
        ("menu_back", lambda: back_to_main_menu(message, state)),
        (
            "settings_reminder_times",
            lambda: settings_handlers.reminder_times_menu(message, state),
        ),
        (
            "menu_daily",
            lambda: settings_handlers.menu_set_daily_time(
                message,
                state,
            ),
        ),
        (
            "menu_weekly",
            lambda: settings_handlers.menu_set_weekly_time(message, state),
        ),
        (
            "menu_monthly",
            lambda: settings_handlers.menu_set_monthly_time(message, state),
        ),
        (
            "settings_language",
            lambda: settings_handlers.settings_language_menu(message, state),
        ),
        (
            "settings_appearance",
            lambda: settings_handlers.appearance_menu(message, state),
        ),
        (
            "settings_toggle_icons",
            lambda: settings_handlers.toggle_icons(message),
        ),
        (
            "menu_questions",
            lambda: settings_handlers.daily_questions_menu(message, state),
        ),
        (
            "menu_questions_change",
            lambda: settings_handlers.change_daily_questions_menu(
                message,
                state,
            ),
        ),
        (
            "menu_questions_count",
            lambda: settings_handlers.set_daily_questions_count_menu(
                message,
                state,
            ),
        ),
        (
            "menu_questions_add",
            lambda: settings_handlers.prompt_add_daily_question(
                message,
                state,
            ),
        ),
        (
            "menu_questions_delete",
            lambda: settings_handlers.prompt_delete_daily_question(
                message,
                state,
            ),
        ),
        (
            "menu_questions_pause",
            lambda: settings_handlers.prompt_pause_daily_question(
                message,
                state,
            ),
        ),
        (
            "menu_questions_resume",
            lambda: settings_handlers.prompt_resume_daily_question(
                message,
                state,
            ),
        ),
        (
            "menu_questions_reset",
            lambda: settings_handlers.reset_daily_questions(message, state),
        ),
    )
    for key, handler in handlers:
        if _menu_text(message, key):
            await state.clear()
            await handler()
            return True
    return False


def _format_recent_entries(entries: list[Entry], user: User) -> str:
    lines = [tr(user.language, "recent_entries_header")]
    for index, entry in enumerate(entries, start=1):
        attachment_line = ""
        if entry.attachments:
            attachment_names = ", ".join(
                attachment.file_name for attachment in entry.attachments
            )
            attachment_line = (
                f"\n{tr(user.language, 'attachments')}: {attachment_names}"
            )
        created_at = cast(datetime, entry.created_at)
        lines.append(
            (
                f"{index}. {format_user_datetime(user, created_at)} "
                f"({entry.entry_type.value}) [{entry.entry_index}]\n"
                f"{entry.text}{attachment_line}"
            )
        )
    return "\n\n".join(lines)


def _shorten_entry_text(text: str) -> str:
    if len(text) <= MANAGE_ENTRIES_PREVIEW_TEXT_LIMIT:
        return text
    limit = MANAGE_ENTRIES_PREVIEW_TEXT_LIMIT
    return f"{text[:limit]}..."


def _build_edit_input_placeholder(text: str) -> str:
    cleaned_text = text.replace("\n", " ").strip()
    max_len = MANAGE_ENTRIES_TEXT_EDIT_PLACEHOLDER_MAX
    if len(cleaned_text) <= max_len:
        return cleaned_text
    return f"{cleaned_text[:max_len - 3]}..."


def _format_manage_entries_preview(entries: list[Entry], language: str) -> str:
    lines = [tr(language, "manage_entries_header")]
    for entry in entries:
        preview = _shorten_entry_text(cast(str, entry.text))
        lines.append(f"[{entry.entry_index}] {preview}")
    return "\n\n".join(lines)


async def _send_entry_details(
    message: Message,
    user: User,
    entry: Entry,
) -> None:
    header = ENTRY_DETAILS_HEADER_TEMPLATE.format(
        entry_index=entry.entry_index,
        created_at=format_user_datetime(
            user,
            cast(datetime, entry.created_at),
        ),
        entry_type=entry.entry_type.value,
        entry_date=entry.entry_date.strftime("%Y-%m-%d"),
    )
    await message.answer(
        f"{header}\n{ENTRY_DETAILS_TEXT_TEMPLATE.format(text=entry.text)}"
    )

    if entry.attachments:
        await message.answer(ENTRY_DETAILS_ATTACHMENTS_HEADER)
        for attachment in entry.attachments:
            if attachment.attachment_type.value == "image":
                await message.answer_photo(
                    photo=attachment.file_id,
                    caption=attachment.file_name,
                )
            else:
                await message.answer_document(
                    document=attachment.file_id,
                    caption=attachment.file_name,
                )


@router.message(CommandStart())
async def start(message: Message) -> None:
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            from app.config import load_config

            config = load_config()
            user = User(
                telegram_id=message.from_user.id,
                timezone=config.timezone,
                language="ru",
                daily_time=config.daily_time_default,
                weekly_day=config.weekly_day_default,
                weekly_time=config.weekly_time_default,
                monthly_day=config.monthly_day_default,
                monthly_time=config.monthly_time_default,
            )
            session.add(user)
            session.commit()
        ensure_default_daily_questions(session, user)
    await message.answer(
        tr(user.language, "start"),
        reply_markup=main_menu_keyboard(user.language),
    )


@router.message(Command("stats"))
async def stats(message: Message) -> None:
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(
                tr("ru", "start"), reply_markup=main_menu_keyboard("ru")
            )
            return
        total = count_entries(session, user)
        mood_counts = mood_breakdown(session, user)
        streak = user.streak
    mood_line = " / ".join(
        f"{key}: {value}"
        for key, value in [
            (MOOD_GOOD_ICON, mood_counts.get("good", 0)),
            (MOOD_NEUTRAL_ICON, mood_counts.get("neutral", 0)),
            (MOOD_BAD_ICON, mood_counts.get("bad", 0)),
        ]
    )
    await message.answer(
        f"{STATS_TOTAL_TEMPLATE.format(total=total)}\n"
        f"{STATS_STREAK_TEMPLATE.format(streak=streak)}\n"
        f"{STATS_MOOD_TEMPLATE.format(mood_line=mood_line)}",
        reply_markup=main_menu_keyboard(user.language),
    )


@router.message(Command("status"))
async def status(message: Message) -> None:
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        pause_until = user.pause_until
        daily_time = user.daily_time
        weekly_day = user.weekly_day
        weekly_time = user.weekly_time
        monthly_day = user.monthly_day
        monthly_time = user.monthly_time
    pause = (
        STATUS_PAUSE_ACTIVE_TEMPLATE.format(pause_until=pause_until)
        if pause_until
        else STATUS_PAUSE_INACTIVE
    )
    weekly_status = STATUS_WEEKLY_TEMPLATE.format(
        weekly_day=weekly_day,
        weekly_time=weekly_time,
    )
    monthly_status = STATUS_MONTHLY_TEMPLATE.format(
        monthly_day=monthly_day,
        monthly_time=monthly_time,
    )
    await message.answer(
        f"{STATUS_HEADER}\n"
        f"{STATUS_DAILY_TEMPLATE.format(daily_time=daily_time)}\n"
        f"{weekly_status}\n"
        f"{monthly_status}\n"
        f"{STATUS_PAUSE_TEMPLATE.format(pause=pause)}",
        reply_markup=main_menu_keyboard(user.language),
    )


@router.message(Command("daily"))
async def daily_prompt(message: Message, state: FSMContext) -> None:
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        questions = list_active_daily_questions(session, user)
    question_pool = questions or DAILY_QUESTIONS
    question = pick_question(question_pool)
    await state.set_state(EntryState.waiting_text)
    await state.update_data(
        entry_type=EntryType.daily.value,
        entry_date=local_date_for_user(user).isoformat(),
        question=question,
        mood=None,
        question_queue=[],
    )
    await message.answer(
        f"{question}\n{DAILY_PROMPT_SUFFIX}", reply_markup=MOOD_KEYBOARD
    )


@router.message(lambda message: _menu_text(message, "menu_create"))
async def create_entry_from_menu(message: Message, state: FSMContext) -> None:
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer(tr("ru", "need_start"))
        return

    await state.set_state(EntryState.waiting_text)
    await state.update_data(
        entry_type=EntryType.user.value,
        entry_date=local_date_for_user(user).isoformat(),
        question=None,
        mood=None,
        question_queue=[],
    )
    await message.answer(MANUAL_ENTRY_PROMPT)


@router.message(lambda message: _menu_text(message, "menu_settings"))
async def reminder_settings_menu(message: Message) -> None:
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
    language = user.language if user else "ru"
    await message.answer(
        tr(language, "settings_menu"),
        reply_markup=reminder_settings_keyboard(language),
    )


@router.message(lambda message: _menu_text(message, "menu_back"))
async def back_to_main_menu(message: Message, state: FSMContext) -> None:
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
    language = user.language if user else "ru"
    current_state = await state.get_state()

    settings_states = {
        SettingsState.waiting_language.state,
        SettingsState.waiting_daily_time.state,
        SettingsState.waiting_weekly_time.state,
        SettingsState.waiting_monthly_time.state,
        SettingsState.waiting_new_daily_question.state,
        SettingsState.waiting_delete_daily_question_id.state,
        SettingsState.waiting_pause_daily_question_id.state,
        SettingsState.waiting_resume_daily_question_id.state,
        SettingsState.in_questions_menu.state,
    }
    if current_state in settings_states:
        await state.clear()
        await message.answer(
            tr(language, "settings_menu"),
            reply_markup=reminder_settings_keyboard(language),
        )
        return

    await state.clear()
    await message.answer(
        tr(language, "main_menu_opened"),
        reply_markup=main_menu_keyboard(language),
    )


@router.message(lambda message: _menu_text(message, "menu_view"))
async def view_entries(message: Message) -> None:
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        recent_entries = list_entries(session, user, limit=3)

    if not recent_entries:
        await message.answer(
            tr(user.language, "recent_entries_empty"),
            reply_markup=main_menu_keyboard(user.language),
        )
        return

    await message.answer(
        _format_recent_entries(recent_entries, user),
        reply_markup=main_menu_keyboard(user.language),
    )
    await message.answer(
        EXPORT_MENU_PROMPT, reply_markup=export_entries_keyboard(user.language)
    )


@router.message(lambda message: _menu_text(message, "menu_manage"))
async def manage_entries(message: Message, state: FSMContext) -> None:
    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        preview_entries = list_entries(
            session,
            user,
            limit=MANAGE_ENTRIES_PREVIEW_LIMIT,
        )
        total_entries = count_entries(session, user)

    if not preview_entries:
        await message.answer(tr(user.language, "manage_entries_empty"))
        return

    await state.set_state(EntryState.waiting_manage_entry_index)
    await message.answer(
        _format_manage_entries_preview(preview_entries, user.language)
    )

    if total_entries > MANAGE_ENTRIES_PREVIEW_LIMIT:
        await message.answer(
            tr(user.language, "manage_entries_prompt"),
            reply_markup=manage_entries_page_keyboard(
                MANAGE_ENTRIES_PREVIEW_LIMIT,
                user.language,
            ),
        )
        return

    await message.answer(tr(user.language, "manage_entries_prompt"))


@router.callback_query(F.data.startswith(MANAGE_SHOW_MORE_PREFIX))
async def show_more_manage_entries(callback: CallbackQuery) -> None:
    if not callback.data:
        await callback.answer()
        return

    offset_text = callback.data.replace(MANAGE_SHOW_MORE_PREFIX, "", 1)
    if not offset_text.isdigit():
        await callback.answer()
        return
    offset = int(offset_text)

    with get_session(callback.bot) as session:
        user = get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            if callback.message:
                await callback.message.answer(NEED_START_MESSAGE)
            await callback.answer()
            return
        entries = list_entries(session, user, limit=None)

    chunk = entries[offset:offset + MANAGE_ENTRIES_PREVIEW_LIMIT]
    if not chunk:
        if callback.message:
            await callback.message.answer(
                tr(user.language, "manage_entries_page_end")
            )
        await callback.answer()
        return

    if callback.message:
        await callback.message.answer(
            _format_manage_entries_preview(chunk, user.language)
        )
        next_offset = offset + MANAGE_ENTRIES_PREVIEW_LIMIT
        if next_offset < len(entries):
            await callback.message.answer(
                tr(user.language, "manage_entries_prompt"),
                reply_markup=manage_entries_page_keyboard(
                    next_offset,
                    user.language,
                ),
            )
        else:
            await callback.message.answer(
                tr(user.language, "manage_entries_prompt")
            )
    await callback.answer()


def _resolve_period_label(period: str, language: str) -> str | None:
    period_labels = {
        "week": tr(language, "export_week"),
        "month": tr(language, "export_month"),
        "3months": tr(language, "export_3months"),
        "year": tr(language, "export_year"),
        "all": tr(language, "export_all"),
    }
    return period_labels.get(period)


@router.callback_query(F.data.startswith(EXPORT_CALLBACK_PREFIX))
async def export_entries(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data:
        await callback.answer()
        return
    period = callback.data.split(":", maxsplit=1)[1]
    if period == "back":
        language = "ru"
        with get_session(callback.bot) as session:
            user = get_user_by_telegram_id(session, callback.from_user.id)
        if user:
            language = user.language
        await callback.answer()
        if callback.message:
            await callback.message.answer(
                tr(language, "main_menu_opened"),
                reply_markup=main_menu_keyboard(language),
            )
        return
    if callback.data == EXPORT_INDEX_CALLBACK:
        with get_session(callback.bot) as session:
            user = get_user_by_telegram_id(session, callback.from_user.id)
        language = user.language if user else "ru"
        await state.set_state(EntryState.waiting_entry_index)
        if callback.message:
            await callback.message.answer(tr(language, "entry_index_prompt"))
        await callback.answer()
        return

    with get_session(callback.bot) as session:
        user = get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            if callback.message:
                await callback.message.answer(NEED_START_MESSAGE)
            await callback.answer()
            return
        local_today = local_date_for_user(user)
        created_from_date = resolve_export_start_date(period, local_today)
        created_from = None
        if created_from_date is not None:
            created_from = local_day_start_to_utc_naive(
                user, created_from_date
            )
        entries = list_entries(
            session, user, limit=None, created_from=created_from
        )

    period_label = _resolve_period_label(period, user.language)
    if period_label is None:
        await callback.answer()
        return

    await callback.answer()
    if not entries:
        if callback.message:
            await callback.message.answer(EXPORT_NO_ENTRIES)
        return

    export_text = format_entries_export(entries)
    export_bytes = export_text.encode("utf-8")
    export_file = BufferedInputFile(
        export_bytes, filename=f"entries_{period}.txt"
    )
    if callback.message:
        await callback.message.answer_document(
            export_file,
            caption=EXPORT_DONE_TEMPLATE.format(period_label=period_label),
        )


@router.message(EntryState.waiting_entry_index)
async def show_entry_by_index(message: Message, state: FSMContext) -> None:
    if await _handle_menu_interrupt(message, state):
        return

    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
    entry_index = (message.text or "").strip().lower()
    if not entry_index:
        await message.answer(tr(user.language, "entry_index_invalid"))
        return

    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        entry = get_entry_by_index(session, user, entry_index)

    if not entry:
        await message.answer(
            tr(user.language, "entry_not_found", entry_index=entry_index)
        )
        return

    await _send_entry_details(message, user, entry)

    await state.clear()


@router.message(EntryState.waiting_manage_entry_index)
async def manage_entry_by_index(message: Message, state: FSMContext) -> None:
    if await _handle_menu_interrupt(message, state):
        return

    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
    entry_index = (message.text or "").strip().lower()
    if not entry_index:
        await message.answer(tr(user.language, "entry_index_invalid"))
        return

    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        entry = get_entry_by_index(session, user, entry_index)

    if not entry:
        await message.answer(
            tr(user.language, "entry_not_found", entry_index=entry_index)
        )
        return

    await _send_entry_details(message, user, entry)
    await message.answer(
        tr(user.language, "manage_entries_actions_prompt"),
        reply_markup=manage_entries_actions_keyboard(
            entry_index,
            user.language,
        ),
    )


@router.callback_query(F.data.startswith(MANAGE_EDIT_PREFIX))
async def start_edit_entry(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data:
        await callback.answer()
        return
    entry_index = callback.data.replace(MANAGE_EDIT_PREFIX, "", 1)

    with get_session(callback.bot) as session:
        user = get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            if callback.message:
                await callback.message.answer(NEED_START_MESSAGE)
            await callback.answer()
            return
        entry = get_entry_by_index(session, user, entry_index)

    if not entry:
        if callback.message:
            await callback.message.answer(
                tr(user.language, "entry_not_found", entry_index=entry_index)
            )
        await callback.answer()
        return

    await state.set_state(EntryState.waiting_manage_entry_edit_text)
    await state.update_data(manage_entry_index=entry_index)
    if callback.message:
        await _send_entry_details(callback.message, user, entry)
        await callback.message.answer(
            MANAGE_ENTRIES_TEXT_EDIT_PROMPT,
            reply_markup=ForceReply(
                input_field_placeholder=_build_edit_input_placeholder(
                    cast(str, entry.text)
                )
            ),
        )
    await callback.answer()


@router.callback_query(F.data.startswith(MANAGE_DELETE_PREFIX))
async def delete_entry(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data:
        await callback.answer()
        return
    entry_index = callback.data.replace(MANAGE_DELETE_PREFIX, "", 1)

    with get_session(callback.bot) as session:
        user = get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            if callback.message:
                await callback.message.answer(NEED_START_MESSAGE)
            await callback.answer()
            return
        is_deleted = delete_entry_by_index(session, user, entry_index)

    if callback.message:
        if is_deleted:
            await callback.message.answer(MANAGE_ENTRIES_DELETED)
        else:
            await callback.message.answer(
                tr(user.language, "entry_not_found", entry_index=entry_index)
            )
    await callback.answer()
    await state.set_state(EntryState.waiting_manage_entry_index)


@router.message(EntryState.waiting_manage_entry_edit_text)
async def update_entry(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer(MANAGE_ENTRIES_TEXT_EMPTY)
        return

    data = await state.get_data()
    entry_index = data.get("manage_entry_index")
    if not entry_index:
        with get_session(message.bot) as session:
            user = get_user_by_telegram_id(session, message.from_user.id)
        language = user.language if user else "ru"
        await message.answer(tr(language, "entry_index_invalid"))
        await state.set_state(EntryState.waiting_manage_entry_index)
        return

    with get_session(message.bot) as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        entry = update_entry_text(session, user, entry_index, text)

    if not entry:
        await message.answer(
            tr(user.language, "entry_not_found", entry_index=entry_index)
        )
        await state.set_state(EntryState.waiting_manage_entry_index)
        return

    await message.answer(MANAGE_ENTRIES_UPDATED)
    await _send_entry_details(message, user, entry)
    await message.answer(
        tr(user.language, "manage_entries_actions_prompt"),
        reply_markup=manage_entries_actions_keyboard(
            entry_index,
            user.language,
        ),
    )
    await state.set_state(EntryState.waiting_manage_entry_index)


@router.callback_query(F.data.startswith(MOOD_CALLBACK_PREFIX))
async def set_mood(callback: CallbackQuery, state: FSMContext) -> None:
    mood = callback.data.split(":", maxsplit=1)[1]
    await state.update_data(mood=mood)
    await callback.answer(MOOD_SAVED_MESSAGE)
