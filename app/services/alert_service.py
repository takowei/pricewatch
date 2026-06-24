"""Alert detection service.

Core design: detect_alerts() is a PURE FUNCTION.
  Inputs:  products (list), history (dict keyed by product_id), watchlists (list)
  Output:  list of PendingAlert dataclass
  No DB, no HTTP — fully unit-testable without any fixture.

DB persistence is handled separately in persist_alerts().
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from sqlmodel import Session

from app.models.price_history import PriceHistory
from app.models.product import Product
from app.models.watchlist import Watchlist
from app.repositories.alert_repo import create_alert_if_new

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PendingAlert:
    user_id: int
    watchlist_id: int
    product_id: int
    triggered_price: int
    reason: str  # "at_target" | "price_drop"


# ── Pure detection logic ──────────────────────────────────────────────────────


def _prev_price(history: list[PriceHistory], today: date) -> int | None:
    """Return the most recent sale_price recorded before *today*, or None."""
    for record in reversed(history):
        if record.recorded_date != today and record.sale_price is not None:
            return record.sale_price
    return None


def detect_alerts(
    products: list[Product],
    history_map: dict[int, list[PriceHistory]],
    watchlists: list[Watchlist],
    today: date,
) -> list[PendingAlert]:
    """Pure function: match products against watchlists; return triggered alerts.

    Args:
        products:    All products to check (typically those scraped today).
        history_map: {product_id: [PriceHistory...]} sorted oldest-first.
        watchlists:  All active watchlists (any user).
        today:       The date considered "today" for price-drop detection.

    Returns:
        List of PendingAlert (may contain duplicates across watchlists/users;
        DB unique constraint handles dedup on persist).
    """
    alerts: list[PendingAlert] = []

    for product in products:
        sale = product.current_sale_price
        if sale is None:
            continue

        name_text = f"{product.name} {product.category}".lower()
        history = history_map.get(product.id or 0, [])
        prev = _prev_price(history, today)

        for wl in watchlists:
            if not wl.is_active:
                continue
            if wl.keyword.lower() not in name_text:
                continue

            reason: str | None = None

            at_target = wl.max_price is None or sale <= wl.max_price
            if at_target:
                reason = "at_target"

            if prev is not None and sale < prev:
                # price_drop takes precedence for notification copy
                reason = "price_drop"

            if reason is not None:
                alerts.append(
                    PendingAlert(
                        user_id=wl.user_id,
                        watchlist_id=wl.id,  # type: ignore[arg-type]
                        product_id=product.id,  # type: ignore[arg-type]
                        triggered_price=sale,
                        reason=reason,
                    )
                )

    return alerts


# ── DB persistence ────────────────────────────────────────────────────────────


def persist_alerts(db: Session, pending: list[PendingAlert]) -> int:
    """Write new alerts to DB; silently skips duplicates via unique constraint.

    Returns count of newly inserted alerts.
    """
    inserted = 0
    for p in pending:
        result = create_alert_if_new(
            db,
            user_id=p.user_id,
            watchlist_id=p.watchlist_id,
            product_id=p.product_id,
            triggered_price=p.triggered_price,
            reason=p.reason,
        )
        if result is not None:
            inserted += 1

    logger.info("persist_alerts: %d new / %d total pending", inserted, len(pending))
    return inserted
