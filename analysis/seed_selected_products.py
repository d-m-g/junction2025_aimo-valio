"""
Utility script that wipes the warehouse demo tables and populates them with the
12 curated products from `selected_product.json`.

Usage:
    cd junction2025_aimo-valio
    python analysis/seed_selected_products.py --qty 25
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, Iterable

import psycopg
from psycopg.rows import dict_row

# Ensure repo-root imports
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.substitution_service.candidates import _normalize_id, _select_by_gtin  # type: ignore  # noqa: E402
from services.substitution_service.availability import get_db_conninfo  # type: ignore  # noqa: E402

SELECTED_PRODUCTS_PATH = REPO_ROOT / "selected_product.json"


def load_selected_products() -> Iterable[Dict[str, Any]]:
    import json

    catalog = json.loads(SELECTED_PRODUCTS_PATH.read_text(encoding="utf-8"))
    for category in catalog.get("categories", []):
        for group in category.get("groups", []):
            for product in group.get("products", []):
                yield product


def extract_name(product: Dict[str, Any]) -> str:
    synkka = product.get("synkkaData") or {}
    names = synkka.get("names")
    if isinstance(names, list):
        preferred = ["en", "fi", "sv"]
        first_any: str | None = None
        for entry in names:
            if isinstance(entry, dict):
                value = entry.get("value")
                if isinstance(value, str) and value:
                    if first_any is None:
                        first_any = value
                    if entry.get("language") in preferred:
                        return value
        if first_any:
            return first_any
    vendor = product.get("vendorName")
    if isinstance(vendor, str) and vendor:
        return vendor
    brand = product.get("brand")
    if isinstance(brand, str) and brand:
        return brand
    gtin = _normalize_id(product.get("salesUnitGtin")) or "product"
    return f"Product {gtin}"


def extract_unit(product: Dict[str, Any]) -> str:
    sales_unit = product.get("salesUnit")
    if isinstance(sales_unit, str) and sales_unit:
        return sales_unit
    base_unit = product.get("baseUnit")
    if isinstance(base_unit, str) and base_unit:
        return base_unit
    return "ST"


def upsert_products(initial_qty: float) -> int:
    conninfo = get_db_conninfo()
    count = 0
    with psycopg.connect(conninfo, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("TRUNCATE TABLE order_items, orders, warehouse_items RESTART IDENTITY CASCADE")
            except psycopg.Error:
                conn.rollback()
                cur.execute("DELETE FROM order_items")
                cur.execute("DELETE FROM orders")
                cur.execute("DELETE FROM warehouse_items")
            for product in load_selected_products():
                gtin = _normalize_id(product.get("salesUnitGtin")) or _normalize_id(
                    (product.get("synkkaData") or {}).get("gtin")
                )
                if not gtin:
                    continue
                line_id = abs(hash(gtin)) % 2_000_000_000
                name = extract_name(product)
                unit = extract_unit(product)
                cur.execute(
                    """
                    INSERT INTO warehouse_items (line_id, product_code, name, qty, unit)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (line_id) DO UPDATE SET
                        product_code = EXCLUDED.product_code,
                        name = EXCLUDED.name,
                        qty = EXCLUDED.qty,
                        unit = EXCLUDED.unit
                    """,
                    (line_id, gtin, name, initial_qty, unit),
                )
                count += 1
        conn.commit()
    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed warehouse_items with selected_product.json entries.")
    parser.add_argument(
        "--qty",
        type=float,
        default=25.0,
        help="Quantity to assign to every seeded product (default: 25.0)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = upsert_products(args.qty)
    print(f"[seed_selected_products] Seeded {count} products with qty={args.qty}")


if __name__ == "__main__":
    main()


