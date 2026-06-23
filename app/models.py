from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db import Base


class EntryType(StrEnum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    user = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    timezone = Column(String(64), nullable=False)
    language = Column(String(8), nullable=False, default="ru")
    display_name = Column(String(128))
    enable_menu_icons = Column(Boolean, nullable=False, default=True)
    voice_recognition_mode = Column(
        String(16),
        nullable=False,
        default="auto",
    )
    entries_page_size = Column(Integer, nullable=False, default=5)
    daily_questions_count = Column(Integer, nullable=False, default=3)
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
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    next_due_at = Column(DateTime(timezone=True), index=True)

    entries = relationship(
        "Entry", back_populates="user", cascade="all, delete-orphan"
    )
    questions = relationship(
        "UserQuestion",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Entry(Base):
    __tablename__ = "entries"
    __table_args__ = (
        UniqueConstraint("user_id", "entry_index", name="uq_entry_index"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entry_type: Column[EntryType] = Column(Enum(EntryType), nullable=False)
    entry_index = Column(String(16), nullable=False)
    entry_date = Column(Date, nullable=False)
    question = Column(String(255))
    text = Column(Text, nullable=False)
    mood = Column(String(16))
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    user = relationship("User", back_populates="entries")
    attachments = relationship(
        "EntryAttachment",
        back_populates="entry",
        cascade="all, delete-orphan",
    )


class AttachmentType(StrEnum):
    image = "image"
    file = "file"


class EntryAttachment(Base):
    __tablename__ = "entry_attachments"

    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=False)
    attachment_type: Column[AttachmentType] = Column(
        Enum(AttachmentType), nullable=False
    )
    file_id = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    extension = Column(String(16), nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    entry = relationship("Entry", back_populates="attachments")


class UserQuestion(Base):
    __tablename__ = "user_questions"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "entry_type", "text", name="uq_user_question_text"
        ),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entry_type: Column[EntryType] = Column(Enum(EntryType), nullable=False)
    text = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    user = relationship("User", back_populates="questions")
