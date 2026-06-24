from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from sqlalchemy.orm import Session

from app.keyboards import MOOD_KEYBOARD
from app.models import EntryType, User
from app.observability import EXTERNAL_API_ERRORS_TOTAL, emit_alert
from app.prompts import build_prompt
from app.questions import (
    DAILY_QUESTIONS,
    MONTHLY_QUESTIONS,
    WEEKLY_QUESTIONS,
    pick_questions,
)
from app.services.greetings import build_reminder_greeting
from app.services.questions import list_active_daily_questions
from app.services.reminders import Reminder
from app.states import EntryState


@dataclass(slots=True)
class ReminderPromptPayload:
    greeting: str
    prompt: str
    question: str
    question_queue: list[str]


def build_reminder_prompt_payload(
    session: Session,
    user: User,
    reminder: Reminder,
) -> ReminderPromptPayload:
    question_queue: list[str] = []
    if reminder.entry_type == EntryType.daily:
        daily_questions = list_active_daily_questions(session, user)
        count = min(max(int(user.daily_questions_count or 3), 1), 10)
        questions = pick_questions(daily_questions or DAILY_QUESTIONS, count)
    elif reminder.entry_type == EntryType.weekly:
        questions = pick_questions(WEEKLY_QUESTIONS, random.randint(4, 6))
    else:
        questions = pick_questions(MONTHLY_QUESTIONS, random.randint(6, 8))

    question = questions[0]
    question_queue = questions[1:]
    return ReminderPromptPayload(
        greeting=build_reminder_greeting(user, reminder.due_at),
        prompt=build_prompt(reminder.entry_type, question),
        question=question,
        question_queue=question_queue,
    )


async def send_reminder_messages(
    bot: Bot,
    user: User,
    reminder: Reminder,
    payload: ReminderPromptPayload,
) -> None:
    try:
        await bot.send_message(chat_id=user.telegram_id, text=payload.greeting)
        await bot.send_message(
            chat_id=user.telegram_id,
            text=payload.prompt,
            reply_markup=(
                MOOD_KEYBOARD
                if reminder.entry_type == EntryType.daily
                else None
            ),
        )
    except TelegramAPIError:
        EXTERNAL_API_ERRORS_TOTAL.labels(
            api="telegram",
            operation="send_message",
            error="telegram_api_error",
        ).inc()
        emit_alert(
            category="external_api",
            message=f"Failed to send reminder for user_id={user.id}",
            severity="warning",
            api="telegram",
            operation="send_message",
        )
        raise


async def set_entry_fsm_state(
    bot: Bot,
    storage: BaseStorage,
    user: User,
    reminder: Reminder,
    payload: ReminderPromptPayload,
    now: datetime,
) -> None:
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
            "question": payload.question,
            "mood": None,
            "question_queue": payload.question_queue,
            "collect_daily_answers": reminder.entry_type == EntryType.daily,
            "answers": [],
        },
    )
