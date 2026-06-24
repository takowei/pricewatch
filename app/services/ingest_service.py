"""Ingest service — scraper output → upsert products + price_history.

Keeps service layer clean: no HTTP, no business logic beyond mapping.
Repository calls are the only DB touch points.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone

from sqlmodel import Session

from app.repositories.product_repo import upsert_price_history, upsert_product
from app.scrapers.base import ScrapedProduct

logger = logging.getLogger(__name__)


def _today_utc() -> date:
    return datetime.now(tz=timezone.utc).date()


def ingest_products(db: Session, scraped: list[ScrapedProduct]) -> int:
    """Upsert products and today's price_history records.

    Returns the number of products processed.
    """
    today = _today_utc()
    count = 0
    for item in scraped:
        product_data = {
            "brand": item.brand,
            "name": item.name,
            "category": item.category,
            "product_url": item.product_url,
            "image_url": item.image_url,
            "current_sale_price": item.sale_price,
            "original_price": item.original_price,
            "discount": item.discount,
            "last_scraped_at": datetime.now(tz=timezone.utc),
        }
        product = upsert_product(db, product_data)
        upsert_price_history(
            db,
            product_id=product.id,  # type: ignore[arg-type]
            sale_price=item.sale_price,
            discount=item.discount,
            recorded_date=today,
        )
        count += 1

    logger.info("ingest: processed %d products", count)
    return count
