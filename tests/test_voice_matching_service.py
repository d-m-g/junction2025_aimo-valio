import json
from typing import Any, Dict, Optional

import pytest
from fastapi.testclient import TestClient

from services.voice_matching_service import main


class _StubNluClient:
    """Simple stub to bypass external NLU calls in tests."""

    def __init__(self, response: Dict[str, Any]):
        self._response = response
        self.base_url: Optional[str] = None

    def parse(
        self,
        *,
        text: str,
        context: Optional[Dict[str, Any]],
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        # Attach echoes so tests can ensure request wiring works if needed
        resp = dict(self._response)
        resp.setdefault("debug", {})
        resp["debug"]["echo_text"] = text
        resp["debug"]["echo_session"] = session_id
        return resp


@pytest.fixture(autouse=True)
def stub_nlu_client(monkeypatch):
    """Replace the real NLU client with a deterministic stub."""

    sample_response = {
        "intent": "confirm_substitution",
        "confidence": 0.92,
        "parameters": {
            "entities": {
                "products": [
                    {
                        "name": "Atria jauheliha 1kg",
                        "gtin": "409510",
                        "confidence": 0.87,
                    }
                ],
                "quantities": [
                    {
                        "value": 5,
                        "unit": "ST",
                        "confidence": 0.8,
                    }
                ],
            }
        },
    }
    stub = _StubNluClient(sample_response)
    monkeypatch.setattr(main, "nlu_client", stub)
    return stub


@pytest.fixture()
def client():
    return TestClient(main.app)


def test_health_endpoint_reports_status(client, stub_nlu_client):
    resp = client.get("/health")
    data = resp.json()
    assert data["status"] == "ok"
    assert data["nlu_backend"] == "in-process"


def test_match_voice_order_returns_line_ids_and_logs_output(client):
    payload = {
        "text": "Please confirm the five packs of ground beef.",
        "order": {
            "orderId": "VOICE-123",
            "items": [
                {
                    "lineId": 1,
                    "productCode": "409510",
                    "name": "Atria jauheliha 1kg",
                    "qty": 5,
                    "unit": "ST",
                },
                {
                    "lineId": 2,
                    "productCode": "123456",
                    "name": "Valio Oat Milk",
                    "qty": 3,
                    "unit": "ST",
                },
            ],
        },
        "sessionId": "session-test",
    }

    response = client.post("/orders/match", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["orderId"] == payload["order"]["orderId"]
    assert data["intent"] == "confirm_substitution"
    assert data["matchedLineIds"] == [1]
    assert len(data["matchedItems"]) == 1
    match = data["matchedItems"][0]
    assert match["lineId"] == 1
    assert match["detectedGtin"] == "409510"
    assert match["detectedQuantity"] == 5

    # Surface the structured response so `pytest -s` shows an example output
    print(json.dumps(data, indent=2))


def test_match_with_partial_name_similarity(client, monkeypatch):
    """Ensure fuzzy name matching links entities even without exact names."""

    custom_response = {
        "intent": "confirm_substitution",
        "confidence": 0.85,
        "parameters": {
            "entities": {
                "products": [
                    {
                        "name": "Atria ground beef one kilo pack",
                        "gtin": None,  # Force name-only matching
                        "confidence": 0.75,
                    }
                ],
                "quantities": [
                    {
                        "value": 5,
                        "unit": "pcs",
                        "confidence": 0.6,
                    }
                ],
            }
        },
    }
    monkeypatch.setattr(main, "nlu_client", _StubNluClient(custom_response))

    payload = {
        "text": "Customer confirmed the kilo of ground beef.",
        "order": {
            "orderId": "VOICE-456",
            "items": [
                {
                    "lineId": 10,
                    "productCode": "6407850050058",
                    "name": "Mestari Forsman Lasagne 3kg",
                    "qty": 5,
                    "unit": "RAS",
                },
                {
                    "lineId": 11,
                    "productCode": "6407850051093",
                    "name": "Mestari Forsman Vegetable Lasagne 3kg",
                    "qty": 2,
                    "unit": "RAS",
                },
            ],
        },
    }

    response = client.post("/orders/match", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["matchedLineIds"] == [10]
    assert data["matchedItems"][0]["lineId"] == 10
    assert data["matchedItems"][0]["matchSource"] == "name"

    print("Partial match result:", json.dumps(data["matchedItems"][0], indent=2))


def test_lookup_line_id_endpoint_returns_best_match(client, monkeypatch):
    samples = [
        {"line_id": 200, "product_code": "6407850051093", "name": "Mestari Forsman Vegetable Lasagne 3kg"},
        {"line_id": 55, "product_code": "6407850050058", "name": "Mestari Forsman Lasagne 3kg"},
    ]

    monkeypatch.setattr(
        main,
        "_fetch_warehouse_items_by_name",
        lambda name, max_candidates=100: samples,
    )

    response = client.post(
        "/warehouse/lookup",
        json={"name": "Atria ground beef one kilogram pack", "limit": 1},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["results"][0]["lineId"] == 55

    print("Lookup response:", json.dumps(data, indent=2))
