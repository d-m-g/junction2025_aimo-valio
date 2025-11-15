from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field


class SuggestRequest(BaseModel):
    sku: str = Field(..., min_length=1, description="Original product SKU that is short or out of stock")
    k: int = Field(3, ge=1, le=20, description="Number of replacement suggestions to return")
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional order context (e.g., customer_id, quantity)",
    )


class Recommendation(BaseModel):
    sku: str
    score: float
    name: Optional[str] = None


class SuggestResponse(BaseModel):
    sku: str
    recommendations: List[Recommendation]


app = FastAPI(
    title="Valio Aimo Substitution Service",
    version="0.1.0",
    description="Suggests replacement SKUs for unavailable items.",
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/substitution/suggest", response_model=SuggestResponse)
def suggest_substitutions(request: SuggestRequest) -> SuggestResponse:
    # Placeholder implementation: returns deterministic example recommendations.
    recommendations = _placeholder_recommendations(request.sku, request.k)
    return SuggestResponse(sku=request.sku, recommendations=recommendations)


def _placeholder_recommendations(sku: str, k: int) -> List[Recommendation]:
    base_candidates = ["REPL_001", "REPL_007", "REPL_015", "REPL_023", "REPL_042"]
    out: List[Recommendation] = []
    for i, code in enumerate(base_candidates[:k]):
        score = round(0.91 - 0.07 * i, 2)
        out.append(Recommendation(sku=code, score=score))
    if len(out) < k:
        for i in range(len(out), k):
            code = f"REPL_{100 + i:03d}"
            score = max(0.1, round(0.6 - 0.05 * (i - len(base_candidates)), 2))
            out.append(Recommendation(sku=code, score=score))
    return out


