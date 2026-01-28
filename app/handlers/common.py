from __future__ import annotations

from datetime import date

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards import MOOD_KEYBOARD
from app.models import EntryType, User
from app.questions import pick_question, DAILY_QUESTIONS
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
    await message.answer(
        "Я дневник-бот. Буду писать первым и просить короткие заметки.\n"
        "Команды: /time, /weekly, /monthly, /pause, /resume, /stats."
    )


@router.message(Command("stats"))
async def stats(message: Message) -> None:
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("Сначала напишите /start.")
            return
        total = count_entries(session, user)
        mood_counts = mood_breakdown(session, user)
    mood_line = " / ".join(
        f"{key}: {value}"
        for key, value in [("🟢", mood_counts.get("good", 0)), ("🟡", mood_counts.get("neutral", 0)), ("🔴", mood_counts.get("bad", 0))]
    )
    await message.answer(
        f"{total} записей всего\n"
        f"Серия: {user.streak} дней подряд\n"
        f"Настроение: {mood_line}"
    )


@router.message(Command("status"))
async def status(message: Message) -> None:
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("Сначала напишите /start.")
            return
    pause = f"пауза до {user.pause_until}" if user.pause_until else "активен"
    await message.answer(
        "Текущие настройки:\n"
        f"День: {user.daily_time}\n"
        f"Неделя: {user.weekly_day} {user.weekly_time}\n"
        f"Месяц: {user.monthly_day} {user.monthly_time}\n"
        f"Статус: {pause}"
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
    )
    await message.answer(f"{question}\nМожно коротко, 1–3 предложения.", reply_markup=MOOD_KEYBOARD)


@router.callback_query(F.data.startswith("mood:"))
async def set_mood(callback: CallbackQuery, state: FSMContext) -> None:
    mood = callback.data.split(":", maxsplit=1)[1]
    await state.update_data(mood=mood)
    await callback.answer("Настроение сохранено.")
