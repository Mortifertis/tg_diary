from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message

from app.constants import (
    EXPORT_DONE_TEMPLATE,
    EXPORT_MENU_PROMPT,
    EXPORT_NO_ENTRIES,
    NEED_START_MESSAGE,
)
from app.handlers.common import _menu_text
from app.i18n import tr
from app.keyboards import (
    export_entries_keyboard,
    view_entries_actions_keyboard,
)
from app.services.entries import (
    format_entries_export,
    list_entries,
    resolve_export_start_date,
)
from app.services.timezones import (
    local_date_for_user,
    local_day_start_to_utc_naive,
)
from app.services.users import get_user_by_telegram_id
from app.states import EntryState
from app.storage import get_session

router = Router()


async def _show_export_menu(message: Message) -> None:
    with get_session() as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
    language = user.language if user else "ru"
    use_icons = bool(user.enable_menu_icons) if user else True
    await message.answer(
        EXPORT_MENU_PROMPT,
        reply_markup=export_entries_keyboard(language, use_icons),
    )


def _resolve_export_period(message: Message) -> str | None:
    mapping = {
        "export_week": "week",
        "export_month": "month",
        "export_3months": "3months",
        "export_year": "year",
        "export_all": "all",
    }
    for key, value in mapping.items():
        if _menu_text(message, key):
            return value
    return None


def _resolve_period_label(period: str, language: str) -> str | None:
    period_labels = {
        "week": tr(language, "export_week"),
        "month": tr(language, "export_month"),
        "3months": tr(language, "export_3months"),
        "year": tr(language, "export_year"),
        "all": tr(language, "export_all"),
    }
    return period_labels.get(period)


@router.message(lambda message: _menu_text(message, "view_export"))
async def export_menu_with_state(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(EntryState.waiting_export_period)
    await _show_export_menu(message)


@router.message(EntryState.waiting_export_period)
async def export_entries_from_menu(
    message: Message,
    state: FSMContext,
) -> None:
    if _menu_text(message, "menu_back"):
        await state.clear()
        with get_session() as session:
            user = get_user_by_telegram_id(session, message.from_user.id)
        language = user.language if user else "ru"
        use_icons = bool(user.enable_menu_icons) if user else True
        await message.answer(
            tr(language, "view_prompt"),
            reply_markup=view_entries_actions_keyboard(language, use_icons),
        )
        return

    period = _resolve_export_period(message)
    if not period:
        await _show_export_menu(message)
        return

    await state.clear()
    with get_session() as session:
        user = get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        local_today = local_date_for_user(user)
        created_from_date = resolve_export_start_date(period, local_today)
        created_from = None
        if created_from_date is not None:
            created_from = local_day_start_to_utc_naive(
                user,
                created_from_date,
            )
        entries = list_entries(
            session,
            user,
            limit=None,
            created_from=created_from,
        )

    period_label = _resolve_period_label(period, user.language)
    if period_label is None:
        return

    if not entries:
        await message.answer(EXPORT_NO_ENTRIES)
        return

    export_text = format_entries_export(entries)
    export_file = BufferedInputFile(
        export_text.encode("utf-8"),
        filename=f"entries_{period}.txt",
    )
    await message.answer_document(
        export_file,
        caption=EXPORT_DONE_TEMPLATE.format(period_label=period_label),
    )
