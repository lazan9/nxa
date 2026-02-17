"""Main orchestrator for running scrapers across multiple countries."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

import yaml

from .exporter import export_results
from .models import ProductQuery, ScrapeResult
from .sites import COUNTRY_MAP, SCRAPERS

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/sites.yaml") -> dict:
    """Load site configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Config not found at {config_path}, using defaults")
        return {"sites": {}, "defaults": {}}

    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class Orchestrator:
    """Coordinates scraping across multiple countries and sites."""

    def __init__(
        self,
        config: dict,
        countries: Optional[list[str]] = None,
        use_playwright: bool = False,
        output_dir: str = "./data",
        output_format: str = "json",
        max_products: int = 0,
    ):
        self.config = config
        self.use_playwright = use_playwright
        self.output_dir = output_dir
        self.output_format = output_format
        self.max_products = max_products

        # Resolve countries
        if countries and "all" in [c.lower() for c in countries]:
            self.countries = list(COUNTRY_MAP.keys())
        elif countries:
            self.countries = [c.lower() for c in countries]
        else:
            self.countries = list(COUNTRY_MAP.keys())

        # Build scraper instances
        self.scrapers = {}
        for country in self.countries:
            site_key = COUNTRY_MAP.get(country)
            if not site_key:
                logger.warning(f"Unknown country: {country}")
                continue
            scraper_cls = SCRAPERS.get(site_key)
            if not scraper_cls:
                logger.warning(f"No scraper for: {site_key}")
                continue
            self.scrapers[country] = scraper_cls(
                config, use_playwright=use_playwright, max_products=max_products
            )

    async def scrape_top_products(self) -> list[ScrapeResult]:
        """Scrape top/hot products from all configured countries concurrently."""
        logger.info(
            f"Starting top products scrape for: {', '.join(self.countries)}"
        )

        max_concurrent = self.config.get("defaults", {}).get("max_concurrent", 5)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _run(country: str, scraper):
            async with semaphore:
                try:
                    return await scraper.run_top_products()
                except Exception as e:
                    logger.error(f"[{country}] Scraper failed: {e}")
                    return ScrapeResult(
                        site=scraper.SITE_KEY,
                        country=scraper.COUNTRY,
                        url=scraper.base_url,
                        errors=[str(e)],
                    )

        tasks = [
            _run(country, scraper) for country, scraper in self.scrapers.items()
        ]
        results = await asyncio.gather(*tasks)

        # Export
        filepath = export_results(
            list(results), self.output_dir, self.output_format
        )
        logger.info(f"Results exported to: {filepath}")

        return list(results)

    async def scrape_categories(
        self, category_urls: dict[str, list[str]]
    ) -> list[ScrapeResult]:
        """Scrape specific category URLs per country.

        Args:
            category_urls: {country_code: [url1, url2, ...]}
        """
        all_results = []
        max_concurrent = self.config.get("defaults", {}).get("max_concurrent", 5)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _run(country, url, scraper):
            async with semaphore:
                try:
                    result = await scraper.scrape_category(url)
                    result.complete()
                    return result
                except Exception as e:
                    logger.error(f"[{country}] Category {url}: {e}")
                    return ScrapeResult(
                        site=scraper.SITE_KEY,
                        country=scraper.COUNTRY,
                        url=url,
                        errors=[str(e)],
                    )

        tasks = []
        for country, urls in category_urls.items():
            scraper = self.scrapers.get(country.lower())
            if not scraper:
                logger.warning(f"No scraper for country: {country}")
                continue
            for url in urls:
                tasks.append(_run(country, url, scraper))

        results = await asyncio.gather(*tasks)
        all_results.extend(results)

        filepath = export_results(all_results, self.output_dir, self.output_format)
        logger.info(f"Results exported to: {filepath}")

        return all_results

    async def search_products(
        self,
        queries: list[ProductQuery],
        countries: Optional[list[str]] = None,
    ) -> list[ScrapeResult]:
        """Search for specific products across countries (Phase 2).

        Args:
            queries: Product queries imported from SQL/XML/XLSX
            countries: Override country list (default: all configured)
        """
        target_countries = countries or self.countries
        all_results = []
        max_concurrent = self.config.get("defaults", {}).get("max_concurrent", 5)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _search(query: ProductQuery, country: str, scraper):
            async with semaphore:
                try:
                    search_term = query.name
                    if query.ean:
                        search_term = query.ean
                    result = await scraper.search_product(search_term)
                    result.complete()
                    # Tag results with source query info
                    for p in result.products:
                        p.extra["query_sku"] = query.sku
                        p.extra["query_ean"] = query.ean
                        p.extra["our_price"] = query.our_price
                    return result
                except Exception as e:
                    logger.error(
                        f"[{country}] Search '{query.name}': {e}"
                    )
                    return ScrapeResult(
                        site=scraper.SITE_KEY,
                        country=scraper.COUNTRY,
                        url="",
                        errors=[str(e)],
                    )

        tasks = []
        for query in queries:
            for country in target_countries:
                scraper = self.scrapers.get(country)
                if scraper:
                    tasks.append(_search(query, country, scraper))

        results = await asyncio.gather(*tasks)
        all_results.extend(results)

        filepath = export_results(all_results, self.output_dir, self.output_format)
        logger.info(f"Search results exported to: {filepath}")

        return all_results
