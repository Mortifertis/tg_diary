from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from celery import Task

from app.celery_app import celery_app
from app.config import load_config
from app.db import create_session_factory
from app.fsm import create_redis_storage
from app.models import User
from app.observability import (
    CELERY_RETRIES_TOTAL,
    REMINDER_TASKS_TOTAL,
    emit_alert,
    observe_duration,
)
from app.services.reminder_delivery import (
    build_reminder_prompt_payload,
    send_reminder_messages,
    set_entry_fsm_state,
)
from app.services.reminders import (
    due_daily_reminders,
    due_monthly_reminder,
    due_weekly_reminder,
    list_due_user_candidates,
    next_due_at,
)

LOGGER = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.reminders.enqueue_due_reminders",
    max_retries=3,
    default_retry_delay=10,
)
def enqueue_due_reminders(self: Task) -> int:
    started_at = time.monotonic()
    config = load_config()
    session_factory = create_session_factory(config.database_url)
    task_name = "enqueue_due_reminders"

    try:
        now_utc = datetime.now(UTC)
        with session_factory() as session:
            users = list_due_user_candidates(session, now_utc)
            user_ids = [user.id for user in users]

        for user_id in user_ids:
            process_user_reminders.delay(user_id)

        REMINDER_TASKS_TOTAL.labels(task=task_name, status="success").inc()
        LOGGER.info("Enqueued reminder tasks for %s users", len(user_ids))
        return len(user_ids)
    except Exception as error:
        REMINDER_TASKS_TOTAL.labels(task=task_name, status="error").inc()
        retries = int(self.request.retries)
        if retries >= int(self.max_retries):
            emit_alert(
                category="celery",
                severity="critical",
                message="enqueue_due_reminders reached retry limit",
                task=task_name,
            )
            raise
        CELERY_RETRIES_TOTAL.labels(
            task=task_name,
            reason="runtime_error",
        ).inc()
        LOGGER.warning(
            "Retrying %s after error: %s",
            task_name,
            error,
            exc_info=True,
        )
        raise self.retry(exc=error)
    finally:
        observe_duration("celery", task_name, started_at)


@celery_app.task(
    bind=True,
    name="app.tasks.reminders.process_user_reminders",
    max_retries=5,
    default_retry_delay=20,
)
def process_user_reminders(self: Task, user_id: int) -> int:
    task_name = "process_user_reminders"
    started_at = time.monotonic()
    try:
        result = asyncio.run(_process_user_reminders_async(user_id))
        REMINDER_TASKS_TOTAL.labels(task=task_name, status="success").inc()
        return result
    except Exception as error:
        REMINDER_TASKS_TOTAL.labels(task=task_name, status="error").inc()
        retries = int(self.request.retries)
        if retries >= int(self.max_retries):
            emit_alert(
                category="celery",
                severity="critical",
                message=(
                    "process_user_reminders reached retry limit "
                    f"for user_id={user_id}"
                ),
                task=task_name,
                user_id=str(user_id),
            )
            raise
        CELERY_RETRIES_TOTAL.labels(
            task=task_name,
            reason="runtime_error",
        ).inc()
        LOGGER.warning(
            "Retrying %s for user_id=%s after error: %s",
            task_name,
            user_id,
            error,
            exc_info=True,
        )
        raise self.retry(exc=error)
    finally:
        observe_duration("celery", task_name, started_at)


async def _process_user_reminders_async(user_id: int) -> int:
    started_at = time.monotonic()
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
                payload = build_reminder_prompt_payload(
                    session,
                    user,
                    reminder,
                )
                await send_reminder_messages(
                    bot,
                    user,
                    reminder,
                    payload,
                )
                await set_entry_fsm_state(
                    bot,
                    storage,
                    user,
                    reminder,
                    payload,
                    now,
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
        observe_duration("celery", "process_user_reminders_async", started_at)
        await storage.close()
        await bot.session.close()

    return reminders_sent
