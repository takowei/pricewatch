"""Watchlist CRUD service — orchestrates repo calls, enforces ownership."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.watchlist import Watchlist
from app.repositories.watchlist_repo import (
    create_watchlist_item,
    delete_watchlist_item,
    get_watchlist_item,
    list_watchlist,
    update_watchlist_item,
)


def get_user_watchlist(db: Session, user_id: int) -> list[Watchlist]:
    return list_watchlist(db, user_id)


def add_to_watchlist(db: Session, user_id: int, keyword: str, max_price: int | None) -> Watchlist:
    return create_watchlist_item(db, user_id=user_id, keyword=keyword, max_price=max_price)


def update_item(
    db: Session,
    user_id: int,
    item_id: int,
    keyword: str | None,
    max_price: int | None,
    is_active: bool | None,
) -> Watchlist:
    item = _get_owned_or_404(db, item_id, user_id)
    updates = {}
    if keyword is not None:
        updates["keyword"] = keyword
    if max_price is not None:
        updates["max_price"] = max_price
    if is_active is not None:
        updates["is_active"] = is_active
    return update_watchlist_item(db, item, **updates)


def remove_item(db: Session, user_id: int, item_id: int) -> None:
    item = _get_owned_or_404(db, item_id, user_id)
    delete_watchlist_item(db, item)


def _get_owned_or_404(db: Session, item_id: int, user_id: int) -> Watchlist:
    item = get_watchlist_item(db, item_id, user_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item
