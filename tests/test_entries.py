from __future__ import annotations

from datetime import date, datetime, timedelta

from app.models import Entry, EntryType
from app.services.entries import (create_entry, delete_entry_by_index,
                                  format_entries_export, get_entry_by_index,
                                  list_entries, resolve_export_start_date,
                                  update_entry_text, update_streak)
from app.services.timezones import format_user_datetime


def test_update_streak_tracks_consecutive_days(user):
    today = date.today()
    update_streak(user, today)
    assert user.streak == 1
    assert user.last_entry_date == today

    next_day = today + timedelta(days=1)
    update_streak(user, next_day)
    assert user.streak == 2
    assert user.last_entry_date == next_day

    skipped_day = today + timedelta(days=3)
    update_streak(user, skipped_day)
    assert user.streak == 1
    assert user.last_entry_date == skipped_day


def test_create_entry_resets_daily_reminders(session, user):
    user.daily_reminder_date = date(2024, 1, 1)
    user.daily_reminder_stage = 2

    entry = create_entry(
        session=session,
        user=user,
        entry_type=EntryType.daily,
        entry_date=date(2024, 1, 2),
        text="Запись",
        mood="good",
        question="Вопрос",
    )
    session.commit()

    assert entry.user_id == user.id
    assert entry.entry_index == "d1"
    assert user.daily_reminder_date == date(2024, 1, 2)
    assert user.daily_reminder_stage == 0


def test_create_entry_with_user_type_does_not_reset_daily_reminders(
    session, user
):
    user.daily_reminder_date = date(2024, 1, 1)
    user.daily_reminder_stage = 2

    create_entry(
        session=session,
        user=user,
        entry_type=EntryType.user,
        entry_date=date(2024, 1, 2),
        text="Ручная запись",
        mood=None,
        question=None,
    )

    assert user.daily_reminder_date == date(2024, 1, 1)
    assert user.daily_reminder_stage == 2


def test_resolve_export_start_date_handles_known_periods():
    today = date(2024, 2, 10)

    assert resolve_export_start_date("week", today) == date(2024, 2, 3)
    assert resolve_export_start_date("month", today) == date(2024, 1, 11)
    assert resolve_export_start_date("3months", today) == date(2023, 11, 12)
    assert resolve_export_start_date("year", today) == date(2023, 2, 10)
    assert resolve_export_start_date("all", today) is None


def test_list_entries_filters_by_created_from(session, user):
    old_entry = Entry(
        user_id=user.id,
        entry_type=EntryType.daily,
        entry_date=date(2024, 1, 1),
        entry_index="d1",
        text="old",
        created_at=datetime(2024, 1, 1, 10, 0, 0),
    )
    new_entry = Entry(
        user_id=user.id,
        entry_type=EntryType.daily,
        entry_date=date(2024, 2, 1),
        entry_index="d2",
        text="new",
        created_at=datetime(2024, 2, 1, 10, 0, 0),
    )
    session.add_all([old_entry, new_entry])
    session.commit()

    entries = list_entries(
        session, user, limit=None, created_from=date(2024, 1, 15)
    )

    assert [entry.text for entry in entries] == ["new"]


def test_entry_index_and_attachments_export(session, user):
    create_entry(
        session=session,
        user=user,
        entry_type=EntryType.daily,
        entry_date=date(2024, 2, 1),
        text="С файлом",
        mood=None,
        question=None,
        attachments=[
            {
                "type": "file",
                "file_id": "file-id",
                "file_name": "report.docx",
                "extension": ".docx",
            }
        ],
    )
    session.commit()

    entry = get_entry_by_index(session, user, "d1")
    assert entry is not None
    assert entry.attachments[0].file_name == "report.docx"

    export = format_entries_export([entry])
    assert "Индекс: d1" in export
    assert "- report.docx" in export


def test_get_entry_by_index_preloads_attachments_for_detached_entry(
    session, user
):
    create_entry(
        session=session,
        user=user,
        entry_type=EntryType.user,
        entry_date=date(2024, 2, 1),
        text="С вложением",
        mood=None,
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

    entry = get_entry_by_index(session, user, "u1")
    session.close()

    assert entry is not None
    assert entry.attachments[0].file_name == "note.txt"


def test_create_entry_allows_explicit_created_at(session, user):
    created_at = datetime(2024, 2, 1, 8, 30, 0)

    entry = create_entry(
        session=session,
        user=user,
        entry_type=EntryType.user,
        entry_date=date(2024, 2, 1),
        text="Время из сообщения",
        mood=None,
        question=None,
        created_at=created_at,
    )
    session.commit()

    assert entry.created_at == created_at


def test_format_user_datetime_converts_utc_to_user_timezone(user):
    user.timezone = "Europe/Moscow"

    created_at = datetime(2024, 2, 1, 13, 12, 0)
    assert format_user_datetime(user, created_at) == "2024-02-01 16:12:00"


def test_update_entry_text_by_index(session, user):
    create_entry(
        session=session,
        user=user,
        entry_type=EntryType.user,
        entry_date=date(2024, 2, 1),
        text="Старый текст",
        mood=None,
        question=None,
    )
    session.commit()

    entry = update_entry_text(session, user, "u1", "Новый текст")
    session.commit()

    assert entry is not None
    assert entry.text == "Новый текст"


def test_delete_entry_by_index(session, user):
    create_entry(
        session=session,
        user=user,
        entry_type=EntryType.user,
        entry_date=date(2024, 2, 1),
        text="Удалить меня",
        mood=None,
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

    is_deleted = delete_entry_by_index(session, user, "u1")
    session.commit()

    assert is_deleted is True
    assert get_entry_by_index(session, user, "u1") is None
