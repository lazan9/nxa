"""Scrapers for geizhals.at (Austria) and geizhals.de (Germany)."""

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


class GeizhalsBaseScraper(BaseScraper):
    """Base scraper for Geizhals sites (AT and DE share the same structure).

    Geizhals has a dedicated /?cat=top100 page listing the most popular products.
    """

    # Additional category codes for deeper scraping
    CATEGORY_CODES = {
        "smartphones": "smartphones",
        "notebooks": "nb",
        "tablets": "tablet",
        "tvs": "tvlcd",
        "gpus": "gra16_512",
        "ssds": "sm_ssd",
        "monitors": "monlcd19wide",
        "headphones": "kh",
        "smartwatches": "umhr",
        "gaming_consoles": "konsolen",
        "washing_machines": "wasch",
        "coffee_machines": "kaffeevoll",
        "vacuum_cleaners": "staubsauger",
        "cameras": "dkam",
    }

    async def scrape_top_products(self) -> ScrapeResult:
        """Scrape the Top-100 page and category top lists."""
        result = ScrapeResult(
            site=self.SITE_KEY,
            country=self.COUNTRY,
            url=f"{self.base_url}/?cat=top100",
        )

        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Top-100 page
            try:
                url = f"{self.base_url}/?cat=top100"
                html = await self.fetch_page(url, client)
                soup = self._parse(html)
                products = self._extract_top100(soup)
                for i, p in enumerate(products):
                    p.rank = i + 1
                result.products.extend(products)
                logger.info(
                    f"[{self.SITE_KEY}] Top-100: {len(products)} products"
                )
            except Exception as e:
                result.errors.append(f"Top-100 page: {e}")
                logger.error(f"[{self.SITE_KEY}] Top-100: {e}")

            # Category pages for additional top products
            for cat_name, cat_code in self.CATEGORY_CODES.items():
                try:
                    url = f"{self.base_url}/?cat={cat_code}"
                    html = await self.fetch_page(url, client)
                    soup = self._parse(html)
                    products = self._extract_category(soup, cat_name)
                    result.products.extend(products[:10])
                    logger.info(
                        f"[{self.SITE_KEY}] {cat_name}: {len(products[:10])} products"
                    )
                    await asyncio.sleep(self.delay)
                except Exception as e:
                    result.errors.append(f"Category {cat_name}: {e}")

        return result

    async def scrape_category(self, category_url: str) -> ScrapeResult:
        """Scrape a category page with pagination."""
        result = ScrapeResult(
            site=self.SITE_KEY, country=self.COUNTRY, url=category_url
        )

        async with httpx.AsyncClient(follow_redirects=True) as client:
            page = 1
            while True:
                url = f"{category_url}&pg={page}" if page > 1 else category_url
                try:
                    html = await self.fetch_page(url, client)
                    soup = self._parse(html)
                    products = self._extract_category(soup)
                    if not products:
                        break
                    result.products.extend(products)
                    page += 1
                    await asyncio.sleep(self.delay)
                except Exception as e:
                    result.errors.append(f"Page {page}: {e}")
                    break

        return result

    async def search_product(self, query: str) -> ScrapeResult:
        """Search for a product on Geizhals."""
        url = f"{self.base_url}/?fs={query}"
        result = ScrapeResult(
            site=self.SITE_KEY, country=self.COUNTRY, url=url
        )

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                html = await self.fetch_page(url, client)
                soup = self._parse(html)
                result.products = self._extract_category(soup)
            except Exception as e:
                result.errors.append(f"Search error: {e}")

        return result

    def _extract_top100(self, soup) -> list[Product]:
        """Extract products from the Top-100 page."""
        products = []

        # Geizhals top-100 uses a list/table structure
        items = soup.select(
            ".productlist__product, "
            ".listview__item, "
            "tr.productlist__product, "
            ".product-list__item, "
            "[class*='productlist'], "
            ".cat_list .cat_list-element"
        )

        # Fallback: try link-based extraction
        if not items:
            items = soup.select(
                "div.listview, .cat_list"
            )
            if items:
                items = items[0].select("a[href*='/a']")

        for el in items:
            try:
                product = self._parse_geizhals_product(el)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"[{self.SITE_KEY}] Top100 parse error: {e}")

        return products

    def _extract_category(self, soup, category: str = "") -> list[Product]:
        """Extract products from a category listing."""
        products = []
        items = soup.select(
            ".productlist__product, "
            ".listview__item, "
            "tr.productlist__product, "
            ".cat_list .cat_list-element, "
            "[class*='productlist']"
        )

        for el in items:
            try:
                product = self._parse_geizhals_product(el, category)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"[{self.SITE_KEY}] Category parse error: {e}")

        return products

    def _parse_geizhals_product(
        self, el: Tag, category: str = ""
    ) -> Optional[Product]:
        """Parse a Geizhals product element."""
        # Name
        name_el = el.select_one(
            ".productlist__name a, "
            ".listview__name a, "
            ".cat_list-element__name a, "
            "a.productlist__link, "
            "a[href*='/a']"
        )
        if not name_el:
            return None

        name = self._clean_text(name_el.get_text())
        if not name or len(name) < 3:
            return None

        # URL
        href = name_el.get("href", "")
        url = self._abs_url(str(href))

        # Price
        price_el = el.select_one(
            ".productlist__price, "
            ".listview__price, "
            ".cat_list-element__price, "
            "[class*='price']"
        )
        price = None
        if price_el:
            price_text = price_el.get_text()
            price = self._parse_price(price_text)

        # Image
        img_el = el.select_one(
            ".productlist__image img, "
            ".listview__image img, "
            "img[src*='gzhls'], "
            "img"
        )
        image_url = ""
        if img_el:
            image_url = str(img_el.get("src", img_el.get("data-src", "")))
            if image_url:
                image_url = self._abs_url(image_url)

        # ID from URL (geizhals uses /a{id}.html pattern)
        product_id = ""
        id_match = re.search(r"/a(\d+)\.html", url)
        if id_match:
            product_id = id_match.group(1)
        else:
            product_id = self._extract_id(el)

        # Offer count
        offers_el = el.select_one(
            ".productlist__offers, [class*='offer']"
        )
        review_count = None
        if offers_el:
            match = re.search(r"(\d+)", offers_el.get_text())
            if match:
                review_count = int(match.group(1))

        return Product(
            product_id=product_id or "",
            name=name,
            url=url,
            country=self.COUNTRY,
            site=self.SITE_KEY,
            category=category,
            price_min=price,
            currency=self.CURRENCY,
            image_url=image_url,
            review_count=review_count,
        )


class GeizhalsAtScraper(GeizhalsBaseScraper):
    SITE_KEY = "geizhals_at"
    COUNTRY = "AT"
    BASE_URL = "https://geizhals.at"
    CURRENCY = "EUR"


class GeizhalsDecraper(GeizhalsBaseScraper):
    SITE_KEY = "geizhals_de"
    COUNTRY = "DE"
    BASE_URL = "https://geizhals.de"
    CURRENCY = "EUR"
