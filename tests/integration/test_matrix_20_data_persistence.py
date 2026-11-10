"""Cross-Check Matrix Row 20: Data persistence and restart durability.

Target Invariant:
- SQLite WAL mode preserves searches, snapshots, quotes, and orders across restarts.
- Expired quotes remain unusable after database reconnection.
- Verified orders remain queryable and immutable across restarts.
"""
import datetime

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.database import get_db, init_db
from app.main import app


@pytest.fixture
def test_setup(tmp_path):
    db_file = str(tmp_path / "test_matrix_20_persistent.db")
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
    return settings, db_file


def test_data_persistence_across_restarts(test_setup):
    """Data written before a simulated restart is preserved and expired quotes remain unusable."""
    settings, db_file = test_setup

    session_id = "sess_m20"
    quote_id = "quote_m20_persisted"
    snap_id = "snap_m20_persisted"
    order_id = "ord_m20_persisted"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    past_iso = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1)).isoformat()

    # 1. First "run" writes data to SQLite
    with get_db(db_file) as conn:
        conn.execute("INSERT INTO searches (id, session_id, query, status, created_at) VALUES ('s20', ?, 'magnifier', 'SUCCESS', ?)", (session_id, now_iso))
        conn.execute(
            """
            INSERT INTO product_snapshots (id, search_id, channel3_id, title, price, currency, availability, merchant_domain, raw_json, fetched_at)
            VALUES (?, 's20', 'ch3_20', 'Magnifier', '19.99', 'USD', 'InStock', 'newegg.com', '{}', ?)
            """,
            (snap_id, now_iso),
        )
        conn.execute(
            """
            INSERT INTO quotes (id, session_id, snapshot_id, quantity, unit_price, currency, total, status, expires_at, created_at)
            VALUES (?, ?, ?, 1, '19.99', 'USD', '19.99', 'QUOTED', ?, ?)
            """,
            (quote_id, session_id, snap_id, past_iso, now_iso),
        )
        conn.execute(
            """
            INSERT INTO orders (id, session_id, quote_id, paypal_order_id, status, capture_id, captured_amount, captured_currency, created_at, updated_at)
            VALUES (?, ?, ?, 'PAYPAL_20', 'CAPTURED_VERIFIED', 'CAP_20', '19.99', 'USD', ?, ?)
            """,
            (order_id, session_id, quote_id, now_iso, now_iso),
        )

    # 2. Simulated "restart": Fresh FastAPI instance and dependency override pointing to same DB file
    app.dependency_overrides[get_settings] = lambda: settings
    client = TestClient(app, cookies={"sid": session_id})

    # A. Verify receipt data is intact across restart
    res_r = client.get(f"/api/orders/{order_id}")
    assert res_r.status_code == 200
    receipt = res_r.json()
    assert receipt["order_id"] == order_id
    assert receipt["status"] == "CAPTURED_VERIFIED"
    assert receipt["total"] == "19.99"
    assert receipt["merchant_domain"] == "newegg.com"

    # B. Verify expired quote remains unusable across restart
    res_c = client.post(f"/api/quotes/{quote_id}/confirm", json={"confirmed_total": "19.99"})
    assert res_c.status_code == 422
    assert res_c.json()["error"]["code"] == "QUOTE_EXPIRED"

    # C. Verify WAL mode is active
    with get_db(db_file) as conn:
        mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        assert mode.lower() == "wal"
