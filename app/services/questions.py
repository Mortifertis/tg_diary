from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import EntryType, User, UserQuestion
from app.questions import DAILY_QUESTIONS


def ensure_default_daily_questions(session: Session, user: User) -> None:
    existing = session.query(UserQuestion).filter_by(
        user_id=user.id,
        entry_type=EntryType.daily,
    )
    if existing.first():
        return

    for question in DAILY_QUESTIONS:
        session.add(
            UserQuestion(
                user_id=user.id,
                entry_type=EntryType.daily,
                text=question,
                is_default=True,
                is_active=True,
            )
        )


def list_daily_questions(session: Session, user: User) -> list[UserQuestion]:
    ensure_default_daily_questions(session, user)
    return (
        session.query(UserQuestion)
        .filter_by(user_id=user.id, entry_type=EntryType.daily)
        .order_by(UserQuestion.id.asc())
        .all()
    )


def list_active_daily_questions(session: Session, user: User) -> list[str]:
    ensure_default_daily_questions(session, user)
    rows = (
        session.query(UserQuestion)
        .filter_by(user_id=user.id, entry_type=EntryType.daily, is_active=True)
        .all()
    )
    return [row.text for row in rows]


def add_daily_question(session: Session, user: User, text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return False

    exists = session.query(UserQuestion).filter_by(
        user_id=user.id,
        entry_type=EntryType.daily,
        text=normalized,
    )
    if exists.first():
        return False

    session.add(
        UserQuestion(
            user_id=user.id,
            entry_type=EntryType.daily,
            text=normalized,
            is_default=False,
            is_active=True,
        )
    )
    return True


def delete_daily_question(session: Session, user: User, question_id: int) -> bool:
    question = session.query(UserQuestion).filter_by(
        id=question_id,
        user_id=user.id,
        entry_type=EntryType.daily,
    ).first()
    if not question:
        return False
    session.delete(question)
    return True


def set_daily_question_active(
    session: Session,
    user: User,
    question_id: int,
    is_active: bool,
) -> bool:
    question = session.query(UserQuestion).filter_by(
        id=question_id,
        user_id=user.id,
        entry_type=EntryType.daily,
    ).first()
    if not question:
        return False
    question.is_active = is_active
    return True
