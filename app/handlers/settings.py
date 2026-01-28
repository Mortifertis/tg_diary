from __future__ import annotations

from datetime import date, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.models import User
from app.storage import get_session

router = Router()


@router.message(Command("time"))
async def set_daily_time(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Укажи время: /time HH:MM")
        return
    time_value = args[1].strip()
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("Сначала напишите /start.")
            return
        user.daily_time = time_value
    await message.answer(f"Ежедневное время обновлено: {time_value}")


@router.message(Command("weekly"))
async def set_weekly_time(message: Message) -> None:
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Укажи день недели и время: /weekly 6 20:00 (0=пн, 6=вс)")
        return
    day = int(args[1])
    time_value = args[2]
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("Сначала напишите /start.")
            return
        user.weekly_day = day
        user.weekly_time = time_value
    await message.answer(f"Еженедельное время обновлено: {day} {time_value}")


@router.message(Command("monthly"))
async def set_monthly_time(message: Message) -> None:
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Укажи день месяца и время: /monthly 1 20:00")
        return
    day = int(args[1])
    time_value = args[2]
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("Сначала напишите /start.")
            return
        user.monthly_day = day
        user.monthly_time = time_value
    await message.answer(f"Ежемесячное время обновлено: {day} {time_value}")


@router.message(Command("pause"))
async def pause(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    days = int(args[1]) if len(args) > 1 else 1
    pause_until = date.today() + timedelta(days=days)
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("Сначала напишите /start.")
            return
        user.pause_until = pause_until
    await message.answer(f"Пауза включена до {pause_until}.")


@router.message(Command("resume"))
async def resume(message: Message) -> None:
    with get_session(message.bot) as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("Сначала напишите /start.")
            return
        user.pause_until = None
    await message.answer("Пауза снята.")
