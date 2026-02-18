from __future__ import annotations

from datetime import date

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.constants import (DAILY_PROMPT_SUFFIX, EXPORT_3_MONTHS, EXPORT_ALL,
                           EXPORT_CALLBACK_PREFIX, EXPORT_DONE_TEMPLATE,
                           EXPORT_MENU_PROMPT, EXPORT_MONTH, EXPORT_NO_ENTRIES,
                           EXPORT_WEEK, EXPORT_YEAR, MANUAL_ENTRY_PROMPT,
                           MENU_BACK, MENU_CREATE_ENTRY, MENU_SETTINGS,
                           MENU_VIEW_ENTRIES, MOOD_BAD_ICON, MOOD_GOOD_ICON,
                           MOOD_NEUTRAL_ICON, MOOD_SAVED_MESSAGE,
                           NEED_START_MESSAGE, RECENT_ENTRIES_EMPTY,
                           RECENT_ENTRIES_HEADER, SETTINGS_MENU_MESSAGE,
                           START_MESSAGE, STATS_MOOD_TEMPLATE,
                           STATS_STREAK_TEMPLATE, STATS_TOTAL_TEMPLATE,
                           STATUS_DAILY_TEMPLATE, STATUS_HEADER,
                           STATUS_MONTHLY_TEMPLATE,
                           STATUS_PAUSE_ACTIVE_TEMPLATE, STATUS_PAUSE_INACTIVE,
                           STATUS_PAUSE_TEMPLATE, STATUS_WEEKLY_TEMPLATE)
from app.keyboards import (EXPORT_ENTRIES_KEYBOARD, MAIN_MENU_KEYBOARD,
                           MOOD_KEYBOARD, REMINDER_SETTINGS_KEYBOARD)
from app.models import Entry, EntryType, User
from app.questions import DAILY_QUESTIONS, pick_question
from app.services.entries import (count_entries, format_entries_export,
                                  list_entries, mood_breakdown,
                                  resolve_export_start_date)
from app.services.questions import (ensure_default_daily_questions,
                                    list_active_daily_questions)
from app.states import EntryState
from app.storage import get_session

router = Router()


def _format_recent_entries(entries: list[Entry]) -> str:
    lines = [RECENT_ENTRIES_HEADER]
    for index, entry in enumerate(entries, start=1):
        lines.append(
            (
                f"{index}. {entry.created_at:%Y-%m-%d %H:%M:%S} "
                f"({entry.entry_type.value})\n"
                f"{entry.text}"
            )
        )
    return "\n\n".join(lines)


@router.message(CommandStart())
async def start(message: Message) -> None:
    with get_session(message.bot) as session:
        user = (
            session.query(User)
            .filter_by(telegram_id=message.from_user.id)
            .first()
        )
        if not user:
            from app.config import load_config

            config = load_config()
            user = User(
                telegram_id=message.from_user.id,
                timezone=config.timezone,
                daily_time=config.daily_time_default,
                weekly_day=config.weekly_day_default,
                weekly_time=config.weekly_time_default,
                monthly_day=config.monthly_day_default,
                monthly_time=config.monthly_time_default,
            )
            session.add(user)
            session.commit()
        ensure_default_daily_questions(session, user)
    await message.answer(START_MESSAGE, reply_markup=MAIN_MENU_KEYBOARD)


@router.message(Command("stats"))
async def stats(message: Message) -> None:
    with get_session(message.bot) as session:
        user = (
            session.query(User)
            .filter_by(telegram_id=message.from_user.id)
            .first()
        )
        if not user:
            await message.answer(
                START_MESSAGE, reply_markup=MAIN_MENU_KEYBOARD
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
        reply_markup=MAIN_MENU_KEYBOARD,
    )


@router.message(Command("status"))
async def status(message: Message) -> None:
    with get_session(message.bot) as session:
        user = (
            session.query(User)
            .filter_by(telegram_id=message.from_user.id)
            .first()
        )
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
        reply_markup=MAIN_MENU_KEYBOARD,
    )


