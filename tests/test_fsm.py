from __future__ import annotations

import asyncio
import os
import uuid

import pytest
from aiogram.fsm.storage.base import StorageKey

pytest.importorskip("redis")
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.fsm import create_redis_storage
from app.states import EntryState


class _FakeRedis:
    def __init__(self, should_fail: bool) -> None:
        self._should_fail = should_fail
        self.closed = False

    async def ping(self) -> bool:
        if self._should_fail:
            raise RedisError("temporary failure")
        return True

    async def aclose(self) -> None:
        self.closed = True


def test_create_redis_storage_retries_until_success(monkeypatch) -> None:
    instances: list[_FakeRedis] = []
    delays: list[float] = []

    def fake_from_url(_url: str) -> _FakeRedis:
        should_fail = len(instances) < 2
        instance = _FakeRedis(should_fail=should_fail)
        instances.append(instance)
        return instance

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr("app.fsm.Redis.from_url", fake_from_url)
    monkeypatch.setattr("app.fsm.asyncio.sleep", fake_sleep)

    storage = asyncio.run(
        create_redis_storage(
            redis_url="redis://example",
            retries=3,
            retry_delay_seconds=0.5,
        )
    )

    assert storage.redis is instances[-1]
    assert len(instances) == 3
    assert delays == [0.5, 0.5]
    assert instances[0].closed
    assert instances[1].closed
    assert not instances[2].closed


def test_create_redis_storage_raises_after_retries(monkeypatch) -> None:
    instances: list[_FakeRedis] = []

    def fake_from_url(_url: str) -> _FakeRedis:
        instance = _FakeRedis(should_fail=True)
        instances.append(instance)
        return instance

    monkeypatch.setattr("app.fsm.Redis.from_url", fake_from_url)

    with pytest.raises(RuntimeError, match="Unable to connect"):
        asyncio.run(
            create_redis_storage(
                redis_url="redis://example",
                retries=2,
                retry_delay_seconds=0.0,
            )
        )

    assert len(instances) == 2
    assert instances[0].closed
    assert instances[1].closed


def test_fsm_state_persists_across_storage_restarts() -> None:
    redis_url = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/15")

    async def can_connect() -> bool:
        redis = Redis.from_url(redis_url)
        try:
            await redis.ping()
            return True
        except RedisError:
            return False
        finally:
            await redis.aclose()

    if not asyncio.run(can_connect()):
        pytest.skip("Redis is unavailable for persistence test")

    unique_id = int(uuid.uuid4().int % 10_000_000)
    key = StorageKey(bot_id=unique_id, chat_id=unique_id, user_id=unique_id)

    async def scenario() -> None:
        storage_first = await create_redis_storage(
            redis_url=redis_url,
            retries=1,
            retry_delay_seconds=0.0,
        )
        await storage_first.set_state(key, EntryState.waiting_text)
        await storage_first.update_data(key, {"step": "first"})
        await storage_first.close()

        storage_second = await create_redis_storage(
            redis_url=redis_url,
            retries=1,
            retry_delay_seconds=0.0,
        )
        state = await storage_second.get_state(key)
        data = await storage_second.get_data(key)
        await storage_second.set_state(key, None)
        await storage_second.set_data(key, {})
        await storage_second.close()

        assert state == EntryState.waiting_text.state
        assert data["step"] == "first"

    asyncio.run(scenario())
