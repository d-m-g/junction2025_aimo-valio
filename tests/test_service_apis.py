import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
import psycopg
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_ORDER_PATH = REPO_ROOT / "stock_prediction" / "test_order.json"
SAMPLE_ORDER = json.loads(TEST_ORDER_PATH.read_text())

NLU_BASE = "http://localhost:6060"
SUBSTITUTION_BASE = "http://localhost:8000"
STOCK_BASE = "http://localhost:8100"
ORDER_BASE = "http://localhost:8080"
WAREHOUSE_DB_CONNINFO = "host=localhost port=6000 dbname=warehouse user=warehouse_user password=warehouse_pass"

REQUEST_TIMEOUT = 20.0
REQUEST_RETRIES = 30
REQUEST_BACKOFF = 2.0


def request_with_retry(
    method: str,
    url: str,
    *,
    json_payload: Optional[Dict[str, Any]] = None,
    expected_status: Optional[int] = None,
) -> httpx.Response:
    """Retry helper to give containers time to start up."""
    last_exc: Optional[Exception] = None
    for attempt in range(REQUEST_RETRIES):
        try:
            response = httpx.request(
                method,
                url,
                json=json_payload,
                timeout=REQUEST_TIMEOUT,
            )
            if expected_status is not None:
                assert (
                    response.status_code == expected_status
                ), f"Expected {expected_status} from {url}, got {response.status_code} ({response.text})"
            return response
        except httpx.TransportError as exc:
            last_exc = exc
            if attempt == REQUEST_RETRIES - 1:
                raise
            time.sleep(REQUEST_BACKOFF)
    raise AssertionError(f"Failed to contact {url}: {last_exc}")


def unique_session_id() -> str:
    return f"session_{int(time.time())}"


# ---------------------------------------------------------------------------
# NLU SERVICE TESTS
# ---------------------------------------------------------------------------


def test_nlu_health_and_root():
    resp_root = request_with_retry("GET", f"{NLU_BASE}/", expected_status=200)
    data_root = resp_root.json()
    assert data_root["service"] == "nlu-parser"

    resp_health = request_with_retry("GET", f"{NLU_BASE}/health", expected_status=200)
    data_health = resp_health.json()
    assert data_health["service"] == "nlu-parser"
    assert data_health["status"] in {"healthy", "degraded"}


def test_nlu_parse_variants():
    session_id = unique_session_id()
    base_payload = {
        "text": "Need lactose free milk tomorrow morning.",
        "context": {"order_number": "TEST-100"},
        "session_id": session_id,
    }

    parse_resp = request_with_retry(
        "POST",
        f"{NLU_BASE}/nlu/parse",
        json_payload=base_payload,
        expected_status=200,
    ).json()
    assert "intent" in parse_resp
    assert parse_resp["session_id"] == session_id

    pre_resp = request_with_retry(
        "POST",
        f"{NLU_BASE}/nlu/pre-parse",
        json_payload=base_payload,
        expected_status=200,
    ).json()
    assert pre_resp["metadata"]["conversation_stage"] == "pre_order_substitution"

    post_payload = {
        **base_payload,
        "context": {
            "order_number": "TEST-222",
            "delivery_date": "2024-09-02",
            "detected_discrepancy": True,
        },
    }
    post_resp = request_with_retry(
        "POST",
        f"{NLU_BASE}/nlu/post-parse",
        json_payload=post_payload,
        expected_status=200,
    ).json()
    assert post_resp["metadata"]["conversation_stage"] == "post_delivery_investigation"

    batch_payload = {
        "texts": [
            "Where is my order?",
            "I need oat milk instead",
        ],
        "context": {"order_number": "BATCH-1"},
        "session_id": session_id,
    }
    batch_resp = request_with_retry(
        "POST",
        f"{NLU_BASE}/nlu/parse/batch",
        json_payload=batch_payload,
        expected_status=200,
    ).json()
    assert batch_resp["count"] == len(batch_payload["texts"])


def test_nlu_session_endpoints():
    session_id = unique_session_id()
    payload = {
        "text": "Order 123 is missing yogurt.",
        "context": {"order_number": "123"},
        "session_id": session_id,
    }
    request_with_retry(
        "POST",
        f"{NLU_BASE}/nlu/parse",
        json_payload=payload,
        expected_status=200,
    )

    get_resp = request_with_retry(
        "GET",
        f"{NLU_BASE}/nlu/session/{session_id}",
        expected_status=200,
    ).json()
    assert get_resp["session_id"] == session_id

    delete_resp = request_with_retry(
        "DELETE",
        f"{NLU_BASE}/nlu/session/{session_id}",
        expected_status=200,
    ).json()
    assert delete_resp["message"].startswith("Session will expire")


# ---------------------------------------------------------------------------
# SUBSTITUTION SERVICE TESTS
# ---------------------------------------------------------------------------


