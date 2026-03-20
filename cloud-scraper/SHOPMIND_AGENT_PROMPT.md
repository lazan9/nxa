# Agent Prompt: Integrate Price Scraper API into shopmind.app

## Task
Integrate the European Price Comparison Scraper API into shopmind.app. The scraper API is deployed at `https://scraper.shopmind.app` (or `http://<hetzner-ip>:8066` during setup).

## What the Scraper API Does
Scrapes product prices from **8 European price comparison sites** and serves them via REST API:
- **HU** - arukereso.hu (HUF)
- **CZ** - heureka.cz (CZK)
- **SK** - heureka.sk (EUR)
- **RO** - compari.ro (RON)
- **SI** - ceneje.si (EUR)
- **AT** - geizhals.at (EUR)
- **DE** - geizhals.de (EUR)
- **PL** - ceneo.pl (PLN)

## Product Categories Covered
- **Electric boat motors**: Minn Kota, Haswing, MotorGuide, Rhino, Lowrance Ghost
- **Petrol outboard motors**: Mercury, Yamaha, Suzuki, Honda, Tohatsu, Parsun, Hidea
- **Inflatable boats & RIB boats**: Kolibri, Aqua Marina, Highfield, Honda Honwave
- **Fish finders / Sonar**: Lowrance, Humminbird, Deeper, Raymarine
- **Fishing gear**: Shimano, Daiwa
- **Boat accessories**: Minn Kota chargers, anchors
- **Water sports**: SUP boards, wakeboards, towable tubes (Aqua Marina, Jobe)
- **Musical instruments**: Fender, Yamaha, Roland, Ibanez (guitars, bass, drums)

## API Endpoints

All endpoints require header `X-API-Key: <key>` (except `/health` and `/docs`).

### GET /health
Health check. Returns status, version, supported countries.

### GET /countries
List all supported countries with site name and currency.

### GET /products
Main endpoint. Query params:
- `countries` - comma-separated codes or "all" (default: "all")
- `category` - filter by category substring (e.g., "motor", "gitar")
- `brand` - filter by brand name substring (e.g., "minn kota", "mercury")
- `min_price` / `max_price` - price range filter
- `limit` - max results (default: 100, max: 1000)
- `offset` - pagination offset
- `demo` - use demo data (true/false)

**Response:**
```json
{
  "scraped_at": "2026-03-20T12:00:00",
  "total_products": 245,
  "countries": ["hu", "de", "at"],
  "products": [
    {
      "product_id": "890001",
      "name": "Minn Kota Terrova 80 i-Pilot elektromos csónakmotor",
      "url": "https://www.arukereso.hu/minn-kota-terrova-80-p890001/",
      "country": "HU",
      "site": "arukereso",
      "category": "elektromos-csonakmotor",
      "price_min": 799990.0,
      "price_max": null,
      "currency": "HUF",
      "image_url": "",
      "rating": 4.7,
      "review_count": 342,
      "rank": 1,
      "offers": [],
      "scraped_at": "2026-03-20T12:00:00",
      "extra": {}
    }
  ],
  "errors": []
}
```

### GET /products/{country}
Same as `/products` but filtered to one country.

### POST /scrape
Trigger a new scrape run. Query params:
- `countries` - comma-separated or "all"
- `format` - json/csv/xlsx
- `demo` - true/false

## Integration Points for shopmind.app

### 1. Price Comparison Widget
Fetch products by brand/category and display competitor prices across countries:
```
GET /products?brand=minn+kota&countries=hu,de,at
```

### 2. Market Overview Dashboard
Show all products for a country:
```
GET /products?countries=hu&limit=500
```

### 3. Category Browser
Filter by product category:
```
GET /products?category=elektromos-csonakmotor&countries=all
```

### 4. Scheduled Data Sync
The scraper cron runs every 6 hours. shopmind.app can:
- Poll `/products` periodically to get fresh data
- Or call `POST /scrape` to trigger on-demand refresh

### 5. Price Alerts
Compare `price_min` across countries for the same product to find arbitrage opportunities.

## File Structure on Server

```
/opt/shopmind/scraper/
├── docker-compose.yml      # Docker services (api, scraper, cron)
├── Dockerfile              # Container build
├── deploy.sh               # Deployment script
├── requirements.txt        # Python dependencies
├── .env                    # SCRAPER_API_KEY=<key>
├── config/
│   └── sites.yaml          # Scraper site configs & CSS selectors
├── data/                   # Scraped output files (JSON/CSV/XLSX)
│   └── scrape_YYYYMMDD_HHMMSS.json
└── scraper/
    ├── api.py              # FastAPI REST API (THIS IS THE API)
    ├── cli.py              # CLI entry point
    ├── models.py           # Product, Offer, ScrapeResult models
    ├── orchestrator.py     # Multi-country scrape coordinator
    ├── exporter.py         # JSON/CSV/XLSX export
    ├── demo.py             # Demo data (250+ products, no internet needed)
    ├── product_import.py   # Import from XLSX/XML/SQL
    └── sites/
        ├── base.py         # Base scraper class
        ├── arukereso.py    # Hungary
        ├── heureka.py      # Czech Republic + Slovakia
        ├── compari.py      # Romania
        ├── ceneje.py       # Slovenia
        ├── geizhals.py     # Austria + Germany
        └── ceneo.py        # Poland
```

## Docker Services

```bash
# Start API server (always running)
docker compose up -d api

# Run one-off scrape
docker compose run --rm scraper top --countries all --format json

# Enable scheduled scraping (every 6h)
docker compose --profile cron up -d scraper-cron

# View API logs
docker compose logs -f api
```

## Authentication
- Set `SCRAPER_API_KEY` in `.env` file
- Pass as header: `X-API-Key: <key>`
- Or query param: `?api_key=<key>`
- No auth needed for `/health`, `/docs`, `/redoc`

## Quick Test
```bash
# Health check
curl https://scraper.shopmind.app/health

# Get demo products
curl -H 'X-API-Key: YOUR_KEY' 'https://scraper.shopmind.app/products?demo=true&limit=5'

# Get Minn Kota motors across all countries
curl -H 'X-API-Key: YOUR_KEY' 'https://scraper.shopmind.app/products?brand=minn+kota'

# Get all Hungarian electric motors
curl -H 'X-API-Key: YOUR_KEY' 'https://scraper.shopmind.app/products?countries=hu&category=elektromos'

# Trigger fresh scrape
curl -X POST -H 'X-API-Key: YOUR_KEY' 'https://scraper.shopmind.app/scrape?countries=hu,de&format=json'
```
