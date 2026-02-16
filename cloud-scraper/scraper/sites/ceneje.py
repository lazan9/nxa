"""Scraper for ceneje.si (Slovenia) - Heureka Group."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx
from bs4 import Tag

from ..models import Product, ScrapeResult
from .base import BaseScraper

logger = logging.getLogger(__name__)


class CenejeScraper(BaseScraper):
    SITE_KEY = "ceneje"
    COUNTRY = "SI"
    BASE_URL = "https://www.ceneje.si"
    CURRENCY = "EUR"

    TOP_CATEGORIES = [
        "/mobilni-telefoni-c3277/",
        "/prenosniki-c3100/",
        "/tablicni-racunalniki-c3340/",
        "/televizorji-c3498/",
        "/graficne-kartice-c3142/",
        "/ssd-diski-c3510/",
        "/monitorji-c3130/",
        "/slusalke-c3389/",
        "/pametne-ure-c3635/",
        "/igralne-konzole-c3378/",
        "/pralni-stroji-c3015/",
        "/kavni-aparati-c3028/",
        "/sesalniki-c3019/",
        "/fotoaparati-c3199/",
    ]

    async def scrape_top_products(self) -> ScrapeResult:
        """Scrape top products from ceneje.si."""
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

            # Top categories
            for cat_path in self.TOP_CATEGORIES:
                try:
                    url = self.base_url + cat_path + "?orderby=3"
                    html = await self.fetch_page(url, client)
                    soup = self._parse(html)
                    products = self._extract_products(soup, cat_path)
                    for i, p in enumerate(products[:10]):
                        p.rank = i + 1
                    result.products.extend(products[:10])
                    logger.info(
                        f"[{self.SITE_KEY}] {cat_path}: {len(products[:10])} products"
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
        """Search for a product on ceneje.si."""
        url = f"{self.base_url}/iskanje/?q={query}"
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
        """Extract products (same structure as arukereso/compari)."""
        products = []
        containers = soup.select(
            "div.product-box, .product-list-item, "
            "[data-product], .search-result-item"
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
