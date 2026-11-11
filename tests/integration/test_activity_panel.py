"""Tests for 'What the assistant did' activity panel.

Target Invariants:
- Events are built SERVER-SIDE from stored database records only.
- Each event matches its database row (query, count, latency, kept/removed, price lock, confirmation, payment events).
- Never contains model-generated text or secrets/tokens.
- Session isolation is respected.
- Frontend uses aria-expanded, keyboard controls, and textContent exclusively.
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.database import get_db, init_db
from app.main import app

ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def activity_test_setup(tmp_path):
    db_file = str(tmp_path / "test_activity.db")
    init_db(db_file)
    settings = Settings(
        OFFLINE_TESTS=1,
        DATABASE_PATH=db_file,
        CHANNEL3_API_KEY="test_channel3_secret_12345",
        GEMINI_API_KEY="test_gemini_secret_67890",
        GEMINI_MODEL="gemini-3.5-flash-lite",
        PAYPAL_CLIENT_ID="test_paypal_client_id_001",
        PAYPAL_CLIENT_SECRET="test_paypal_secret_99999",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    return settings, db_file


def test_activity_events_match_database_rows(activity_test_setup):
    """Verify each event in /api/activity exactly reflects its underlying database row."""
    settings, db_file = activity_test_setup
    session_id = "sess_activity_user_1"
    search_id = "search_act_001"
    snap_id = "snap_act_001"
    quote_id = "quote_act_001"
    order_id = "ord_act_001"

    with get_db(db_file) as conn:
        # 1. Search row
        conn.execute(
            """
            INSERT INTO searches (id, session_id, query, params_json, result_count, latency_ms, status, created_at)
            VALUES (?, ?, 'wooden walking stick', '{}', 8, 342, 'SUCCESS', '2026-11-11T08:00:00Z')
            """,
            (search_id, session_id),
        )
        # 2. Grounding run row
        conn.execute(
            """
            INSERT INTO grounding_runs (id, search_id, session_id, kept_count, removed_count, created_at)
            VALUES ('gr_001', ?, ?, 3, 5, '2026-11-11T08:00:01Z')
            """,
            (search_id, session_id),
        )
        # 3. Product snapshot row
        conn.execute(
            """
            INSERT INTO product_snapshots (id, search_id, channel3_id, title, price, currency, availability, merchant_domain, buy_url, raw_json, fetched_at)
            VALUES (?, ?, 'ch3_001', 'Sturdy Walking Cane', '39.99', 'USD', 'InStock', 'walgreens.com', 'https://walgreens.com/cane', '{}', '2026-11-11T08:00:01Z')
            """,
            (snap_id, search_id),
        )
        # 4. Quote row with confirmation
        conn.execute(
            """
            INSERT INTO quotes (id, session_id, snapshot_id, quantity, unit_price, currency, total, status, confirmed_at, expires_at, created_at)
            VALUES (?, ?, ?, 1, '39.99', 'USD', '39.99', 'CONFIRMED', '2026-11-11T08:05:00Z', '2026-11-11T08:15:00Z', '2026-11-11T08:02:00Z')
            """,
            (quote_id, session_id, snap_id),
        )
        # 5. Order row (CAPTURED_VERIFIED)
        conn.execute(
            """
            INSERT INTO orders (id, session_id, quote_id, paypal_order_id, status, capture_id, captured_amount, captured_currency, created_at, updated_at)
            VALUES (?, ?, ?, 'PAYPAL_ORDER_LIVE_123', 'CAPTURED_VERIFIED', 'CAP_LIVE_999', '39.99', 'USD', '2026-11-11T08:06:00Z', '2026-11-11T08:06:30Z')
            """,
            (order_id, session_id, quote_id),
        )
        # 6. Payment events rows
        conn.execute(
            """
            INSERT INTO payment_events (order_id, step, http_status, paypal_debug_id, summary, created_at)
            VALUES (?, 'CREATE_ORDER', 201, 'dbg_create_001', 'Created order', '2026-11-11T08:06:05Z')
            """,
            (order_id,),
        )
        conn.execute(
            """
            INSERT INTO payment_events (order_id, step, http_status, paypal_debug_id, summary, created_at)
            VALUES (?, 'CAPTURE_ORDER', 201, 'dbg_capture_002', 'Captured order', '2026-11-11T08:06:30Z')
            """,
            (order_id,),
        )

    client = TestClient(app, cookies={"sid": session_id})
    res = client.get("/api/activity")
    assert res.status_code == 200
    events = res.json()["events"]

    assert len(events) == 6

    # 1. Channel3 search check
    s_ev = events[0]
    assert s_ev["step"] == "channel3_search"
    assert s_ev["source_table"] == "searches"
    assert "wooden walking stick" in s_ev["detail"]
    assert "8 products" in s_ev["detail"]
    assert "342ms" in s_ev["detail"]

    # 2. Grounding check
    g_ev = events[1]
    assert g_ev["step"] == "grounding"
    assert g_ev["source_table"] == "grounding_runs"
    assert "3 recommendations" in g_ev["detail"]
    assert "5 ungrounded" in g_ev["detail"]

    # 3. Price lock check
    p_ev = events[2]
    assert p_ev["step"] == "price_lock"
    assert p_ev["source_table"] == "quotes"
    assert "$39.99 USD" in p_ev["detail"]
    assert "walgreens.com" in p_ev["detail"]

    # 4. Confirmation check
    c_ev = events[3]
    assert c_ev["step"] == "buyer_confirmation"
    assert c_ev["source_table"] == "quotes"
    assert "$39.99 USD" in c_ev["detail"]

    # 5. PayPal create check
    pc_ev = events[4]
    assert pc_ev["step"] == "paypal_order_created"
    assert pc_ev["source_table"] == "payment_events"
    assert "HTTP 201" in pc_ev["detail"]

    # 6. PayPal capture check
    cap_ev = events[5]
    assert cap_ev["step"] == "paypal_capture_verified"
    assert cap_ev["source_table"] == "payment_events"
    assert "order COMPLETED, capture COMPLETED" in cap_ev["detail"]
    assert "$39.99 USD" in cap_ev["detail"]


def test_activity_never_contains_secrets(activity_test_setup):
    """Verify that no API keys, client secrets, passwords, or tokens appear in activity output."""
    settings, db_file = activity_test_setup
    session_id = "sess_activity_sec_check"

    with get_db(db_file) as conn:
        conn.execute(
            """
            INSERT INTO searches (id, session_id, query, params_json, result_count, latency_ms, status, created_at)
            VALUES ('s_sec', ?, 'magnifier', '{"secret": "should_not_leak"}', 5, 200, 'SUCCESS', '2026-11-11T09:00:00Z')
            """,
            (session_id,),
        )

    client = TestClient(app, cookies={"sid": session_id})
    res = client.get("/api/activity")
    assert res.status_code == 200
    res_text = res.text.lower()

    # None of the configured secrets can appear
    assert "test_channel3_secret" not in res_text
    assert "test_gemini_secret" not in res_text
    assert "test_paypal_secret" not in res_text
    assert "should_not_leak" not in res_text
    assert "bearer" not in res_text


def test_activity_session_isolation(activity_test_setup):
    """Verify that User B cannot view User A's activity events."""
    settings, db_file = activity_test_setup

    with get_db(db_file) as conn:
        conn.execute(
            """
            INSERT INTO searches (id, session_id, query, params_json, result_count, latency_ms, status, created_at)
            VALUES ('s_user_a', 'sess_user_a', 'private user query', '{}', 1, 100, 'SUCCESS', '2026-11-11T09:00:00Z')
            """,
        )

    # User B requests activity
    client_b = TestClient(app, cookies={"sid": "sess_user_b"})
    res_b = client_b.get("/api/activity")
    assert res_b.status_code == 200
    events_b = res_b.json()["events"]
    assert len(events_b) == 0


def test_frontend_has_activity_toggle_and_aria_expanded():
    """Verify index.html and receipt.html contain expandable activity panel with aria-expanded."""
    index_html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert 'id="activity-panel"' in index_html
    assert 'id="activity-toggle-btn"' in index_html
    assert 'aria-expanded="false"' in index_html
    assert 'aria-controls="activity-content"' in index_html
    assert "What the assistant did" in index_html

    receipt_html = (ROOT / "static" / "receipt.html").read_text(encoding="utf-8")
    assert 'id="rcpt-activity-panel"' in receipt_html
    assert 'id="rcpt-activity-toggle-btn"' in receipt_html
    assert 'aria-expanded="false"' in receipt_html
    assert "What the assistant did" in receipt_html
