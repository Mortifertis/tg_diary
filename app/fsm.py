from __future__ import annotations

import asyncio
import logging

from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from redis.exceptions import RedisError

LOGGER = logging.getLogger(__name__)


async def create_redis_storage(
    redis_url: str,
    retries: int,
    retry_delay_seconds: float,
) -> RedisStorage:
    """Create Redis-backed FSM storage with retry policy."""
    retries = max(retries, 1)
    retry_delay_seconds = max(retry_delay_seconds, 0.0)
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        redis = Redis.from_url(redis_url)
        try:
            await redis.ping()
            LOGGER.info(
                "Connected to Redis FSM storage on attempt %s/%s",
                attempt,
                retries,
            )
            return RedisStorage(redis=redis)
        except RedisError as error:
            last_error = error
            await redis.aclose()
            LOGGER.warning(
                "Redis FSM connection failed on attempt %s/%s: %s",
                attempt,
                retries,
                error,
            )
            if attempt < retries:
                await asyncio.sleep(retry_delay_seconds)

    raise RuntimeError("Unable to connect to Redis FSM storage") from last_error
