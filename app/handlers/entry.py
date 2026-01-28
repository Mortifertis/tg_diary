from __future__ import annotations

from datetime import date

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.constants import ENTRY_SAVED_MESSAGE, NEED_START_MESSAGE
from app.models import EntryType, User
from app.services.entries import create_entry
from app.states import EntryState
from app.storage import get_session

router = Router()


@router.message(EntryState.waiting_text)
async def save_entry(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    entry_type = EntryType(data["entry_type"])
    entry_date = date.fromisoformat(data["entry_date"])
    question = data.get("question")
    mood = data.get("mood")

    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        create_entry(
            session=session,
            user=user,
            entry_type=entry_type,
            entry_date=entry_date,
            text=message.text,
            mood=mood,
            question=question,
        )
    await state.clear()
    await message.answer(ENTRY_SAVED_MESSAGE)
