from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import math
import pandas as pd

from .features import compute_pair_features
from .data_loaders import product_data_df
from .model import load_default_model


def _normalize_id(val: Any) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, (int,)):
        return str(val)
    if isinstance(val, float):
        # NaN guard
        if math.isnan(val):
            return None
        # Convert 6408430001071.0 -> "6408430001071"
        i = int(round(val))
        if abs(val - i) < 1e-9:
            return str(i)
        return str(val)
    s = str(val)
    # Handle textual NaN/None/empty
    sl = s.strip().lower()
    if sl in ("nan", "none", ""):
        return None
    if s.endswith(".0"):
        return s[:-2]
    return s


def _select_by_gtin(df: pd.DataFrame, gtin: str) -> Optional[Dict[str, Any]]:
    # Try direct on salesUnitGtin
    if "salesUnitGtin" in df.columns:
        s = df["salesUnitGtin"].apply(_normalize_id)
        hits = df[s == gtin]
        if not hits.empty:
            return hits.iloc[0].to_dict()
    # Try synkkaData.gtin if present
    if "synkkaData" in df.columns:
        for _, row in df.iterrows():
            sd = row.get("synkkaData")
            if isinstance(sd, dict) and _normalize_id(sd.get("gtin")) == gtin:
                return row.to_dict()
    return None


def _safe_get_category(product: Dict[str, Any]) -> Optional[str]:
    cat = product.get("category")
    return str(cat) if cat is not None else None


def suggest_candidates_by_gtin(
    sku: str,
    k: int = 3,
    max_pool: int = 500,
) -> Tuple[Dict[str, Any], List[Tuple[str, float, Dict[str, Any]]]]:
    """
    Returns:
      original_product, list of (candidate_gtin, score, candidate_row_dict)
    """
    products = product_data_df()
    orig = _select_by_gtin(products, _normalize_id(sku) or sku)
    if orig is None:
        return {}, []

    cat = _safe_get_category(orig)
    if not cat:
        return orig, []

    # Build pool: same category, excluding original
    same_cat = products[products["category"].astype(str) == cat].copy()
    # Randomly limit pool size for speed
    if len(same_cat) > max_pool:
        same_cat = same_cat.sample(n=max_pool, random_state=42)
    # Exclude original by GTIN
    orig_gtin = _normalize_id(orig.get("salesUnitGtin")) or _normalize_id(orig.get("synkkaData", {}).get("gtin"))
    def not_same(row: pd.Series) -> bool:
        r_gtin = _normalize_id(row.get("salesUnitGtin")) or _normalize_id((row.get("synkkaData") or {}).get("gtin"))
        return r_gtin != orig_gtin
    pool = same_cat[same_cat.apply(not_same, axis=1)]

    scored: List[Tuple[str, float, Dict[str, Any]]] = []
    scorer = load_default_model()
    for _, row in pool.iterrows():
        cand = row.to_dict()
        feats = compute_pair_features(orig, cand)
        if scorer:
            score = scorer.score(feats)
        else:
            # Heuristic weighted scoring fallback
            score = (
                1.5 * feats["name_jaccard"]
                + 0.8 * feats["size_similarity"]
                + 0.4 * feats["diet_compatible"]
                + 0.3 * feats["vendor_match"]
                - 1.0 * feats["allergen_conflict"]
                - 0.05 * feats["temperature_abs_diff"]
                + 0.3 * feats.get("popularity_overall", 0.0)
                + 0.5 * feats.get("popularity_by_category", 0.0)
            )
        cand_gtin = _normalize_id(cand.get("salesUnitGtin")) or _normalize_id((cand.get("synkkaData") or {}).get("gtin"))
        if cand_gtin:
            scored.append((cand_gtin, float(score), cand))

    # Sort and take top-k
    scored.sort(key=lambda x: x[1], reverse=True)
    return orig, scored[:k]


