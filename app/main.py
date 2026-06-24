from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from app.config import load_config, validate_config
from app.db import create_session_factory, run_migrations
from app.fsm import create_redis_storage
from app.handlers import common, entry, settings
from app.observability import (
    BOT_STARTUPS_TOTAL,
    POLLING_EXCEPTIONS_TOTAL,
    setup_logging,
    setup_sentry,
    start_observability_server,
)
from app.storage import set_session_factory


async def main() -> None:
    load_dotenv()
    config = load_config()
    validate_config(config)
    setup_logging(config.log_level)
    setup_sentry(
        dsn=config.sentry_dsn,
        environment=config.sentry_environment,
        traces_sample_rate=config.sentry_traces_sample_rate,
    )

    observability_server = start_observability_server(
        host=config.observability_host,
        port=config.observability_port,
    )

    if config.run_migrations_on_startup:
        run_migrations(config.database_url)
    session_factory = create_session_factory(config.database_url)
    set_session_factory(session_factory)

    storage = await create_redis_storage(
        redis_url=config.redis_url,
        retries=config.redis_connect_retries,
        retry_delay_seconds=config.redis_retry_delay_seconds,
    )
    bot = Bot(token=config.bot_token)

    dp = Dispatcher(storage=storage)
    dp.include_router(common.router)
    dp.include_router(settings.router)
    dp.include_router(entry.router)

    BOT_STARTUPS_TOTAL.inc()
    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        logging.info("Polling cancelled")
    except Exception:
        POLLING_EXCEPTIONS_TOTAL.labels(component="polling").inc()
        logging.exception("Unexpected polling error")
        raise
    finally:
        await storage.close()
        await bot.session.close()
        if observability_server is not None:
            observability_server.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
