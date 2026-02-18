from __future__ import annotations

from datetime import date

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.constants import (ENTRY_EMPTY_CONTENT_MESSAGE, ENTRY_MEDIA_MAX_IMAGES,
                           ENTRY_SAVED_MESSAGE, ENTRY_TOO_MANY_IMAGES_TEMPLATE,
                           ENTRY_UNSUPPORTED_EXTENSION_TEMPLATE,
                           NEED_START_MESSAGE)
from app.models import EntryType, User
from app.prompts import build_prompt
from app.services.attachments import (AttachmentValidationError,
                                      has_entry_content, parse_attachments)
from app.services.entries import create_entry
from app.services.timezones import message_datetime_to_utc_naive
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
    question_queue = data.get("question_queue") or []

    try:
        attachments = parse_attachments(message)
    except AttachmentValidationError as error:
        extension = str(error)
        if extension == "too_many_images":
            await message.answer(
                ENTRY_TOO_MANY_IMAGES_TEMPLATE.format(max_images=ENTRY_MEDIA_MAX_IMAGES)
            )
            return
        await message.answer(
            ENTRY_UNSUPPORTED_EXTENSION_TEMPLATE.format(extension=extension)
        )
        return

    if not has_entry_content(message, attachments):
        await message.answer(ENTRY_EMPTY_CONTENT_MESSAGE)
        return

    with get_session(message.bot) as session:
        user = (
            session.query(User)
            .filter_by(telegram_id=message.from_user.id)
            .first()
        )
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        create_entry(
            session=session,
            user=user,
            entry_type=entry_type,
            entry_date=entry_date,
            text=(message.text or message.caption or "").strip(),
            mood=mood,
            question=question,
            attachments=attachments,
            created_at=message_datetime_to_utc_naive(message.date),
        )
    await message.answer(ENTRY_SAVED_MESSAGE)

    if question_queue:
        next_question = question_queue.pop(0)
        await state.update_data(
            question=next_question, question_queue=question_queue
        )
        await message.answer(build_prompt(entry_type, next_question))
        return

    await state.clear()
