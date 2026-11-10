"""Cross-Check Matrix Row 6: Order to PayPal payload format and idempotency.

Target Invariant:
- create-order has exact quote total, USD currency, and custom_id = internal order ID.
- Header PayPal-Request-Id is passed for idempotency.
- Plain amount without item breakdown to avoid breakdown mismatch errors.
- paypal_debug_id is logged in payment_events table.
"""
import httpx
import pytest

from app.config import Settings
from app.database import get_db, init_db
from app.paypal import PayPalClient


@pytest.fixture
def test_setup(tmp_path):
    db_file = str(tmp_path / "test_matrix_06.db")
    init_db(db_file)
    settings = Settings(
        OFFLINE_TESTS=1,
        DATABASE_PATH=db_file,
        CHANNEL3_API_KEY="test-key",
        GEMINI_API_KEY="test-key",
        GEMINI_MODEL="test-model",
        PAYPAL_CLIENT_ID="mock_client_id",
        PAYPAL_CLIENT_SECRET="mock_client_sec",
    )
    return settings, db_file


def test_paypal_create_order_payload_and_idempotency(test_setup, monkeypatch):
    """Verify PayPal order payload meets all invariants and logs debug_id."""
    settings, db_file = test_setup
    client = PayPalClient(settings=settings)

    captured_requests = []

    def mock_post(url, headers=None, json=None, auth=None, data=None):
        req = {"url": url, "headers": headers, "json": json, "auth": auth, "data": data}
        captured_requests.append(req)

        if "oauth2/token" in url:
            return httpx.Response(
                200,
                json={"access_token": "mock_token_abc", "expires_in": 3600},
                headers={"Paypal-Debug-Id": "token_debug_001"},
            )
        elif "checkout/orders" in url:
            return httpx.Response(
                201,
                json={"id": "PAYPAL_ORDER_789", "status": "CREATED"},
                headers={"Paypal-Debug-Id": "create_debug_999"},
            )
        return httpx.Response(404)

    monkeypatch.setattr(httpx.Client, "post", lambda self, url, **kwargs: mock_post(url, **kwargs))

    internal_order_id = "ord_test_006"
    quote_total = "39.99"
    paypal_order_id, debug_id = client.create_order(
        order_id=internal_order_id,
        total=quote_total,
        currency="USD",
    )

    assert paypal_order_id == "PAYPAL_ORDER_789"
    assert debug_id == "create_debug_999"

    # Find the checkout/orders request
    order_req = [r for r in captured_requests if "checkout/orders" in r["url"]][0]

    # Verify idempotency header
    assert order_req["headers"]["PayPal-Request-Id"] == internal_order_id
    assert order_req["headers"]["Authorization"] == "Bearer mock_token_abc"

    # Verify payload
    payload = order_req["json"]
    assert payload["intent"] == "CAPTURE"
    assert len(payload["purchase_units"]) == 1

    unit = payload["purchase_units"][0]
    assert unit["custom_id"] == internal_order_id
    assert unit["amount"]["currency_code"] == "USD"
    assert unit["amount"]["value"] == quote_total
    assert "breakdown" not in unit["amount"]  # Plain amount to prevent breakdown mismatch

    # Verify debug_id logged in payment_events table
    with get_db(db_file) as conn:
        row = conn.execute(
            "SELECT step, paypal_debug_id, summary FROM payment_events WHERE order_id = ?",
            (internal_order_id,),
        ).fetchone()
        assert row is not None
        assert row["step"] == "CREATE_ORDER"
        assert row["paypal_debug_id"] == "create_debug_999"
