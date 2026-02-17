"""Demo data generator for testing the scraper pipeline without internet access."""

from __future__ import annotations

import random
from datetime import datetime

from .models import Product, ScrapeResult

# Realistic product data per country
DEMO_PRODUCTS = {
    "HU": {
        "site": "arukereso",
        "currency": "HUF",
        "base_url": "https://www.arukereso.hu",
        "products": [
            ("Samsung Galaxy S25 Ultra 256GB", "/samsung-galaxy-s25-ultra-p789012/", 549990, "mobiltelefon"),
            ("Apple iPhone 16 Pro 256GB", "/apple-iphone-16-pro-p789013/", 599990, "mobiltelefon"),
            ("Xiaomi 15 256GB", "/xiaomi-15-p789014/", 289990, "mobiltelefon"),
            ("Lenovo IdeaPad Slim 5 16", "/lenovo-ideapad-slim-5-p789015/", 279990, "notebook"),
            ("ASUS ROG Strix G16 RTX 4060", "/asus-rog-strix-g16-p789016/", 549990, "notebook"),
            ("Samsung Galaxy Tab S10 FE", "/samsung-galaxy-tab-s10-fe-p789017/", 189990, "tablet"),
            ("LG OLED55C4 55\" 4K OLED TV", "/lg-oled55c4-p789018/", 499990, "tv"),
            ("Sony WH-1000XM5 fejhallgato", "/sony-wh-1000xm5-p789019/", 129990, "fejhallgato"),
            ("Samsung 990 EVO Plus 2TB SSD", "/samsung-990-evo-plus-p789020/", 79990, "ssd"),
            ("Apple Watch Series 10 GPS", "/apple-watch-series-10-p789021/", 159990, "okosora"),
        ],
    },
    "CZ": {
        "site": "heureka_cz",
        "currency": "CZK",
        "base_url": "https://www.heureka.cz",
        "products": [
            ("Samsung Galaxy S25 Ultra 256GB", "/samsung-galaxy-s25-ultra/", 34990, "mobilni-telefony"),
            ("Apple iPhone 16 Pro 256GB", "/apple-iphone-16-pro/", 36990, "mobilni-telefony"),
            ("Xiaomi 15 256GB", "/xiaomi-15/", 17990, "mobilni-telefony"),
            ("Lenovo IdeaPad Slim 5", "/lenovo-ideapad-slim-5/", 18990, "notebooky"),
            ("ASUS ROG Strix G16", "/asus-rog-strix-g16/", 34990, "notebooky"),
            ("Samsung Galaxy Tab S10 FE", "/samsung-galaxy-tab-s10-fe/", 12990, "tablety"),
            ("LG OLED55C4 55\" OLED", "/lg-oled55c4/", 29990, "televize"),
            ("Sony WH-1000XM5", "/sony-wh-1000xm5/", 7990, "sluchatka"),
            ("Samsung 990 EVO Plus 2TB", "/samsung-990-evo-plus/", 4990, "ssd-disky"),
            ("Apple Watch Series 10", "/apple-watch-series-10/", 10990, "chytre-hodinky"),
        ],
    },
    "SK": {
        "site": "heureka_sk",
        "currency": "EUR",
        "base_url": "https://www.heureka.sk",
        "products": [
            ("Samsung Galaxy S25 Ultra 256GB", "/samsung-galaxy-s25-ultra/", 1399, "mobilne-telefony"),
            ("Apple iPhone 16 Pro 256GB", "/apple-iphone-16-pro/", 1479, "mobilne-telefony"),
            ("Xiaomi 15 256GB", "/xiaomi-15/", 719, "mobilne-telefony"),
            ("Lenovo IdeaPad Slim 5", "/lenovo-ideapad-slim-5/", 749, "notebooky"),
            ("ASUS ROG Strix G16", "/asus-rog-strix-g16/", 1399, "notebooky"),
            ("Samsung Galaxy Tab S10 FE", "/samsung-galaxy-tab-s10-fe/", 519, "tablety"),
            ("LG OLED55C4 55\" OLED", "/lg-oled55c4/", 1199, "televizory"),
            ("Sony WH-1000XM5", "/sony-wh-1000xm5/", 319, "sluchadla"),
            ("Samsung 990 EVO Plus 2TB", "/samsung-990-evo-plus/", 199, "ssd-disky"),
            ("Apple Watch Series 10", "/apple-watch-series-10/", 439, "smart-hodinky"),
        ],
    },
    "RO": {
        "site": "compari",
        "currency": "RON",
        "base_url": "https://www.compari.ro",
        "products": [
            ("Samsung Galaxy S25 Ultra 256GB", "/samsung-galaxy-s25-ultra-p123/", 6999, "telefoane-mobile"),
            ("Apple iPhone 16 Pro 256GB", "/apple-iphone-16-pro-p124/", 7399, "telefoane-mobile"),
            ("Xiaomi 15 256GB", "/xiaomi-15-p125/", 3599, "telefoane-mobile"),
            ("Lenovo IdeaPad Slim 5", "/lenovo-ideapad-slim-5-p126/", 3749, "laptop-notebook"),
            ("ASUS ROG Strix G16", "/asus-rog-strix-g16-p127/", 6999, "laptop-notebook"),
            ("Samsung Galaxy Tab S10 FE", "/samsung-galaxy-tab-s10-fe-p128/", 2599, "tablete"),
            ("LG OLED55C4 55\" OLED", "/lg-oled55c4-p129/", 5999, "televizoare-led"),
            ("Sony WH-1000XM5", "/sony-wh-1000xm5-p130/", 1599, "casti-audio"),
            ("Samsung 990 EVO Plus 2TB", "/samsung-990-evo-plus-p131/", 999, "ssd"),
            ("Apple Watch Series 10", "/apple-watch-series-10-p132/", 2199, "smartwatch"),
        ],
    },
    "SI": {
        "site": "ceneje",
        "currency": "EUR",
        "base_url": "https://www.ceneje.si",
        "products": [
            ("Samsung Galaxy S25 Ultra 256GB", "/samsung-galaxy-s25-ultra/", 1419, "mobilni-telefoni"),
            ("Apple iPhone 16 Pro 256GB", "/apple-iphone-16-pro/", 1499, "mobilni-telefoni"),
            ("Xiaomi 15 256GB", "/xiaomi-15/", 729, "mobilni-telefoni"),
            ("Lenovo IdeaPad Slim 5", "/lenovo-ideapad-slim-5/", 759, "prenosniki"),
            ("ASUS ROG Strix G16", "/asus-rog-strix-g16/", 1419, "prenosniki"),
            ("Samsung Galaxy Tab S10 FE", "/samsung-galaxy-tab-s10-fe/", 529, "tablicni-racunalniki"),
            ("LG OLED55C4 55\" OLED", "/lg-oled55c4/", 1219, "televizorji"),
            ("Sony WH-1000XM5", "/sony-wh-1000xm5/", 329, "slusalke"),
            ("Samsung 990 EVO Plus 2TB", "/samsung-990-evo-plus/", 209, "ssd-diski"),
            ("Apple Watch Series 10", "/apple-watch-series-10/", 449, "pametne-ure"),
        ],
    },
    "AT": {
        "site": "geizhals_at",
        "currency": "EUR",
        "base_url": "https://geizhals.at",
        "products": [
            ("Samsung Galaxy S25 Ultra 256GB", "/a3456789.html", 1379, "smartphones"),
            ("Apple iPhone 16 Pro 256GB", "/a3456790.html", 1449, "smartphones"),
            ("Xiaomi 15 256GB", "/a3456791.html", 699, "smartphones"),
            ("Lenovo IdeaPad Slim 5 16ABR9", "/a3456792.html", 729, "nb"),
            ("ASUS ROG Strix G16 G614JU", "/a3456793.html", 1379, "nb"),
            ("Samsung Galaxy Tab S10 FE WiFi", "/a3456794.html", 509, "tablet"),
            ("LG OLED55C4 55\" OLED", "/a3456795.html", 1189, "tvlcd"),
            ("Sony WH-1000XM5", "/a3456796.html", 299, "kh"),
            ("Samsung 990 EVO Plus 2TB NVMe", "/a3456797.html", 189, "sm_ssd"),
            ("Apple Watch Series 10 GPS 46mm", "/a3456798.html", 429, "umhr"),
        ],
    },
    "DE": {
        "site": "geizhals_de",
        "currency": "EUR",
        "base_url": "https://geizhals.de",
        "products": [
            ("Samsung Galaxy S25 Ultra 256GB", "/a3456789.html", 1349, "smartphones"),
            ("Apple iPhone 16 Pro 256GB", "/a3456790.html", 1419, "smartphones"),
            ("Xiaomi 15 256GB", "/a3456791.html", 679, "smartphones"),
            ("Lenovo IdeaPad Slim 5 16ABR9", "/a3456792.html", 699, "nb"),
            ("ASUS ROG Strix G16 G614JU", "/a3456793.html", 1349, "nb"),
            ("Samsung Galaxy Tab S10 FE WiFi", "/a3456794.html", 489, "tablet"),
            ("LG OLED55C4 55\" OLED", "/a3456795.html", 1149, "tvlcd"),
            ("Sony WH-1000XM5", "/a3456796.html", 289, "kh"),
            ("Samsung 990 EVO Plus 2TB NVMe", "/a3456797.html", 179, "sm_ssd"),
            ("Apple Watch Series 10 GPS 46mm", "/a3456798.html", 419, "umhr"),
        ],
    },
    "PL": {
        "site": "ceneo",
        "currency": "PLN",
        "base_url": "https://www.ceneo.pl",
        "products": [
            ("Samsung Galaxy S25 Ultra 256GB", "/123456789", 5999, "Smartfony"),
            ("Apple iPhone 16 Pro 256GB", "/123456790", 6299, "Smartfony"),
            ("Xiaomi 15 256GB", "/123456791", 3099, "Smartfony"),
            ("Lenovo IdeaPad Slim 5", "/123456792", 3199, "Laptopy"),
            ("ASUS ROG Strix G16", "/123456793", 5999, "Laptopy"),
            ("Samsung Galaxy Tab S10 FE", "/123456794", 2199, "Tablety"),
            ("LG OLED55C4 55\" OLED", "/123456795", 5199, "Telewizory"),
            ("Sony WH-1000XM5", "/123456796", 1399, "Sluchawki"),
            ("Samsung 990 EVO Plus 2TB", "/123456797", 879, "Dyski_SSD"),
            ("Apple Watch Series 10", "/123456798", 1899, "Smartwatche"),
        ],
    },
}


def generate_demo_results(countries: list[str], max_products: int = 10) -> list[ScrapeResult]:
    """Generate realistic demo data for all requested countries."""
    results = []

    for country in countries:
        country = country.upper()
        data = DEMO_PRODUCTS.get(country)
        if not data:
            continue

        products = []
        for i, (name, path, price, category) in enumerate(data["products"][:max_products]):
            product = Product(
                product_id=path.split("/")[-1].replace(".html", "").lstrip("p") or f"demo_{i}",
                name=name,
                url=data["base_url"] + path,
                country=country,
                site=data["site"],
                category=category,
                price_min=float(price),
                currency=data["currency"],
                rating=round(random.uniform(4.0, 5.0), 1),
                review_count=random.randint(50, 5000),
                rank=i + 1,
            )
            products.append(product)

        result = ScrapeResult(
            site=data["site"],
            country=country,
            url=data["base_url"],
            products=products,
            total_found=len(products),
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            duration_seconds=0.1,
        )
        results.append(result)

    return results
