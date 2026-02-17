"""Scraper for ceneo.pl (Poland)."""

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


class CeneoScraper(BaseScraper):
    SITE_KEY = "ceneo"
    COUNTRY = "PL"
    BASE_URL = "https://www.ceneo.pl"
    CURRENCY = "PLN"

    # Top category paths on ceneo.pl
    TOP_CATEGORIES = [
        "/Silniki_zaburtowe",
        "/Smartfony",
        "/Laptopy",
        "/Tablety",
        "/Telewizory",
        "/Karty_graficzne",
        "/Dyski_SSD",
        "/Monitory",
        "/Sluchawki",
        "/Smartwatche",
        "/Konsole",
        "/Pralki",
        "/Ekspresy_do_kawy",
        "/Odkurzacze",
        "/Aparaty_fotograficzne",
    ]

    async def scrape_top_products(self) -> ScrapeResult:
        """Scrape top/popular products from ceneo.pl."""
        result = ScrapeResult(
            site=self.SITE_KEY, country=self.COUNTRY, url=self.base_url
        )

        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Main page for featured products
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
                logger.error(f"[{self.SITE_KEY}] Main page: {e}")

            # Category pages sorted by popularity
            for cat_path in self.TOP_CATEGORIES:
                if self.max_products and len(result.products) >= self.max_products:
                    break
                try:
                    # ;szukaj-t: sort by popularity on ceneo
                    url = f"{self.base_url}{cat_path};0020-0,,,,d0.htm"
                    html = await self.fetch_page(url, client)
                    soup = self._parse(html)
                    products = self._extract_products(soup, cat_path.strip("/"))
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
                    logger.error(f"[{self.SITE_KEY}] {cat_path}: {e}")

        return result

    async def scrape_category(self, category_url: str) -> ScrapeResult:
        """Scrape products from a category with pagination."""
        result = ScrapeResult(
            site=self.SITE_KEY, country=self.COUNTRY, url=category_url
        )

        async with httpx.AsyncClient(follow_redirects=True) as client:
            page = 1
            while True:
                url = (
                    f"{category_url};0020-0,,,,d0,p{page}.htm"
                    if page > 1
                    else category_url
                )
                try:
                    html = await self.fetch_page(url, client)
                    soup = self._parse(html)
                    products = self._extract_products(soup)
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
        """Search for a product on ceneo.pl."""
        url = f"{self.base_url}/szukaj-{query}"
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
        """Extract products from a Ceneo page."""
        products = []

        # Ceneo uses several container patterns
        containers = soup.select(
            ".cat-prod-row, "
            ".category-list-body .cat-prod-row__content, "
            ".js_category-list-body .cat-prod-row__content, "
            ".product-row, "
            "[data-productid], "
            "[data-pid]"
        )

        # Fallback
        if not containers:
            containers = soup.select(
                "[class*='product'], [class*='prod-row']"
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
        """Parse a Ceneo product element."""
        # Name
        name_el = el.select_one(
            ".cat-prod-row__name a, "
            ".go-to-product, "
            ".product-name a, "
            "a.go-to-product, "
            "strong.cat-prod-row__name, "
            "a[href*='ceneo.pl/']"
        )
        if not name_el:
            name_el = el.select_one("a[href]")
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
            ".cat-prod-row__price .price-format, "
            ".price-format.nowrap, "
            ".product-price, "
            "[class*='price']"
        )
        price = None
        if price_el:
            price = self._parse_price(price_el.get_text())

        # Image
        img_el = el.select_one(
            ".cat-prod-row__foto img, "
            ".lazy-image, "
            "img[src], img[data-src], img[data-original]"
        )
        image_url = ""
        if img_el:
            image_url = str(
                img_el.get("src", img_el.get("data-src", img_el.get("data-original", "")))
            )
            if image_url and not image_url.startswith("data:"):
                image_url = self._abs_url(image_url)
            elif image_url.startswith("data:"):
                image_url = ""

        # Product ID
        product_id = (
            str(el.get("data-productid", ""))
            or str(el.get("data-pid", ""))
            or self._extract_id(el)
        )

        # Rating
        rating = None
        rating_el = el.select_one(
            ".product-score, .score-marker, [class*='rating']"
        )
        if rating_el:
            match = re.search(r"(\d[,.]?\d?)", rating_el.get_text())
            if match:
                try:
                    rating = float(match.group(1).replace(",", "."))
                except ValueError:
                    pass

        # Review count
        review_count = None
        reviews_el = el.select_one(
            ".cat-prod-row__opinions, .product-reviews-count, [class*='opinion']"
        )
        if reviews_el:
            match = re.search(r"(\d+)", reviews_el.get_text())
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
            rating=rating,
            review_count=review_count,
        )
