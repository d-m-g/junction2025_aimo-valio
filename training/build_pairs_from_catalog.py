from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd

# Ensure repo root imports
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.substitution_service.data_loaders import product_data_df  # noqa: E402
from services.substitution_service.candidates import _normalize_id  # noqa: E402


def _extract_sub_gtins(substitutions: Any) -> List[str]:
    """
    Attempt to parse 'substitutions' field into a list of GTIN strings.
    Accepts several structures: list of str/int/float, or list of dicts with gtin/salesUnitGtin.
    """
    result: List[str] = []
    if substitutions is None or (isinstance(substitutions, float) and pd.isna(substitutions)):
        return result
    if isinstance(substitutions, (str,)):
        # Try JSON decoding if it looks like JSON
        s = substitutions.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                data = json.loads(s)
                return _extract_sub_gtins(data)
            except Exception:
                return result
        # Comma separated list
        for token in s.split(","):
            gt = _normalize_id(token.strip())
            if gt:
                result.append(gt)
        return result
    if isinstance(substitutions, list):
        for item in substitutions:
            if isinstance(item, (str, int, float)):
                gt = _normalize_id(item)
                if gt:
                    result.append(gt)
            elif isinstance(item, dict):
                gt = _normalize_id(item.get("gtin")) or _normalize_id(item.get("salesUnitGtin"))
                if gt:
                    result.append(gt)
        return result
    if isinstance(substitutions, dict):
        # Single object
        gt = _normalize_id(substitutions.get("gtin")) or _normalize_id(substitutions.get("salesUnitGtin"))
        if gt:
            result.append(gt)
        return result
    return result


def build_pairs_from_catalog(max_neg_per_pos: int = 5) -> List[Tuple[str, str, int]]:
    """
    Build (orig_gtin, cand_gtin, label) from product catalog 'substitutions' field.
    Positive pairs come directly from catalog; negatives are sampled from same category.
    """
    df = product_data_df()
    if "salesUnitGtin" not in df.columns:
        raise RuntimeError("Expected 'salesUnitGtin' in product data.")
    # Build category index
    df["__gtin__"] = df["salesUnitGtin"].apply(_normalize_id)
    df = df.dropna(subset=["__gtin__"])
    cat_groups = df.groupby(df["category"].astype(str))
    cat_to_gtins: Dict[str, List[str]] = {
        cat: [g for g in grp["__gtin__"].tolist() if g is not None] for cat, grp in cat_groups
    }
    # Collect positives
    pairs: List[Tuple[str, str, int]] = []
    pos_per_orig: Dict[str, Set[str]] = {}
    for _, row in df.iterrows():
        orig = row["__gtin__"]
        subs = _extract_sub_gtins(row.get("substitutions"))
        if not subs:
            continue
        for cand in subs:
            if cand and cand != orig:
                pairs.append((orig, cand, 1))
                pos_per_orig.setdefault(orig, set()).add(cand)
    # Negatives
    for _, row in df.iterrows():
        orig = row["__gtin__"]
        cat = str(row.get("category"))
        pool = cat_to_gtins.get(cat, [])
        bad: Set[str] = set()
        bad.add(orig)
        bad |= pos_per_orig.get(orig, set())
        neg_added = 0
        for cand in pool:
            if cand not in bad:
                pairs.append((orig, cand, 0))
                neg_added += 1
                if neg_added >= max_neg_per_pos * len(pos_per_orig.get(orig, [])):
                    break
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build pairs CSV from catalog substitutions field.")
    parser.add_argument("--out", type=str, default="data/pairs_from_catalog.csv", help="Output CSV path")
    parser.add_argument("--max-neg-per-pos", type=int, default=5, help="Max negatives per positive")
    args = parser.parse_args()

    pairs = build_pairs_from_catalog(max_neg_per_pos=args.max_neg_per_pos)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["orig_gtin", "cand_gtin", "label"])
        for o, c, y in pairs:
            w.writerow([o, c, y])
    print(f"[pairs] Wrote {len(pairs)} rows to {out_path}")


if __name__ == "__main__":
    main()


