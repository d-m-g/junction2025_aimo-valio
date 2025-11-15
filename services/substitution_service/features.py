from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Support both package-relative and absolute imports when run in different contexts
try:
    from .utils_text import jaccard_similarity, simple_tokenize
except Exception:  # pragma: no cover - fallback for direct script execution
    # Ensure repo root is on sys.path so `services.*` absolute import works
    REPO_ROOT = Path(__file__).resolve().parents[2]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from services.substitution_service.utils_text import jaccard_similarity, simple_tokenize


def _get(d: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def _collect_names(product: Dict[str, Any]) -> List[str]:
    # Prefer multilingual names under synkkaData.names[*].value; fallback to vendorName / brand
    names = []
    names_list = _get(product, ["synkkaData", "names"], [])
    if isinstance(names_list, list):
        for n in names_list:
            if isinstance(n, dict) and "value" in n and isinstance(n["value"], str):
                names.append(n["value"])
    # Fallbacks
    vendor = product.get("vendorName")
    if isinstance(vendor, str):
        names.append(vendor)
    brand = product.get("brand")
    if isinstance(brand, str):
        names.append(brand)
    return names


def _extract_allergen_sets(product: Dict[str, Any]) -> Tuple[set, set]:
    """
    Returns:
      contains_allergens: set of allergen ids marked as CONTAINS
      free_from_allergens: set of allergen ids marked as FREE_FROM (from nonAllergen or nutritionalClaim)
    """
    contains = set()
    free_from = set()
    classifications = product.get("classifications", [])
    if isinstance(classifications, list):
        for c in classifications:
            if not isinstance(c, dict):
                continue
            name = c.get("name")
            values = c.get("values", [])
            if not isinstance(values, list):
                continue
            if name == "allergen":
                for v in values:
                    if isinstance(v, dict) and v.get("unit") == "CONTAINS" and "id" in v:
                        contains.add(str(v["id"]))
            elif name == "nonAllergen":
                for v in values:
                    if isinstance(v, dict) and v.get("unit") == "FREE_FROM" and "id" in v:
                        free_from.add(str(v["id"]))
            elif name == "nutritionalClaim":
                for v in values:
                    # Some claims reflect diet restrictions; treat FREE_FROM similarly
                    if isinstance(v, dict) and v.get("unit") == "FREE_FROM" and "synkkaId" in v:
                        free_from.add(str(v["synkkaId"]))
    return contains, free_from


def _extract_preferred_unit_size(product: Dict[str, Any]) -> Optional[float]:
    """
    Heuristic for a comparable size value:
      - Try to use the smallest sales unit size if present in product['units'] -> sizeInBaseUnits for unitId matching product['salesUnit']
      - Fallback to allowedLotSize
    """
    sales_unit = product.get("salesUnit")
    units = product.get("units")
    if isinstance(units, list) and isinstance(sales_unit, str):
        for u in units:
            if isinstance(u, dict) and u.get("unitId") == sales_unit and isinstance(u.get("sizeInBaseUnits"), (int, float)):
                return float(u["sizeInBaseUnits"])
    # Fallback
    als = product.get("allowedLotSize")
    if isinstance(als, (int, float)):
        return float(als)
    return None


def _size_similarity(orig_size: Optional[float], cand_size: Optional[float]) -> float:
    """
    Symmetric size similarity: 1.0 if equal; decays as log-ratio diverges.
    """
    if not orig_size or not cand_size or orig_size <= 0 or cand_size <= 0:
        return 0.0
    r = orig_size / cand_size
    # Use log-distance; clamp at 0
    dist = abs(math.log(r))
    # Map distance to similarity in (0,1], e^{-dist}
    return math.exp(-dist)


def _temperature_diff(orig: Dict[str, Any], cand: Dict[str, Any]) -> float:
    to = orig.get("temperatureCondition")
    tc = cand.get("temperatureCondition")
    if isinstance(to, (int, float)) and isinstance(tc, (int, float)):
        return float(abs(float(to) - float(tc)))
    return 999.0


def _bool(value: bool) -> int:
    return 1 if value else 0


def compute_pair_features(
    original: Dict[str, Any],
    candidate: Dict[str, Any],
    popularity_overall: Optional[float] = None,
    popularity_by_category: Optional[float] = None,
) -> Dict[str, float]:
    """
    Compute numeric features describing suitability of candidate as a replacement for original.
    Inputs should be dict-like rows derived from the product catalog JSON.
    Popularity features (optional) can be provided from replacement history stats.
    """
    # Basic categorical matches
    category_match = _bool(original.get("category") == candidate.get("category"))
    # Treat matches as true only when both sides are present and equal
    ov = original.get("vendorName")
    cv = candidate.get("vendorName")
    vendor_match = _bool(isinstance(ov, str) and isinstance(cv, str) and ov == cv)
    ob = original.get("brand")
    cb = candidate.get("brand")
    brand_match = _bool(isinstance(ob, str) and isinstance(cb, str) and ob == cb)

    # Sales unit match and size similarity
    same_sales_unit = _bool(original.get("salesUnit") == candidate.get("salesUnit"))
    size_sim = _size_similarity(_extract_preferred_unit_size(original), _extract_preferred_unit_size(candidate))

    # Temperature proximity
    temp_diff = _temperature_diff(original, candidate)

    # Allergen/diet compatibility
    cand_contains, cand_free_from = _extract_allergen_sets(candidate)
    orig_contains, orig_free_from = _extract_allergen_sets(original)
    # Conflict if candidate CONTAINS something original explicitly FREE_FROM
    allergen_conflict = _bool(len(cand_contains & orig_free_from) > 0)
    # Diet compatibility: if original claims FREE_FROM_X, candidate should also be FREE_FROM_X (subset condition)
    diet_compatible = _bool(orig_free_from.issubset(cand_free_from) if orig_free_from else True)

    # Name similarity (multilingual names concatenated)
    name_tokens_o = set()
    for n in _collect_names(original):
        name_tokens_o |= simple_tokenize(n)
    name_tokens_c = set()
    for n in _collect_names(candidate):
        name_tokens_c |= simple_tokenize(n)
    name_jaccard = jaccard_similarity(name_tokens_o, name_tokens_c)

    # Popularity priors (optional; default to 0 if not provided)
    pop_overall = float(popularity_overall) if popularity_overall is not None else 0.0
    pop_by_cat = float(popularity_by_category) if popularity_by_category is not None else 0.0

    return {
        "category_match": float(category_match),
        "vendor_match": float(vendor_match),
        "brand_match": float(brand_match),
        "same_sales_unit": float(same_sales_unit),
        "size_similarity": float(size_sim),
        "temperature_abs_diff": float(temp_diff),
        "allergen_conflict": float(allergen_conflict),
        "diet_compatible": float(diet_compatible),
        "name_jaccard": float(name_jaccard),
        "popularity_overall": pop_overall,
        "popularity_by_category": pop_by_cat,
    }


