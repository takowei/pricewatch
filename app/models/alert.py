"""Alert model — triggered price alerts with DB-level dedup."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from sqlmodel import Field, SQLModel, UniqueConstraint


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


AlertReason = Literal["at_target", "price_drop"]


class Alert(SQLModel, table=True):
    __tablename__ = "alerts"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "product_id",
            "triggered_price",
            name="uq_alert_dedup",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    watchlist_id: int = Field(foreign_key="watchlists.id")
    product_id: int = Field(foreign_key="products.id", index=True)
    triggered_price: int
    reason: str = Field(max_length=32)  # "at_target" | "price_drop"
    is_notified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utcnow)
