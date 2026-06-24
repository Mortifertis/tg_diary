from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.constants import (
    DAILY_PROMPT_SUFFIX,
    MANUAL_ENTRY_PROMPT,
    MOOD_CALLBACK_PREFIX,
    MOOD_SAVED_MESSAGE,
    NEED_START_MESSAGE,
)
from app.handlers.common import _menu_text
from app.i18n import tr
from app.keyboards import (
    MOOD_KEYBOARD,
)
from app.models import EntryType
from app.questions import DAILY_QUESTIONS, pick_question
from app.services.questions import (
    list_active_daily_questions,
)
from app.services.timezones import (
    local_date_for_user,
)
from app.services.users import get_user_by_telegram_id
from app.states import EntryState
from app.storage import get_session

router = Router()


@router.message(Command("daily"))
async def daily_prompt(message: Message, state: FSMContext) -> None:
    with get_session() as session:
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
    with get_session() as session:
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


@router.callback_query(F.data.startswith(MOOD_CALLBACK_PREFIX))
async def set_mood(callback: CallbackQuery, state: FSMContext) -> None:
    mood = callback.data.split(":", maxsplit=1)[1]
    await state.update_data(mood=mood)
    await callback.answer(MOOD_SAVED_MESSAGE)
