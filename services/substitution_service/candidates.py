from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Set

import math
from functools import lru_cache

import pandas as pd

from .features import compute_pair_features
from .data_loaders import product_data_df
from .utils_text import simple_tokenize, jaccard_similarity
# Heuristic-only scorer (model intentionally not used for MVP)


def heuristic_score(feats: Dict[str, float]) -> float:
    """
    Heuristic scoring used when no trained model is applied.
    Higher is better.
    """
    return (
        1.5 * feats["name_jaccard"]
        + 0.8 * feats["size_similarity"]
        + 0.4 * feats["diet_compatible"]
        + 0.3 * feats["vendor_match"]
        - 1.0 * feats["allergen_conflict"]
        - 0.05 * feats["temperature_abs_diff"]
        + 0.3 * feats.get("popularity_overall", 0.0)
        + 0.5 * feats.get("popularity_by_category", 0.0)
    )


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
    available_qty_by_code: Optional[Dict[str, float]] = None,
    required_qty: Optional[float] = None,
    fallback_name: Optional[str] = None,
) -> Tuple[Dict[str, Any], List[Tuple[str, float, Dict[str, Any]]]]:
    """
    Returns:
      original_product, list of (candidate_gtin, score, candidate_row_dict)
    """
    products = product_data_df()
    normalized_sku = _normalize_id(sku) or sku
    orig = _select_by_gtin(products, normalized_sku)
    if (not orig) and fallback_name:
        orig = _select_by_name(products, fallback_name)
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

    # If no availability map provided, attempt to resolve via callback from DB (optional, imported at API layer)
    if available_qty_by_code is None:
        try:
            # Create the candidate list of GTINs to resolve availability for
            cand_gtins: List[str] = []
            for _, row in pool.iterrows():
                cand = row.to_dict()
                cg = _normalize_id(cand.get("salesUnitGtin")) or _normalize_id((cand.get("synkkaData") or {}).get("gtin"))
                if cg:
                    cand_gtins.append(cg)
            # Lazy import to avoid hard dependency if DB not used
            from .availability import get_availability_for_gtins  # type: ignore
            available_qty_by_code = get_availability_for_gtins(cand_gtins)
            if not available_qty_by_code:
                # Treat empty map the same as no availability snapshot so we don't reject every candidate.
                available_qty_by_code = None
        except Exception:
            available_qty_by_code = None

    def _is_available(candidate_gtin: Optional[str]) -> bool:
        if available_qty_by_code is None:
            return True
        if not candidate_gtin:
            return False
        qty_avail = available_qty_by_code.get(candidate_gtin)
        if qty_avail is None:
            return False
        if required_qty is None:
            return qty_avail > 0
        return qty_avail >= float(required_qty)

    scored: List[Tuple[str, float, Dict[str, Any]]] = []
    scorer = None  # force heuristic-only scoring
    for _, row in pool.iterrows():
        cand = row.to_dict()
        feats = compute_pair_features(orig, cand)
        # Heuristic weighted scoring
        score = heuristic_score(feats)
        cand_gtin = _normalize_id(cand.get("salesUnitGtin")) or _normalize_id((cand.get("synkkaData") or {}).get("gtin"))
        if cand_gtin and _is_available(cand_gtin):
            scored.append((cand_gtin, float(score), cand))

    # Sort and take top-k
    scored.sort(key=lambda x: x[1], reverse=True)
    return orig, scored[:k]


def _collect_candidate_names(product: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    synkka = product.get("synkkaData")
    if isinstance(synkka, dict):
        entries = synkka.get("names")
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict):
                    value = entry.get("value")
                    if isinstance(value, str) and value:
                        names.append(value)
    vendor = product.get("vendorName")
    if isinstance(vendor, str) and vendor:
        names.append(vendor)
    brand = product.get("brand")
    if isinstance(brand, str) and brand:
        names.append(brand)
    return names


def _name_tokens(product: Dict[str, Any]) -> Set[str]:
    tokens: Set[str] = set()
    for text in _collect_candidate_names(product):
        tokens |= simple_tokenize(text)
    return tokens


def _normalize_token_key(name: str) -> Optional[Tuple[str, ...]]:
    tokens = sorted(simple_tokenize(name))
    if not tokens:
        return None
    return tuple(tokens)


@lru_cache(maxsize=2048)
def _lookup_gtin_by_tokens(token_key: Tuple[str, ...]) -> Optional[str]:
    df = product_data_df()
    target = set(token_key)
    best_score = 0.0
    best_gtin: Optional[str] = None
    for _, row in df.iterrows():
        product = row.to_dict()
        tokens = _name_tokens(product)
        if not tokens:
            continue
        score = jaccard_similarity(target, tokens)
        if score > best_score:
            candidate_gtin = _normalize_id(product.get("salesUnitGtin")) or _normalize_id(
                (product.get("synkkaData") or {}).get("gtin")
            )
            if candidate_gtin:
                best_score = score
                best_gtin = candidate_gtin
    if best_score < 0.2:
        return None
    return best_gtin


def _select_by_name(df: pd.DataFrame, name: str) -> Optional[Dict[str, Any]]:
    token_key = _normalize_token_key(name)
    if token_key is None:
        return None
    gtin = _lookup_gtin_by_tokens(token_key)
    if not gtin:
        return None
    return _select_by_gtin(df, gtin)


