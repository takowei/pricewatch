"""Alert repository — pure DB access, no business logic."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.alert import Alert


def list_alerts(
    db: Session,
    user_id: int,
    offset: int = 0,
    limit: int = 50,
) -> list[Alert]:
    return list(
        db.exec(
            select(Alert)
            .where(Alert.user_id == user_id)
            .order_by(Alert.created_at.desc())  # type: ignore[union-attr]
            .offset(offset)
            .limit(limit)
        ).all()
    )


def create_alert_if_new(
    db: Session,
    user_id: int,
    watchlist_id: int,
    product_id: int,
    triggered_price: int,
    reason: str,
) -> Alert | None:
    """Insert alert; return None (silently) if the dedup constraint fires."""
    alert = Alert(
        user_id=user_id,
        watchlist_id=watchlist_id,
        product_id=product_id,
        triggered_price=triggered_price,
        reason=reason,
    )
    try:
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert
    except IntegrityError:
        db.rollback()
        return None


def mark_notified(db: Session, alert_id: int) -> None:
    alert = db.get(Alert, alert_id)
    if alert:
        alert.is_notified = True
        db.add(alert)
        db.commit()
