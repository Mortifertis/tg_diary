from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import User


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )
    with SessionLocal() as session:
        yield session


@pytest.fixture()
def user(session):
    user = User(
        telegram_id=1,
        timezone="UTC",
        daily_time="09:00",
        weekly_day=6,
        weekly_time="20:00",
        monthly_day=1,
        monthly_time="20:00",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
