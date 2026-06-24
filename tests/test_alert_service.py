"""Alert service unit tests — pure function, zero DB dependency."""

from __future__ import annotations

from datetime import date

import pytest

from app.models.price_history import PriceHistory
from app.models.product import Product
from app.models.watchlist import Watchlist
from app.services.alert_service import PendingAlert, detect_alerts

# ── Helpers ───────────────────────────────────────────────────────────────────


def _product(
    pid: int = 1,
    name: str = "Test Pants",
    category: str = "男裝特價",
    sale_price: int = 590,
) -> Product:
    p = Product(
        brand="uniqlo",
        name=name,
        category=category,
        product_url=f"https://example.com/{pid}",
        image_url="",
        current_sale_price=sale_price,
        original_price=990,
        discount=40,
    )
    p.id = pid
    return p


def _history(product_id: int, price: int, day: date) -> PriceHistory:
    ph = PriceHistory(
        product_id=product_id,
        sale_price=price,
        discount=0,
        recorded_date=day,
    )
    return ph


def _watchlist(
    wid: int = 1,
    user_id: int = 1,
    keyword: str = "Pants",
    max_price: int | None = 800,
) -> Watchlist:
    w = Watchlist(user_id=user_id, keyword=keyword, max_price=max_price)
    w.id = wid
    return w


TODAY = date(2026, 6, 24)
YESTERDAY = date(2026, 6, 23)


# ── Tests: at_target ──────────────────────────────────────────────────────────


def test_at_target_when_price_below_max():
    product = _product(sale_price=590)
    wl = _watchlist(max_price=800)
    alerts = detect_alerts([product], {}, [wl], TODAY)
    assert len(alerts) == 1
    assert alerts[0].reason == "at_target"
    assert alerts[0].triggered_price == 590


def test_at_target_when_max_price_is_none():
    """max_price=None means: alert whenever on sale."""
    product = _product(sale_price=990)
    wl = _watchlist(max_price=None)
    alerts = detect_alerts([product], {}, [wl], TODAY)
    assert len(alerts) == 1
    assert alerts[0].reason == "at_target"


def test_no_alert_when_above_max_price():
    product = _product(sale_price=1200)
    wl = _watchlist(max_price=800)
    alerts = detect_alerts([product], {}, [wl], TODAY)
    assert alerts == []


# ── Tests: price_drop ─────────────────────────────────────────────────────────


def test_price_drop_detected():
    product = _product(pid=1, sale_price=490)
    history = {1: [_history(1, 590, YESTERDAY)]}
    wl = _watchlist(max_price=None)  # at_target always fires; drop overrides reason
    alerts = detect_alerts([product], history, [wl], TODAY)
    assert len(alerts) == 1
    assert alerts[0].reason == "price_drop"
    assert alerts[0].triggered_price == 490


def test_no_drop_when_price_same():
    product = _product(pid=1, sale_price=590)
    history = {1: [_history(1, 590, YESTERDAY)]}
    wl = _watchlist(max_price=None)
    alerts = detect_alerts([product], history, [wl], TODAY)
    # at_target fires (max_price=None), but NOT price_drop
    assert len(alerts) == 1
    assert alerts[0].reason == "at_target"


def test_no_drop_when_price_increased():
    product = _product(pid=1, sale_price=790)
    history = {1: [_history(1, 590, YESTERDAY)]}
    wl = _watchlist(max_price=None)
    alerts = detect_alerts([product], history, [wl], TODAY)
    assert alerts[0].reason == "at_target"  # not drop


def test_same_day_history_ignored_for_prev_price():
    """Records from today must not count as prev price."""
    product = _product(pid=1, sale_price=490)
    # Only today's record — no previous day available
    history = {1: [_history(1, 590, TODAY)]}
    wl = _watchlist(max_price=None)
    alerts = detect_alerts([product], history, [wl], TODAY)
    assert alerts[0].reason == "at_target"  # no drop detected


# ── Tests: keyword matching ───────────────────────────────────────────────────


def test_keyword_match_is_case_insensitive():
    product = _product(name="Slim Fit Pants", sale_price=600)
    wl = _watchlist(keyword="pants", max_price=800)
    alerts = detect_alerts([product], {}, [wl], TODAY)
    assert len(alerts) == 1


def test_keyword_no_match():
    product = _product(name="Knit Sweater", sale_price=490)
    wl = _watchlist(keyword="pants", max_price=800)
    alerts = detect_alerts([product], {}, [wl], TODAY)
    assert alerts == []


def test_keyword_matches_category():
    product = _product(name="UV Cut Shirt", category="男裝特價 pants", sale_price=490)
    wl = _watchlist(keyword="pants", max_price=800)
    alerts = detect_alerts([product], {}, [wl], TODAY)
    assert len(alerts) == 1


# ── Tests: multi-user, multi-watchlist ───────────────────────────────────────


def test_multiple_watchlists_same_product():
    product = _product(pid=1, name="Jogger Pants", sale_price=590)
    wl1 = _watchlist(wid=1, user_id=1, keyword="Pants", max_price=800)
    wl2 = _watchlist(wid=2, user_id=2, keyword="Jogger", max_price=700)
    alerts = detect_alerts([product], {}, [wl1, wl2], TODAY)
    assert len(alerts) == 2
    user_ids = {a.user_id for a in alerts}
    assert user_ids == {1, 2}


def test_inactive_watchlist_skipped():
    product = _product(sale_price=590)
    wl = _watchlist(max_price=800)
    wl.is_active = False
    alerts = detect_alerts([product], {}, [wl], TODAY)
    assert alerts == []


def test_product_with_no_sale_price_skipped():
    product = _product(sale_price=590)
    product.current_sale_price = None
    wl = _watchlist(max_price=800)
    alerts = detect_alerts([product], {}, [wl], TODAY)
    assert alerts == []


# ── Tests: dedup structure ────────────────────────────────────────────────────


def test_pending_alert_is_frozen_dataclass():
    """PendingAlert must be immutable (frozen=True) for safe set usage."""
    a = PendingAlert(
        user_id=1,
        watchlist_id=1,
        product_id=1,
        triggered_price=590,
        reason="at_target",
    )
    from dataclasses import FrozenInstanceError

    with pytest.raises(FrozenInstanceError):
        a.triggered_price = 999  # type: ignore[misc]
