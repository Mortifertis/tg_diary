from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from app.config import load_config
from app.constants import BOT_TOKEN_MISSING
from app.db import create_session_factory, init_db
from app.handlers import common, entry, settings
from app.scheduler import create_scheduler


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    load_dotenv()
    config = load_config()
    if not config.bot_token:
        raise RuntimeError(BOT_TOKEN_MISSING)

    session_factory = create_session_factory(config.database_url)
    engine = session_factory.kw["bind"]
    init_db(engine)

    storage = MemoryStorage()
    bot = Bot(token=config.bot_token)
    bot.session_factory = session_factory

    dp = Dispatcher(storage=storage)
    dp.include_router(common.router)
    dp.include_router(settings.router)
    dp.include_router(entry.router)

    scheduler = create_scheduler(bot, storage)
    scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
