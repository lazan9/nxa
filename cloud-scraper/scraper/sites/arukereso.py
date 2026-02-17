"""Scraper for arukereso.hu (Hungary) - Heureka Group."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional

import httpx
from bs4 import Tag

from ..models import Offer, Product, ScrapeResult
from .base import BaseScraper

logger = logging.getLogger(__name__)


class ArukeresoScraper(BaseScraper):
    SITE_KEY = "arukereso"
    COUNTRY = "HU"
    BASE_URL = "https://www.arukereso.hu"
    CURRENCY = "HUF"

    # Known top category URLs on arukereso.hu for discovering hot products
    TOP_CATEGORIES = [
        "/mobiltelefon-c3277/",
        "/notebook-c3100/",
        "/tablet-c3340/",
        "/led-tv-c3498/",
        "/videokartya-c3142/",
        "/ssd-c3498/",
        "/monitor-c3130/",
        "/fejhallgato-c3389/",
        "/okosora-c3635/",
        "/jatekkonzol-c3378/",
        "/haztartasi-nagygep-c3015/",
        "/kavefozoek-c3028/",
        "/porszivo-c3019/",
        "/fenykepezo-c3199/",
    ]

    async def scrape_top_products(self) -> ScrapeResult:
        """Scrape hot/top selling products from the main page and top categories."""
        result = ScrapeResult(
            site=self.SITE_KEY, country=self.COUNTRY, url=self.base_url
        )

        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Scrape the main page for featured/top products
            try:
                html = await self.fetch_page(self.base_url, client)
                soup = self._parse(html)
                main_products = self._extract_main_page_products(soup)
                result.products.extend(main_products)
                logger.info(
                    f"[{self.SITE_KEY}] Found {len(main_products)} products on main page"
                )
            except Exception as e:
                result.errors.append(f"Main page error: {e}")
                logger.error(f"[{self.SITE_KEY}] Main page error: {e}")

            # Scrape top categories for bestsellers (sorted by popularity)
            for cat_path in self.TOP_CATEGORIES:
                if self.max_products and len(result.products) >= self.max_products:
                    break
                try:
                    # Add popularity sort parameter
                    url = self.base_url + cat_path + "?orderby=3"
                    html = await self.fetch_page(url, client)
                    soup = self._parse(html)
                    products = self._extract_category_products(soup, cat_path)
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
                    result.errors.append(f"Category {cat_path} error: {e}")
                    logger.error(f"[{self.SITE_KEY}] Category {cat_path}: {e}")

        return result

    async def scrape_category(self, category_url: str) -> ScrapeResult:
        """Scrape all products from a category URL with pagination."""
        result = ScrapeResult(
            site=self.SITE_KEY, country=self.COUNTRY, url=category_url
        )

        async with httpx.AsyncClient(follow_redirects=True) as client:
            # First get total count
            html = await self.fetch_page(category_url, client)
            soup = self._parse(html)

            count_el = soup.select_one(self.selectors.get("product_count", ""))
            total = 0
            if count_el:
                match = re.search(r"(\d[\d\s]*)", count_el.get_text())
                if match:
                    total = int(match.group(1).replace(" ", ""))

            products = self._extract_category_products(soup)
            result.products.extend(products)

            # Paginate
            page = self.pagination_step
            while page < total:
                base = category_url.split("?")[0]
                url = f"{base}?{self.pagination_param}={page}"
                try:
                    html = await self.fetch_page(url, client)
                    soup = self._parse(html)
                    batch = self._extract_category_products(soup)
                    if not batch:
                        break
                    result.products.extend(batch)
                    page += self.pagination_step
                    await asyncio.sleep(self.delay)
                except Exception as e:
                    result.errors.append(f"Page {page} error: {e}")
                    break

        return result

    async def search_product(self, query: str) -> ScrapeResult:
        """Search for a product on arukereso.hu."""
        url = f"{self.base_url}/kereses/?q={query}"
        result = ScrapeResult(
            site=self.SITE_KEY, country=self.COUNTRY, url=url
        )

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                html = await self.fetch_page(url, client)
                soup = self._parse(html)
                result.products = self._extract_category_products(soup)
            except Exception as e:
                result.errors.append(f"Search error: {e}")

        return result

    def _extract_main_page_products(self, soup) -> list[Product]:
        """Extract products from the main/home page."""
        products = []
        # Try multiple selectors for main page product listings
        containers = soup.select(
            ".opciok-lista .termek-box, "
            ".product-box, "
            ".top-product-item, "
            "[data-product]"
        )

        for el in containers:
            try:
                product = self._parse_product_element(el)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"[{self.SITE_KEY}] Parse error: {e}")

        return products

    def _extract_category_products(
        self, soup, category: str = ""
    ) -> list[Product]:
        """Extract products from a category listing page."""
        products = []
        containers = soup.select(
            self.selectors.get("product_list", "div.product-box")
        )

        for el in containers:
            try:
                product = self._parse_product_element(el, category)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"[{self.SITE_KEY}] Parse error: {e}")

        return products

    def _parse_product_element(
        self, el: Tag, category: str = ""
    ) -> Optional[Product]:
        """Parse a single product element into a Product model."""
        # Name
        name_el = el.select_one(
            self.selectors.get("product_name", "div.name a, .product-name a, h2 a")
        )
        if not name_el:
            name_el = el.select_one("a[href]")
        if not name_el:
            return None

        name = self._clean_text(name_el.get_text())
        if not name:
            return None

        # URL
        href = name_el.get("href", "")
        url = self._abs_url(str(href))

        # Price
        price_el = el.select_one(
            self.selectors.get("product_price", ".price, .product-price")
        )
        price = self._parse_price(price_el.get_text() if price_el else "")

        # Image
        img_el = el.select_one(
            self.selectors.get("product_image", "img")
        )
        image_url = ""
        if img_el:
            image_url = str(
                img_el.get("src", img_el.get("data-src", img_el.get("data-lazy", "")))
            )
            if image_url:
                image_url = self._abs_url(image_url)

        # ID
        product_id = self._extract_id(el) or self._extract_id(name_el)

        # Rating
        rating = None
        rating_el = el.select_one(".rating, [data-rating]")
        if rating_el:
            rating_text = rating_el.get("data-rating") or rating_el.get_text()
            try:
                rating = float(str(rating_text).replace(",", "."))
            except (ValueError, TypeError):
                pass

        return Product(
            product_id=product_id or url.split("/")[-2] if "/" in url else "",
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
