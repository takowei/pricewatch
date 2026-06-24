"""Admin router: manual scrape trigger (demo/dev only)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.deps import CurrentUser, get_db
from app.scrapers.net_scraper import NetScraper
from app.scrapers.uniqlo import UniqloScraper
from app.services.ingest_service import ingest_products

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/scrape")
def trigger_scrape(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> dict:
    """Manually trigger scrape + ingest (requires auth; any active user in demo)."""
    total = 0
    for scraper in (UniqloScraper(), NetScraper()):
        try:
            products = scraper.run()
            total += ingest_products(db, products)
        except Exception as exc:  # noqa: BLE001
            logger.error("Scrape error %s: %s", type(scraper).__name__, exc)
    return {"ingested": total}
