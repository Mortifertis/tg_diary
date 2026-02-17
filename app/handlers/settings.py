from __future__ import annotations

from datetime import date
from datetime import time as dt_time
from datetime import timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.constants import (DAILY_TIME_UPDATED_TEMPLATE,
                           MONTHLY_TIME_UPDATED_TEMPLATE,
                           MONTHLY_USAGE_MESSAGE, NEED_START_MESSAGE,
                           PAUSE_DISABLED_MESSAGE, PAUSE_ENABLED_TEMPLATE,
                           TIME_USAGE_MESSAGE, WEEKLY_TIME_UPDATED_TEMPLATE,
                           WEEKLY_USAGE_MESSAGE)
from app.models import User
from app.storage import get_session

router = Router()


def _is_valid_time(value: str) -> bool:
    try:
        dt_time.fromisoformat(value)
    except ValueError:
        return False
    return len(value) == 5


@router.message(Command("time"))
async def set_daily_time(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(TIME_USAGE_MESSAGE)
        return
    time_value = args[1].strip()
    if not _is_valid_time(time_value):
        await message.answer(TIME_USAGE_MESSAGE)
        return
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        user.daily_time = time_value
        user.daily_reminder_date = None
        user.daily_reminder_stage = 0
    await message.answer(DAILY_TIME_UPDATED_TEMPLATE.format(time_value=time_value))


@router.message(Command("weekly"))
async def set_weekly_time(message: Message) -> None:
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer(WEEKLY_USAGE_MESSAGE)
        return
    try:
        day = int(args[1])
    except ValueError:
        await message.answer(WEEKLY_USAGE_MESSAGE)
        return
    if day < 0 or day > 6:
        await message.answer(WEEKLY_USAGE_MESSAGE)
        return
    time_value = args[2].strip()
    if not _is_valid_time(time_value):
        await message.answer(WEEKLY_USAGE_MESSAGE)
        return
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        user.weekly_day = day
        user.weekly_time = time_value
    await message.answer(WEEKLY_TIME_UPDATED_TEMPLATE.format(day=day, time_value=time_value))


@router.message(Command("monthly"))
async def set_monthly_time(message: Message) -> None:
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer(MONTHLY_USAGE_MESSAGE)
        return
    try:
        day = int(args[1])
    except ValueError:
        await message.answer(MONTHLY_USAGE_MESSAGE)
        return
    if day < 1 or day > 31:
        await message.answer(MONTHLY_USAGE_MESSAGE)
        return
    time_value = args[2].strip()
    if not _is_valid_time(time_value):
        await message.answer(MONTHLY_USAGE_MESSAGE)
        return
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        user.monthly_day = day
        user.monthly_time = time_value
    await message.answer(MONTHLY_TIME_UPDATED_TEMPLATE.format(day=day, time_value=time_value))


@router.message(Command("pause"))
async def pause(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    days = int(args[1]) if len(args) > 1 else 1
    pause_until = date.today() + timedelta(days=days)
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        user.pause_until = pause_until
    await message.answer(PAUSE_ENABLED_TEMPLATE.format(pause_until=pause_until))


@router.message(Command("resume"))
async def resume(message: Message) -> None:
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer(NEED_START_MESSAGE)
            return
        user.pause_until = None
    await message.answer(PAUSE_DISABLED_MESSAGE)
