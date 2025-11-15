from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.substitution_service.data_loaders import product_data_df  # noqa: E402
from services.substitution_service.features import compute_pair_features  # noqa: E402


def _normalize_gtin_str(val: Any) -> Optional[str]:
    if val is None:
        return None
    # Numeric types
    if isinstance(val, (int,)):
        return str(val)
    if isinstance(val, float):
        if abs(val - round(val)) < 1e-9:
            return str(int(round(val)))
        return str(val)
    # Strings: strip trailing ".0" if present
    s = str(val)
    if s.endswith(".0"):
        return s[:-2]
    return s


def find_products_by_category(df: pd.DataFrame) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    grouped = df.groupby("category")
    for cat, group in grouped:
        if len(group) >= 2:
            g = group.reset_index(drop=True)
            orig = g.iloc[0].to_dict()
            cand = g.iloc[1].to_dict()
            return orig, cand
    raise RuntimeError("Could not find a category with at least two products")


def select_by_gtin(df: pd.DataFrame, gtin: str) -> Optional[Dict[str, Any]]:
    cols = [c for c in ["salesUnitGtin", "synkkaData"] if c in df.columns]
    # Direct match on salesUnitGtin if present
    if "salesUnitGtin" in cols:
        hit = df[df["salesUnitGtin"].astype(str) == str(gtin)]
        if not hit.empty:
            return hit.iloc[0].to_dict()
    # Look inside synkkaData.gtin if present
    if "synkkaData" in cols:
        for _, row in df.iterrows():
            sd = row.get("synkkaData")
            if isinstance(sd, dict) and str(sd.get("gtin", "")) == str(gtin):
                return row.to_dict()
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test for feature computation on product pairs.")
    parser.add_argument("--orig-gtin", type=str, help="Original product GTIN (salesUnitGtin or synkkaData.gtin)")
    parser.add_argument("--cand-gtin", type=str, help="Candidate product GTIN (salesUnitGtin or synkkaData.gtin)")
    args = parser.parse_args()

    df = product_data_df()
    # Ensure minimal columns exist
    if "category" not in df.columns:
        raise RuntimeError("Expected 'category' column in product data")

    if args.orig_gtin and args.cand_gtin:
        orig = select_by_gtin(df, args.orig_gtin)
        cand = select_by_gtin(df, args.cand_gtin)
        if orig is None or cand is None:
            raise RuntimeError("Could not find both products by provided GTINs")
    else:
        orig, cand = find_products_by_category(df)

    features = compute_pair_features(orig, cand)

    out = {
        "original": {
            "salesUnitGtin": _normalize_gtin_str(orig.get("salesUnitGtin")),
            "category": orig.get("category"),
            "vendorName": orig.get("vendorName"),
            "brand": orig.get("brand"),
            "salesUnit": orig.get("salesUnit"),
            "temperatureCondition": orig.get("temperatureCondition"),
        },
        "candidate": {
            "salesUnitGtin": _normalize_gtin_str(cand.get("salesUnitGtin")),
            "category": cand.get("category"),
            "vendorName": cand.get("vendorName"),
            "brand": cand.get("brand"),
            "salesUnit": cand.get("salesUnit"),
            "temperatureCondition": cand.get("temperatureCondition"),
        },
        "features": features,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


