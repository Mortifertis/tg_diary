from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (Boolean, Column, Date, DateTime, Enum, ForeignKey,
                        Integer, String, Text, UniqueConstraint)
from sqlalchemy.orm import relationship

from app.db import Base


class EntryType(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    user = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    timezone = Column(String(64), nullable=False)
    daily_time = Column(String(5), nullable=False)
    weekly_day = Column(Integer, nullable=False)
    weekly_time = Column(String(5), nullable=False)
    monthly_day = Column(Integer, nullable=False)
    monthly_time = Column(String(5), nullable=False)
    streak = Column(Integer, default=0)
    last_entry_date = Column(Date)
    pause_until = Column(Date)
    daily_reminder_date = Column(Date)
    daily_reminder_stage = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    entries = relationship("Entry", back_populates="user", cascade="all, delete-orphan")
    questions = relationship(
        "UserQuestion",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Entry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entry_type = Column(Enum(EntryType), nullable=False)
    entry_date = Column(Date, nullable=False)
    question = Column(String(255))
    text = Column(Text, nullable=False)
    mood = Column(String(16))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="entries")


class UserQuestion(Base):
    __tablename__ = "user_questions"
    __table_args__ = (
        UniqueConstraint("user_id", "entry_type", "text", name="uq_user_question_text"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entry_type = Column(Enum(EntryType), nullable=False)
    text = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="questions")
