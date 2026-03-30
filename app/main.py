from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from app.config import load_config
from app.constants import BOT_TOKEN_MISSING
from app.db import create_session_factory, run_migrations
from app.fsm import create_redis_storage
from app.handlers import common, entry, settings
from app.scheduler import create_scheduler


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    load_dotenv()
    config = load_config()
    if not config.bot_token:
        raise RuntimeError(BOT_TOKEN_MISSING)

    run_migrations(config.database_url)
    session_factory = create_session_factory(config.database_url)

    storage = await create_redis_storage(
        redis_url=config.redis_url,
        retries=config.redis_connect_retries,
        retry_delay_seconds=config.redis_retry_delay_seconds,
    )
    bot = Bot(token=config.bot_token)
    bot.session_factory = session_factory

    dp = Dispatcher(storage=storage)
    dp.include_router(common.router)
    dp.include_router(settings.router)
    dp.include_router(entry.router)

    scheduler = create_scheduler(bot, storage)
    scheduler.start()

    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        logging.info("Polling cancelled")
    finally:
        scheduler.shutdown(wait=False)
        await storage.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
