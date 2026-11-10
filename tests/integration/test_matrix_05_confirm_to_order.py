"""Cross-Check Matrix Row 5: Confirm to order transition.

Target Invariant:
- Unconfirmed quote cannot create order (422 QUOTE_NOT_CONFIRMED).
- Expired quote cannot create order (422 QUOTE_EXPIRED).
- Confirmed, unexpired quote creates internal order and triggers PayPal create-order.
"""
import datetime

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.database import get_db, init_db
from app.main import app
from app.paypal import PayPalClient
from app.routers.orders import get_paypal_client


@pytest.fixture
def test_setup(tmp_path):
    db_file = str(tmp_path / "test_matrix_05.db")
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

    session_id = "sess_m05"
    snapshot_id = "snap_m05"

    with get_db(db_file) as conn:
        conn.execute(
            """
            INSERT INTO searches (id, session_id, query, status, created_at)
            VALUES ('s_05', ?, 'item', 'SUCCESS', '2026-11-10T00:00:00Z')
            """,
            (session_id,),
        )
        conn.execute(
            """
            INSERT INTO product_snapshots (
                id, search_id, channel3_id, title, price, currency,
                availability, merchant_domain, raw_json, fetched_at
            ) VALUES (?, 's_05', 'ch3_05', 'Product', '20.00', 'USD', 'InStock', 'shop.com', '{}', '2026-11-10T00:00:00Z')
            """,
            (snapshot_id,),
        )

    return settings, session_id, snapshot_id


def test_order_creation_fails_on_unconfirmed_quote(test_setup):
    """Creating an order for a quote in QUOTED status is blocked."""
    settings, session_id, snapshot_id = test_setup
    future_iso = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)).isoformat()
    quote_id = "quote_unconfirmed_01"

    with get_db(settings.DATABASE_PATH) as conn:
        conn.execute(
            """
            INSERT INTO quotes (id, session_id, snapshot_id, quantity, unit_price, currency, total, status, expires_at, created_at)
            VALUES (?, ?, ?, 1, '20.00', 'USD', '20.00', 'QUOTED', ?, ?)
            """,
            (quote_id, session_id, snapshot_id, future_iso, future_iso),
        )

    client = TestClient(app, cookies={"sid": session_id})
    res = client.post("/api/orders", json={"quote_id": quote_id})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "QUOTE_NOT_CONFIRMED"


def test_order_creation_fails_on_expired_quote(test_setup):
    """Creating an order for an expired confirmed quote is blocked."""
    settings, session_id, snapshot_id = test_setup
    past_iso = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=10)).isoformat()
    quote_id = "quote_expired_02"

    with get_db(settings.DATABASE_PATH) as conn:
        conn.execute(
            """
            INSERT INTO quotes (id, session_id, snapshot_id, quantity, unit_price, currency, total, status, confirmed_at, expires_at, created_at)
            VALUES (?, ?, ?, 1, '20.00', 'USD', '20.00', 'CONFIRMED', ?, ?, ?)
            """,
            (quote_id, session_id, snapshot_id, past_iso, past_iso, past_iso),
        )

    client = TestClient(app, cookies={"sid": session_id})
    res = client.post("/api/orders", json={"quote_id": quote_id})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "QUOTE_EXPIRED"


def test_order_creation_succeeds_for_confirmed_quote(test_setup, monkeypatch):
    """Confirmed, unexpired quote successfully generates an internal and PayPal order."""
    settings, session_id, snapshot_id = test_setup
    future_iso = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)).isoformat()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    quote_id = "quote_confirmed_03"

    with get_db(settings.DATABASE_PATH) as conn:
        conn.execute(
            """
            INSERT INTO quotes (id, session_id, snapshot_id, quantity, unit_price, currency, total, status, confirmed_at, expires_at, created_at)
            VALUES (?, ?, ?, 1, '20.00', 'USD', '20.00', 'CONFIRMED', ?, ?, ?)
            """,
            (quote_id, session_id, snapshot_id, now_iso, future_iso, now_iso),
        )

    paypal_client = PayPalClient(settings=settings)
    monkeypatch.setattr(
        paypal_client,
        "create_order",
        lambda order_id, total, currency: ("paypal_order_mock_123", "debug_id_mock_456"),
    )
    app.dependency_overrides[get_paypal_client] = lambda: paypal_client

    client = TestClient(app, cookies={"sid": session_id})
    res = client.post("/api/orders", json={"quote_id": quote_id})
    assert res.status_code == 200
    data = res.json()
    assert data["order_id"].startswith("ord_")
    assert data["paypal_order_id"] == "paypal_order_mock_123"
    assert data["status"] == "ORDER_CREATED"
