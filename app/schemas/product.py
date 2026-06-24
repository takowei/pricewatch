"""Product and price-history response schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class ProductResponse(BaseModel):
    id: int
    brand: str
    name: str
    category: str
    product_url: str
    image_url: str
    current_sale_price: int | None
    original_price: int | None
    discount: int | None
    last_scraped_at: datetime

    model_config = {"from_attributes": True}


class PriceHistoryPoint(BaseModel):
    recorded_date: date
    sale_price: int | None
    discount: int | None

    model_config = {"from_attributes": True}
