from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.constants import (
    NEED_START_MESSAGE,
    VIEW_SHOW_MORE_PREFIX,
)
from app.handlers.common import (
    _entries_page_size,
    _format_recent_entries,
    _menu_text,
)
from app.i18n import tr
from app.keyboards import (
    main_menu_keyboard,
    view_entries_actions_keyboard,
    view_entries_page_keyboard,
)
from app.services.entries import (
    list_entries,
)
from app.services.users import get_user_by_telegram_id
from app.states import EntryState
from app.storage import get_session

router = Router()


@router.message(lambda message: _menu_text(message, "menu_view"))
async def view_entries(message: Message) -> None:
    with get_session() as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        entries = list_entries(session, user, limit=None)

    if not entries:
        await message.answer(
            tr(user.language, "recent_entries_empty"),
            reply_markup=main_menu_keyboard(
                user.language,
                bool(user.enable_menu_icons),
            ),
        )
        return

    page_size = _entries_page_size(user)
    first_page = entries[:page_size]
    await message.answer(_format_recent_entries(first_page, user))

    if len(entries) > page_size:
        await message.answer(
            tr(user.language, "view_prompt"),
            reply_markup=view_entries_page_keyboard(
                user.language,
                page_size,
                page_size,
            ),
        )

    await message.answer(
        tr(user.language, "view_prompt"),
        reply_markup=view_entries_actions_keyboard(
            user.language,
            bool(user.enable_menu_icons),
        ),
    )


@router.callback_query(F.data.startswith(VIEW_SHOW_MORE_PREFIX))
async def show_more_view_entries(callback: CallbackQuery) -> None:
    if not callback.data:
        await callback.answer()
        return

    offset_text = callback.data.replace(VIEW_SHOW_MORE_PREFIX, "", 1)
    if not offset_text.isdigit():
        await callback.answer()
        return
    offset = int(offset_text)

    with get_session() as session:
        user = get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            if callback.message:
                await callback.message.answer(NEED_START_MESSAGE)
            await callback.answer()
            return
        entries = list_entries(session, user, limit=None)

    page_size = _entries_page_size(user)
    page = entries[offset : offset + page_size]
    if not page:
        await callback.answer()
        return

    if callback.message:
        await callback.message.answer(_format_recent_entries(page, user))
        next_offset = offset + page_size
        if next_offset < len(entries):
            await callback.message.answer(
                tr(user.language, "view_prompt"),
                reply_markup=view_entries_page_keyboard(
                    user.language,
                    next_offset,
                    page_size,
                ),
            )
    await callback.answer()


@router.message(lambda message: _menu_text(message, "view_find_by_id"))
async def prompt_find_entry_by_id(
    message: Message,
    state: FSMContext,
) -> None:
    with get_session() as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
    language = user.language if user else "ru"
    await state.set_state(EntryState.waiting_entry_index)
    await message.answer(tr(language, "entry_index_prompt"))
