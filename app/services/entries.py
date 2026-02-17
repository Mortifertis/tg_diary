from __future__ import annotations

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Entry, EntryType, User


def create_entry(
    session: Session,
    user: User,
    entry_type: EntryType,
    entry_date: date,
    text: str,
    mood: str | None,
    question: str | None,
) -> Entry:
    entry = Entry(
        user_id=user.id,
        entry_type=entry_type,
        entry_date=entry_date,
        text=text,
        mood=mood,
        question=question,
    )
    session.add(entry)
    update_streak(user, entry_date)
    reset_daily_reminders(user, entry_type, entry_date)
    return entry


def update_streak(user: User, entry_date: date) -> None:
    if user.last_entry_date is None:
        user.streak = 1
    elif (entry_date - user.last_entry_date).days == 1:
        user.streak += 1
    elif entry_date != user.last_entry_date:
        user.streak = 1
    user.last_entry_date = entry_date


def reset_daily_reminders(user: User, entry_type: EntryType, entry_date: date) -> None:
    if entry_type != EntryType.daily:
        return
    user.daily_reminder_date = entry_date
    user.daily_reminder_stage = 0


def count_entries(session: Session, user: User, entry_type: EntryType | None = None) -> int:
    query = session.query(func.count(Entry.id)).filter(Entry.user_id == user.id)
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


def has_entry_for_date(session: Session, user: User, entry_type: EntryType, entry_date: date) -> bool:
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


def list_entries(session: Session, user: User, limit: int | None) -> list[Entry]:
    query = (
        session.query(Entry)
        .filter(Entry.user_id == user.id)
        .order_by(Entry.created_at.desc(), Entry.id.desc())
    )
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def format_entries_export(entries: list[Entry]) -> str:
    lines = []
    for entry in entries:
        lines.append(f"Дата создания: {entry.created_at:%Y-%m-%d %H:%M:%S}")
        lines.append(f"Тип: {entry.entry_type.value}")
        lines.append(f"Дата записи: {entry.entry_date:%Y-%m-%d}")
        if entry.question:
            lines.append(f"Вопрос: {entry.question}")
        if entry.mood:
            lines.append(f"Настроение: {entry.mood}")
        lines.append(f"Текст: {entry.text}")
        lines.append("-" * 40)
    return "\n".join(lines)
