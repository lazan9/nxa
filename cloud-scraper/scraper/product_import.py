"""Import product lists from SQL, XML, and XLSX for targeted scraping (Phase 2)."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text

from .models import ProductQuery

logger = logging.getLogger(__name__)


def import_from_xlsx(
    filepath: str,
    name_col: str = "name",
    sku_col: str = "sku",
    ean_col: str = "ean",
    brand_col: str = "brand",
    category_col: str = "category",
    price_col: str = "price",
    currency_col: str = "currency",
    sheet_name: Optional[str] = None,
) -> list[ProductQuery]:
    """Import product queries from an Excel file."""
    logger.info(f"Importing products from XLSX: {filepath}")
    df = pd.read_excel(filepath, sheet_name=sheet_name or 0)
    df.columns = [c.strip().lower() for c in df.columns]

    products = []
    for _, row in df.iterrows():
        pq = ProductQuery(
            name=str(row.get(name_col, row.get("name", row.get("product", "")))),
            sku=str(row.get(sku_col, row.get("sku", ""))),
            ean=str(row.get(ean_col, row.get("ean", row.get("barcode", "")))),
            brand=str(row.get(brand_col, row.get("brand", row.get("manufacturer", "")))),
            category=str(row.get(category_col, row.get("category", ""))),
            our_price=_safe_float(row.get(price_col, row.get("price"))),
            currency=str(row.get(currency_col, row.get("currency", ""))),
        )
        if pq.name and pq.name != "nan":
            products.append(pq)

    logger.info(f"Imported {len(products)} products from XLSX")
    return products


def import_from_xml(
    filepath: str,
    product_tag: str = "product",
    name_tag: str = "name",
    sku_tag: str = "sku",
    ean_tag: str = "ean",
    brand_tag: str = "brand",
    category_tag: str = "category",
    price_tag: str = "price",
    currency_tag: str = "currency",
) -> list[ProductQuery]:
    """Import product queries from an XML file.

    Supports common e-commerce XML feed formats:
    - Heureka XML feed
    - Google Shopping XML
    - Custom XML with configurable tags
    """
    logger.info(f"Importing products from XML: {filepath}")
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Strip namespace if present
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    products = []
    for item in root.iter(f"{ns}{product_tag}"):
        name = _xml_text(item, f"{ns}{name_tag}") or _xml_text(item, f"{ns}PRODUCTNAME")
        if not name:
            # Try common alternative tag names
            for alt in ("title", "PRODUCT", "item_name", "productname"):
                name = _xml_text(item, f"{ns}{alt}")
                if name:
                    break

        if not name:
            continue

        pq = ProductQuery(
            name=name,
            sku=_xml_text(item, f"{ns}{sku_tag}") or _xml_text(item, f"{ns}ITEM_ID") or "",
            ean=_xml_text(item, f"{ns}{ean_tag}") or _xml_text(item, f"{ns}EAN") or "",
            brand=_xml_text(item, f"{ns}{brand_tag}") or _xml_text(item, f"{ns}MANUFACTURER") or "",
            category=_xml_text(item, f"{ns}{category_tag}") or _xml_text(item, f"{ns}CATEGORYTEXT") or "",
            our_price=_safe_float(
                _xml_text(item, f"{ns}{price_tag}") or _xml_text(item, f"{ns}PRICE_VAT")
            ),
            currency=_xml_text(item, f"{ns}{currency_tag}") or "",
        )
        products.append(pq)

    logger.info(f"Imported {len(products)} products from XML")
    return products


def import_from_sql(
    connection_string: str,
    query: str,
    name_col: str = "name",
    sku_col: str = "sku",
    ean_col: str = "ean",
    brand_col: str = "brand",
    category_col: str = "category",
    price_col: str = "price",
    currency_col: str = "currency",
) -> list[ProductQuery]:
    """Import product queries from a SQL database.

    Args:
        connection_string: SQLAlchemy connection string, e.g.:
            - sqlite:///products.db
            - postgresql://user:pass@host/db
            - mysql+pymysql://user:pass@host/db
            - mssql+pyodbc://user:pass@host/db
        query: SQL query to execute
    """
    logger.info(f"Importing products from SQL: {connection_string.split('@')[-1]}")
    engine = create_engine(connection_string)

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    df.columns = [c.strip().lower() for c in df.columns]

    products = []
    for _, row in df.iterrows():
        pq = ProductQuery(
            name=str(row.get(name_col, row.get("name", row.get("product_name", "")))),
            sku=str(row.get(sku_col, row.get("sku", row.get("product_sku", "")))),
            ean=str(row.get(ean_col, row.get("ean", row.get("barcode", "")))),
            brand=str(row.get(brand_col, row.get("brand", row.get("manufacturer", "")))),
            category=str(row.get(category_col, row.get("category", ""))),
            our_price=_safe_float(row.get(price_col, row.get("price"))),
            currency=str(row.get(currency_col, row.get("currency", ""))),
        )
        if pq.name and pq.name != "nan":
            products.append(pq)

    logger.info(f"Imported {len(products)} products from SQL")
    return products


def import_products(source: str, **kwargs) -> list[ProductQuery]:
    """Auto-detect source type and import products.

    Args:
        source: File path (.xlsx, .xls, .xml) or SQL connection string
    """
    path = Path(source)
    if path.suffix in (".xlsx", ".xls"):
        return import_from_xlsx(source, **kwargs)
    elif path.suffix == ".xml":
        return import_from_xml(source, **kwargs)
    elif "://" in source:
        query = kwargs.pop("query", "SELECT * FROM products")
        return import_from_sql(source, query, **kwargs)
    else:
        raise ValueError(
            f"Unknown source type: {source}. "
            "Use .xlsx, .xml file or a SQL connection string (e.g. sqlite:///db.sqlite)"
        )


def _xml_text(parent, tag: str) -> Optional[str]:
    el = parent.find(tag)
    if el is not None and el.text:
        return el.text.strip()
    return None


def _safe_float(val) -> Optional[float]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(str(val).replace(",", ".").replace(" ", ""))
    except (ValueError, TypeError):
        return None
