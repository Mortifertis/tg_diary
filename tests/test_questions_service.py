from __future__ import annotations

from app.models import UserQuestion
from app.questions import DAILY_QUESTIONS
from app.services.questions import (
    add_daily_question,
    delete_daily_question,
    ensure_default_daily_questions,
    list_active_daily_questions,
    list_daily_questions,
    reset_daily_questions_to_default,
    set_daily_question_active,
)


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
    assert (
        session.query(UserQuestion).filter_by(text="Мой вопрос").first()
        is None
    )


def test_add_daily_question_rejects_duplicates(session, user) -> None:
    ensure_default_daily_questions(session, user)
    session.commit()

    added = add_daily_question(session, user, DAILY_QUESTIONS[0])

    assert added is False


def test_add_daily_question_strips_whitespace(session, user) -> None:
    ensure_default_daily_questions(session, user)
    session.commit()

    added = add_daily_question(session, user, "   Мой вопрос с пробелами   ")
    session.commit()

    assert added is True
    stored = (
        session.query(UserQuestion)
        .filter_by(user_id=user.id, text="Мой вопрос с пробелами")
        .first()
    )
    assert stored is not None


def test_add_daily_question_rejects_empty_text(session, user) -> None:
    ensure_default_daily_questions(session, user)
    session.commit()

    added = add_daily_question(session, user, "   ")

    assert added is False


def test_delete_daily_question_returns_false_for_unknown_id(
    session, user
) -> None:
    ensure_default_daily_questions(session, user)
    session.commit()

    deleted = delete_daily_question(session, user, 999999)

    assert deleted is False


def test_set_daily_question_active_returns_false_for_unknown_id(
    session, user
) -> None:
    ensure_default_daily_questions(session, user)
    session.commit()

    paused = set_daily_question_active(session, user, 999999, False)

    assert paused is False


def test_ensure_default_daily_questions_restores_missing_defaults(
    session, user
) -> None:
    ensure_default_daily_questions(session, user)
    session.commit()

    first_default = (
        session.query(UserQuestion)
        .filter_by(
            user_id=user.id,
            text=DAILY_QUESTIONS[0],
        )
        .first()
    )
    assert first_default is not None
    session.delete(first_default)
    session.commit()

    ensure_default_daily_questions(session, user)
    session.commit()

    restored = (
        session.query(UserQuestion)
        .filter_by(
            user_id=user.id,
            text=DAILY_QUESTIONS[0],
            is_default=True,
        )
        .first()
    )
    assert restored is not None


def test_reset_daily_questions_to_default(session, user) -> None:
    ensure_default_daily_questions(session, user)
    add_daily_question(session, user, "Мой вопрос")
    session.commit()

    reset_daily_questions_to_default(session, user)
    session.commit()

    questions = list_daily_questions(session, user)

    assert len(questions) == len(DAILY_QUESTIONS)
    assert all(question.is_default for question in questions)
    assert all(question.is_active for question in questions)
