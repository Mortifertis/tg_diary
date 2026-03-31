from __future__ import annotations

import json
from datetime import date, datetime
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from app.constants import BACKUP_SCHEMA_VERSION
from app.models import (
    AttachmentType,
    Entry,
    EntryAttachment,
    EntryType,
    User,
    UserQuestion,
)


def _parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


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
        "entries_page_size": user.entries_page_size,
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
        "next_due_at": _serialize_datetime(user.next_due_at),
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


def import_user_backup_archive(user: User, archive_bytes: bytes) -> None:
    with ZipFile(BytesIO(archive_bytes)) as zip_file:
        schema_version = zip_file.read("schema_version.txt").decode().strip()
        if schema_version != BACKUP_SCHEMA_VERSION:
            raise ValueError("unsupported_schema_version")

        settings_payload = json.loads(zip_file.read("settings.json"))
        db_payload = json.loads(zip_file.read("database.json"))

    user.timezone = settings_payload["timezone"]
    user.language = settings_payload["language"]
    user.enable_menu_icons = bool(settings_payload["enable_menu_icons"])
    user.voice_recognition_mode = settings_payload["voice_recognition_mode"]
    user.daily_questions_count = int(settings_payload["daily_questions_count"])
    user.entries_page_size = int(settings_payload.get("entries_page_size", 5))
    user.daily_time = settings_payload["daily_time"]
    user.weekly_day = int(settings_payload["weekly_day"])
    user.weekly_time = settings_payload["weekly_time"]
    user.monthly_day = int(settings_payload["monthly_day"])
    user.monthly_time = settings_payload["monthly_time"]
    user.streak = int(settings_payload.get("streak", 0))
    user.last_entry_date = _parse_iso_date(
        settings_payload.get("last_entry_date")
    )
    user.pause_until = _parse_iso_date(settings_payload.get("pause_until"))
    user.daily_reminder_date = _parse_iso_date(
        settings_payload.get("daily_reminder_date")
    )
    user.daily_reminder_stage = int(
        settings_payload.get("daily_reminder_stage", 0)
    )
    user.next_due_at = _parse_iso_datetime(settings_payload.get("next_due_at"))

    user.entries.clear()
    user.questions.clear()

    for entry_item in db_payload.get("entries", []):
        entry = Entry(
            user=user,
            entry_index=entry_item["entry_index"],
            entry_type=EntryType(entry_item["entry_type"]),
            entry_date=date.fromisoformat(entry_item["entry_date"]),
            question=entry_item.get("question"),
            text=entry_item["text"],
            mood=entry_item.get("mood"),
            created_at=_parse_iso_datetime(entry_item.get("created_at")),
        )
        for attachment_item in entry_item.get("attachments", []):
            entry.attachments.append(
                EntryAttachment(
                    attachment_type=AttachmentType(
                        attachment_item["attachment_type"]
                    ),
                    file_id=attachment_item["file_id"],
                    file_name=attachment_item["file_name"],
                    extension=attachment_item["extension"],
                    created_at=_parse_iso_datetime(
                        attachment_item.get("created_at")
                    ),
                )
            )
        user.entries.append(entry)

    for question_item in db_payload.get("questions", []):
        question = UserQuestion(
            user=user,
            entry_type=EntryType(question_item["entry_type"]),
            text=question_item["text"],
            is_active=bool(question_item.get("is_active", True)),
            is_default=bool(question_item.get("is_default", False)),
            created_at=_parse_iso_datetime(question_item.get("created_at")),
        )
        user.questions.append(question)
