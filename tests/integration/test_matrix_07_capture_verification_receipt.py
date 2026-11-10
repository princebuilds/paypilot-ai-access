"""Cross-Check Matrix Row 7: Capture verification, status mapping, and receipt honesty.

Target Invariant:
- Order and capture COMPLETED + matching amount/currency + matching custom_id = CAPTURED_VERIFIED.
- Capture status PENDING is mapped to PENDING (never completed).
- Capture status DECLINED or amount mismatch is mapped to FAILED.
- Receipt shows stored amounts, merchant domain, and sandbox: true banner.
"""
import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.database import get_db, init_db
from app.main import app
from app.paypal import PayPalClient
from app.routers.orders import get_paypal_client


@pytest.fixture
def test_setup(tmp_path):
    db_file = str(tmp_path / "test_matrix_07.db")
    init_db(db_file)
    settings = Settings(
        OFFLINE_TESTS=1,
        DATABASE_PATH=db_file,
        CHANNEL3_API_KEY="test-key",
        GEMINI_API_KEY="test-key",
        GEMINI_MODEL="test-model",
        PAYPAL_CLIENT_ID="test-id",
        PAYPAL_CLIENT_SECRET="test-sec",
    )
    app.dependency_overrides[get_settings] = lambda: settings

    session_id = "sess_m07"
    order_id = "ord_m07_test"
    quote_id = "quote_m07"
    snap_id = "snap_m07"

    with get_db(db_file) as conn:
        conn.execute("INSERT INTO searches (id, session_id, query, status, created_at) VALUES ('s07', ?, 'magnifier', 'SUCCESS', '2026-11-10T00:00:00Z')", (session_id,))
        conn.execute(
            """
            INSERT INTO product_snapshots (id, search_id, channel3_id, title, price, currency, availability, merchant_domain, buy_url, raw_json, fetched_at)
            VALUES (?, 's07', 'ch3_07', 'LED Magnifying Glass', '22.99', 'USD', 'InStock', 'wayfair.com', 'https://wayfair.com/buy', '{}', '2026-11-10T00:00:00Z')
            """,
            (snap_id,),
        )
        conn.execute(
            """
            INSERT INTO quotes (id, session_id, snapshot_id, quantity, unit_price, currency, total, status, expires_at, created_at)
            VALUES (?, ?, ?, 1, '22.99', 'USD', '22.99', 'CONFIRMED', '2026-11-10T12:00:00Z', '2026-11-10T00:00:00Z')
            """,
            (quote_id, session_id, snap_id),
        )
        conn.execute(
            """
            INSERT INTO orders (id, session_id, quote_id, paypal_order_id, status, created_at, updated_at)
            VALUES (?, ?, ?, 'PAYPAL_ORDER_M07', 'ORDER_CREATED', '2026-11-10T00:00:00Z', '2026-11-10T00:00:00Z')
            """,
            (order_id, session_id, quote_id),
        )

    return settings, session_id, order_id


def test_capture_verified_when_all_invariants_hold(test_setup, monkeypatch):
    """COMPLETED order + COMPLETED capture + amount match + custom_id match = CAPTURED_VERIFIED."""
    settings, session_id, order_id = test_setup
    paypal_client = PayPalClient(settings=settings)

    mock_paypal_payload = {
        "id": "PAYPAL_ORDER_M07",
        "status": "COMPLETED",
        "purchase_units": [
            {
                "custom_id": order_id,
                "payments": {
                    "captures": [
                        {
                            "id": "CAP_SUCCESS_001",
                            "status": "COMPLETED",
                            "amount": {"value": "22.99", "currency_code": "USD"},
                        }
                    ]
                },
            }
        ],
    }

    monkeypatch.setattr(paypal_client, "capture_order", lambda *args, **kwargs: (mock_paypal_payload, "dbg_123"))
    app.dependency_overrides[get_paypal_client] = lambda: paypal_client

    client = TestClient(app, cookies={"sid": session_id})
    res = client.post(f"/api/orders/{order_id}/capture")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "CAPTURED_VERIFIED"
    assert "Payment verified" in data["message"]

    # Verify receipt endpoint
    r_res = client.get(f"/api/orders/{order_id}")
    assert r_res.status_code == 200
    receipt = r_res.json()
    assert receipt["status"] == "CAPTURED_VERIFIED"
    assert receipt["total"] == "22.99"
    assert receipt["currency"] == "USD"
    assert receipt["paypal_capture_id"] == "CAP_SUCCESS_001"
    assert receipt["merchant_domain"] == "wayfair.com"
    assert receipt["sandbox"] is True


def test_capture_pending_mapped_to_pending(test_setup, monkeypatch):
    """Capture status PENDING must remain PENDING (not marked as paid)."""
    settings, session_id, order_id = test_setup
    paypal_client = PayPalClient(settings=settings)

    mock_paypal_payload = {
        "id": "PAYPAL_ORDER_M07",
        "status": "COMPLETED",
        "purchase_units": [
            {
                "custom_id": order_id,
                "payments": {
                    "captures": [
                        {
                            "id": "CAP_PENDING_002",
                            "status": "PENDING",
                            "amount": {"value": "22.99", "currency_code": "USD"},
                        }
                    ]
                },
            }
        ],
    }

    monkeypatch.setattr(paypal_client, "capture_order", lambda *args, **kwargs: (mock_paypal_payload, "dbg_pending"))
    app.dependency_overrides[get_paypal_client] = lambda: paypal_client

    client = TestClient(app, cookies={"sid": session_id})
    res = client.post(f"/api/orders/{order_id}/capture")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "PENDING"
    assert "still pending" in data["message"].lower()


def test_capture_fails_on_amount_mismatch(test_setup, monkeypatch):
    """If captured amount does not match the quote, payment status transitions to FAILED."""
    settings, session_id, order_id = test_setup
    paypal_client = PayPalClient(settings=settings)

    mock_paypal_payload = {
        "id": "PAYPAL_ORDER_M07",
        "status": "COMPLETED",
        "purchase_units": [
            {
                "custom_id": order_id,
                "payments": {
                    "captures": [
                        {
                            "id": "CAP_WRONG_AMT_003",
                            "status": "COMPLETED",
                            "amount": {"value": "10.00", "currency_code": "USD"},  # Expected 22.99
                        }
                    ]
                },
            }
        ],
    }

    monkeypatch.setattr(paypal_client, "capture_order", lambda *args, **kwargs: (mock_paypal_payload, "dbg_mismatch"))
    app.dependency_overrides[get_paypal_client] = lambda: paypal_client

    client = TestClient(app, cookies={"sid": session_id})
    res = client.post(f"/api/orders/{order_id}/capture")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "FAILED"
