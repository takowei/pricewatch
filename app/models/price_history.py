"""PriceHistory model — one record per product per day."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlmodel import Field, SQLModel, UniqueConstraint


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class PriceHistory(SQLModel, table=True):
    __tablename__ = "price_history"
    __table_args__ = (UniqueConstraint("product_id", "recorded_date", name="uq_product_date"),)

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    sale_price: int | None = Field(default=None)
    discount: int | None = Field(default=None)
    recorded_date: date = Field(index=True)
    created_at: datetime = Field(default_factory=_utcnow)
