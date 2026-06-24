"""Scraper Protocol — defines the interface all brand scrapers must satisfy."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


class ScrapedProduct:
    """Normalised product dict from any scraper.

    Fields mirror sale-tracker's JSON schema so ingest_service needs no
    per-brand mapping.
    """

    __slots__ = (
        "brand",
        "category",
        "name",
        "original_price",
        "sale_price",
        "discount",
        "sizes",
        "colors",
        "image_url",
        "product_url",
        "scraped_at",
    )

    def __init__(
        self,
        *,
        brand: str,
        category: str,
        name: str,
        original_price: int,
        sale_price: int,
        discount: int,
        sizes: list[str],
        colors: list[str],
        image_url: str,
        product_url: str,
        scraped_at: str,
    ) -> None:
        self.brand = brand
        self.category = category
        self.name = name
        self.original_price = original_price
        self.sale_price = sale_price
        self.discount = discount
        self.sizes = sizes
        self.colors = colors
        self.image_url = image_url
        self.product_url = product_url
        self.scraped_at = scraped_at

    def to_dict(self) -> dict:
        return {slot: getattr(self, slot) for slot in self.__slots__}


@runtime_checkable
class ScraperProtocol(Protocol):
    """Any class implementing this can be used as a scraper by ingest_service."""

    def run(self) -> list[ScrapedProduct]:
        """Fetch and parse products; return list of ScrapedProduct."""
        ...
