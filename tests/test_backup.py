from __future__ import annotations

import json
from datetime import date
from io import BytesIO
from zipfile import ZipFile

from app.models import EntryType
from app.services.backup import build_user_backup_archive
from app.services.entries import create_entry
from app.services.questions import list_daily_questions


def test_build_user_backup_archive_contains_required_files(session, user):
    create_entry(
        session=session,
        user=user,
        entry_type=EntryType.user,
        entry_date=date(2024, 2, 1),
        text="Текст записи",
        mood="good",
        question=None,
        attachments=[
            {
                "type": "file",
                "file_id": "file-id",
                "file_name": "note.txt",
                "extension": ".txt",
            }
        ],
    )
    session.commit()

    questions = list_daily_questions(session, user)
    entries = list(user.entries)
    archive_bytes = build_user_backup_archive(user, entries, questions)

    with ZipFile(BytesIO(archive_bytes)) as zip_file:
        names = set(zip_file.namelist())
        assert "schema_version.txt" in names
        assert "settings.json" in names
        assert "database.json" in names
        assert "attachments/manifest.json" in names

        db_payload = json.loads(zip_file.read("database.json"))
        assert db_payload["user"]["telegram_id"] == user.telegram_id
        assert db_payload["entries"][0]["entry_index"] == "u1"

        settings_payload = json.loads(zip_file.read("settings.json"))
        assert settings_payload["timezone"] == user.timezone
