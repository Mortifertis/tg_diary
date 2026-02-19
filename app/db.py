from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


def create_session_factory(database_url: str):
    engine = create_engine(database_url, future=True)
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


def init_db(engine):
    Base.metadata.create_all(engine)
    _ensure_sqlite_schema_compatibility(engine)


def _ensure_sqlite_schema_compatibility(engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "entries" not in table_names:
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("entries")
    }
    if "entry_index" not in existing_columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE entries ADD COLUMN entry_index VARCHAR(16)")
            )
            connection.execute(
                text(
                    """
                    UPDATE entries
                    SET entry_index = CASE entry_type
                        WHEN 'daily' THEN 'd' || id
                        WHEN 'weekly' THEN 'w' || id
                        WHEN 'monthly' THEN 'm' || id
                        WHEN 'user' THEN 'u' || id
                        ELSE 'e' || id
                    END
                    WHERE entry_index IS NULL
                    """
                )
            )

    user_columns = {
        column["name"] for column in inspector.get_columns("users")
    }
    if "language" in user_columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE users ADD COLUMN language "
                "VARCHAR(8) NOT NULL DEFAULT 'ru'"
            )
        )
