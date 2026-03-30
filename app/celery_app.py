from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import load_config

config = load_config()

celery_app = Celery(
    "tg_diary",
    broker=config.celery_broker_url,
    backend=config.celery_result_backend,
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

celery_app.conf.beat_schedule = {
    "enqueue-due-reminders-every-minute": {
        "task": "app.tasks.reminders.enqueue_due_reminders",
        "schedule": crontab(),
    }
}

celery_app.autodiscover_tasks(["app.tasks"])
