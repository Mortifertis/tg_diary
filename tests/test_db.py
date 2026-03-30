from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

from app.db import create_session_factory, init_db, run_migrations


def test_create_session_factory_disables_expire_on_commit():
    session_factory = create_session_factory("sqlite:///:memory:")

    assert session_factory.kw["expire_on_commit"] is False


def test_init_db_creates_users_table_for_test_setup():
    engine = create_engine("sqlite:///:memory:", future=True)

    init_db(engine)

    inspector = inspect(engine)
    assert "users" in inspector.get_table_names()


def test_run_migrations_upgrades_schema_to_head(tmp_path: Path):
    pytest.importorskip("alembic")
    sqlite_path = tmp_path / "migration_test.db"
    database_url = f"sqlite:///{sqlite_path}"

    run_migrations(database_url)

    engine = create_engine(database_url, future=True)
    inspector = inspect(engine)
    assert "entries" in inspector.get_table_names()


def test_run_migrations_adds_next_due_at_column(tmp_path: Path):
    pytest.importorskip("alembic")
    sqlite_path = tmp_path / "migration_test_with_next_due_at.db"
    database_url = f"sqlite:///{sqlite_path}"

    run_migrations(database_url)

    engine = create_engine(database_url, future=True)
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("users")}
    assert "next_due_at" in columns


def test_run_migrations_is_idempotent_for_latest_revision(tmp_path: Path):
    pytest.importorskip("alembic")
    sqlite_path = tmp_path / "migration_test_idempotent.db"
    database_url = f"sqlite:///{sqlite_path}"

    run_migrations(database_url)
    run_migrations(database_url)

    engine = create_engine(database_url, future=True)
    inspector = inspect(engine)
    assert "user_questions" in inspector.get_table_names()
