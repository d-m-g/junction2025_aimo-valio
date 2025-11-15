from __future__ import annotations

import joblib
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

DEFAULT_MODEL_PATHS = [
    Path("models/substitution_rf.joblib"),
]


class ModelScorer:
    def __init__(self, artifact: Dict[str, Any]) -> None:
        self.model = artifact.get("model")
        self.feature_names: List[str] = list(artifact.get("feature_names", []))
        if not self.model or not self.feature_names:
            raise ValueError("Invalid model artifact")

    def score(self, feature_dict: Dict[str, float]) -> float:
        x = np.asarray([[float(feature_dict.get(fn, 0.0)) for fn in self.feature_names]], dtype=np.float32)
        proba = self.model.predict_proba(x)[:, 1]
        return float(proba[0])


_SCORER: Optional[ModelScorer] = None


def load_default_model() -> Optional[ModelScorer]:
    global _SCORER
    if _SCORER is not None:
        return _SCORER
    for p in DEFAULT_MODEL_PATHS:
        if p.exists():
            artifact = joblib.load(p)
            _SCORER = ModelScorer(artifact)
            return _SCORER
    return None


