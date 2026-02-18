from __future__ import annotations

from sqlalchemy import create_engine, text

from app.db import create_session_factory, init_db


def test_create_session_factory_disables_expire_on_commit():
    session_factory = create_session_factory("sqlite:///:memory:")

    assert session_factory.kw["expire_on_commit"] is False


def test_init_db_adds_missing_entry_index_column_for_legacy_sqlite_schema():
    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE entries (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    entry_type VARCHAR(7) NOT NULL,
                    entry_date DATE NOT NULL,
                    question VARCHAR(255),
                    text TEXT NOT NULL,
                    mood VARCHAR(16),
                    created_at DATETIME
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO entries (id, user_id, entry_type, entry_date, text)
                VALUES (1, 1, 'daily', '2024-01-01', 'legacy')
                """
            )
        )

    init_db(engine)

    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT entry_index FROM entries WHERE id = 1")
        ).one()

    assert row.entry_index == "d1"
