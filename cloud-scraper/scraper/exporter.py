"""Export scraped data to JSON, CSV, XLSX formats."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from .models import Product, ScrapeResult

logger = logging.getLogger(__name__)


def _products_to_dicts(products: list[Product]) -> list[dict]:
    """Flatten products into dicts suitable for tabular export."""
    rows = []
    for p in products:
        row = {
            "product_id": p.product_id,
            "name": p.name,
            "url": p.url,
            "country": p.country,
            "site": p.site,
            "category": p.category,
            "price_min": p.price_min,
            "price_max": p.price_max,
            "currency": p.currency,
            "image_url": p.image_url,
            "rating": p.rating,
            "review_count": p.review_count,
            "rank": p.rank,
            "offer_count": p.offer_count(),
            "best_price": p.best_price(),
            "scraped_at": p.scraped_at.isoformat(),
        }
        rows.append(row)
    return rows


def _results_to_products(results: list[ScrapeResult]) -> list[Product]:
    """Collect all products from multiple results."""
    products = []
    for r in results:
        products.extend(r.products)
    return products


def export_json(
    results: list[ScrapeResult], output_dir: str, filename: Optional[str] = None
) -> Path:
    """Export results to JSON."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not filename:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"scrape_{ts}.json"

    filepath = out / filename
    products = _results_to_products(results)
    data = {
        "scraped_at": datetime.utcnow().isoformat(),
        "total_products": len(products),
        "sites": [
            {
                "site": r.site,
                "country": r.country,
                "url": r.url,
                "total_found": r.total_found,
                "duration_seconds": r.duration_seconds,
                "errors": r.errors,
            }
            for r in results
        ],
        "products": [p.model_dump(mode="json") for p in products],
    }
    filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Exported {len(products)} products to {filepath}")
    return filepath


def export_csv(
    results: list[ScrapeResult], output_dir: str, filename: Optional[str] = None
) -> Path:
    """Export results to CSV."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not filename:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"scrape_{ts}.csv"

    filepath = out / filename
    products = _results_to_products(results)
    rows = _products_to_dicts(products)
    df = pd.DataFrame(rows)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    logger.info(f"Exported {len(products)} products to {filepath}")
    return filepath


def export_xlsx(
    results: list[ScrapeResult], output_dir: str, filename: Optional[str] = None
) -> Path:
    """Export results to XLSX with one sheet per country."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not filename:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"scrape_{ts}.xlsx"

    filepath = out / filename
    products = _results_to_products(results)
    rows = _products_to_dicts(products)
    df = pd.DataFrame(rows)

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        # Summary sheet
        summary_data = []
        for r in results:
            summary_data.append(
                {
                    "Site": r.site,
                    "Country": r.country,
                    "URL": r.url,
                    "Products Found": r.total_found,
                    "Duration (s)": r.duration_seconds,
                    "Errors": len(r.errors),
                }
            )
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)

        # All products sheet
        if not df.empty:
            df.to_excel(writer, sheet_name="All Products", index=False)

        # Per-country sheets
        for country in df["country"].unique() if not df.empty else []:
            country_df = df[df["country"] == country]
            sheet_name = f"{country}"[:31]  # Excel max sheet name
            country_df.to_excel(writer, sheet_name=sheet_name, index=False)

    logger.info(f"Exported {len(products)} products to {filepath}")
    return filepath


EXPORTERS = {
    "json": export_json,
    "csv": export_csv,
    "xlsx": export_xlsx,
}


def export_results(
    results: list[ScrapeResult],
    output_dir: str = "./data",
    fmt: str = "json",
    filename: Optional[str] = None,
) -> Path:
    """Export results in the given format."""
    exporter = EXPORTERS.get(fmt)
    if not exporter:
        raise ValueError(f"Unknown format: {fmt}. Use: {list(EXPORTERS.keys())}")
    return exporter(results, output_dir, filename)
