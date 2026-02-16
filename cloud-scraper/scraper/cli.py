"""CLI entry point for the European price comparison scraper."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from .orchestrator import Orchestrator, load_config
from .product_import import import_products
from .sites import COUNTRY_MAP

console = Console()

ALL_COUNTRIES = list(COUNTRY_MAP.keys())
COUNTRY_NAMES = {
    "hu": "Hungary (arukereso.hu)",
    "cz": "Czech Republic (heureka.cz)",
    "sk": "Slovakia (heureka.sk)",
    "ro": "Romania (compari.ro)",
    "si": "Slovenia (ceneje.si)",
    "at": "Austria (geizhals.at)",
    "de": "Germany (geizhals.de)",
    "pl": "Poland (ceneo.pl)",
}


def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@click.group()
@click.option(
    "--config",
    default=os.environ.get("SCRAPER_CONFIG", "config/sites.yaml"),
    help="Path to sites.yaml config",
)
@click.option(
    "--log-level",
    default=os.environ.get("SCRAPER_LOG_LEVEL", "INFO"),
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
)
@click.pass_context
def cli(ctx, config, log_level):
    """European Price Comparison Scraper - Cloud Edition

    Scrapes top/hot selling products from price comparison sites across
    8 European countries: HU, CZ, SK, RO, SI, AT, DE, PL.
    """
    setup_logging(log_level)
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config)


@cli.command()
@click.option(
    "--countries",
    "-c",
    default="all",
    help="Comma-separated country codes (hu,cz,sk,ro,si,at,de,pl) or 'all'",
)
@click.option(
    "--format",
    "-f",
    "fmt",
    default=os.environ.get("SCRAPER_OUTPUT_FORMAT", "json"),
    type=click.Choice(["json", "csv", "xlsx"]),
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    default=os.environ.get("SCRAPER_OUTPUT_DIR", "./data"),
    help="Output directory",
)
@click.option(
    "--playwright/--no-playwright",
    default=os.environ.get("SCRAPER_USE_PLAYWRIGHT", "").lower() == "true",
    help="Use Playwright for JS-rendered pages",
)
@click.pass_context
def top(ctx, countries, fmt, output, playwright):
    """Scrape top/hot selling products from all configured sites."""
    config = ctx.obj["config"]
    country_list = (
        ALL_COUNTRIES if countries == "all" else countries.split(",")
    )

    # Show what we're doing
    table = Table(title="Scraping Top Products")
    table.add_column("Country", style="cyan")
    table.add_column("Site", style="green")
    for c in country_list:
        c = c.strip().lower()
        table.add_row(c.upper(), COUNTRY_NAMES.get(c, "Unknown"))
    console.print(table)
    console.print()

    orch = Orchestrator(
        config=config,
        countries=country_list,
        use_playwright=playwright,
        output_dir=output,
        output_format=fmt,
    )

    results = asyncio.run(orch.scrape_top_products())

    # Summary
    console.print()
    summary = Table(title="Scrape Results Summary")
    summary.add_column("Country", style="cyan")
    summary.add_column("Site", style="green")
    summary.add_column("Products", style="yellow", justify="right")
    summary.add_column("Errors", style="red", justify="right")
    summary.add_column("Duration", style="blue", justify="right")

    total_products = 0
    total_errors = 0
    for r in results:
        total_products += r.total_found
        total_errors += len(r.errors)
        summary.add_row(
            r.country,
            r.site,
            str(r.total_found),
            str(len(r.errors)),
            f"{r.duration_seconds:.1f}s" if r.duration_seconds else "N/A",
        )
    summary.add_row(
        "TOTAL", "", str(total_products), str(total_errors), "", style="bold"
    )
    console.print(summary)


@cli.command()
@click.argument("source")
@click.option(
    "--countries",
    "-c",
    default="all",
    help="Comma-separated country codes or 'all'",
)
@click.option(
    "--format",
    "-f",
    "fmt",
    default="xlsx",
    type=click.Choice(["json", "csv", "xlsx"]),
)
@click.option("--output", "-o", default="./data")
@click.option("--playwright/--no-playwright", default=False)
@click.option(
    "--query",
    "-q",
    default="SELECT * FROM products",
    help="SQL query (only for SQL sources)",
)
@click.pass_context
def search(ctx, source, countries, fmt, output, playwright, query):
    """Search for products from a file (XLSX, XML) or SQL database.

    SOURCE: Path to .xlsx/.xml file or SQL connection string

    Examples:
        scraper search products.xlsx
        scraper search feed.xml
        scraper search "sqlite:///products.db" -q "SELECT * FROM products"
        scraper search "postgresql://user:pass@host/db" -q "SELECT name, ean FROM items"
    """
    config = ctx.obj["config"]
    country_list = (
        ALL_COUNTRIES if countries == "all" else countries.split(",")
    )

    # Import products
    console.print(f"[cyan]Importing products from:[/cyan] {source}")
    kwargs = {}
    if "://" in source:
        kwargs["query"] = query
    products = import_products(source, **kwargs)
    console.print(f"[green]Imported {len(products)} products[/green]")

    if not products:
        console.print("[red]No products found in source. Exiting.[/red]")
        return

    # Show sample
    table = Table(title=f"Sample Products (first 5 of {len(products)})")
    table.add_column("Name")
    table.add_column("SKU")
    table.add_column("EAN")
    table.add_column("Brand")
    for p in products[:5]:
        table.add_row(p.name[:50], p.sku, p.ean, p.brand)
    console.print(table)
    console.print()

    orch = Orchestrator(
        config=config,
        countries=country_list,
        use_playwright=playwright,
        output_dir=output,
        output_format=fmt,
    )

    results = asyncio.run(orch.search_products(products, country_list))

    # Summary
    total = sum(r.total_found for r in results)
    console.print(f"\n[green]Found {total} matching products across {len(results)} searches[/green]")


@cli.command()
@click.argument("url")
@click.option("--format", "-f", "fmt", default="json", type=click.Choice(["json", "csv", "xlsx"]))
@click.option("--output", "-o", default="./data")
@click.option("--playwright/--no-playwright", default=False)
@click.pass_context
def category(ctx, url, fmt, output, playwright):
    """Scrape all products from a specific category URL.

    Example:
        scraper category "https://www.arukereso.hu/mobiltelefon-c3277/"
        scraper category "https://geizhals.at/?cat=smartphones"
    """
    config = ctx.obj["config"]

    # Detect which site this URL belongs to
    country = None
    for c, site_key in COUNTRY_MAP.items():
        site_cfg = config.get("sites", {}).get(site_key, {})
        base = site_cfg.get("base_url", "")
        if base and base in url:
            country = c
            break

    if not country:
        console.print("[red]Could not detect site from URL. Provide a URL from a supported site.[/red]")
        return

    orch = Orchestrator(
        config=config,
        countries=[country],
        use_playwright=playwright,
        output_dir=output,
        output_format=fmt,
    )

    results = asyncio.run(
        orch.scrape_categories({country: [url]})
    )

    total = sum(r.total_found for r in results)
    console.print(f"\n[green]Scraped {total} products from category[/green]")


@cli.command(name="list")
def list_sites():
    """List all supported sites and countries."""
    table = Table(title="Supported Price Comparison Sites")
    table.add_column("Country", style="cyan")
    table.add_column("Code", style="green")
    table.add_column("Site", style="yellow")
    table.add_column("Group", style="blue")

    sites = [
        ("Hungary", "hu", "arukereso.hu", "Heureka"),
        ("Czech Republic", "cz", "heureka.cz", "Heureka"),
        ("Slovakia", "sk", "heureka.sk", "Heureka"),
        ("Romania", "ro", "compari.ro", "Heureka"),
        ("Slovenia", "si", "ceneje.si", "Heureka"),
        ("Austria", "at", "geizhals.at", "Geizhals"),
        ("Germany", "de", "geizhals.de", "Geizhals"),
        ("Poland", "pl", "ceneo.pl", "Ceneo/Allegro"),
    ]
    for name, code, site, group in sites:
        table.add_row(name, code, site, group)

    console.print(table)
    console.print()
    console.print("[dim]Usage:[/dim]")
    console.print("  python -m scraper.cli top --countries all --format xlsx")
    console.print("  python -m scraper.cli top --countries hu,cz,de --format json")
    console.print("  python -m scraper.cli search products.xlsx --countries hu,ro")
    console.print("  python -m scraper.cli category 'https://geizhals.at/?cat=smartphones'")


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
