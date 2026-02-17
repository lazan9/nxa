"""Scrapers for heureka.cz (Czech Republic) and heureka.sk (Slovakia)."""

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


class HeurekaScraper(BaseScraper):
    """Base scraper for Heureka sites (CZ and SK share the same structure)."""

    # Popular categories for discovering top products
    CATEGORIES = [
        "lodni-motory",
        "mobilni-telefony",
        "notebooky",
        "tablety",
        "televize",
        "graficke-karty",
        "ssd-disky",
        "monitory",
        "sluchatka",
        "chytre-hodinky",
        "herni-konzole",
        "pracky",
        "kavovary",
        "vysavace",
        "fotoaparaty",
    ]

    def _category_url(self, category: str) -> str:
        """Build full category URL using Heureka's subdomain pattern."""
        # Heureka uses subdomain-based categories: {category}.heureka.{tld}
        # Strip www. from base URL for subdomain construction
        domain = self.base_url.split("//")[1].replace("www.", "")
        return f"https://{category}.{domain}/"

    async def scrape_top_products(self) -> ScrapeResult:
        """Scrape top/popular products from main categories."""
        result = ScrapeResult(
            site=self.SITE_KEY, country=self.COUNTRY, url=self.base_url
        )

        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Scrape main page
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

            # Scrape top categories (sorted by popularity/top)
            for cat in self.CATEGORIES:
                if self.max_products and len(result.products) >= self.max_products:
                    break
                try:
                    url = self._category_url(cat)
                    html = await self.fetch_page(url, client)
                    soup = self._parse(html)
                    products = self._extract_products(soup, cat)
                    take = 10
                    if self.max_products:
                        take = min(take, self.max_products - len(result.products))
                    for i, p in enumerate(products[:take]):
                        p.rank = i + 1
                    result.products.extend(products[:take])
                    logger.info(
                        f"[{self.SITE_KEY}] {cat}: {len(products[:take])} products"
                    )
                    await asyncio.sleep(self.delay)
                except Exception as e:
                    result.errors.append(f"Category {cat}: {e}")
                    logger.error(f"[{self.SITE_KEY}] {cat}: {e}")

        return result

    async def scrape_category(self, category_url: str) -> ScrapeResult:
        """Scrape products from a category URL."""
        result = ScrapeResult(
            site=self.SITE_KEY, country=self.COUNTRY, url=category_url
        )

        async with httpx.AsyncClient(follow_redirects=True) as client:
            page = 1
            while True:
                url = f"{category_url}?f={page}" if page > 1 else category_url
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
        """Search for a product on Heureka."""
        url = f"{self.base_url}/?h%5Bfraze%5D={query}"
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
        """Extract products from a Heureka page."""
        products = []

        # Heureka uses several container patterns
        containers = soup.select(
            self.selectors.get(
                "product_list",
                "[data-testid='product-card'], "
                ".c-product__wrap, "
                ".product-list__item, "
                "article.c-product"
            )
        )

        # Fallback: try generic product containers
        if not containers:
            containers = soup.select(
                "[class*='product'], [class*='Product'], "
                "[data-product], article"
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
        """Parse a product element."""
        # Name
        name_el = el.select_one(
            self.selectors.get(
                "product_name",
                "[data-testid='product-card-title'], "
                ".c-product__title a, "
                "h2 a, h3 a, .product-name a"
            )
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
            self.selectors.get(
                "product_price",
                "[data-testid='product-card-price'], "
                ".c-product__price, "
                ".product-price, .price"
            )
        )
        price = self._parse_price(price_el.get_text() if price_el else "")

        # Image
        img_el = el.select_one(
            self.selectors.get(
                "product_image",
                "[data-testid='product-card-image'] img, "
                ".c-product__img img, "
                "img[src], img[data-src]"
            )
        )
        image_url = ""
        if img_el:
            image_url = str(
                img_el.get("src", img_el.get("data-src", ""))
            )

        # ID
        product_id = self._extract_id(el) or ""

        # Rating
        rating = None
        rating_el = el.select_one(
            "[data-testid='product-card-rating'], .c-star-rating, .rating"
        )
        if rating_el:
            rating_text = (
                rating_el.get("data-rating")
                or rating_el.get("title", "")
                or rating_el.get_text()
            )
            match = re.search(r"(\d[,.]?\d?)", str(rating_text))
            if match:
                try:
                    rating = float(match.group(1).replace(",", "."))
                except ValueError:
                    pass

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
            rating=rating,
        )


class HeurekaCzScraper(HeurekaScraper):
    SITE_KEY = "heureka_cz"
    COUNTRY = "CZ"
    BASE_URL = "https://www.heureka.cz"
    CURRENCY = "CZK"


class HeurekaSkScraper(HeurekaScraper):
    SITE_KEY = "heureka_sk"
    COUNTRY = "SK"
    BASE_URL = "https://www.heureka.sk"
    CURRENCY = "EUR"

    CATEGORIES = [
        "lodne-motory",
        "mobilne-telefony",
        "notebooky",
        "tablety",
        "televizory",
        "graficke-karty",
        "ssd-disky",
        "monitory",
        "sluchadla",
        "smart-hodinky",
        "herne-konzoly",
        "pracky",
        "kavovary",
        "vysavace",
        "fotoaparaty",
    ]
