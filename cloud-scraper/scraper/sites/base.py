"""Base scraper class with common functionality."""

from __future__ import annotations

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import Offer, Product, ScrapeResult

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all site scrapers."""

    SITE_KEY: str = ""
    COUNTRY: str = ""
    BASE_URL: str = ""
    CURRENCY: str = ""

    def __init__(self, config: dict, use_playwright: bool = False):
        self.config = config
        self.use_playwright = use_playwright
        self.ua = UserAgent()
        self.delay = config.get("defaults", {}).get("request_delay_ms", 1500) / 1000
        self.max_retries = config.get("defaults", {}).get("max_retries", 3)
        self.timeout = config.get("defaults", {}).get("timeout_seconds", 30)
        self.proxy = config.get("defaults", {}).get("proxy")

        site_cfg = config.get("sites", {}).get(self.SITE_KEY, {})
        self.selectors = site_cfg.get("selectors", {})
        self.base_url = site_cfg.get("base_url", self.BASE_URL)
        self.top_path = site_cfg.get("top_products_path", "/")
        self.pagination_param = site_cfg.get("pagination_param", "start")
        self.pagination_step = site_cfg.get("pagination_step", 25)

    def _headers(self) -> dict:
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": f"{self.COUNTRY.lower()},en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _fetch(self, url: str, client: httpx.AsyncClient) -> str:
        """Fetch a URL and return HTML content."""
        logger.info(f"[{self.SITE_KEY}] Fetching: {url}")
        resp = await client.get(
            url,
            headers=self._headers(),
            timeout=self.timeout,
            follow_redirects=True,
        )
        resp.raise_for_status()
        return resp.text

    async def _fetch_with_playwright(self, url: str) -> str:
        """Fetch using Playwright for JS-rendered pages."""
        from playwright.async_api import async_playwright

        logger.info(f"[{self.SITE_KEY}] Playwright fetch: {url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent=self.ua.random,
                locale=f"{self.COUNTRY.lower()}-{self.COUNTRY}",
            )
            page = await ctx.new_page()
            await page.goto(url, wait_until="networkidle", timeout=self.timeout * 1000)
            content = await page.content()
            await browser.close()
            return content

    async def fetch_page(self, url: str, client: httpx.AsyncClient) -> str:
        """Fetch page, falling back to Playwright if needed."""
        try:
            html = await self._fetch(url, client)
            if self.use_playwright and self._is_js_blocked(html):
                html = await self._fetch_with_playwright(url)
            return html
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (403, 429) and self.use_playwright:
                logger.warning(
                    f"[{self.SITE_KEY}] HTTP {e.response.status_code}, trying Playwright"
                )
                return await self._fetch_with_playwright(url)
            raise

    def _is_js_blocked(self, html: str) -> bool:
        """Check if the response is a JS challenge/CAPTCHA page."""
        indicators = [
            "enable javascript",
            "captcha",
            "challenge-platform",
            "cf-browser-verification",
            "just a moment",
        ]
        lower = html.lower()
        return any(i in lower for i in indicators) and len(html) < 5000

    def _parse(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    def _abs_url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return urljoin(self.base_url, path)

    @staticmethod
    def _parse_price(text: str) -> Optional[float]:
        """Parse European-style price strings like '12 345,67 Ft'."""
        if not text:
            return None
        cleaned = re.sub(r"[^\d,.\s]", "", text.strip())
        cleaned = re.sub(r"\s+", "", cleaned)
        # Handle European format: 1.234,56 or 1234,56
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")
        try:
            return round(float(cleaned), 2)
        except ValueError:
            return None

    @staticmethod
    def _clean_text(text: Optional[str]) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", text.strip())

    def _extract_id(self, el: Tag) -> str:
        """Extract product ID from element attributes."""
        for selector in ("data-product", "data-product-id", "data-id", "data-pid"):
            val = el.get(selector)
            if val:
                return str(val)
        # Try from href
        href = el.get("href", "")
        match = re.search(r"[/\-]p?(\d{5,})", str(href))
        if match:
            return match.group(1)
        return ""

    @abstractmethod
    async def scrape_top_products(self) -> ScrapeResult:
        """Scrape top/hot/bestselling products. Implement in subclass."""
        ...

    @abstractmethod
    async def scrape_category(self, category_url: str) -> ScrapeResult:
        """Scrape all products from a category page. Implement in subclass."""
        ...

    @abstractmethod
    async def search_product(self, query: str) -> ScrapeResult:
        """Search for a product by name/keyword. Implement in subclass."""
        ...

    async def scrape_product_page(
        self, url: str, client: httpx.AsyncClient
    ) -> Optional[Product]:
        """Scrape a single product detail page. Override in subclass."""
        return None

    async def run_top_products(self) -> ScrapeResult:
        """Public entry point for top products scraping."""
        logger.info(f"[{self.SITE_KEY}] Starting top products scrape")
        result = await self.scrape_top_products()
        result.complete()
        logger.info(
            f"[{self.SITE_KEY}] Done: {result.total_found} products, "
            f"{len(result.errors)} errors, {result.duration_seconds:.1f}s"
        )
        return result
