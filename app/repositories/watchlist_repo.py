"""Watchlist repository — pure DB access, no business logic."""

from __future__ import annotations

from sqlmodel import Session, select

from app.models.watchlist import Watchlist


def get_watchlist_item(db: Session, item_id: int, user_id: int) -> Watchlist | None:
    return db.exec(
        select(Watchlist).where(
            Watchlist.id == item_id,
            Watchlist.user_id == user_id,
        )
    ).first()


def list_watchlist(db: Session, user_id: int) -> list[Watchlist]:
    return list(
        db.exec(
            select(Watchlist)
            .where(Watchlist.user_id == user_id, Watchlist.is_active == True)  # noqa: E712
            .order_by(Watchlist.created_at)
        ).all()
    )


def list_all_active_watchlists(db: Session) -> list[Watchlist]:
    """Used by alert detection — returns every active watchlist across all users."""
    return list(
        db.exec(select(Watchlist).where(Watchlist.is_active == True)).all()  # noqa: E712
    )


def create_watchlist_item(
    db: Session, user_id: int, keyword: str, max_price: int | None
) -> Watchlist:
    item = Watchlist(user_id=user_id, keyword=keyword, max_price=max_price)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_watchlist_item(db: Session, item: Watchlist, **fields) -> Watchlist:
    for key, value in fields.items():
        setattr(item, key, value)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def delete_watchlist_item(db: Session, item: Watchlist) -> None:
    db.delete(item)
    db.commit()
