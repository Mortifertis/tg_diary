from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

_session_factory: ContextVar[Callable[[], Any] | None] = ContextVar(
    "session_factory",
    default=None,
)


def set_session_factory(session_factory: Callable[[], Any]) -> None:
    _session_factory.set(session_factory)


@contextmanager
def get_session() -> Iterator[Any]:
    session_factory = _session_factory.get()
    if session_factory is None:
        raise RuntimeError("DB session factory is not initialized")
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
