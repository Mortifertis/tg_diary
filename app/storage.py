from __future__ import annotations

from contextlib import contextmanager

from aiogram import Bot


@contextmanager
def get_session(bot: Bot):
    session_factory = bot["session_factory"]
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
