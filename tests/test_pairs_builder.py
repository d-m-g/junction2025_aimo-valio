from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

import random

from services.substitution_service.data_loaders import product_data_df
from training.build_pairs_from_catalog import build_pairs_from_catalog, _extract_sub_gtins
from services.substitution_service.candidates import _normalize_id


def _gtin_category_maps() -> Tuple[Dict[str, str], Dict[str, Set[str]]]:
    """
    Returns:
      gtin_to_category: GTIN -> category string
      orig_to_catalog_subs: original GTIN -> set of catalog-declared substitute GTINs
    """
    df = product_data_df()
    gtin_to_category: Dict[str, str] = {}
    orig_to_catalog_subs: Dict[str, Set[str]] = {}
    if "salesUnitGtin" not in df.columns:
        return gtin_to_category, orig_to_catalog_subs
    for _, row in df.iterrows():
        gtin_raw = row.get("salesUnitGtin")
        gtin = _normalize_id(gtin_raw)
        if gtin is None:
            continue
        cat = row.get("category")
        if cat is not None:
            gtin_to_category[gtin] = str(cat)
        subs = _extract_sub_gtins(row.get("substitutions"))
        if subs:
            orig_to_catalog_subs.setdefault(gtin, set()).update(subs)
    return gtin_to_category, orig_to_catalog_subs


def test_build_pairs_from_catalog_basic_properties():
    pairs = build_pairs_from_catalog(max_neg_per_pos=3)
    assert isinstance(pairs, list)
    assert len(pairs) > 0
    # Check tuple structure and label domain on a sample
    sample = pairs[:500] if len(pairs) > 500 else pairs
    for tup in sample:
        assert isinstance(tup, tuple) and len(tup) == 3
        o, c, y = tup
        assert isinstance(o, str) and isinstance(c, str)
        assert o != c
        assert y in (0, 1)


def test_build_pairs_catalog_consistency():
    pairs = build_pairs_from_catalog(max_neg_per_pos=2)
    gtin_to_cat, orig_to_pos = _gtin_category_maps()
    # Randomly sample up to N pairs to validate
    random.seed(42)
    if len(pairs) > 400:
        sample = random.sample(pairs, 400)
    else:
        sample = pairs
    for o, c, y in sample:
        # If categories are known for both, they should match (pool is same-category)
        if o in gtin_to_cat and c in gtin_to_cat:
            assert gtin_to_cat[o] == gtin_to_cat[c]
        # Positives should appear in catalog-declared substitutions when available
        if y == 1 and o in orig_to_pos:
            assert c in orig_to_pos[o]
        # Negatives must not be equal to original and should not violate basic constraints
        if y == 0:
            assert o != c


