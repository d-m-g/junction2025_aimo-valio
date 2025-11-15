from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split

# Ensure repo-root imports
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.substitution_service.data_loaders import (  # noqa: E402
    product_data_df,
)
from services.substitution_service.features import (  # noqa: E402
    compute_pair_features,
)
from services.substitution_service.candidates import _normalize_id  # noqa: E402


def load_pairs_csv(path: Path) -> pd.DataFrame:
    """
    Expected columns:
      - orig_gtin: str or numeric
      - cand_gtin: str or numeric
      - label: 1 or 0
    """
    df = pd.read_csv(path)
    expected = {"orig_gtin", "cand_gtin", "label"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"Pairs CSV missing required columns: {missing}")
    # Normalize IDs to strings
    df["orig_gtin"] = df["orig_gtin"].apply(_normalize_id)
    df["cand_gtin"] = df["cand_gtin"].apply(_normalize_id)
    df = df.dropna(subset=["orig_gtin", "cand_gtin"])
    return df


def _index_products_by_gtin(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    idx: Dict[str, Dict[str, Any]] = {}
    if "salesUnitGtin" not in df.columns:
        return idx
    for _, row in df.iterrows():
        gtin = _normalize_id(row.get("salesUnitGtin"))
        if gtin:
            idx[gtin] = row.to_dict()
    return idx


def build_feature_matrix(pairs: pd.DataFrame, prod_index: Dict[str, Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    feature_rows: List[List[float]] = []
    labels: List[int] = []
    # Feature names from compute_pair_features
    example = {
        "category_match": 0.0,
        "vendor_match": 0.0,
        "brand_match": 0.0,
        "same_sales_unit": 0.0,
        "size_similarity": 0.0,
        "temperature_abs_diff": 0.0,
        "allergen_conflict": 0.0,
        "diet_compatible": 0.0,
        "name_jaccard": 0.0,
        "popularity_overall": 0.0,
        "popularity_by_category": 0.0,
    }
    feature_names = list(example.keys())
    for _, r in pairs.iterrows():
        o = prod_index.get(r["orig_gtin"])
        c = prod_index.get(r["cand_gtin"])
        if not o or not c:
            continue
        feats = compute_pair_features(o, c)
        row = [float(feats.get(fn, 0.0)) for fn in feature_names]
        feature_rows.append(row)
        labels.append(int(r["label"]))
    if not feature_rows:
        raise RuntimeError("No usable training rows (failed to join GTINs to product catalog).")
    X = np.asarray(feature_rows, dtype=np.float32)
    y = np.asarray(labels, dtype=np.int32)
    return X, y, feature_names


def main() -> None:
    parser = argparse.ArgumentParser(description="Train baseline substitution model.")
    parser.add_argument("--pairs", type=str, required=True, help="CSV file with columns: orig_gtin,cand_gtin,label")
    parser.add_argument("--out", type=str, default="models/substitution_rf.joblib", help="Output model path")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    pairs_path = Path(args.pairs)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[train] Loading pairs from {pairs_path}")
    pairs_df = load_pairs_csv(pairs_path)
    print(f"[train] Pairs rows: {len(pairs_df)}")

    print("[train] Loading product catalog")
    products = product_data_df()
    prod_index = _index_products_by_gtin(products)
    print(f"[train] Catalog indexed GTINs: {len(prod_index)}")

    print("[train] Building feature matrix")
    X, y, feature_names = build_feature_matrix(pairs_df, prod_index)
    print(f"[train] Samples: {X.shape[0]}, Features: {X.shape[1]}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.random_state, stratify=y
    )
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        random_state=args.random_state,
        n_jobs=-1,
        class_weight="balanced_subsample",
    )
    print("[train] Fitting model")
    clf.fit(X_train, y_train)
    proba = clf.predict_proba(X_test)[:, 1]
    ap = average_precision_score(y_test, proba)
    print(f"[train] Validation AP: {ap:.4f}")

    artifact = {
        "model": clf,
        "feature_names": feature_names,
        "metadata": {
            "average_precision": float(ap),
            "samples": int(X.shape[0]),
        },
    }
    joblib.dump(artifact, out_path)
    print(f"[train] Saved model to {out_path}")


if __name__ == "__main__":
    main()


