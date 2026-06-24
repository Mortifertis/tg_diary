from __future__ import annotations

import logging
import time
from datetime import date

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import load_config
from app.constants import (
    ENTRY_EMPTY_CONTENT_MESSAGE,
    ENTRY_MEDIA_MAX_IMAGES,
    ENTRY_SAVED_MESSAGE,
    ENTRY_TOO_MANY_IMAGES_TEMPLATE,
    ENTRY_UNSUPPORTED_EXTENSION_TEMPLATE,
    NEED_START_MESSAGE,
)
from app.i18n import tr
from app.models import EntryType
from app.observability import (
    EXTERNAL_API_ERRORS_TOTAL,
    emit_alert,
    observe_duration,
)
from app.prompts import build_prompt
from app.services.attachments import (
    AttachmentValidationError,
    has_entry_content,
    parse_attachments,
)
from app.services.entries import create_entry
from app.services.speech import (
    SpeechRecognitionError,
    local_speech_available,
    transcribe_voice,
)
from app.services.timezones import message_datetime_to_utc_naive
from app.services.users import get_user_by_telegram_id
from app.states import EntryState
from app.storage import get_session

router = Router()
LOGGER = logging.getLogger(__name__)


async def _save_entry_message(
    message: Message,
    state: FSMContext,
    forced_text: str | None = None,
) -> None:
    started_at = time.monotonic()
    try:
        data = await state.get_data()
        entry_type = EntryType(data["entry_type"])
        entry_date = date.fromisoformat(data["entry_date"])
        question = data.get("question")
        mood = data.get("mood")
        question_queue = data.get("question_queue") or []
        collect_daily_answers = bool(data.get("collect_daily_answers"))
        answers = data.get("answers") or []

        try:
            attachments = parse_attachments(message)
        except AttachmentValidationError as error:
            extension = str(error)
            if extension == "too_many_images":
                await message.answer(
                    ENTRY_TOO_MANY_IMAGES_TEMPLATE.format(
                        max_images=ENTRY_MEDIA_MAX_IMAGES,
                    )
                )
                return
            await message.answer(
                ENTRY_UNSUPPORTED_EXTENSION_TEMPLATE.format(
                    extension=extension,
                )
            )
            return

        if not has_entry_content(message, attachments):
            await message.answer(ENTRY_EMPTY_CONTENT_MESSAGE)
            return

        text_value = (
            forced_text or (message.text or message.caption or "").strip()
        )

        if collect_daily_answers and entry_type == EntryType.daily:
            answers.append(f"{question}\n{text_value}")
            if question_queue:
                next_question = question_queue.pop(0)
                await state.update_data(
                    question=next_question,
                    question_queue=question_queue,
                    answers=answers,
                )
                await message.answer(build_prompt(entry_type, next_question))
                return
            text_value = "\n\n".join(answers)
            question = None

        with get_session() as session:
            user = get_user_by_telegram_id(session, message.from_user.id)
            if not user:
                await message.answer(NEED_START_MESSAGE)
                return
            create_entry(
                session=session,
                user=user,
                entry_type=entry_type,
                entry_date=entry_date,
                text=text_value,
                mood=mood,
                question=question,
                attachments=attachments,
                created_at=message_datetime_to_utc_naive(message.date),
            )
        await message.answer(ENTRY_SAVED_MESSAGE)

        if question_queue and not collect_daily_answers:
            next_question = question_queue.pop(0)
            await state.update_data(
                question=next_question,
                question_queue=question_queue,
            )
            await message.answer(build_prompt(entry_type, next_question))
            return

        await state.clear()
    finally:
        observe_duration("handler", "_save_entry_message", started_at)


async def _transcribe_voice_if_needed(
    message: Message,
    state: FSMContext,
    ask_confirmation: bool,
) -> bool:
    started_at = time.monotonic()
    if not message.voice:
        return False

    with get_session() as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
    language = user.language if user else "ru"
    use_icons = bool(user.enable_menu_icons) if user else True

    if ask_confirmation:
        from app.keyboards import voice_confirmation_keyboard

        await state.set_state(
            EntryState.waiting_voice_recognition_confirmation
        )
        await state.update_data(pending_voice_message=message)
        await message.answer(
            tr(language, "voice_convert_confirmation"),
            reply_markup=voice_confirmation_keyboard(language, use_icons),
        )
        return True

    if not local_speech_available():
        await message.answer(tr(language, "voice_convert_engine_missing"))
        return False

    config = load_config()
    model_name = config.whisper_model
    device = config.whisper_device
    await message.answer(tr(language, "voice_convert_in_progress"))
    try:
        text = await transcribe_voice(
            message.bot,
            message.voice,
            model_name,
            device,
        )
    except SpeechRecognitionError as error:
        EXTERNAL_API_ERRORS_TOTAL.labels(
            api="speech",
            operation="transcribe_voice",
            error=str(error),
        ).inc()
        emit_alert(
            category="external_api",
            message="Speech transcription failed",
            severity="warning",
            api="speech",
            operation="transcribe_voice",
            error=str(error),
        )
        LOGGER.warning(
            "Speech transcription failed for user_id=%s",
            message.from_user.id if message.from_user else "unknown",
            exc_info=True,
        )
        await message.answer(tr(language, "voice_convert_failed"))
        return False
    finally:
        observe_duration("handler", "_transcribe_voice_if_needed", started_at)

    await message.answer(
        tr(language, "voice_convert_done", text=text),
    )
    await _save_entry_message(message, state, forced_text=text)
    return True


@router.message(EntryState.waiting_text)
async def save_entry(message: Message, state: FSMContext) -> None:
    started_at = time.monotonic()
    try:
        with get_session() as session:
            user = get_user_by_telegram_id(session, message.from_user.id)
        mode = user.voice_recognition_mode if user else "auto"

        if mode == "confirm":
            if await _transcribe_voice_if_needed(
                message,
                state,
                ask_confirmation=True,
            ):
                return
        if mode == "auto":
            if await _transcribe_voice_if_needed(
                message,
                state,
                ask_confirmation=False,
            ):
                return

        await _save_entry_message(message, state)
    finally:
        observe_duration("handler", "save_entry", started_at)


@router.message(EntryState.waiting_voice_recognition_confirmation)
async def save_entry_voice_confirmation(
    message: Message,
    state: FSMContext,
) -> None:
    started_at = time.monotonic()
    try:
        with get_session() as session:
            user = get_user_by_telegram_id(session, message.from_user.id)
        language = user.language if user else "ru"

        if (message.text or "").strip() == tr(language, "toggle_yes"):
            data = await state.get_data()
            original = data.get("pending_voice_message")
            if not isinstance(original, Message):
                await state.set_state(EntryState.waiting_text)
                await message.answer(tr(language, "voice_convert_failed"))
                return
            await state.set_state(EntryState.waiting_text)
            await _transcribe_voice_if_needed(
                original,
                state,
                ask_confirmation=False,
            )
            return

        data = await state.get_data()
        original = data.get("pending_voice_message")
        await state.set_state(EntryState.waiting_text)
        if isinstance(original, Message):
            await _save_entry_message(original, state)
            return
        await _save_entry_message(message, state)
    finally:
        observe_duration(
            "handler",
            "save_entry_voice_confirmation",
            started_at,
        )
