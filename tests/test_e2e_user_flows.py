from __future__ import annotations

import asyncio
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

pytest.importorskip("redis")

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.fsm import create_redis_storage
from app.handlers import common, entry, settings
from app.models import Entry, EntryType, User
from app.states import EntryState


@dataclass(slots=True)
class _RecordedDocument:
    filename: str
    caption: str | None


class _FakeMessage:
    def __init__(
        self,
        *,
        bot: Any,
        user_id: int,
        text: str,
        full_name: str = "Test User",
    ) -> None:
        self.bot = bot
        self.text = text
        self.caption = None
        self.photo: list[Any] = []
        self.document = None
        self.voice = None
        self.date = datetime.now(UTC)
        self.from_user = SimpleNamespace(
            id=user_id,
            full_name=full_name,
            username=None,
        )
        self.answers: list[str] = []
        self.documents: list[_RecordedDocument] = []

    async def answer(self, text: str, reply_markup: Any = None) -> None:
        del reply_markup
        self.answers.append(text)

    async def answer_document(self, document: Any, caption: str = "") -> None:
        self.documents.append(
            _RecordedDocument(
                filename=document.filename,
                caption=caption,
            )
        )


async def _redis_available(redis_url: str) -> bool:
    redis = Redis.from_url(redis_url)
    try:
        await redis.ping()
        return True
    except RedisError:
        return False
    finally:
        await redis.aclose()


def test_e2e_user_flow_start_entry_reminders_export() -> None:
    redis_url = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/15")
    if not asyncio.run(_redis_available(redis_url)):
        pytest.skip("Redis is unavailable for E2E user flow test")

    unique_id = int(uuid.uuid4().int % 10_000_000)

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )

    bot = SimpleNamespace(session_factory=session_factory)

    async def scenario() -> None:
        storage = await create_redis_storage(
            redis_url=redis_url,
            retries=1,
            retry_delay_seconds=0.0,
        )
        key = StorageKey(
            bot_id=unique_id,
            chat_id=unique_id,
            user_id=unique_id,
        )
        state = FSMContext(storage=storage, key=key)

        try:
            start_message = _FakeMessage(
                bot=bot,
                user_id=unique_id,
                text="/start",
            )
            await common.start(start_message)

            with session_factory() as session:
                user = session.query(User).filter_by(telegram_id=unique_id).one()
                assert user.language == "ru"

            create_message = _FakeMessage(
                bot=bot,
                user_id=unique_id,
                text="Сделать новую запись",
            )
            await common.create_entry_from_menu(create_message, state)
            assert await state.get_state() == EntryState.waiting_text.state

            entry_message = _FakeMessage(
                bot=bot,
                user_id=unique_id,
                text="Сегодня сделал полноценный e2e флоу",
            )
            await entry.save_entry(entry_message, state)
            assert await state.get_state() is None

            with session_factory() as session:
                entries = session.query(Entry).filter_by(user_id=user.id).all()
                assert len(entries) == 1
                assert entries[0].entry_type == EntryType.user
                assert entries[0].text == "Сегодня сделал полноценный e2e флоу"

            reminder_message = _FakeMessage(
                bot=bot,
                user_id=unique_id,
                text="/time 08:30",
            )
            await settings.set_daily_time(reminder_message)
            assert reminder_message.answers

            with session_factory() as session:
                user = session.query(User).filter_by(telegram_id=unique_id).one()
                assert user.daily_time == "08:30"

            export_menu_message = _FakeMessage(
                bot=bot,
                user_id=unique_id,
                text="Экспорт",
            )
            await common.export_menu_with_state(export_menu_message, state)
            assert await state.get_state() == EntryState.waiting_export_period.state

            export_period_message = _FakeMessage(
                bot=bot,
                user_id=unique_id,
                text="Последняя неделя",
            )
            await common.export_entries_from_menu(export_period_message, state)

            assert export_period_message.documents
            document = export_period_message.documents[-1]
            assert document.filename == "entries_week.txt"
            assert document.caption is not None
            assert "Последняя неделя" in document.caption
        finally:
            await state.clear()
            await storage.close()

    asyncio.run(scenario())
