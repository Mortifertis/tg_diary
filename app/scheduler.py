from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.fsm.storage.base import StorageKey
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import load_config
from app.constants import DAILY_PROMPT_SUFFIX, MONTHLY_PROMPT_PREFIX, WEEKLY_PROMPT_PREFIX
from app.keyboards import MOOD_KEYBOARD
from app.models import EntryType, User
from app.questions import (DAILY_QUESTIONS, MONTHLY_QUESTIONS,
                           WEEKLY_QUESTIONS, pick_question)
from app.services.reminders import (due_daily_reminders, due_monthly_reminder,
                                    due_weekly_reminder)
from app.states import EntryState
from app.storage import get_session


def create_scheduler(bot: Bot, storage) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=ZoneInfo("UTC"))

    async def reminder_job() -> None:
        config = load_config()
        with get_session(bot) as session:
            users = session.query(User).all()
            for user in users:
                now = datetime.now(tz=ZoneInfo(user.timezone))
                reminders = []
                reminders.extend(due_daily_reminders(session, user, now, config.reminder_evening_hour))
                reminders.extend(due_weekly_reminder(session, user, now))
                reminders.extend(due_monthly_reminder(session, user, now))

                for reminder in reminders:
                    question_pool = {
                        EntryType.daily: DAILY_QUESTIONS,
                        EntryType.weekly: WEEKLY_QUESTIONS,
                        EntryType.monthly: MONTHLY_QUESTIONS,
                    }[reminder.entry_type]
                    question = pick_question(question_pool)
                    message = _build_prompt(reminder.entry_type, question)
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=message,
                        reply_markup=MOOD_KEYBOARD if reminder.entry_type == EntryType.daily else None,
                    )
                    key = StorageKey(bot_id=bot.id, chat_id=user.telegram_id, user_id=user.telegram_id)
                    await storage.set_state(key, EntryState.waiting_text)
                    await storage.update_data(
                        key,
                        {
                            "entry_type": reminder.entry_type.value,
                            "entry_date": now.date().isoformat(),
                            "question": question,
                            "mood": None,
                        },
                    )

    scheduler.add_job(reminder_job, "interval", minutes=1)
    return scheduler


def _build_prompt(entry_type: EntryType, question: str) -> str:
    if entry_type == EntryType.daily:
        return f"{question}\n{DAILY_PROMPT_SUFFIX}"
    if entry_type == EntryType.weekly:
        return f"{WEEKLY_PROMPT_PREFIX} {question}"
    return f"{MONTHLY_PROMPT_PREFIX} {question}"
