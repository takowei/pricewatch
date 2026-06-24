"""User model."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    telegram_chat_id: str | None = Field(default=None, max_length=64)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=_utcnow)
