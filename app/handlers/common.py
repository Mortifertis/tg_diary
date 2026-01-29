from __future__ import annotations

from datetime import date

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.constants import (DAILY_PROMPT_SUFFIX, MOOD_BAD_ICON, MOOD_GOOD_ICON,
                           MOOD_NEUTRAL_ICON, MOOD_SAVED_MESSAGE,
                           NEED_START_MESSAGE, START_MESSAGE,
                           STATS_MOOD_TEMPLATE, STATS_STREAK_TEMPLATE,
                           STATS_TOTAL_TEMPLATE, STATUS_DAILY_TEMPLATE,
                           STATUS_HEADER, STATUS_MONTHLY_TEMPLATE,
                           STATUS_PAUSE_ACTIVE_TEMPLATE, STATUS_PAUSE_INACTIVE,
                           STATUS_PAUSE_TEMPLATE, STATUS_WEEKLY_TEMPLATE)
from app.keyboards import MOOD_KEYBOARD
from app.models import EntryType, User
from app.questions import DAILY_QUESTIONS, pick_question
from app.services.entries import count_entries, mood_breakdown
from app.states import EntryState
from app.storage import get_session

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
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
    await message.answer(START_MESSAGE)


@router.message(Command("stats"))
async def stats(message: Message) -> None:
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer(START_MESSAGE)
            return
        total = count_entries(session, user)
        mood_counts = mood_breakdown(session, user)
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
        f"{STATS_STREAK_TEMPLATE.format(streak=user.streak)}\n"
        f"{STATS_MOOD_TEMPLATE.format(mood_line=mood_line)}"
    )


@router.message(Command("status"))
async def status(message: Message) -> None:
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
    pause = (
        STATUS_PAUSE_ACTIVE_TEMPLATE.format(pause_until=user.pause_until)
        if user.pause_until
        else STATUS_PAUSE_INACTIVE
    )
    await message.answer(
        f"{STATUS_HEADER}\n"
        f"{STATUS_DAILY_TEMPLATE.format(daily_time=user.daily_time)}\n"
        f"{STATUS_WEEKLY_TEMPLATE.format(weekly_day=user.weekly_day, weekly_time=user.weekly_time)}\n"
        f"{STATUS_MONTHLY_TEMPLATE.format(monthly_day=user.monthly_day, monthly_time=user.monthly_time)}\n"
        f"{STATUS_PAUSE_TEMPLATE.format(pause=pause)}"
    )


@router.message(Command("daily"))
async def daily_prompt(message: Message, state: FSMContext) -> None:
    question = pick_question(DAILY_QUESTIONS)
    await state.set_state(EntryState.waiting_text)
    await state.update_data(
        entry_type=EntryType.daily.value,
        entry_date=date.today().isoformat(),
        question=question,
        mood=None,
        question_queue=[],
    )
    await message.answer(f"{question}\n{DAILY_PROMPT_SUFFIX}", reply_markup=MOOD_KEYBOARD)


@router.callback_query(F.data.startswith("mood:"))
async def set_mood(callback: CallbackQuery, state: FSMContext) -> None:
    mood = callback.data.split(":", maxsplit=1)[1]
    await state.update_data(mood=mood)
    await callback.answer(MOOD_SAVED_MESSAGE)