@router.message(Command("daily"))
async def daily_prompt(message: Message, state: FSMContext) -> None:
    with get_session(message.bot) as session:
        user = (
            session.query(User)
            .filter_by(telegram_id=message.from_user.id)
            .first()
        )
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        questions = list_active_daily_questions(session, user)
    question_pool = questions or DAILY_QUESTIONS
    question = pick_question(question_pool)
    await state.set_state(EntryState.waiting_text)
    await state.update_data(
        entry_type=EntryType.daily.value,
        entry_date=date.today().isoformat(),
        question=question,
        mood=None,
        question_queue=[],
    )
    await message.answer(
        f"{question}\n{DAILY_PROMPT_SUFFIX}", reply_markup=MOOD_KEYBOARD
    )


@router.message(F.text == MENU_CREATE_ENTRY)
async def create_entry_from_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(EntryState.waiting_text)
    await state.update_data(
        entry_type=EntryType.user.value,
        entry_date=date.today().isoformat(),
        question=None,
        mood=None,
        question_queue=[],
    )
    await message.answer(MANUAL_ENTRY_PROMPT)


@router.message(F.text == MENU_SETTINGS)
async def reminder_settings_menu(message: Message) -> None:
    await message.answer(
        SETTINGS_MENU_MESSAGE,
        reply_markup=REMINDER_SETTINGS_KEYBOARD,
    )


@router.message(F.text == MENU_BACK)
async def back_to_main_menu(message: Message) -> None:
    await message.answer(START_MESSAGE, reply_markup=MAIN_MENU_KEYBOARD)


@router.message(F.text == MENU_VIEW_ENTRIES)
async def view_entries(message: Message) -> None:
    with get_session(message.bot) as session:
        user = (
            session.query(User)
            .filter_by(telegram_id=message.from_user.id)
            .first()
        )
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        recent_entries = list_entries(session, user, limit=3)

    if not recent_entries:
        await message.answer(
            RECENT_ENTRIES_EMPTY, reply_markup=MAIN_MENU_KEYBOARD
        )
        return

    await message.answer(
        _format_recent_entries(recent_entries),
        reply_markup=MAIN_MENU_KEYBOARD,
    )
    await message.answer(
        EXPORT_MENU_PROMPT, reply_markup=EXPORT_ENTRIES_KEYBOARD
    )


def _resolve_period_label(period: str) -> str | None:
    period_labels = {
        "week": EXPORT_WEEK,
        "month": EXPORT_MONTH,
        "3months": EXPORT_3_MONTHS,
        "year": EXPORT_YEAR,
        "all": EXPORT_ALL,
    }
    return period_labels.get(period)


@router.callback_query(F.data.startswith(EXPORT_CALLBACK_PREFIX))
async def export_entries(callback: CallbackQuery) -> None:
    if not callback.data:
        await callback.answer()
        return
    period = callback.data.split(":", maxsplit=1)[1]
    if period == "back":
        await callback.answer()
        if callback.message:
            await callback.message.answer(
                START_MESSAGE,
                reply_markup=MAIN_MENU_KEYBOARD,
            )
        return

    period_label = _resolve_period_label(period)
    if period_label is None:
        await callback.answer()
        return

    with get_session(callback.bot) as session:
        user = (
            session.query(User)
            .filter_by(telegram_id=callback.from_user.id)
            .first()
        )
        if not user:
            if callback.message:
                await callback.message.answer(NEED_START_MESSAGE)
            await callback.answer()
            return
        created_from = resolve_export_start_date(period, date.today())
        entries = list_entries(
            session, user, limit=None, created_from=created_from
        )

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


@router.callback_query(F.data.startswith("mood:"))
async def set_mood(callback: CallbackQuery, state: FSMContext) -> None:
    mood = callback.data.split(":", maxsplit=1)[1]
    await state.update_data(mood=mood)
    await callback.answer(MOOD_SAVED_MESSAGE)
