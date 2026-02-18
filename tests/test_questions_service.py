from __future__ import annotations

from app.models import UserQuestion
from app.questions import DAILY_QUESTIONS
from app.services.questions import (add_daily_question, delete_daily_question,
                                    ensure_default_daily_questions,
                                    list_active_daily_questions,
                                    list_daily_questions,
                                    set_daily_question_active)


def test_ensure_default_daily_questions_creates_seed(session, user) -> None:
    ensure_default_daily_questions(session, user)
    session.commit()

    questions = list_daily_questions(session, user)

    assert len(questions) == len(DAILY_QUESTIONS)
    assert questions[0].text == DAILY_QUESTIONS[0]


def test_add_delete_and_pause_daily_question(session, user) -> None:
    ensure_default_daily_questions(session, user)
    session.commit()

    added = add_daily_question(session, user, "Мой вопрос")
    session.commit()

    assert added is True
    custom = session.query(UserQuestion).filter_by(text="Мой вопрос").first()
    assert custom is not None

    paused = set_daily_question_active(session, user, custom.id, False)
    session.commit()

    assert paused is True
    active_questions = list_active_daily_questions(session, user)
    assert "Мой вопрос" not in active_questions

    deleted = delete_daily_question(session, user, custom.id)
    session.commit()

    assert deleted is True
    assert session.query(UserQuestion).filter_by(text="Мой вопрос").first() is None


def test_add_daily_question_rejects_duplicates(session, user) -> None:
    ensure_default_daily_questions(session, user)
    session.commit()

    added = add_daily_question(session, user, DAILY_QUESTIONS[0])

    assert added is False
