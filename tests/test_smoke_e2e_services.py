from __future__ import annotations

import asyncio
import os
import uuid

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from sqlalchemy import select

from app.db import create_session_factory, run_migrations
from app.fsm import create_redis_storage
from app.models import Entry, EntryType, User


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    pytest.skip(f"{name} is not configured")


def test_smoke_e2e_with_postgres_and_redis_services() -> None:
    database_url = _require_env("TEST_DATABASE_URL")
    redis_url = _require_env("TEST_REDIS_URL")

    run_migrations(database_url)
    session_factory = create_session_factory(database_url)

    unique_suffix = uuid.uuid4().hex[:10]
    telegram_id = int(uuid.uuid4().int % 1_000_000_000)

    with session_factory() as session:
        user = User(
            telegram_id=telegram_id,
            timezone="UTC",
            language="ru",
            daily_time="09:00",
            weekly_day=0,
            weekly_time="10:00",
            monthly_day=1,
            monthly_time="11:00",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        entry = Entry(
            user_id=user.id,
            entry_type=EntryType.user,
            entry_index=f"smoke-{unique_suffix}",
            entry_date=user.created_at.date(),
            text="CI smoke entry",
        )
        session.add(entry)
        session.commit()

        stored_entry = session.execute(
            select(Entry).where(Entry.entry_index == entry.entry_index)
        ).scalar_one()
        assert stored_entry.text == "CI smoke entry"

    async def redis_scenario() -> None:
        storage = await create_redis_storage(
            redis_url=redis_url,
            retries=2,
            retry_delay_seconds=0.0,
        )
        key = StorageKey(
            bot_id=telegram_id,
            chat_id=telegram_id,
            user_id=telegram_id,
        )
        state = FSMContext(storage=storage, key=key)

        try:
            await state.set_state("smoke:ready")
            assert await state.get_state() == "smoke:ready"
        finally:
            await state.clear()
            await storage.close()

    asyncio.run(redis_scenario())
