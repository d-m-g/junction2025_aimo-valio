from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .candidates import suggest_candidates_by_gtin
from .candidates import _normalize_id  # reuse normalization for response
from .availability import get_line_ids_for_gtins


class SuggestRequest(BaseModel):
    sku: str = Field(..., min_length=1, description="Original product SKU that is short or out of stock")
    name: Optional[str] = Field(
        default=None,
        description="Optional human-readable name for the SKU (used to improve matching when GTIN lookup fails)",
    )
    k: int = Field(3, ge=1, le=20, description="Number of replacement suggestions to return")
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional order context (e.g., customer_id, quantity)",
    )
    # Optional warehouse availability snapshot for filtering
    availability: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional list of availability objects: {lineId:int, productCode:str, qty:float}",
    )
    # Optional required quantity for this order line; used when availability is provided
    requiredQty: Optional[float] = Field(
        default=None,
        description="Requested quantity for original line; if provided, candidates require >= this qty in availability map",
    )


class Recommendation(BaseModel):
    sku: str
    score: float
    name: Optional[str] = None


class SuggestResponse(BaseModel):
    sku: str
    name: Optional[str] = None
    recommendations: List[Recommendation]


class OrderSubstitutionRequest(BaseModel):
    lineId: int
    productCode: str
    qty: float
    name: Optional[str] = None


class OrderSubstitutionResponse(BaseModel):
    lineId: int
    suggestedLineIds: List[int]


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


@app.post("/substitution/suggest_debug", response_model=SuggestResponse)
def suggest_substitutions_debug(request: SuggestRequest) -> SuggestResponse:
    # For MVP, treat sku as GTIN (salesUnitGtin or synkkaData.gtin)
    # Build availability map if provided; assume productCode corresponds to candidate GTIN
    avail_map: Optional[Dict[str, float]] = None
    if request.availability:
        tmp: Dict[str, float] = {}
        for item in request.availability:
            if not isinstance(item, dict):
                continue
            code = item.get("productCode")
            qty = item.get("qty")
            if isinstance(code, str) and isinstance(qty, (int, float)):
                norm = _normalize_id(code) or code
                # Keep max qty per code if duplicates
                prev = tmp.get(norm)
                tmp[norm] = float(max(qty, prev if prev is not None else 0.0))
        avail_map = tmp if tmp else None

    orig, scored = suggest_candidates_by_gtin(
        request.sku,
        k=request.k,
        available_qty_by_code=avail_map,
        required_qty=request.requiredQty,
        fallback_name=request.name,
    )
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


@app.post("/substitution/suggest", response_model=OrderSubstitutionResponse)
def suggest_substitutions(request: OrderSubstitutionRequest) -> OrderSubstitutionResponse:
    """
    Order-fulfilment facing API compatible with SubstitutionRequest/SubstitutionResponse:

      Request:  { lineId, productCode, qty }
      Response: { lineId, suggestedLineIds: [warehouse_items.line_id, ...] }
    """
    # Treat productCode as GTIN
    sku = request.productCode
    # Use DB-driven availability and requiredQty = requested qty
    orig, scored = suggest_candidates_by_gtin(
        sku,
        k=3,
        available_qty_by_code=None,
        required_qty=request.qty,
        fallback_name=request.name,
    )
    # Map recommended GTINs to warehouse line_ids
    gtins = [_normalize_id(g) or g for (g, _score, _cand) in scored]
    code_to_line_id = get_line_ids_for_gtins(gtins)
    suggested_ids: List[int] = []
    for g, _score, _cand in scored:
        code = _normalize_id(g) or g
        line_id = code_to_line_id.get(code)
        if line_id is not None:
            suggested_ids.append(line_id)
    return OrderSubstitutionResponse(
        lineId=request.lineId,
        suggestedLineIds=suggested_ids,
    )


def _placeholder_recommendations(_: str, __: int) -> List[Recommendation]:
    # Deprecated: kept to avoid breaking imports; not used.
    return []


