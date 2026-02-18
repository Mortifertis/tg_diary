from __future__ import annotations

import random
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.fsm.storage.base import StorageKey
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import load_config
from app.keyboards import MOOD_KEYBOARD
from app.models import EntryType, User
from app.prompts import build_prompt
from app.questions import (DAILY_QUESTIONS, MONTHLY_QUESTIONS,
                           WEEKLY_QUESTIONS, pick_question, pick_questions)
from app.services.questions import list_active_daily_questions
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
                reminders.extend(
                    due_daily_reminders(
                        session, user, now, config.reminder_evening_hour
                    )
                )
                reminders.extend(due_weekly_reminder(session, user, now))
                reminders.extend(due_monthly_reminder(session, user, now))

                for reminder in reminders:
                    question_queue = []
                    if reminder.entry_type == EntryType.daily:
                        daily_questions = list_active_daily_questions(
                            session, user
                        )
                        question = pick_question(
                            daily_questions or DAILY_QUESTIONS
                        )
                    elif reminder.entry_type == EntryType.weekly:
                        questions = pick_questions(
                            WEEKLY_QUESTIONS, random.randint(4, 6)
                        )
                        question = questions[0]
                        question_queue = questions[1:]
                    else:
                        questions = pick_questions(
                            MONTHLY_QUESTIONS, random.randint(6, 8)
                        )
                        question = questions[0]
                        question_queue = questions[1:]
                    message = build_prompt(reminder.entry_type, question)
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=message,
                        reply_markup=MOOD_KEYBOARD
                        if reminder.entry_type == EntryType.daily
                        else None,
                    )
                    key = StorageKey(
                        bot_id=bot.id,
                        chat_id=user.telegram_id,
                        user_id=user.telegram_id,
                    )
                    await storage.set_state(key, EntryState.waiting_text)
                    await storage.update_data(
                        key,
                        {
                            "entry_type": reminder.entry_type.value,
                            "entry_date": now.date().isoformat(),
                            "question": question,
                            "mood": None,
                            "question_queue": question_queue,
                        },
                    )

    scheduler.add_job(reminder_job, "interval", minutes=1)
    return scheduler
