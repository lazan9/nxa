"""Site-specific scraper implementations."""

from .arukereso import ArukeresoScraper
from .heureka import HeurekaCzScraper, HeurekaSkScraper
from .compari import CompariScraper
from .ceneje import CenejeScraper
from .geizhals import GeizhalsAtScraper, GeizhalsDecraper
from .ceneo import CeneoScraper

SCRAPERS = {
    "arukereso": ArukeresoScraper,
    "heureka_cz": HeurekaCzScraper,
    "heureka_sk": HeurekaSkScraper,
    "compari": CompariScraper,
    "ceneje": CenejeScraper,
    "geizhals_at": GeizhalsAtScraper,
    "geizhals_de": GeizhalsDecraper,
    "ceneo": CeneoScraper,
}

COUNTRY_MAP = {
    "hu": "arukereso",
    "cz": "heureka_cz",
    "sk": "heureka_sk",
    "ro": "compari",
    "si": "ceneje",
    "at": "geizhals_at",
    "de": "geizhals_de",
    "pl": "ceneo",
}

__all__ = [
    "SCRAPERS",
    "COUNTRY_MAP",
    "ArukeresoScraper",
    "HeurekaCzScraper",
    "HeurekaSkScraper",
    "CompariScraper",
    "CenejeScraper",
    "GeizhalsAtScraper",
    "GeizhalsDecraper",
    "CeneoScraper",
]
