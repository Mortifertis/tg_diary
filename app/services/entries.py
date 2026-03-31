from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import cast

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models import AttachmentType, Entry, EntryAttachment, EntryType, User

ENTRY_TYPE_INDEX_PREFIXES = {
    EntryType.daily: "d",
    EntryType.weekly: "w",
    EntryType.monthly: "m",
    EntryType.user: "u",
}


def create_entry(
    session: Session,
    user: User,
    entry_type: EntryType,
    entry_date: date,
    text: str,
    mood: str | None,
    question: str | None,
    attachments: list[dict[str, str]] | None = None,
    created_at: datetime | None = None,
) -> Entry:
    entry = Entry(
        user_id=user.id,
        entry_type=entry_type,
        entry_index="pending",
        entry_date=entry_date,
        text=text,
        mood=mood,
        question=question,
        created_at=created_at,
    )
    for attachment in attachments or []:
        entry.attachments.append(
            EntryAttachment(
                attachment_type=AttachmentType(attachment["type"]),
                file_id=attachment["file_id"],
                file_name=attachment["file_name"],
                extension=attachment["extension"],
            )
        )
    session.add(entry)
    session.flush()
    setattr(
        entry,
        "entry_index",
        f"{ENTRY_TYPE_INDEX_PREFIXES[entry_type]}{cast(int, entry.id)}",
    )
    update_streak(user, entry_date)
    reset_daily_reminders(user, entry_type, entry_date)
    return entry


def update_streak(user: User, entry_date: date) -> None:
    last_entry_date = cast(date | None, user.last_entry_date)
    streak = cast(int, user.streak)

    if last_entry_date is None:
        setattr(user, "streak", 1)
    elif (entry_date - last_entry_date).days == 1:
        setattr(user, "streak", streak + 1)
    elif entry_date != last_entry_date:
        setattr(user, "streak", 1)
    setattr(user, "last_entry_date", entry_date)


def reset_daily_reminders(
    user: User, entry_type: EntryType, entry_date: date
) -> None:
    if entry_type != EntryType.daily:
        return
    setattr(user, "daily_reminder_date", entry_date)
    setattr(user, "daily_reminder_stage", 0)


def count_entries(
    session: Session, user: User, entry_type: EntryType | None = None
) -> int:
    query = session.query(func.count(Entry.id)).filter(
        Entry.user_id == user.id
    )
    if entry_type:
        query = query.filter(Entry.entry_type == entry_type)
    return query.scalar() or 0


def mood_breakdown(session: Session, user: User) -> dict[str, int]:
    rows = (
        session.query(Entry.mood, func.count(Entry.id))
        .filter(Entry.user_id == user.id, Entry.mood.isnot(None))
        .group_by(Entry.mood)
        .all()
    )
    return {mood: count for mood, count in rows}


def has_entry_for_date(
    session: Session, user: User, entry_type: EntryType, entry_date: date
) -> bool:
    return (
        session.query(Entry.id)
        .filter(
            Entry.user_id == user.id,
            Entry.entry_type == entry_type,
            Entry.entry_date == entry_date,
        )
        .first()
        is not None
    )


def list_entries(
    session: Session,
    user: User,
    limit: int | None,
    created_from: datetime | None = None,
) -> list[Entry]:
    query = (
        session.query(Entry)
        .options(selectinload(Entry.attachments))
        .filter(Entry.user_id == user.id)
    )
    if created_from is not None:
        query = query.filter(Entry.created_at >= created_from)
    query = query.order_by(Entry.created_at.desc(), Entry.id.desc())
    if limit is not None:
        query = query.limit(limit)
    entries = query.all()
    return cast(list[Entry], entries)


def format_entries_export(entries: list[Entry]) -> str:
    lines = []
    for entry in entries:
        lines.append(f"{entry.entry_date:%d.%m.%Y}")
        if entry.mood:
            lines.append(f"Настроение: {entry.mood}")
        lines.append(cast(str, entry.text))
        lines.append("")
        lines.append("----")
        lines.append("")
    return "\n".join(lines).strip()


def get_entry_by_index(
    session: Session, user: User, entry_index: str
) -> Entry | None:
    return (
        session.query(Entry)
        .options(selectinload(Entry.attachments))
        .filter(
            Entry.user_id == user.id,
            Entry.entry_index == entry_index,
        )
        .first()
    )


def update_entry_text(
    session: Session, user: User, entry_index: str, text: str
) -> Entry | None:
    entry = get_entry_by_index(session, user, entry_index)
    if not entry:
        return None
    setattr(entry, "text", text)
    session.flush()
    return entry


def delete_entry_by_index(
    session: Session, user: User, entry_index: str
) -> bool:
    entry = get_entry_by_index(session, user, entry_index)
    if not entry:
        return False
    session.delete(entry)
    session.flush()
    return True


def resolve_export_start_date(period: str, today: date) -> date | None:
    period_days = {
        "week": 7,
        "month": 30,
        "3months": 90,
        "year": 365,
    }
    if period == "all":
        return None
    days = period_days.get(period)
    if days is None:
        return None
    return today - timedelta(days=days)
