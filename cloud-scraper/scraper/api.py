"""FastAPI REST API for the European Price Comparison Scraper.

Exposes scraper data as JSON endpoints for consumption by shopmind.app
and other services.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .demo import generate_demo_results
from .exporter import export_results
from .models import Product, ScrapeResult
from .orchestrator import Orchestrator, load_config
from .sites import COUNTRY_MAP

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ShopMind Price Scraper API",
    description="European price comparison data for shopmind.app",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS - allow shopmind.app and local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://shopmind.app",
        "https://www.shopmind.app",
        "http://localhost:3000",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global config
CONFIG_PATH = os.environ.get("SCRAPER_CONFIG", "config/sites.yaml")
OUTPUT_DIR = os.environ.get("SCRAPER_OUTPUT_DIR", "./data")
API_KEY = os.environ.get("SCRAPER_API_KEY", "")

ALL_COUNTRIES = list(COUNTRY_MAP.keys())


# --- Auth middleware ---
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for docs and health
        if request.url.path in ("/", "/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)
        if API_KEY:
            key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
            if key != API_KEY:
                return JSONResponse(status_code=401, content={"error": "Invalid API key"})
        return await call_next(request)


app.add_middleware(APIKeyMiddleware)


# --- Response models ---
class HealthResponse(BaseModel):
    status: str
    version: str
    countries: list[str]
    timestamp: str


class ScrapeResponse(BaseModel):
    scraped_at: str
    total_products: int
    countries: list[str]
    products: list[dict]
    errors: list[dict]


class CountryInfo(BaseModel):
    code: str
    name: str
    site: str
    currency: str


# --- Cached results store ---
_cache: dict[str, dict] = {}
CACHE_TTL_SECONDS = int(os.environ.get("SCRAPER_CACHE_TTL", "3600"))


def _cache_key(countries: list[str], demo: bool) -> str:
    return f"{'demo' if demo else 'live'}:{','.join(sorted(countries))}"


def _get_cached(key: str) -> Optional[list[ScrapeResult]]:
    if key in _cache:
        entry = _cache[key]
        age = (datetime.utcnow() - entry["time"]).total_seconds()
        if age < CACHE_TTL_SECONDS:
            return entry["results"]
        del _cache[key]
    return None


def _set_cached(key: str, results: list[ScrapeResult]):
    _cache[key] = {"results": results, "time": datetime.utcnow()}


# --- Load latest file from disk ---
def _load_latest_json() -> Optional[dict]:
    """Load the most recent scrape JSON file from data dir."""
    data_dir = Path(OUTPUT_DIR)
    if not data_dir.exists():
        return None
    json_files = sorted(data_dir.glob("scrape_*.json"), reverse=True)
    if not json_files:
        return None
    with open(json_files[0], encoding="utf-8") as f:
        return json.load(f)


# --- Endpoints ---
@app.get("/", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        countries=ALL_COUNTRIES,
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/countries", response_model=list[CountryInfo])
async def list_countries():
    """List all supported countries and sites."""
    country_info = {
        "hu": ("Hungary", "arukereso.hu", "HUF"),
        "cz": ("Czech Republic", "heureka.cz", "CZK"),
        "sk": ("Slovakia", "heureka.sk", "EUR"),
        "ro": ("Romania", "compari.ro", "RON"),
        "si": ("Slovenia", "ceneje.si", "EUR"),
        "at": ("Austria", "geizhals.at", "EUR"),
        "de": ("Germany", "geizhals.de", "EUR"),
        "pl": ("Poland", "ceneo.pl", "PLN"),
    }
    return [
        CountryInfo(code=code, name=info[0], site=info[1], currency=info[2])
        for code, info in country_info.items()
    ]


@app.get("/products", response_model=ScrapeResponse)
async def get_products(
    countries: str = Query("all", description="Comma-separated country codes or 'all'"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand name (substring match)"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    limit: int = Query(100, ge=1, le=1000, description="Max products to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    demo: bool = Query(False, description="Use demo data"),
):
    """Get scraped products with optional filtering."""
    country_list = ALL_COUNTRIES if countries == "all" else [c.strip().lower() for c in countries.split(",")]

    # Validate countries
    invalid = [c for c in country_list if c not in COUNTRY_MAP]
    if invalid:
        raise HTTPException(400, f"Unknown countries: {invalid}. Valid: {ALL_COUNTRIES}")

    # Try cache first
    cache_key = _cache_key(country_list, demo)
    results = _get_cached(cache_key)

    if not results:
        if demo:
            results = generate_demo_results(country_list, max_products=50)
        else:
            # Try loading from latest file on disk
            file_data = _load_latest_json()
            if file_data:
                # Convert file data to filtered product list
                all_products = file_data.get("products", [])
                filtered = [p for p in all_products if p.get("country", "").lower() in country_list]
                # Apply filters inline and return
                if category:
                    filtered = [p for p in filtered if category.lower() in p.get("category", "").lower()]
                if brand:
                    filtered = [p for p in filtered if brand.lower() in p.get("name", "").lower()]
                if min_price is not None:
                    filtered = [p for p in filtered if (p.get("price_min") or 0) >= min_price]
                if max_price is not None:
                    filtered = [p for p in filtered if (p.get("price_min") or float("inf")) <= max_price]

                total = len(filtered)
                filtered = filtered[offset : offset + limit]

                return ScrapeResponse(
                    scraped_at=file_data.get("scraped_at", datetime.utcnow().isoformat()),
                    total_products=total,
                    countries=country_list,
                    products=filtered,
                    errors=[],
                )
            else:
                # No cached data, no file - run demo as fallback
                results = generate_demo_results(country_list, max_products=50)

        _set_cached(cache_key, results)

    # Flatten products
    all_products = []
    all_errors = []
    for r in results:
        for p in r.products:
            d = p.model_dump(mode="json")
            all_products.append(d)
        for e in r.errors:
            all_errors.append({"site": r.site, "country": r.country, "error": e})

    # Apply filters
    if category:
        all_products = [p for p in all_products if category.lower() in p.get("category", "").lower()]
    if brand:
        all_products = [p for p in all_products if brand.lower() in p.get("name", "").lower()]
    if min_price is not None:
        all_products = [p for p in all_products if (p.get("price_min") or 0) >= min_price]
    if max_price is not None:
        all_products = [p for p in all_products if (p.get("price_min") or float("inf")) <= max_price]

    total = len(all_products)
    all_products = all_products[offset : offset + limit]

    return ScrapeResponse(
        scraped_at=datetime.utcnow().isoformat(),
        total_products=total,
        countries=country_list,
        products=all_products,
        errors=all_errors,
    )


@app.post("/scrape")
async def trigger_scrape(
    countries: str = Query("all", description="Comma-separated country codes or 'all'"),
    format: str = Query("json", description="Output format: json, csv, xlsx"),
    demo: bool = Query(False, description="Use demo data"),
):
    """Trigger a new scrape run. Returns results immediately for demo, async for live."""
    country_list = ALL_COUNTRIES if countries == "all" else [c.strip().lower() for c in countries.split(",")]

    if demo:
        results = generate_demo_results(country_list, max_products=50)
        filepath = export_results(results, OUTPUT_DIR, format)
        _set_cached(_cache_key(country_list, True), results)

        total = sum(r.total_found for r in results)
        return {
            "status": "completed",
            "total_products": total,
            "countries": country_list,
            "file": str(filepath),
        }

    # Live scrape
    config = load_config(CONFIG_PATH)
    orch = Orchestrator(
        config=config,
        countries=country_list,
        output_dir=OUTPUT_DIR,
        output_format=format,
    )

    results = await orch.scrape_top_products()
    _set_cached(_cache_key(country_list, False), results)

    total = sum(r.total_found for r in results)
    errors = sum(len(r.errors) for r in results)
    return {
        "status": "completed",
        "total_products": total,
        "total_errors": errors,
        "countries": country_list,
    }


@app.get("/products/{country}")
async def get_country_products(
    country: str,
    category: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    demo: bool = Query(False),
):
    """Get products for a specific country."""
    country = country.lower()
    if country not in COUNTRY_MAP:
        raise HTTPException(404, f"Unknown country: {country}. Valid: {ALL_COUNTRIES}")

    return await get_products(
        countries=country,
        category=category,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
        offset=offset,
        demo=demo,
    )
