from __future__ import annotations

import re
from typing import Iterable, Set

_TOKEN_RE = re.compile(r"[A-Za-zÅÄÖåäö0-9]+", flags=re.UNICODE)


def simple_tokenize(text: str) -> Set[str]:
    if not text:
        return set()
    return {t.lower() for t in _TOKEN_RE.findall(text)}


def jaccard_similarity(tokens_a: Iterable[str], tokens_b: Iterable[str]) -> float:
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    if not set_a and not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    if union == 0:
        return 0.0
    return inter / union


