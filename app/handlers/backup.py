from __future__ import annotations

from datetime import UTC, datetime

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message

from app.constants import (
    NEED_START_MESSAGE,
)
from app.handlers.common import _handle_menu_interrupt, _menu_text
from app.i18n import tr
from app.services.backup import (
    build_user_backup_archive,
    import_user_backup_archive,
)
from app.services.entries import (
    list_entries,
)
from app.services.questions import (
    list_daily_questions,
)
from app.services.reminders import next_due_at
from app.services.users import get_user_by_telegram_id
from app.states import EntryState
from app.storage import get_session

router = Router()


@router.message(lambda message: _menu_text(message, "view_backup"))
async def send_backup(message: Message) -> None:
    with get_session() as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        entries = list_entries(session, user, limit=None)
        questions = list_daily_questions(session, user)
        backup_bytes = build_user_backup_archive(user, entries, questions)
        backup_file = BufferedInputFile(
            backup_bytes,
            filename=f"backup_{user.telegram_id}.zip",
        )
    await message.answer_document(
        backup_file,
        caption=tr(user.language, "view_backup"),
    )


@router.message(lambda message: _menu_text(message, "view_import"))
async def import_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(EntryState.waiting_import_archive)
    with get_session() as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
    language = user.language if user else "ru"
    await message.answer(tr(language, "import_prompt"))


@router.message(EntryState.waiting_import_archive)
async def import_archive(message: Message, state: FSMContext) -> None:
    if await _handle_menu_interrupt(message, state):
        return

    with get_session() as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
    language = user.language if user else "ru"

    if not message.document:
        await message.answer(tr(language, "import_no_document"))
        return

    archive_bytes = await message.bot.download(message.document)
    if archive_bytes is None:
        await message.answer(tr(language, "import_invalid_archive"))
        return

    payload = archive_bytes.read()
    with get_session() as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        try:
            import_user_backup_archive(user, payload)
            from app.config import load_config

            config = load_config()
            user.next_due_at = next_due_at(
                session,
                user,
                datetime.now(UTC),
                config.reminder_evening_hour,
            )
        except (KeyError, OSError, ValueError):
            await message.answer(tr(user.language, "import_invalid_archive"))
            return

    await state.clear()
    await message.answer(tr(user.language, "import_done_message"))
