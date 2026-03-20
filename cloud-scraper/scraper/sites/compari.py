"""Scraper for compari.ro (Romania) - Heureka Group."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional

import httpx
from bs4 import Tag

from ..models import Product, ScrapeResult
from .base import BaseScraper

logger = logging.getLogger(__name__)


class CompariScraper(BaseScraper):
    SITE_KEY = "compari"
    COUNTRY = "RO"
    BASE_URL = "https://www.compari.ro"
    CURRENCY = "RON"

    # NXA.hu product categories: boat motors, boats, water sports, musical instruments
    TOP_CATEGORIES = [
        "/motoare-barca-c3586/",
        "/motoare-electrice-barca-c3597/",
        "/barci-gonflabile-c3587/",
        "/barci-rib-c3598/",
        "/sonar-fishfinder-c3589/",
        "/echipament-navigatie-c3591/",
        "/accesorii-barca-c3592/",
        "/echipament-pescuit-c3599/",
        "/sup-paddleboard-c3593/",
        "/schi-nautic-wakeboard-c3594/",
        "/jucarii-acvatice-tractabile-c3595/",
        "/remorca-barca-c3600/",
        "/chitara-acustica-c3400/",
        "/chitara-electrica-c3401/",
        "/chitara-bass-c3402/",
        "/tobe-percutie-c3403/",
    ]

    async def scrape_top_products(self) -> ScrapeResult:
        """Scrape top/popular products from compari.ro."""
        result = ScrapeResult(
            site=self.SITE_KEY, country=self.COUNTRY, url=self.base_url
        )

        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Main page
            try:
                html = await self.fetch_page(self.base_url, client)
                soup = self._parse(html)
                main_products = self._extract_products(soup)
                result.products.extend(main_products)
                logger.info(
                    f"[{self.SITE_KEY}] Main page: {len(main_products)} products"
                )
            except Exception as e:
                result.errors.append(f"Main page: {e}")

            # Top categories sorted by popularity
            for cat_path in self.TOP_CATEGORIES:
                if self.max_products and len(result.products) >= self.max_products:
                    break
                try:
                    url = self.base_url + cat_path + "?orderby=3"
                    html = await self.fetch_page(url, client)
                    soup = self._parse(html)
                    products = self._extract_products(soup, cat_path)
                    take = 10
                    if self.max_products:
                        take = min(take, self.max_products - len(result.products))
                    for i, p in enumerate(products[:take]):
                        p.rank = i + 1
                    result.products.extend(products[:take])
                    logger.info(
                        f"[{self.SITE_KEY}] {cat_path}: {len(products[:take])} products"
                    )
                    await asyncio.sleep(self.delay)
                except Exception as e:
                    result.errors.append(f"Category {cat_path}: {e}")

        return result

    async def scrape_category(self, category_url: str) -> ScrapeResult:
        """Scrape a category with pagination."""
        result = ScrapeResult(
            site=self.SITE_KEY, country=self.COUNTRY, url=category_url
        )

        async with httpx.AsyncClient(follow_redirects=True) as client:
            page = 0
            while True:
                url = (
                    f"{category_url}?start={page}"
                    if page > 0
                    else category_url
                )
                try:
                    html = await self.fetch_page(url, client)
                    soup = self._parse(html)
                    products = self._extract_products(soup)
                    if not products:
                        break
                    result.products.extend(products)
                    page += self.pagination_step
                    await asyncio.sleep(self.delay)
                except Exception as e:
                    result.errors.append(f"Page {page}: {e}")
                    break

        return result

    async def search_product(self, query: str) -> ScrapeResult:
        """Search for a product on compari.ro."""
        url = f"{self.base_url}/cautare/?q={query}"
        result = ScrapeResult(
            site=self.SITE_KEY, country=self.COUNTRY, url=url
        )

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                html = await self.fetch_page(url, client)
                soup = self._parse(html)
                result.products = self._extract_products(soup)
            except Exception as e:
                result.errors.append(f"Search error: {e}")

        return result

    def _extract_products(self, soup, category: str = "") -> list[Product]:
        """Extract products from a Compari page (shares structure with arukereso)."""
        products = []
        containers = soup.select(
            "div.product-box, "
            ".product-list-item, "
            "[data-product], "
            ".search-result-item"
        )

        for el in containers:
            try:
                product = self._parse_product(el, category)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"[{self.SITE_KEY}] Parse error: {e}")

        return products

    def _parse_product(self, el: Tag, category: str = "") -> Optional[Product]:
        name_el = el.select_one("div.name a, .product-name a, h2 a, h3 a, a[href]")
        if not name_el:
            return None

        name = self._clean_text(name_el.get_text())
        if not name or len(name) < 3:
            return None

        href = name_el.get("href", "")
        url = self._abs_url(str(href))

        price_el = el.select_one(".price, .product-price, .price-format")
        price = self._parse_price(price_el.get_text() if price_el else "")

        img_el = el.select_one("img.product-image, img[src], img[data-src]")
        image_url = ""
        if img_el:
            image_url = str(img_el.get("src", img_el.get("data-src", "")))
            if image_url:
                image_url = self._abs_url(image_url)

        product_id = self._extract_id(el) or ""

        return Product(
            product_id=product_id,
            name=name,
            url=url,
            country=self.COUNTRY,
            site=self.SITE_KEY,
            category=category,
            price_min=price,
            currency=self.CURRENCY,
            image_url=image_url,
        )
