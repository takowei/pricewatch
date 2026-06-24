"""Product model — shared across all users."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    brand: str = Field(max_length=64)
    name: str = Field(max_length=512)
    category: str = Field(default="", max_length=128)
    product_url: str = Field(unique=True, index=True, max_length=1024)
    image_url: str = Field(default="", max_length=1024)
    current_sale_price: int | None = Field(default=None)
    original_price: int | None = Field(default=None)
    discount: int | None = Field(default=None)
    last_scraped_at: datetime = Field(default_factory=_utcnow)
