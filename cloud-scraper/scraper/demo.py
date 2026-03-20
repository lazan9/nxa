"""Demo data generator for testing the scraper pipeline without internet access."""

from __future__ import annotations

import random
from datetime import datetime

from .models import Product, ScrapeResult

# NXA.hu product categories: boat motors, boats, water sports, musical instruments
DEMO_PRODUCTS = {
    "HU": {
        "site": "arukereso",
        "currency": "HUF",
        "base_url": "https://www.arukereso.hu",
        "products": [
            # Electric boat motors
            ("Minn Kota Terrova 80 i-Pilot elektromos csónakmotor", "/minn-kota-terrova-80-p890001/", 799990, "elektromos-csonakmotor"),
            ("Minn Kota Riptide Terrova 112 elektromos csónakmotor", "/minn-kota-riptide-terrova-112-p890050/", 1299990, "elektromos-csonakmotor"),
            ("Minn Kota Endura C2 55 elektromos csónakmotor", "/minn-kota-endura-c2-55-p890051/", 189990, "elektromos-csonakmotor"),
            ("Minn Kota Ultrex 112 i-Pilot Link", "/minn-kota-ultrex-112-p890052/", 1899990, "elektromos-csonakmotor"),
            ("Haswing Protruar 3.0 elektromos csónakmotor", "/haswing-protruar-3-p890002/", 289990, "elektromos-csonakmotor"),
            ("Haswing Cayman B 55 lbs elektromos motor", "/haswing-cayman-b-55-p890053/", 189990, "elektromos-csonakmotor"),
            ("Haswing Osapian 55 lbs elektromos motor", "/haswing-osapian-55-p890054/", 129990, "elektromos-csonakmotor"),
            ("MotorGuide Xi5 105 lbs elektromos csónakmotor", "/motorguide-xi5-105-p890055/", 1099990, "elektromos-csonakmotor"),
            ("MotorGuide Tour Pro 109 lbs", "/motorguide-tour-pro-109-p890056/", 1499990, "elektromos-csonakmotor"),
            ("Rhino BLX 70 elektromos csónakmotor", "/rhino-blx-70-p890057/", 179990, "elektromos-csonakmotor"),
            ("Lowrance Ghost 52\" elektromos motor", "/lowrance-ghost-52-p890058/", 1599990, "elektromos-csonakmotor"),
            # Outboard motors (petrol)
            ("Mercury F5 MH csónakmotor", "/mercury-f5-mh-p890003/", 549990, "csonakmotor"),
            ("Mercury F9.9 EL csónakmotor", "/mercury-f9-9-el-p890059/", 1149990, "csonakmotor"),
            ("Mercury F20 EL csónakmotor", "/mercury-f20-el-p890060/", 1699990, "csonakmotor"),
            ("Yamaha F6 CMHS csónakmotor", "/yamaha-f6-cmhs-p890061/", 649990, "csonakmotor"),
            ("Yamaha F9.9 JMHS csónakmotor", "/yamaha-f9-9-jmhs-p890062/", 1099990, "csonakmotor"),
            ("Yamaha F25 GMHS csónakmotor", "/yamaha-f25-gmhs-p890063/", 1899990, "csonakmotor"),
            ("Suzuki DF6A csónakmotor", "/suzuki-df6a-p890064/", 599990, "csonakmotor"),
            ("Suzuki DF20A csónakmotor", "/suzuki-df20a-p890065/", 1599990, "csonakmotor"),
            ("Honda BF5 csónakmotor", "/honda-bf5-p890066/", 599990, "csonakmotor"),
            ("Honda BF15 csónakmotor", "/honda-bf15-p890067/", 1399990, "csonakmotor"),
            ("Tohatsu MFS6D csónakmotor", "/tohatsu-mfs6d-p890068/", 579990, "csonakmotor"),
            ("Tohatsu MFS20E csónakmotor", "/tohatsu-mfs20e-p890069/", 1549990, "csonakmotor"),
            ("Parsun F9.8 BMS csónakmotor", "/parsun-f9-8-bms-p890070/", 499990, "csonakmotor"),
            ("Hidea HDF5HS csónakmotor", "/hidea-hdf5hs-p890071/", 399990, "csonakmotor"),
            # Inflatable & RIB boats
            ("Kolibri KM-330D gumicsónak", "/kolibri-km-330d-p890004/", 349990, "gumicsónak"),
            ("Kolibri KM-400DSL gumicsónak", "/kolibri-km-400dsl-p890072/", 549990, "gumicsónak"),
            ("Aqua Marina Deluxe 360 gumicsónak", "/aqua-marina-deluxe-360-p890073/", 279990, "gumicsónak"),
            ("Intex Mariner 4 gumicsónak", "/intex-mariner-4-p890074/", 189990, "gumicsónak"),
            ("Highfield CL360 RIB csónak", "/highfield-cl360-p890075/", 1899990, "rib-csónak"),
            ("Honda Honwave T40 RIB csónak", "/honda-honwave-t40-p890076/", 799990, "rib-csónak"),
            # Fish finders / Sonar
            ("Lowrance HDS-12 Live halradar", "/lowrance-hds-12-live-p890005/", 699990, "halradar"),
            ("Lowrance Hook Reveal 7 TripleShot", "/lowrance-hook-reveal-7-p890077/", 249990, "halradar"),
            ("Humminbird Helix 7 CHIRP MSI GPS G4N", "/humminbird-helix-7-p890078/", 399990, "halradar"),
            ("Humminbird SOLIX 15 CHIRP MSI+", "/humminbird-solix-15-p890079/", 1999990, "halradar"),
            ("Deeper PRO+ 2 horgász szonár", "/deeper-pro-plus-2-p890080/", 129990, "halradar"),
            ("Raymarine Element 9 HV halradar", "/raymarine-element-9-p890081/", 549990, "halradar"),
            # Fishing gear
            ("Shimano Stradic FL 4000 orsó", "/shimano-stradic-fl-4000-p890082/", 79990, "horgasz-felszereles"),
            ("Daiwa Tatula Elite 7'3\" pergető bot", "/daiwa-tatula-elite-p890083/", 109990, "horgasz-felszereles"),
            # Boat accessories
            ("Minn Kota MK-330D fedélzeti töltő", "/minn-kota-mk330d-p890084/", 119990, "csonak-tartozek"),
            ("Minn Kota Talon 12 ft Shallow Water Anchor", "/minn-kota-talon-12-p890085/", 699990, "csonak-tartozek"),
            # Water sports
            ("Aqua Marina Fusion SUP deszka", "/aqua-marina-fusion-sup-p890006/", 189990, "sup"),
            ("Jobe Thunder 1 személyes fánk", "/jobe-thunder-p890007/", 49990, "vizisport"),
            ("Jobe Vanity 15.0 wakeboard", "/jobe-vanity-15-p890086/", 159990, "vizisport"),
            # Musical instruments
            ("Fender Player Stratocaster elektromos gitár", "/fender-player-stratocaster-p890008/", 329990, "elektromos-gitar"),
            ("Yamaha FG800 akusztikus gitár", "/yamaha-fg800-p890009/", 89990, "akusztikus-gitar"),
            ("Roland TD-17KV elektromos dobszett", "/roland-td-17kv-p890010/", 449990, "dob"),
            ("Fender Player Jazz Bass basszusgitár", "/fender-player-jazz-bass-p890087/", 349990, "basszusgitar"),
            ("Ibanez SR300E basszusgitár", "/ibanez-sr300e-p890088/", 159990, "basszusgitar"),
        ],
    },
    "CZ": {
        "site": "heureka_cz",
        "currency": "CZK",
        "base_url": "https://www.heureka.cz",
        "products": [
            # Electric boat motors
            ("Minn Kota Terrova 80 i-Pilot elektrický lodní motor", "/minn-kota-terrova-80/", 49990, "elektricke-lodni-motory"),
            ("Minn Kota Riptide Terrova 112", "/minn-kota-riptide-terrova-112/", 79990, "elektricke-lodni-motory"),
            ("Minn Kota Endura C2 55", "/minn-kota-endura-c2-55/", 11990, "elektricke-lodni-motory"),
            ("Haswing Protruar 3.0 elektrický lodní motor", "/haswing-protruar-3/", 17990, "elektricke-lodni-motory"),
            ("Haswing Cayman B 55 lbs", "/haswing-cayman-b-55/", 11590, "elektricke-lodni-motory"),
            ("Haswing Osapian 55 lbs", "/haswing-osapian-55/", 7990, "elektricke-lodni-motory"),
            ("MotorGuide Xi5 105 lbs", "/motorguide-xi5-105/", 67990, "elektricke-lodni-motory"),
            ("Rhino BLX 70", "/rhino-blx-70/", 10990, "elektricke-lodni-motory"),
            # Outboard motors
            ("Mercury F5 MH přívěsný motor", "/mercury-f5-mh/", 33990, "lodni-motory"),
            ("Mercury F20 EL", "/mercury-f20-el/", 104990, "lodni-motory"),
            ("Yamaha F6 CMHS", "/yamaha-f6-cmhs/", 39990, "lodni-motory"),
            ("Yamaha F25 GMHS", "/yamaha-f25-gmhs/", 117990, "lodni-motory"),
            ("Suzuki DF6A", "/suzuki-df6a/", 36990, "lodni-motory"),
            ("Honda BF5", "/honda-bf5/", 36990, "lodni-motory"),
            ("Tohatsu MFS6D", "/tohatsu-mfs6d/", 35490, "lodni-motory"),
            ("Parsun F9.8 BMS", "/parsun-f9-8-bms/", 30990, "lodni-motory"),
            # Boats
            ("Kolibri KM-330D nafukovací člun", "/kolibri-km-330d/", 21990, "nafukovaci-cluny"),
            ("Aqua Marina Deluxe 360 člun", "/aqua-marina-deluxe-360/", 17290, "nafukovaci-cluny"),
            ("Highfield CL360 RIB", "/highfield-cl360/", 117990, "rib-cluny"),
            # Fish finders
            ("Lowrance HDS-12 Live sonar", "/lowrance-hds-12-live/", 42990, "sonary-echoluty"),
            ("Lowrance Hook Reveal 7", "/lowrance-hook-reveal-7/", 15390, "sonary-echoluty"),
            ("Humminbird Helix 7 CHIRP", "/humminbird-helix-7/", 24590, "sonary-echoluty"),
            ("Deeper PRO+ 2 sonar", "/deeper-pro-plus-2/", 7990, "sonary-echoluty"),
            # Water sports
            ("Aqua Marina Fusion SUP", "/aqua-marina-fusion-sup/", 11990, "paddleboardy"),
            ("Jobe Thunder tažný kruh", "/jobe-thunder/", 2990, "tahane-vodní-atrakce"),
            # Musical instruments
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
            # Electric boat motors
            ("Minn Kota Terrova 80 i-Pilot", "/minn-kota-terrova-80/", 1999, "elektricke-lodne-motory"),
            ("Minn Kota Riptide Terrova 112", "/minn-kota-riptide-terrova-112/", 3199, "elektricke-lodne-motory"),
            ("Minn Kota Endura C2 55", "/minn-kota-endura-c2-55/", 479, "elektricke-lodne-motory"),
            ("Haswing Protruar 3.0 elektrický lodný motor", "/haswing-protruar-3/", 719, "elektricke-lodne-motory"),
            ("Haswing Cayman B 55 lbs", "/haswing-cayman-b-55/", 459, "elektricke-lodne-motory"),
            ("MotorGuide Xi5 105 lbs", "/motorguide-xi5-105/", 2719, "elektricke-lodne-motory"),
            ("Rhino BLX 70", "/rhino-blx-70/", 439, "elektricke-lodne-motory"),
            # Outboard motors
            ("Mercury F5 MH závesný motor", "/mercury-f5-mh/", 1359, "lodne-motory"),
            ("Mercury F20 EL", "/mercury-f20-el/", 4199, "lodne-motory"),
            ("Yamaha F6 CMHS", "/yamaha-f6-cmhs/", 1599, "lodne-motory"),
            ("Yamaha F25 GMHS", "/yamaha-f25-gmhs/", 4719, "lodne-motory"),
            ("Suzuki DF6A", "/suzuki-df6a/", 1479, "lodne-motory"),
            ("Honda BF5", "/honda-bf5/", 1479, "lodne-motory"),
            ("Tohatsu MFS6D", "/tohatsu-mfs6d/", 1419, "lodne-motory"),
            # Boats
            ("Kolibri KM-330D nafukovací čln", "/kolibri-km-330d/", 879, "nafukovacie-clny"),
            ("Highfield CL360 RIB", "/highfield-cl360/", 4719, "rib-clny"),
            # Fish finders
            ("Lowrance HDS-12 Live sonar", "/lowrance-hds-12-live/", 1719, "sonary-echoloty"),
            ("Humminbird Helix 7 CHIRP", "/humminbird-helix-7/", 979, "sonary-echoloty"),
            ("Deeper PRO+ 2 sonar", "/deeper-pro-plus-2/", 319, "sonary-echoloty"),
            # Water sports
            ("Aqua Marina Fusion SUP", "/aqua-marina-fusion-sup/", 479, "paddleboardy"),
            ("Jobe Thunder ťahaný kruh", "/jobe-thunder/", 119, "vodne-atrakcie"),
            # Musical instruments
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
            # Electric boat motors
            ("Minn Kota Terrova 80 i-Pilot motor electric", "/minn-kota-terrova-80-p123/", 9999, "motoare-electrice-barca"),
            ("Minn Kota Riptide Terrova 112", "/minn-kota-riptide-terrova-112-p150/", 15999, "motoare-electrice-barca"),
            ("Minn Kota Endura C2 55", "/minn-kota-endura-c2-55-p151/", 2399, "motoare-electrice-barca"),
            ("Haswing Protruar 3.0 motor electric barca", "/haswing-protruar-3-p124/", 3599, "motoare-electrice-barca"),
            ("Haswing Cayman B 55 lbs", "/haswing-cayman-b-55-p152/", 2299, "motoare-electrice-barca"),
            ("MotorGuide Xi5 105 lbs", "/motorguide-xi5-105-p153/", 13499, "motoare-electrice-barca"),
            ("Rhino BLX 70", "/rhino-blx-70-p154/", 2199, "motoare-electrice-barca"),
            # Outboard motors
            ("Mercury F5 MH motor barca", "/mercury-f5-mh-p125/", 6799, "motoare-barca"),
            ("Mercury F20 EL", "/mercury-f20-el-p155/", 20999, "motoare-barca"),
            ("Yamaha F6 CMHS", "/yamaha-f6-cmhs-p156/", 7999, "motoare-barca"),
            ("Yamaha F25 GMHS", "/yamaha-f25-gmhs-p157/", 23499, "motoare-barca"),
            ("Suzuki DF6A", "/suzuki-df6a-p158/", 7399, "motoare-barca"),
            ("Honda BF5", "/honda-bf5-p159/", 7399, "motoare-barca"),
            ("Tohatsu MFS6D", "/tohatsu-mfs6d-p160/", 7099, "motoare-barca"),
            # Boats
            ("Kolibri KM-330D barca gonflabila", "/kolibri-km-330d-p126/", 4399, "barci-gonflabile"),
            ("Highfield CL360 RIB", "/highfield-cl360-p161/", 23499, "barci-rib"),
            # Fish finders
            ("Lowrance HDS-12 Live sonar", "/lowrance-hds-12-live-p127/", 8599, "sonar-fishfinder"),
            ("Humminbird Helix 7 CHIRP", "/humminbird-helix-7-p162/", 4899, "sonar-fishfinder"),
            ("Deeper PRO+ 2 sonar", "/deeper-pro-plus-2-p163/", 1599, "sonar-fishfinder"),
            # Water sports
            ("Aqua Marina Fusion SUP", "/aqua-marina-fusion-sup-p128/", 2399, "sup-paddleboard"),
            ("Jobe Thunder cerc tractabil", "/jobe-thunder-p129/", 599, "jucarii-acvatice-tractabile"),
            # Musical instruments
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
            # Electric boat motors
            ("Minn Kota Terrova 80 i-Pilot", "/minn-kota-terrova-80/", 1999, "elektricni-izvenkrmni-motorji"),
            ("Minn Kota Endura C2 55", "/minn-kota-endura-c2-55/", 479, "elektricni-izvenkrmni-motorji"),
            ("Haswing Protruar 3.0 električni izvenkrmni motor", "/haswing-protruar-3/", 729, "elektricni-izvenkrmni-motorji"),
            ("Haswing Cayman B 55 lbs", "/haswing-cayman-b-55/", 459, "elektricni-izvenkrmni-motorji"),
            ("MotorGuide Xi5 105 lbs", "/motorguide-xi5-105/", 2719, "elektricni-izvenkrmni-motorji"),
            ("Rhino BLX 70", "/rhino-blx-70/", 439, "elektricni-izvenkrmni-motorji"),
            # Outboard motors
            ("Mercury F5 MH izvenkrmni motor", "/mercury-f5-mh/", 1379, "izvenkrmni-motorji"),
            ("Mercury F20 EL", "/mercury-f20-el/", 4199, "izvenkrmni-motorji"),
            ("Yamaha F6 CMHS", "/yamaha-f6-cmhs/", 1599, "izvenkrmni-motorji"),
            ("Suzuki DF6A", "/suzuki-df6a/", 1479, "izvenkrmni-motorji"),
            ("Honda BF5", "/honda-bf5/", 1479, "izvenkrmni-motorji"),
            ("Tohatsu MFS6D", "/tohatsu-mfs6d/", 1419, "izvenkrmni-motorji"),
            # Boats
            ("Kolibri KM-330D napihljivi čoln", "/kolibri-km-330d/", 889, "napihljivi-colni"),
            ("Highfield CL360 RIB", "/highfield-cl360/", 4719, "rib-colni"),
            # Fish finders
            ("Lowrance HDS-12 Live sonar", "/lowrance-hds-12-live/", 1739, "sonarji-globinomeri"),
            ("Humminbird Helix 7 CHIRP", "/humminbird-helix-7/", 979, "sonarji-globinomeri"),
            ("Deeper PRO+ 2", "/deeper-pro-plus-2/", 319, "sonarji-globinomeri"),
            # Water sports
            ("Aqua Marina Fusion SUP", "/aqua-marina-fusion-sup/", 489, "sup-deske"),
            ("Jobe Thunder vlečna igrača", "/jobe-thunder/", 119, "vlecne-vodne-igrace"),
            # Musical instruments
            ("Fender Player Stratocaster", "/fender-player-stratocaster/", 819, "elektricne-kitare"),
            ("Yamaha FG800 akustična kitara", "/yamaha-fg800/", 229, "akusticne-kitare"),
            ("Roland TD-17KV elektronski bobni", "/roland-td-17kv/", 1139, "bobni-tolkala"),
        ],
    },
    "AT": {
        "site": "geizhals_at",
        "currency": "EUR",
        "base_url": "https://geizhals.at",
        "products": [
            # Electric boat motors
            ("Minn Kota Terrova 80 i-Pilot Elektro-Außenborder", "/a4560001.html", 1949, "elektro_aussenborder"),
            ("Minn Kota Riptide Terrova 112", "/a4560050.html", 3149, "elektro_aussenborder"),
            ("Minn Kota Endura C2 55", "/a4560051.html", 469, "elektro_aussenborder"),
            ("Haswing Protruar 3.0 Elektro-Außenborder", "/a4560002.html", 699, "elektro_aussenborder"),
            ("Haswing Cayman B 55 lbs", "/a4560052.html", 449, "elektro_aussenborder"),
            ("MotorGuide Xi5 105 lbs", "/a4560053.html", 2669, "elektro_aussenborder"),
            ("Rhino BLX 70", "/a4560054.html", 429, "elektro_aussenborder"),
            # Outboard motors
            ("Mercury F5 MH Außenbordmotor", "/a4560003.html", 1329, "aussenborder"),
            ("Mercury F20 EL", "/a4560055.html", 4099, "aussenborder"),
            ("Yamaha F6 CMHS", "/a4560056.html", 1559, "aussenborder"),
            ("Yamaha F25 GMHS", "/a4560057.html", 4619, "aussenborder"),
            ("Suzuki DF6A", "/a4560058.html", 1449, "aussenborder"),
            ("Honda BF5", "/a4560059.html", 1449, "aussenborder"),
            ("Tohatsu MFS6D", "/a4560060.html", 1389, "aussenborder"),
            # Boats
            ("Kolibri KM-330D Schlauchboot", "/a4560004.html", 859, "schlauchboote"),
            ("Highfield CL360 RIB Boot", "/a4560061.html", 4619, "rib_boote"),
            # Fish finders
            ("Lowrance HDS-12 Live Echolot", "/a4560005.html", 1689, "echolote"),
            ("Humminbird Helix 7 CHIRP", "/a4560062.html", 959, "echolote"),
            ("Deeper PRO+ 2 Echolot", "/a4560063.html", 309, "echolote"),
            # Water sports
            ("Aqua Marina Fusion SUP Board", "/a4560006.html", 469, "sup"),
            ("Jobe Thunder Towable Tube", "/a4560007.html", 109, "wasserattraktionen"),
            # Musical instruments
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
            # Electric boat motors
            ("Minn Kota Terrova 80 i-Pilot Elektro-Außenborder", "/a4560001.html", 1899, "elektro_aussenborder"),
            ("Minn Kota Riptide Terrova 112", "/a4560050.html", 3099, "elektro_aussenborder"),
            ("Minn Kota Endura C2 55", "/a4560051.html", 459, "elektro_aussenborder"),
            ("Minn Kota Ultrex 112 i-Pilot Link", "/a4560064.html", 4699, "elektro_aussenborder"),
            ("Haswing Protruar 3.0 Elektro-Außenborder", "/a4560002.html", 679, "elektro_aussenborder"),
            ("Haswing Cayman B 55 lbs", "/a4560052.html", 439, "elektro_aussenborder"),
            ("Haswing Osapian 55 lbs", "/a4560065.html", 329, "elektro_aussenborder"),
            ("MotorGuide Xi5 105 lbs", "/a4560053.html", 2619, "elektro_aussenborder"),
            ("MotorGuide Tour Pro 109 lbs", "/a4560066.html", 3699, "elektro_aussenborder"),
            ("Rhino BLX 70", "/a4560054.html", 419, "elektro_aussenborder"),
            ("Lowrance Ghost 52\"", "/a4560067.html", 3949, "elektro_aussenborder"),
            # Outboard motors
            ("Mercury F5 MH Außenbordmotor", "/a4560003.html", 1299, "aussenborder"),
            ("Mercury F9.9 EL", "/a4560068.html", 2799, "aussenborder"),
            ("Mercury F20 EL", "/a4560055.html", 3999, "aussenborder"),
            ("Yamaha F6 CMHS", "/a4560056.html", 1529, "aussenborder"),
            ("Yamaha F9.9 JMHS", "/a4560069.html", 2699, "aussenborder"),
            ("Yamaha F25 GMHS", "/a4560057.html", 4549, "aussenborder"),
            ("Suzuki DF6A", "/a4560058.html", 1419, "aussenborder"),
            ("Suzuki DF20A", "/a4560070.html", 3899, "aussenborder"),
            ("Honda BF5", "/a4560059.html", 1419, "aussenborder"),
            ("Honda BF15", "/a4560071.html", 3449, "aussenborder"),
            ("Tohatsu MFS6D", "/a4560060.html", 1359, "aussenborder"),
            ("Tohatsu MFS20E", "/a4560072.html", 3799, "aussenborder"),
            ("Parsun F9.8 BMS", "/a4560073.html", 1229, "aussenborder"),
            ("Hidea HDF5HS", "/a4560074.html", 979, "aussenborder"),
            # Boats
            ("Kolibri KM-330D Schlauchboot", "/a4560004.html", 839, "schlauchboote"),
            ("Kolibri KM-400DSL Schlauchboot", "/a4560075.html", 1349, "schlauchboote"),
            ("Aqua Marina Deluxe 360", "/a4560076.html", 679, "schlauchboote"),
            ("Highfield CL360 RIB Boot", "/a4560061.html", 4549, "rib_boote"),
            ("Honda Honwave T40 RIB", "/a4560077.html", 1949, "rib_boote"),
            # Fish finders
            ("Lowrance HDS-12 Live Echolot", "/a4560005.html", 1649, "echolote"),
            ("Lowrance Hook Reveal 7 TripleShot", "/a4560078.html", 609, "echolote"),
            ("Humminbird Helix 7 CHIRP MSI GPS G4N", "/a4560062.html", 949, "echolote"),
            ("Humminbird SOLIX 15 CHIRP MSI+", "/a4560079.html", 4899, "echolote"),
            ("Deeper PRO+ 2 Echolot", "/a4560063.html", 299, "echolote"),
            ("Raymarine Element 9 HV", "/a4560080.html", 1349, "echolote"),
            # Fishing gear
            ("Shimano Stradic FL 4000 Rolle", "/a4560081.html", 199, "angelzubehoer"),
            ("Daiwa Tatula Elite 7'3\" Rute", "/a4560082.html", 269, "angelzubehoer"),
            # Boat accessories
            ("Minn Kota MK-330D Bordladegerät", "/a4560083.html", 299, "bootszubehoer"),
            ("Minn Kota Talon 12 ft Anker", "/a4560084.html", 1699, "bootszubehoer"),
            # Water sports
            ("Aqua Marina Fusion SUP Board", "/a4560006.html", 449, "sup"),
            ("Jobe Thunder Towable Tube", "/a4560007.html", 99, "wasserattraktionen"),
            ("Jobe Vanity 15.0 Wakeboard", "/a4560085.html", 389, "wasserski"),
            # Musical instruments
            ("Fender Player Stratocaster", "/a4560008.html", 769, "e_gitarren"),
            ("Yamaha FG800 Akustikgitarre", "/a4560009.html", 209, "akustikgitarren"),
            ("Roland TD-17KV E-Drum Set", "/a4560010.html", 1079, "schlagzeug"),
            ("Fender Player Jazz Bass", "/a4560086.html", 849, "bassgitarren"),
            ("Ibanez SR300E Bass", "/a4560087.html", 389, "bassgitarren"),
        ],
    },
    "PL": {
        "site": "ceneo",
        "currency": "PLN",
        "base_url": "https://www.ceneo.pl",
        "products": [
            # Electric boat motors
            ("Minn Kota Terrova 80 i-Pilot silnik elektryczny", "/234560001", 8699, "Silniki_elektryczne_do_lodzi"),
            ("Minn Kota Riptide Terrova 112", "/234560050", 13999, "Silniki_elektryczne_do_lodzi"),
            ("Minn Kota Endura C2 55", "/234560051", 2099, "Silniki_elektryczne_do_lodzi"),
            ("Haswing Protruar 3.0 silnik elektryczny", "/234560002", 3099, "Silniki_elektryczne_do_lodzi"),
            ("Haswing Cayman B 55 lbs", "/234560052", 1999, "Silniki_elektryczne_do_lodzi"),
            ("Haswing Osapian 55 lbs", "/234560053", 1399, "Silniki_elektryczne_do_lodzi"),
            ("MotorGuide Xi5 105 lbs", "/234560054", 11799, "Silniki_elektryczne_do_lodzi"),
            ("Rhino BLX 70", "/234560055", 1899, "Silniki_elektryczne_do_lodzi"),
            # Outboard motors
            ("Mercury F5 MH silnik zaburtowy", "/234560003", 5899, "Silniki_zaburtowe"),
            ("Mercury F20 EL", "/234560056", 18299, "Silniki_zaburtowe"),
            ("Yamaha F6 CMHS", "/234560057", 6999, "Silniki_zaburtowe"),
            ("Yamaha F25 GMHS", "/234560058", 20599, "Silniki_zaburtowe"),
            ("Suzuki DF6A", "/234560059", 6399, "Silniki_zaburtowe"),
            ("Honda BF5", "/234560060", 6399, "Silniki_zaburtowe"),
            ("Tohatsu MFS6D", "/234560061", 6149, "Silniki_zaburtowe"),
            ("Parsun F9.8 BMS", "/234560062", 5399, "Silniki_zaburtowe"),
            # Boats
            ("Kolibri KM-330D ponton", "/234560004", 3799, "Pontony_i_lodzie_dmuchane"),
            ("Highfield CL360 RIB", "/234560063", 20499, "Lodzie_RIB"),
            # Fish finders
            ("Lowrance HDS-12 Live echosonda", "/234560005", 7499, "Echosondy_i_sonar"),
            ("Humminbird Helix 7 CHIRP", "/234560064", 4299, "Echosondy_i_sonar"),
            ("Deeper PRO+ 2 sonar", "/234560065", 1399, "Echosondy_i_sonar"),
            # Water sports
            ("Aqua Marina Fusion deska SUP", "/234560006", 2099, "Deski_SUP"),
            ("Jobe Thunder kolo wodne", "/234560007", 529, "Holowane_atrakcje_wodne"),
            # Musical instruments
            ("Fender Player Stratocaster", "/234560008", 3499, "Gitary_elektryczne"),
            ("Yamaha FG800 gitara akustyczna", "/234560009", 959, "Gitary_akustyczne"),
            ("Roland TD-17KV perkusja elektroniczna", "/234560010", 4899, "Perkusja"),
        ],
    },
}


def generate_demo_results(countries: list[str], max_products: int = 50) -> list[ScrapeResult]:
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
