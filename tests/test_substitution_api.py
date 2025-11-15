from __future__ import annotations

from typing import Any, Dict, Optional

import math
import json

from fastapi.testclient import TestClient

# Ensure imports work when running pytest from repo root
from services.substitution_service.main import app  # type: ignore
from services.substitution_service.data_loaders import product_data_df  # type: ignore


def _norm_gtin(val: Any) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, (int,)):
        return str(val)
    if isinstance(val, float):
        if math.isnan(val):
            return None
        i = int(round(val))
        if abs(val - i) < 1e-9:
            return str(i)
        return str(val)
    s = str(val)
    if s.endswith(".0"):
        return s[:-2]
    return s


def _gtin_to_category() -> Dict[str, str]:
    df = product_data_df()
    mapping: Dict[str, str] = {}
    if "salesUnitGtin" in df.columns:
        for _, row in df.iterrows():
            gtin = _norm_gtin(row.get("salesUnitGtin"))
            cat = row.get("category")
            if gtin is not None and cat is not None:
                mapping[gtin] = str(cat)
    return mapping


def test_substitution_suggest_basic_roundtrip():
    client = TestClient(app)
    # A small set of known GTINs observed in the dataset
    skus = ["6408430001071", "6416597016579", "6416796729140", "5017764112257"]
    cat_map = _gtin_to_category()
    for sku in skus:
        resp = client.post("/substitution/suggest", json={"sku": sku, "k": 3})
        assert resp.status_code == 200, f"status {resp.status_code} for sku {sku}: {resp.text}"
        data = resp.json()
        assert data["sku"] == sku
        assert "recommendations" in data
        recs = data["recommendations"]
        assert isinstance(recs, list)
        assert len(recs) <= 3
        # Scores sorted descending
        scores = [r["score"] for r in recs]
        assert scores == sorted(scores, reverse=True)
        # Unique candidate skus, none equal to original
        cand_skus = [r["sku"] for r in recs]
        assert len(set(cand_skus)) == len(cand_skus)
        assert all(c != sku for c in cand_skus)
        # Optional name fields
        for r in recs:
            assert "name" in r
        # If we have categories for both, validate same category constraint
        if sku in cat_map:
            orig_cat = cat_map[sku]
            for csku in cand_skus:
                if csku in cat_map:
                    assert cat_map[csku] == orig_cat
        # Emit human-readable output for manual inspection (use `-s` to see)
        summary = {
            "sku": data.get("sku"),
            "name": data.get("name"),
            "recommendations": [
                {"sku": r["sku"], "name": r.get("name"), "score": r["score"]} for r in recs
            ],
        }
        print("[TestOutput]", json.dumps(summary, ensure_ascii=False))


