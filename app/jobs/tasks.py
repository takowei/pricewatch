"""Scheduled task: full scrape → ingest → detect alerts → notify pipeline."""

from __future__ import annotations

import logging
from datetime import date

from sqlmodel import Session

from app.db.session import get_engine
from app.repositories.product_repo import get_price_history, list_products
from app.repositories.watchlist_repo import list_all_active_watchlists
from app.scrapers.net_scraper import NetScraper
from app.scrapers.uniqlo import UniqloScraper
from app.services.alert_service import detect_alerts, persist_alerts
from app.services.ingest_service import ingest_products
from app.services.notify_service import notify_pending_alerts

logger = logging.getLogger(__name__)


def scrape_all() -> None:
    """Full pipeline: scrape → ingest → detect alerts → persist → notify.

    This runs as a scheduled job. Creates its own DB session so it is
    independent of any request context.
    """
    logger.info("scrape_all: starting")

    # 1. Scrape
    scraped = []
    for scraper_cls in (UniqloScraper, NetScraper):
        try:
            items = scraper_cls().run()
            scraped.extend(items)
            logger.info("scrape_all: %s returned %d items", scraper_cls.__name__, len(items))
        except Exception:  # noqa: BLE001
            logger.exception("scrape_all: %s failed", scraper_cls.__name__)

    if not scraped:
        logger.warning("scrape_all: no items scraped; aborting pipeline")
        return

    engine = get_engine()
    with Session(engine) as db:
        # 2. Ingest → upsert products + price_history
        ingest_products(db, scraped)

        # 3. Detect alerts
        today = date.today()
        products = list_products(db, limit=10_000)
        history_map = {p.id: get_price_history(db, p.id) for p in products if p.id}
        watchlists = list_all_active_watchlists(db)
        pending = detect_alerts(products, history_map, watchlists, today)

        # 4. Persist (DB unique constraint deduplicates)
        new_count = persist_alerts(db, pending)
        logger.info("scrape_all: %d new alerts inserted", new_count)

        # 5. Telegram notify
        sent = notify_pending_alerts(db)
        logger.info("scrape_all: %d Telegram notifications sent", sent)

    logger.info("scrape_all: complete")
