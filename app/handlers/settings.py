from __future__ import annotations

from datetime import date
from datetime import time as dt_time
from datetime import timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.constants import (DAILY_TIME_UPDATED_TEMPLATE, MENU_DAILY,
                           MENU_MONTHLY, MENU_PAUSE, MENU_RESUME, MENU_WEEKLY,
                           MONTHLY_TIME_UPDATED_TEMPLATE,
                           MONTHLY_USAGE_MESSAGE, NEED_START_MESSAGE,
                           PAUSE_DISABLED_MESSAGE, PAUSE_ENABLED_TEMPLATE,
                           SETTINGS_DAILY_PROMPT, SETTINGS_MONTHLY_PROMPT,
                           SETTINGS_WEEKLY_PROMPT, TIME_USAGE_MESSAGE,
                           WEEKLY_TIME_UPDATED_TEMPLATE, WEEKLY_USAGE_MESSAGE)
from app.models import User
from app.states import SettingsState
from app.storage import get_session

router = Router()


def _is_valid_time(value: str) -> bool:
    try:
        dt_time.fromisoformat(value)
    except ValueError:
        return False
    return len(value) == 5


def _parse_daily_time(raw_value: str) -> str | None:
    time_value = raw_value.strip()
    if not _is_valid_time(time_value):
        return None
    return time_value


def _parse_weekly(raw_value: str) -> tuple[int, str] | None:
    args = raw_value.split(maxsplit=1)
    if len(args) != 2:
        return None
    try:
        day = int(args[0])
    except ValueError:
        return None
    if day < 0 or day > 6:
        return None
    time_value = args[1].strip()
    if not _is_valid_time(time_value):
        return None
    return day, time_value


def _parse_monthly(raw_value: str) -> tuple[int, str] | None:
    args = raw_value.split(maxsplit=1)
    if len(args) != 2:
        return None
    try:
        day = int(args[0])
    except ValueError:
        return None
    if day < 1 or day > 31:
        return None
    time_value = args[1].strip()
    if not _is_valid_time(time_value):
        return None
    return day, time_value


def _update_daily_time(message: Message, time_value: str) -> str:
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            return NEED_START_MESSAGE
        user.daily_time = time_value
        user.daily_reminder_date = None
        user.daily_reminder_stage = 0
    return DAILY_TIME_UPDATED_TEMPLATE.format(time_value=time_value)


def _update_weekly_time(message: Message, day: int, time_value: str) -> str:
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            return NEED_START_MESSAGE
        user.weekly_day = day
        user.weekly_time = time_value
    return WEEKLY_TIME_UPDATED_TEMPLATE.format(day=day, time_value=time_value)


def _update_monthly_time(message: Message, day: int, time_value: str) -> str:
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            return NEED_START_MESSAGE
        user.monthly_day = day
        user.monthly_time = time_value
    return MONTHLY_TIME_UPDATED_TEMPLATE.format(day=day, time_value=time_value)


@router.message(Command("time"))
async def set_daily_time(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(TIME_USAGE_MESSAGE)
        return
    time_value = _parse_daily_time(args[1])
    if not time_value:
        await message.answer(TIME_USAGE_MESSAGE)
        return
    await message.answer(_update_daily_time(message, time_value))


@router.message(Command("weekly"))
async def set_weekly_time(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(WEEKLY_USAGE_MESSAGE)
        return
    parsed = _parse_weekly(args[1])
    if not parsed:
        await message.answer(WEEKLY_USAGE_MESSAGE)
        return
    day, time_value = parsed
    await message.answer(_update_weekly_time(message, day, time_value))


@router.message(Command("monthly"))
async def set_monthly_time(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(MONTHLY_USAGE_MESSAGE)
        return
    parsed = _parse_monthly(args[1])
    if not parsed:
        await message.answer(MONTHLY_USAGE_MESSAGE)
        return
    day, time_value = parsed
    await message.answer(_update_monthly_time(message, day, time_value))


@router.message(F.text == MENU_DAILY)
async def menu_set_daily_time(message: Message, state: FSMContext) -> None:
    await state.set_state(SettingsState.waiting_daily_time)
    await message.answer(SETTINGS_DAILY_PROMPT)


@router.message(F.text == MENU_WEEKLY)
async def menu_set_weekly_time(message: Message, state: FSMContext) -> None:
    await state.set_state(SettingsState.waiting_weekly_time)
    await message.answer(SETTINGS_WEEKLY_PROMPT)


@router.message(F.text == MENU_MONTHLY)
async def menu_set_monthly_time(message: Message, state: FSMContext) -> None:
    await state.set_state(SettingsState.waiting_monthly_time)
    await message.answer(SETTINGS_MONTHLY_PROMPT)


@router.message(SettingsState.waiting_daily_time)
async def save_daily_time_from_menu(message: Message, state: FSMContext) -> None:
    time_value = _parse_daily_time(message.text)
    if not time_value:
        await message.answer(TIME_USAGE_MESSAGE)
        return
    await state.clear()
    await message.answer(_update_daily_time(message, time_value))


@router.message(SettingsState.waiting_weekly_time)
async def save_weekly_time_from_menu(message: Message, state: FSMContext) -> None:
    parsed = _parse_weekly(message.text)
    if not parsed:
        await message.answer(WEEKLY_USAGE_MESSAGE)
        return
    await state.clear()
    day, time_value = parsed
    await message.answer(_update_weekly_time(message, day, time_value))


@router.message(SettingsState.waiting_monthly_time)
async def save_monthly_time_from_menu(message: Message, state: FSMContext) -> None:
    parsed = _parse_monthly(message.text)
    if not parsed:
        await message.answer(MONTHLY_USAGE_MESSAGE)
        return
    await state.clear()
    day, time_value = parsed
    await message.answer(_update_monthly_time(message, day, time_value))


@router.message(Command("pause"))
@router.message(F.text == MENU_PAUSE)
async def pause(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    days = int(args[1]) if len(args) > 1 and args[1].isdigit() else 36500
    pause_until = date.today() + timedelta(days=days)
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        user.pause_until = pause_until
    await message.answer(PAUSE_ENABLED_TEMPLATE.format(pause_until=pause_until))


@router.message(Command("resume"))
@router.message(F.text == MENU_RESUME)
async def resume(message: Message) -> None:
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        user.pause_until = None
    await message.answer(PAUSE_DISABLED_MESSAGE)
