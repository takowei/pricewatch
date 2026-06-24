"""NET Taiwan scraper — adapted from sale-tracker/scrapers/net_scraper.py.

Personal/research use only. Respects robots.txt.
Rate-limited to ≥0.75 s between requests.
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any

import requests
from bs4 import BeautifulSoup

from app.scrapers.base import ScrapedProduct

logger = logging.getLogger(__name__)

_HUB_URL = "https://www.net-fashion.net/promotion/658"
_PROMO_BASE = "https://www.net-fashion.net/promotion/"
_MEN_CATEGORY_ID = 2
_REQUEST_INTERVAL = 0.75

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _get_soup(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except requests.RequestException as exc:
        logger.warning("NET fetch failed %s: %s", url, exc)
        return None


def _extract_promotions_map(soup: BeautifulSoup) -> dict[int, list[dict]]:
    for script in soup.find_all("script"):
        text = script.string or ""
        if "promotions:" not in text:
            continue
        m = re.search(r"promotions:\s*(\{.*?\})\s*,\s*\n\s*\w+:", text, re.DOTALL)
        if not m:
            continue
        try:
            raw: dict[str, list] = json.loads(m.group(1))
            return {int(k): v for k, v in raw.items() if k.isdigit()}
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("NET promotions parse error: %s", exc)
    return {}


def _extract_promotion_name(soup: BeautifulSoup) -> str:
    for script in soup.find_all("script"):
        text = script.string or ""
        if "var getPromotionData" not in text:
            continue
        m = re.search(r'name:\s*"([^"]+)"', text)
        if m:
            try:
                return json.loads(f'"{m.group(1)}"')
            except json.JSONDecodeError:
                return m.group(1)
    return "男裝特價"


def _extract_products(soup: BeautifulSoup) -> list[dict]:
    for script in soup.find_all("script"):
        text = script.string or ""
        if "promotionProducts" not in text:
            continue
        idx = text.find("promotionProducts: [")
        if idx == -1:
            continue
        idx += len("promotionProducts: ")
        try:
            products, _ = json.JSONDecoder().raw_decode(text, idx)
            return products
        except json.JSONDecodeError as exc:
            logger.warning("NET products parse error: %s", exc)
    return []


def _parse_product(
    raw: dict[str, Any], category: str, scraped_at: str, promo_url: str
) -> ScrapedProduct:
    original = int(float(raw.get("fake_price", 0)))
    sale = int(float(raw.get("promotion_price", original)))
    discount = round((1 - sale / original) * 100) if original > 0 else 0

    sizes_raw = raw.get("sizes", [])
    seen_sizes: list[str] = []
    seen_colors: list[str] = []
    for s in sizes_raw:
        sz = s.get("size", "")
        if sz and sz not in seen_sizes:
            seen_sizes.append(sz)
        color = re.sub(r"^\d+", "", s.get("color", "")).strip()
        if color and color not in seen_colors:
            seen_colors.append(color)

    return ScrapedProduct(
        brand="net",
        category=category,
        name=raw.get("name", ""),
        original_price=original,
        sale_price=sale,
        discount=discount,
        sizes=seen_sizes,
        colors=seen_colors,
        image_url=raw.get("image400", {}).get("file_name", ""),
        product_url=promo_url,
        scraped_at=scraped_at,
    )


def _scrape_promotion(promo_id: int, scraped_at: str) -> list[ScrapedProduct]:
    url = f"{_PROMO_BASE}{promo_id}"
    soup = _get_soup(url)
    if soup is None:
        return []
    category = _extract_promotion_name(soup)
    results: list[ScrapedProduct] = []
    seen: set[str] = set()
    for raw in _extract_products(soup):
        pid = str(raw.get("parent_id", ""))
        if pid in seen:
            continue
        seen.add(pid)
        try:
            original = float(raw.get("fake_price", 0))
            promo = float(raw.get("promotion_price", original))
        except (TypeError, ValueError):
            continue
        if promo >= original:
            continue
        results.append(_parse_product(raw, category, scraped_at, url))
    return results


class NetScraper:
    """Implements ScraperProtocol."""

    def run(self) -> list[ScrapedProduct]:
        scraped_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        hub = _get_soup(_HUB_URL)
        if hub is None:
            logger.error("NET hub page unavailable")
            return []
        promo_map = _extract_promotions_map(hub)
        men = promo_map.get(_MEN_CATEGORY_ID, [])
        results: list[ScrapedProduct] = []
        for entry in men:
            results.extend(_scrape_promotion(int(entry["id"]), scraped_at))
            time.sleep(_REQUEST_INTERVAL)
        logger.info("[net] %d products scraped", len(results))
        return results
