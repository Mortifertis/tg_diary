from __future__ import annotations

from app.db import create_session_factory


def test_create_session_factory_disables_expire_on_commit():
    session_factory = create_session_factory("sqlite:///:memory:")

    assert session_factory.kw["expire_on_commit"] is False
