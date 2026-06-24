"""Watchlist router: CRUD for /watchlist."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.deps import CurrentUser, get_db
from app.schemas.watchlist import (
    WatchlistCreateRequest,
    WatchlistResponse,
    WatchlistUpdateRequest,
)
from app.services import watchlist_service

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=list[WatchlistResponse])
def list_watchlist(current_user: CurrentUser, db: Session = Depends(get_db)) -> list:
    return watchlist_service.get_user_watchlist(db, current_user.id)  # type: ignore[arg-type]


@router.post("", response_model=WatchlistResponse, status_code=201)
def create_item(
    body: WatchlistCreateRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    return watchlist_service.add_to_watchlist(
        db,
        user_id=current_user.id,  # type: ignore[arg-type]
        keyword=body.keyword,
        max_price=body.max_price,
    )


@router.patch("/{item_id}", response_model=WatchlistResponse)
def update_item(
    item_id: int,
    body: WatchlistUpdateRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    return watchlist_service.update_item(
        db,
        user_id=current_user.id,  # type: ignore[arg-type]
        item_id=item_id,
        keyword=body.keyword,
        max_price=body.max_price,
        is_active=body.is_active,
    )


@router.delete("/{item_id}", status_code=204)
def delete_item(
    item_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> None:
    watchlist_service.remove_item(
        db,
        user_id=current_user.id,  # type: ignore[arg-type]
        item_id=item_id,
    )
