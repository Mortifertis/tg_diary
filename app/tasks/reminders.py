from __future__ import annotations

import asyncio
import logging
import random
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.fsm.storage.base import StorageKey

from app.celery_app import celery_app
from app.config import load_config
from app.db import create_session_factory
from app.fsm import create_redis_storage
from app.keyboards import MOOD_KEYBOARD
from app.models import EntryType, User
from app.prompts import build_prompt
from app.questions import (DAILY_QUESTIONS, MONTHLY_QUESTIONS,
                           WEEKLY_QUESTIONS, pick_questions)
from app.services.greetings import build_reminder_greeting
from app.services.questions import list_active_daily_questions
from app.services.reminders import (due_daily_reminders, due_monthly_reminder,
                                    due_weekly_reminder,
                                    list_due_user_candidates, next_due_at)
from app.states import EntryState

LOGGER = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.reminders.enqueue_due_reminders")
def enqueue_due_reminders() -> int:
    config = load_config()
    session_factory = create_session_factory(config.database_url)
    now_utc = datetime.now(UTC)

    with session_factory() as session:
        users = list_due_user_candidates(session, now_utc)
        user_ids = [user.id for user in users]

    for user_id in user_ids:
        process_user_reminders.delay(user_id)

    LOGGER.info("Enqueued reminder tasks for %s users", len(user_ids))
    return len(user_ids)


@celery_app.task(name="app.tasks.reminders.process_user_reminders")
def process_user_reminders(user_id: int) -> int:
    return asyncio.run(_process_user_reminders_async(user_id))


async def _process_user_reminders_async(user_id: int) -> int:
    config = load_config()
    session_factory = create_session_factory(config.database_url)

    bot = Bot(token=config.bot_token)
    storage = await create_redis_storage(
        redis_url=config.redis_url,
        retries=config.redis_connect_retries,
        retry_delay_seconds=config.redis_retry_delay_seconds,
    )

    reminders_sent = 0
    try:
        with session_factory() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user is None:
                return 0

            now_utc = datetime.now(UTC)
            now = now_utc.astimezone(ZoneInfo(user.timezone))
            reminders = []
            reminders.extend(
                due_daily_reminders(
                    session,
                    user,
                    now,
                    config.reminder_evening_hour,
                )
            )
            reminders.extend(due_weekly_reminder(session, user, now))
            reminders.extend(due_monthly_reminder(session, user, now))

            for reminder in reminders:
                question_queue = []
                if reminder.entry_type == EntryType.daily:
                    daily_questions = list_active_daily_questions(
                        session,
                        user,
                    )
                    count = min(
                        max(int(user.daily_questions_count or 3), 1),
                        10,
                    )
                    selected_questions = pick_questions(
                        daily_questions or DAILY_QUESTIONS,
                        count,
                    )
                    question = selected_questions[0]
                    question_queue = selected_questions[1:]
                elif reminder.entry_type == EntryType.weekly:
                    questions = pick_questions(
                        WEEKLY_QUESTIONS,
                        random.randint(4, 6),
                    )
                    question = questions[0]
                    question_queue = questions[1:]
                else:
                    questions = pick_questions(
                        MONTHLY_QUESTIONS,
                        random.randint(6, 8),
                    )
                    question = questions[0]
                    question_queue = questions[1:]

                greeting_message = build_reminder_greeting(
                    user,
                    reminder.due_at,
                )
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=greeting_message,
                )
                prompt = build_prompt(reminder.entry_type, question)
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=prompt,
                    reply_markup=(
                        MOOD_KEYBOARD
                        if reminder.entry_type == EntryType.daily
                        else None
                    ),
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
                        "collect_daily_answers": (
                            reminder.entry_type == EntryType.daily
                        ),
                        "answers": [],
                    },
                )
                reminders_sent += 1

            user.next_due_at = next_due_at(
                session,
                user,
                now_utc,
                config.reminder_evening_hour,
            )
            session.commit()
    finally:
        await storage.close()
        await bot.session.close()

    return reminders_sent
