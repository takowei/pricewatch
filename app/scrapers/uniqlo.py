"""UNIQLO Taiwan scraper — adapted from sale-tracker/scrapers/uniqlo_scraper.py.

Personal/research use only. Respects robots.txt (no disallowed paths fetched).
Rate-limited to ≥0.75 s between requests.
"""

from __future__ import annotations

import logging
import math
import time
from datetime import datetime, timezone
from typing import Any

import requests

from app.scrapers.base import ScrapedProduct

logger = logging.getLogger(__name__)

_API_URL = "https://d.uniqlo.com/tw/p/search/products/by-category"
_PAGE_SIZE = 24
_REQUEST_INTERVAL = 0.75

_HEADERS = {
    "accept": "application/json",
    "accept-language": "zh-TW,zh;q=0.9",
    "content-type": "application/json; charset=utf-8",
    "langcode": "zh_TW",
    "origin": "https://www.uniqlo.com",
    "referer": "https://www.uniqlo.com/",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
}

_SIZE_MAP: dict[str, str] = {
    "SMA002": "XS",
    "SMA003": "S",
    "SMA004": "M",
    "SMA005": "L",
    "SMA006": "XL",
    "SMA007": "XXL",
    "SMA008": "3XL",
    "SMA009": "4XL",
    "INS028": "28inch",
    "INS029": "29inch",
    "INS031": "31inch",
    "INS032": "32inch",
    "INS033": "33inch",
    "INS034": "34inch",
}

_CATEGORIES: list[tuple[str, str]] = [
    ("feature-sale-men", "男裝特價"),
    ("feature-sale-men-ut", "UT 印花T恤特價"),
]


def _build_payload(category_code: str, page: int) -> dict[str, Any]:
    return {
        "pageInfo": {"page": page, "pageSize": _PAGE_SIZE},
        "belongTo": "pc",
        "rank": "overall",
        "priceRange": {"low": 0, "high": 0},
        "categoryCode": category_code,
        "color": [],
        "description": "",
        "exist": [],
        "identity": [],
        "size": [],
        "stockFilter": "warehouse",
        "searchFlag": False,
    }


def _parse_colors(style_text: list[str]) -> list[str]:
    return [e.split(" ", 1)[1] if " " in e else e for e in style_text]


def _parse_product(raw: dict[str, Any], category: str, scraped_at: str) -> ScrapedProduct:
    code = raw.get("productCode", raw.get("code", ""))
    original = int(raw.get("originPrice", 0))
    sale = int(raw.get("minPrice", raw.get("originPrice", 0)))
    discount = round((1 - sale / original) * 100) if original > 0 else 0
    main_pic = raw.get("mainPic", "").replace("/hmall/test/", "/hmall/")
    return ScrapedProduct(
        brand="uniqlo",
        category=category,
        name=raw.get("name", ""),
        original_price=original,
        sale_price=sale,
        discount=discount,
        sizes=[_SIZE_MAP.get(s, s) for s in raw.get("size", [])],
        colors=_parse_colors(raw.get("styleText", [])),
        image_url=f"https://www.uniqlo.com{main_pic}" if main_pic else "",
        product_url=(f"https://www.uniqlo.com/tw/zh_TW/product-detail.html?productCode={code}"),
        scraped_at=scraped_at,
    )


def _fetch_page(category_code: str, page: int) -> tuple[list[dict], int]:
    payload = _build_payload(category_code, page)
    try:
        resp = requests.post(_API_URL, headers=_HEADERS, json=payload, timeout=20)
        resp.raise_for_status()
        body = resp.json()["resp"][0]
        return body.get("productList", []), int(body.get("productSum", 0))
    except Exception as exc:  # noqa: BLE001
        logger.warning("UNIQLO fetch error cat=%s page=%d: %s", category_code, page, exc)
        return [], 0


class UniqloScraper:
    """Implements ScraperProtocol."""

    def run(self) -> list[ScrapedProduct]:
        scraped_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        results: list[ScrapedProduct] = []
        seen_urls: set[str] = set()

        for code, label in _CATEGORIES:
            raw_list, total = _fetch_page(code, 1)
            total_pages = math.ceil(total / _PAGE_SIZE) if total else 1
            pages_data = [raw_list] + [
                _fetch_page(code, p)[0]
                for p in range(2, total_pages + 1)
                if not time.sleep(_REQUEST_INTERVAL)  # type: ignore[func-returns-value]
            ]
            for page_products in pages_data:
                for raw in page_products:
                    p = _parse_product(raw, label, scraped_at)
                    if p.product_url not in seen_urls:
                        seen_urls.add(p.product_url)
                        results.append(p)
            time.sleep(_REQUEST_INTERVAL)

        logger.info("[uniqlo] %d unique products scraped", len(results))
        return results
