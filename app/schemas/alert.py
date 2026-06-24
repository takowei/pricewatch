"""Alert response schema."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: int
    user_id: int
    watchlist_id: int
    product_id: int
    triggered_price: int
    reason: str
    is_notified: bool
    created_at: datetime

    model_config = {"from_attributes": True}
