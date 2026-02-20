from __future__ import annotations

import json
from datetime import date, datetime
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from app.constants import BACKUP_SCHEMA_VERSION
from app.models import Entry, User, UserQuestion


def _serialize_date(value: date | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def build_user_backup_archive(
    user: User,
    entries: list[Entry],
    questions: list[UserQuestion],
) -> bytes:
    settings_payload = {
        "timezone": user.timezone,
        "language": user.language,
        "enable_menu_icons": bool(user.enable_menu_icons),
        "voice_recognition_mode": user.voice_recognition_mode,
        "daily_questions_count": user.daily_questions_count,
        "daily_time": user.daily_time,
        "weekly_day": user.weekly_day,
        "weekly_time": user.weekly_time,
        "monthly_day": user.monthly_day,
        "monthly_time": user.monthly_time,
        "streak": user.streak,
        "last_entry_date": _serialize_date(user.last_entry_date),
        "pause_until": _serialize_date(user.pause_until),
        "daily_reminder_date": _serialize_date(user.daily_reminder_date),
        "daily_reminder_stage": user.daily_reminder_stage,
    }

    entries_payload = []
    attachment_refs = []
    for entry in entries:
        attachments_payload = []
        for attachment in entry.attachments:
            attachment_item = {
                "attachment_type": attachment.attachment_type.value,
                "file_id": attachment.file_id,
                "file_name": attachment.file_name,
                "extension": attachment.extension,
                "created_at": _serialize_datetime(attachment.created_at),
            }
            attachments_payload.append(attachment_item)
            attachment_refs.append(
                {
                    "entry_index": entry.entry_index,
                    **attachment_item,
                }
            )
        entries_payload.append(
            {
                "entry_index": entry.entry_index,
                "entry_type": entry.entry_type.value,
                "entry_date": entry.entry_date.isoformat(),
                "question": entry.question,
                "text": entry.text,
                "mood": entry.mood,
                "created_at": _serialize_datetime(entry.created_at),
                "attachments": attachments_payload,
            }
        )

    questions_payload = [
        {
            "id": question.id,
            "entry_type": question.entry_type.value,
            "text": question.text,
            "is_active": bool(question.is_active),
            "is_default": bool(question.is_default),
            "created_at": _serialize_datetime(question.created_at),
        }
        for question in questions
    ]

    db_payload = {
        "user": {
            "telegram_id": user.telegram_id,
            "created_at": _serialize_datetime(user.created_at),
            "updated_at": _serialize_datetime(user.updated_at),
        },
        "entries": entries_payload,
        "questions": questions_payload,
    }

    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, mode="w", compression=ZIP_DEFLATED) as zip_file:
        zip_file.writestr("schema_version.txt", BACKUP_SCHEMA_VERSION)
        zip_file.writestr(
            "settings.json",
            json.dumps(settings_payload, ensure_ascii=False, indent=2),
        )
        zip_file.writestr(
            "database.json",
            json.dumps(db_payload, ensure_ascii=False, indent=2),
        )
        zip_file.writestr("attachments/.keep", "")
        zip_file.writestr(
            "attachments/manifest.json",
            json.dumps(attachment_refs, ensure_ascii=False, indent=2),
        )

    return zip_buffer.getvalue()
