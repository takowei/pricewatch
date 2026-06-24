"""Watchlist request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class WatchlistCreateRequest(BaseModel):
    keyword: str
    max_price: int | None = None


class WatchlistUpdateRequest(BaseModel):
    keyword: str | None = None
    max_price: int | None = None
    is_active: bool | None = None


class WatchlistResponse(BaseModel):
    id: int
    user_id: int
    keyword: str
    max_price: int | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
