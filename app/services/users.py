from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import User


def get_user_by_telegram_id(session: Session, telegram_id: int) -> User | None:
    return session.query(User).filter_by(telegram_id=telegram_id).first()
