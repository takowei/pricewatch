"""Integration: scrape→ingest→detect→persist pipeline (all external IO mocked)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import patch

from sqlmodel import Session

from app.repositories.alert_repo import list_alerts
from app.repositories.product_repo import get_price_history, get_product_by_url
from app.scrapers.base import ScrapedProduct
from app.scrapers.uniqlo import UniqloScraper
from app.services.alert_service import PendingAlert, detect_alerts, persist_alerts
from app.services.ingest_service import ingest_products
from tests.factories import make_product, make_user, make_watchlist


def _scraped(
    name: str = "Slim Fit Pants",
    sale_price: int = 590,
    url: str = "https://example.com/p/1",
) -> ScrapedProduct:
    return ScrapedProduct(
        brand="uniqlo",
        category="男裝特價",
        name=name,
        original_price=990,
        sale_price=sale_price,
        discount=40,
        sizes=["M", "L"],
        colors=["Black"],
        image_url="https://example.com/img.jpg",
        product_url=url,
        scraped_at=datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def test_ingest_creates_product_and_price_history(db: Session):
    scraped = [_scraped(name="Jogger Pants", url="https://example.com/p/jogger")]
    count = ingest_products(db, scraped)
    assert count == 1

    product = get_product_by_url(db, "https://example.com/p/jogger")
    assert product is not None
    assert product.current_sale_price == 590

    history = get_price_history(db, product.id)
    assert len(history) == 1
    assert history[0].sale_price == 590


def test_ingest_idempotent_same_day(db: Session):
    """Running ingest twice same day: product updated, history still one record."""
    scraped = [_scraped(url="https://example.com/p/idem")]
    ingest_products(db, scraped)
    ingest_products(db, scraped)

    product = get_product_by_url(db, "https://example.com/p/idem")
    assert len(get_price_history(db, product.id)) == 1


def test_full_pipeline_alert_created(db: Session):
    """Ingest → detect → persist: alert row must appear for matching watchlist."""
    user = make_user(db, email="pipe@b.com", password="pass1234")
    wl = make_watchlist(db, user_id=user.id, keyword="Pants", max_price=800)

    ingest_products(db, [_scraped(name="Slim Fit Pants", url="https://example.com/p/pipe")])

    product = get_product_by_url(db, "https://example.com/p/pipe")
    history_map = {product.id: get_price_history(db, product.id)}

    pending = detect_alerts([product], history_map, [wl], date.today())
    assert len(pending) == 1

    inserted = persist_alerts(db, pending)
    assert inserted == 1

    rows = list_alerts(db, user.id)
    assert len(rows) == 1
    assert rows[0].triggered_price == 590
    assert rows[0].reason == "at_target"


def test_persist_alerts_dedup(db: Session):
    """Calling persist_alerts twice with same data: second call inserts 0."""
    user = make_user(db, email="dedup@b.com", password="pass1234")
    wl = make_watchlist(db, user_id=user.id, keyword="Pants", max_price=800)
    product = make_product(db, product_url="https://example.com/p/dedup")

    pending = [
        PendingAlert(
            user_id=user.id,
            watchlist_id=wl.id,
            product_id=product.id,
            triggered_price=590,
            reason="at_target",
        )
    ]
    first = persist_alerts(db, pending)
    second = persist_alerts(db, pending)
    assert first == 1
    assert second == 0


def test_uniqlo_scraper_run_is_mocked():
    """Verify scraper can be mocked cleanly — no real HTTP in tests."""
    fake = [_scraped(name="Mock Item", url="https://example.com/mock")]
    with patch.object(UniqloScraper, "run", return_value=fake):
        scraper = UniqloScraper()
        result = scraper.run()
    assert len(result) == 1
    assert result[0].name == "Mock Item"