def test_substitution_health_and_suggest_debug():
    resp_health = request_with_retry(
        "GET", f"{SUBSTITUTION_BASE}/health", expected_status=200
    ).json()
    assert resp_health["status"] == "ok"

    payload = {
        "sku": "6408430001000",
        "k": 2,
        "context": {"order_number": "SUB-1"},
    }
    resp = request_with_retry(
        "POST",
        f"{SUBSTITUTION_BASE}/substitution/suggest_debug",
        json_payload=payload,
        expected_status=200,
    ).json()
    assert resp["sku"] == payload["sku"]
    assert "recommendations" in resp


def test_substitution_suggest_order_flow():
    payload = {
        "lineId": 10,
        "productCode": "6408430001000",
        "qty": 5.0,
    }
    resp = request_with_retry(
        "POST",
        f"{SUBSTITUTION_BASE}/substitution/suggest",
        json_payload=payload,
        expected_status=200,
    ).json()
    assert resp["lineId"] == payload["lineId"]
    assert "suggestedLineIds" in resp


# ---------------------------------------------------------------------------
# STOCK PREDICTION SERVICE TESTS
# ---------------------------------------------------------------------------


def test_stock_prediction_endpoints():
    resp_root = request_with_retry("GET", f"{STOCK_BASE}/", expected_status=200).json()
    assert resp_root["service"] == "Stock Availability Predictor"

    resp_health = request_with_retry(
        "GET", f"{STOCK_BASE}/health", expected_status=200
    ).json()
    assert resp_health["status"] == "healthy"

    predict_resp = request_with_retry(
        "POST",
        f"{STOCK_BASE}/predict",
        json_payload=SAMPLE_ORDER,
        expected_status=200,
    ).json()
    assert "prediction" in predict_resp
    assert "items" in predict_resp

    detailed_resp = request_with_retry(
        "POST",
        f"{STOCK_BASE}/predict/detailed",
        json_payload=SAMPLE_ORDER,
        expected_status=200,
    ).json()
    assert detailed_resp["order_id"] == SAMPLE_ORDER["order_id"]
    assert "items" in detailed_resp

    order_resp = request_with_retry(
        "POST",
        f"{STOCK_BASE}/predict/order",
        json_payload=SAMPLE_ORDER,
        expected_status=200,
    ).json()
    assert "lineIds" in order_resp


# ---------------------------------------------------------------------------
# ORDER FULFILMENT SERVICE TESTS
# ---------------------------------------------------------------------------


def test_order_fulfilment_create_and_events():
    create_resp = request_with_retry(
        "POST",
        f"{ORDER_BASE}/api/orders",
        json_payload=SAMPLE_ORDER,
        expected_status=200,
    ).json()
    assert create_resp["orderId"] == SAMPLE_ORDER["order_id"]
    assert "items" in create_resp
    assert "shortages" in create_resp

    pick_payload = {
        "orderId": SAMPLE_ORDER["order_id"],
        "lineId": SAMPLE_ORDER["items"][0]["line_id"],
        "productCode": SAMPLE_ORDER["items"][0]["product_code"],
        "expectedQty": SAMPLE_ORDER["items"][0]["qty"],
        "pickedQty": SAMPLE_ORDER["items"][0]["qty"] - 1,
        "pickerId": "picker-1",
    }
    pick_resp = request_with_retry(
        "POST",
        f"{ORDER_BASE}/api/orders/events/pick-shortage",
        json_payload=pick_payload,
        expected_status=200,
    ).json()
    assert pick_resp["orderId"] == pick_payload["orderId"]
    assert pick_resp["lineId"] == pick_payload["lineId"]
    assert pick_resp["action"] in {"KEEP", "REPLACE", "DELETE"}
    assert "replacements" in pick_resp

    shortage_payload = {
        "items": [
            {
                "from": {
                    "lineId": pick_payload["lineId"],
                    "qty": pick_payload["expectedQty"],
                }
            }
        ]
    }
    shortage_resp = request_with_retry(
        "POST",
        f"{ORDER_BASE}/api/orders/shortage/proactive-call",
        json_payload=shortage_payload,
        expected_status=200,
    ).json()
    assert "decisions" in shortage_resp
    assert shortage_resp["decisions"][0]["lineId"] == pick_payload["lineId"]

    claim_payload = {
        "orderId": SAMPLE_ORDER["order_id"],
        "customerId": SAMPLE_ORDER["customer_id"],
        "channel": "nlu",
        "description": "Missing oat milk",
        "attachmentIds": ["photo-1"],
    }
    claim_resp = request_with_retry(
        "POST",
        f"{ORDER_BASE}/api/orders/claims/create",
        json_payload=claim_payload,
        expected_status=501,
    ).json()
    assert claim_resp["endpoint"].endswith("claims/create")


# ---------------------------------------------------------------------------
# WAREHOUSE DB TEST
# ---------------------------------------------------------------------------


def test_warehouse_db_connection():
    deadline = time.time() + 60
    last_exc: Optional[Exception] = None
    while time.time() < deadline:
        try:
            with psycopg.connect(WAREHOUSE_DB_CONNINFO) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    assert cur.fetchone()[0] == 1
            return
        except psycopg.Error as exc:
            last_exc = exc
            time.sleep(REQUEST_BACKOFF)
    raise AssertionError(f"Unable to connect to warehouse DB: {last_exc}")


