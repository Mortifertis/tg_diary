from __future__ import annotations

from typing import cast

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ForceReply, Message

from app.constants import (
    MANAGE_DELETE_PREFIX,
    MANAGE_EDIT_PREFIX,
    MANAGE_ENTRIES_DELETED,
    MANAGE_ENTRIES_PREVIEW_LIMIT,
    MANAGE_ENTRIES_TEXT_EDIT_PROMPT,
    MANAGE_ENTRIES_TEXT_EMPTY,
    MANAGE_ENTRIES_UPDATED,
    MANAGE_SHOW_MORE_PREFIX,
    NEED_START_MESSAGE,
)
from app.handlers.common import (
    _build_edit_input_placeholder,
    _format_manage_entries_preview,
    _handle_menu_interrupt,
    _menu_text,
    _send_entry_details,
)
from app.i18n import tr
from app.keyboards import (
    manage_entries_actions_keyboard,
    manage_entries_page_keyboard,
)
from app.services.entries import (
    count_entries,
    delete_entry_by_index,
    get_entry_by_index,
    list_entries,
    update_entry_text,
)
from app.services.users import get_user_by_telegram_id
from app.states import EntryState
from app.storage import get_session

router = Router()


@router.message(lambda message: _menu_text(message, "menu_manage"))
async def manage_entries(message: Message, state: FSMContext) -> None:
    with get_session() as session:
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
                bool(user.enable_menu_icons),
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

    with get_session() as session:
        user = get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            if callback.message:
                await callback.message.answer(NEED_START_MESSAGE)
            await callback.answer()
            return
        entries = list_entries(session, user, limit=None)

    chunk = entries[offset : offset + MANAGE_ENTRIES_PREVIEW_LIMIT]
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
                    bool(user.enable_menu_icons),
                ),
            )
        else:
            await callback.message.answer(
                tr(user.language, "manage_entries_prompt")
            )
    await callback.answer()


@router.message(EntryState.waiting_entry_index)
async def show_entry_by_index(message: Message, state: FSMContext) -> None:
    if await _handle_menu_interrupt(message, state):
        return

    with get_session() as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
    entry_index = (message.text or "").strip().lower()
    if not entry_index:
        await message.answer(tr(user.language, "entry_index_invalid"))
        return

    with get_session() as session:
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

    with get_session() as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
    entry_index = (message.text or "").strip().lower()
    if not entry_index:
        await message.answer(tr(user.language, "entry_index_invalid"))
        return

    with get_session() as session:
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
            bool(user.enable_menu_icons),
        ),
    )


@router.callback_query(F.data.startswith(MANAGE_EDIT_PREFIX))
async def start_edit_entry(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data:
        await callback.answer()
        return
    entry_index = callback.data.replace(MANAGE_EDIT_PREFIX, "", 1)

    with get_session() as session:
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

    with get_session() as session:
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
        with get_session() as session:
            user = get_user_by_telegram_id(session, message.from_user.id)
        language = user.language if user else "ru"
        await message.answer(tr(language, "entry_index_invalid"))
        await state.set_state(EntryState.waiting_manage_entry_index)
        return

    with get_session() as session:
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
            bool(user.enable_menu_icons),
        ),
    )
    await state.set_state(EntryState.waiting_manage_entry_index)
