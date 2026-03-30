from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


def create_session_factory(database_url: str):
    engine = create_engine(
        database_url,
        future=True,
        pool_pre_ping=True,
    )
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


def init_db(engine) -> None:
    """Create schema directly.

    This helper is intended for tests and local scripts.
    Production schema updates should be managed via Alembic migrations.
    """
    Base.metadata.create_all(engine)


def run_migrations(database_url: str) -> None:
    """Upgrade database schema to the latest Alembic revision."""
    from alembic import command
    from alembic.config import Config

    alembic_ini_path = Path(__file__).resolve().parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")
