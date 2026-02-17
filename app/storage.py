from __future__ import annotations

from contextlib import contextmanager

from aiogram import Bot


@contextmanager
def get_session(bot: Bot):
    session_factory = getattr(bot, "session_factory", None)
    if session_factory is None:
        raise RuntimeError("Bot session_factory is not initialized")
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
