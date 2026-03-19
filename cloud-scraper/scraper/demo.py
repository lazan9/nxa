"""Demo data generator for testing the scraper pipeline without internet access."""

from __future__ import annotations

import random
from datetime import datetime

from .models import Product, ScrapeResult

# NXA.hu product categories: marine/boating, water sports, musical instruments
DEMO_PRODUCTS = {
    "HU": {
        "site": "arukereso",
        "currency": "HUF",
        "base_url": "https://www.arukereso.hu",
        "products": [
            ("Haswing Protruar 3.0 elektromos csónakmotor", "/haswing-protruar-3-p890001/", 289990, "csonakmotor"),
            ("Mercury F5 MH csónakmotor", "/mercury-f5-mh-p890002/", 549990, "csonakmotor"),
            ("Kolibri KM-330D gumicsónak", "/kolibri-km-330d-p890003/", 349990, "gumicsónak"),
            ("Garmin ECHOMAP UHD2 72sv halradar", "/garmin-echomap-uhd2-72sv-p890004/", 399990, "halradar"),
            ("Garmin GPSMAP 1243xsv hajós GPS", "/garmin-gpsmap-1243xsv-p890005/", 699990, "hajos-gps"),
            ("Aqua Marina Fusion SUP deszka", "/aqua-marina-fusion-sup-p890006/", 189990, "sup"),
            ("Jobe Thunder 1 személyes fánk", "/jobe-thunder-p890007/", 49990, "vizisport"),
            ("Fender Player Stratocaster elektromos gitár", "/fender-player-stratocaster-p890008/", 329990, "elektromos-gitar"),
            ("Yamaha FG800 akusztikus gitár", "/yamaha-fg800-p890009/", 89990, "akusztikus-gitar"),
            ("Roland TD-17KV elektromos dobszett", "/roland-td-17kv-p890010/", 449990, "dob"),
        ],
    },
    "CZ": {
        "site": "heureka_cz",
        "currency": "CZK",
        "base_url": "https://www.heureka.cz",
        "products": [
            ("Haswing Protruar 3.0 elektrický lodní motor", "/haswing-protruar-3/", 17990, "lodni-motory"),
            ("Mercury F5 MH přívěsný motor", "/mercury-f5-mh/", 33990, "lodni-motory"),
            ("Kolibri KM-330D nafukovací člun", "/kolibri-km-330d/", 21990, "nafukovaci-cluny"),
            ("Garmin ECHOMAP UHD2 72sv sonar", "/garmin-echomap-uhd2-72sv/", 24990, "sonary-echoluty"),
            ("Garmin GPSMAP 1243xsv GPS", "/garmin-gpsmap-1243xsv/", 42990, "lodní-gps"),
            ("Aqua Marina Fusion SUP", "/aqua-marina-fusion-sup/", 11990, "paddleboardy"),
            ("Jobe Thunder tažný kruh", "/jobe-thunder/", 2990, "vodní-atrakce"),
            ("Fender Player Stratocaster", "/fender-player-stratocaster/", 19990, "elektricke-kytary"),
            ("Yamaha FG800 akustická kytara", "/yamaha-fg800/", 5490, "akusticke-kytary"),
            ("Roland TD-17KV elektronické bicí", "/roland-td-17kv/", 27990, "bici-soupravy"),
        ],
    },
    "SK": {
        "site": "heureka_sk",
        "currency": "EUR",
        "base_url": "https://www.heureka.sk",
        "products": [
            ("Haswing Protruar 3.0 elektrický lodný motor", "/haswing-protruar-3/", 719, "lodne-motory"),
            ("Mercury F5 MH závesný motor", "/mercury-f5-mh/", 1359, "lodne-motory"),
            ("Kolibri KM-330D nafukovací čln", "/kolibri-km-330d/", 879, "nafukovacie-clny"),
            ("Garmin ECHOMAP UHD2 72sv sonar", "/garmin-echomap-uhd2-72sv/", 999, "sonary-echoloty"),
            ("Garmin GPSMAP 1243xsv GPS", "/garmin-gpsmap-1243xsv/", 1719, "lodna-gps"),
            ("Aqua Marina Fusion SUP", "/aqua-marina-fusion-sup/", 479, "paddleboardy"),
            ("Jobe Thunder ťahaný kruh", "/jobe-thunder/", 119, "vodne-atrakcie"),
            ("Fender Player Stratocaster", "/fender-player-stratocaster/", 799, "elektricke-gitary"),
            ("Yamaha FG800 akustická gitara", "/yamaha-fg800/", 219, "akusticke-gitary"),
            ("Roland TD-17KV elektronické bicie", "/roland-td-17kv/", 1119, "bicie-supravy"),
        ],
    },
    "RO": {
        "site": "compari",
        "currency": "RON",
        "base_url": "https://www.compari.ro",
        "products": [
            ("Haswing Protruar 3.0 motor electric barca", "/haswing-protruar-3-p123/", 3599, "motoare-barca"),
            ("Mercury F5 MH motor barca", "/mercury-f5-mh-p124/", 6799, "motoare-barca"),
            ("Kolibri KM-330D barca gonflabila", "/kolibri-km-330d-p125/", 4399, "barci-gonflabile"),
            ("Garmin ECHOMAP UHD2 72sv sonar", "/garmin-echomap-uhd2-72sv-p126/", 4999, "sonar-fishfinder"),
            ("Garmin GPSMAP 1243xsv GPS nautic", "/garmin-gpsmap-1243xsv-p127/", 8599, "gps-navigatie"),
            ("Aqua Marina Fusion SUP", "/aqua-marina-fusion-sup-p128/", 2399, "sup-paddleboard"),
            ("Jobe Thunder cerc tractabil", "/jobe-thunder-p129/", 599, "atractii-tractabile"),
            ("Fender Player Stratocaster", "/fender-player-stratocaster-p130/", 3999, "chitara-electrica"),
            ("Yamaha FG800 chitara acustica", "/yamaha-fg800-p131/", 1099, "chitara-acustica"),
            ("Roland TD-17KV tobe electronice", "/roland-td-17kv-p132/", 5599, "tobe-percutie"),
        ],
    },
    "SI": {
        "site": "ceneje",
        "currency": "EUR",
        "base_url": "https://www.ceneje.si",
        "products": [
            ("Haswing Protruar 3.0 električni izvenkrmni motor", "/haswing-protruar-3/", 729, "izvenkrmni-motorji"),
            ("Mercury F5 MH izvenkrmni motor", "/mercury-f5-mh/", 1379, "izvenkrmni-motorji"),
            ("Kolibri KM-330D napihljivi čoln", "/kolibri-km-330d/", 889, "napihljivi-colni"),
            ("Garmin ECHOMAP UHD2 72sv sonar", "/garmin-echomap-uhd2-72sv/", 1019, "sonarji"),
            ("Garmin GPSMAP 1243xsv GPS", "/garmin-gpsmap-1243xsv/", 1739, "gps-plovila"),
            ("Aqua Marina Fusion SUP", "/aqua-marina-fusion-sup/", 489, "sup-deske"),
            ("Jobe Thunder vlečna igrača", "/jobe-thunder/", 119, "vodne-igrace"),
            ("Fender Player Stratocaster", "/fender-player-stratocaster/", 819, "elektricne-kitare"),
            ("Yamaha FG800 akustična kitara", "/yamaha-fg800/", 229, "akusticne-kitare"),
            ("Roland TD-17KV elektronski bobni", "/roland-td-17kv/", 1139, "bobni"),
        ],
    },
    "AT": {
        "site": "geizhals_at",
        "currency": "EUR",
        "base_url": "https://geizhals.at",
        "products": [
            ("Haswing Protruar 3.0 Elektro-Außenborder", "/a4560001.html", 699, "aussenborder"),
            ("Mercury F5 MH Außenbordmotor", "/a4560002.html", 1329, "aussenborder"),
            ("Kolibri KM-330D Schlauchboot", "/a4560003.html", 859, "schlauchboote"),
            ("Garmin ECHOMAP UHD2 72sv Echolot", "/a4560004.html", 989, "echolote"),
            ("Garmin GPSMAP 1243xsv Marine GPS", "/a4560005.html", 1689, "gps_marine"),
            ("Aqua Marina Fusion SUP Board", "/a4560006.html", 469, "sup"),
            ("Jobe Thunder Towable Tube", "/a4560007.html", 109, "wasserattraktionen"),
            ("Fender Player Stratocaster", "/a4560008.html", 789, "e_gitarren"),
            ("Yamaha FG800 Akustikgitarre", "/a4560009.html", 219, "akustikgitarren"),
            ("Roland TD-17KV E-Drum Set", "/a4560010.html", 1099, "schlagzeug"),
        ],
    },
    "DE": {
        "site": "geizhals_de",
        "currency": "EUR",
        "base_url": "https://geizhals.de",
        "products": [
            ("Haswing Protruar 3.0 Elektro-Außenborder", "/a4560001.html", 679, "aussenborder"),
            ("Mercury F5 MH Außenbordmotor", "/a4560002.html", 1299, "aussenborder"),
            ("Kolibri KM-330D Schlauchboot", "/a4560003.html", 839, "schlauchboote"),
            ("Garmin ECHOMAP UHD2 72sv Echolot", "/a4560004.html", 969, "echolote"),
            ("Garmin GPSMAP 1243xsv Marine GPS", "/a4560005.html", 1649, "gps_marine"),
            ("Aqua Marina Fusion SUP Board", "/a4560006.html", 449, "sup"),
            ("Jobe Thunder Towable Tube", "/a4560007.html", 99, "wasserattraktionen"),
            ("Fender Player Stratocaster", "/a4560008.html", 769, "e_gitarren"),
            ("Yamaha FG800 Akustikgitarre", "/a4560009.html", 209, "akustikgitarren"),
            ("Roland TD-17KV E-Drum Set", "/a4560010.html", 1079, "schlagzeug"),
        ],
    },
    "PL": {
        "site": "ceneo",
        "currency": "PLN",
        "base_url": "https://www.ceneo.pl",
        "products": [
            ("Haswing Protruar 3.0 silnik elektryczny", "/234560001", 3099, "Silniki_zaburtowe"),
            ("Mercury F5 MH silnik zaburtowy", "/234560002", 5899, "Silniki_zaburtowe"),
            ("Kolibri KM-330D ponton", "/234560003", 3799, "Pontony"),
            ("Garmin ECHOMAP UHD2 72sv echosonda", "/234560004", 4299, "Echosondy"),
            ("Garmin GPSMAP 1243xsv GPS morski", "/234560005", 7499, "GPS_morski"),
            ("Aqua Marina Fusion deska SUP", "/234560006", 2099, "Deski_SUP"),
            ("Jobe Thunder kolo wodne", "/234560007", 529, "Atrakcje_wodne"),
            ("Fender Player Stratocaster", "/234560008", 3499, "Gitary_elektryczne"),
            ("Yamaha FG800 gitara akustyczna", "/234560009", 959, "Gitary_akustyczne"),
            ("Roland TD-17KV perkusja elektroniczna", "/234560010", 4899, "Perkusja"),
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
