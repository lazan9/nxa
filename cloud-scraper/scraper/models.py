"""Data models for scraped products and offers."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Offer(BaseModel):
    """A single shop offer for a product."""

    shop_name: str
    price: float
    currency: str
    url: str
    in_stock: Optional[bool] = None
    shipping_cost: Optional[float] = None


class Product(BaseModel):
    """A product scraped from a price comparison site."""

    product_id: str
    name: str
    url: str
    country: str
    site: str
    category: str = ""
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    currency: str = ""
    image_url: str = ""
    rating: Optional[float] = None
    review_count: Optional[int] = None
    rank: Optional[int] = None
    offers: list[Offer] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    extra: dict = Field(default_factory=dict)

    def best_price(self) -> Optional[float]:
        if self.offers:
            return min(o.price for o in self.offers)
        return self.price_min

    def offer_count(self) -> int:
        return len(self.offers)


class ScrapeResult(BaseModel):
    """Result of a scraping session for one site."""

    site: str
    country: str
    url: str
    products: list[Product] = Field(default_factory=list)
    total_found: int = 0
    errors: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    def complete(self):
        self.finished_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = (
                self.finished_at - self.started_at
            ).total_seconds()
        self.total_found = len(self.products)


class ProductQuery(BaseModel):
    """A product to search for (imported from user's SQL/XML/XLSX)."""

    sku: str = ""
    name: str
    ean: str = ""
    brand: str = ""
    category: str = ""
    our_price: Optional[float] = None
    currency: str = ""
    extra: dict = Field(default_factory=dict)
