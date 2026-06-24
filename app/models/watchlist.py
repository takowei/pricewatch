"""Watchlist model — per-user keyword + optional price target."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class Watchlist(SQLModel, table=True):
    __tablename__ = "watchlists"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    keyword: str = Field(max_length=128)
    max_price: int | None = Field(default=None)  # None = alert on any sale
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=_utcnow)
