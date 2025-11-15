from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .candidates import suggest_candidates_by_gtin
from .data_loaders import product_data_df
from .candidates import _normalize_id  # reuse normalization for response


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
    name: Optional[str] = None
    recommendations: List[Recommendation]


app = FastAPI(
    title="Valio Aimo Substitution Service",
    version="0.1.0",
    description="Suggests replacement SKUs for unavailable items.",
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


def _extract_display_name(prod: Dict[str, Any]) -> Optional[str]:
    sd = prod.get("synkkaData")
    if isinstance(sd, dict):
        names = sd.get("names")
        if isinstance(names, list):
            # Prefer EN, then FI, then SV, else first
            preferred = ["en", "fi", "sv"]
            first_any: Optional[str] = None
            for n in names:
                if isinstance(n, dict) and isinstance(n.get("value"), str):
                    if first_any is None:
                        first_any = n["value"]
            for lang in preferred:
                for n in names:
                    if (
                        isinstance(n, dict)
                        and n.get("language") == lang
                        and isinstance(n.get("value"), str)
                    ):
                        return n["value"]
            if first_any:
                return first_any
    brand = prod.get("brand")
    if isinstance(brand, str) and brand:
        gtin = _normalize_id(prod.get("salesUnitGtin")) or ""
        return f"{brand}{f' [{gtin}]' if gtin else ''}"
    vendor = prod.get("vendorName")
    if isinstance(vendor, str) and vendor:
        return vendor
    return None


@app.post("/substitution/suggest", response_model=SuggestResponse)
def suggest_substitutions(request: SuggestRequest) -> SuggestResponse:
    # For MVP, treat sku as GTIN (salesUnitGtin or synkkaData.gtin)
    orig, scored = suggest_candidates_by_gtin(request.sku, k=request.k)
    recs: List[Recommendation] = []
    for cand_gtin, score, cand in scored:
        recs.append(
            Recommendation(
                sku=_normalize_id(cand_gtin) or cand_gtin,
                score=round(float(score), 4),
                name=_extract_display_name(cand),
            )
        )
    return SuggestResponse(
        sku=request.sku,
        name=_extract_display_name(orig) if isinstance(orig, dict) else None,
        recommendations=recs,
    )


def _placeholder_recommendations(_: str, __: int) -> List[Recommendation]:
    # Deprecated: kept to avoid breaking imports; not used.
    return []


