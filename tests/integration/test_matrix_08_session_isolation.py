from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


def test_session_cookie_created_on_first_request(tmp_path):
    db_file = str(tmp_path / "test.db")
    app.dependency_overrides[get_settings] = lambda: Settings(
        OFFLINE_TESTS=1, DATABASE_PATH=db_file
    )
    client = TestClient(app)

    response = client.get("/api/health")
    assert response.status_code == 200
    assert "sid" in response.cookies
    sid = response.cookies["sid"]
    assert len(sid) == 32

    # Second request with cookie preserves session ID
    response2 = client.get("/api/health")
    assert response2.status_code == 200


def test_different_clients_receive_isolated_sessions(tmp_path):
    db_file = str(tmp_path / "test.db")
    app.dependency_overrides[get_settings] = lambda: Settings(
        OFFLINE_TESTS=1, DATABASE_PATH=db_file
    )
    client1 = TestClient(app)
    client2 = TestClient(app)

    res1 = client1.get("/api/health")
    res2 = client2.get("/api/health")

    sid1 = res1.cookies.get("sid")
    sid2 = res2.cookies.get("sid")

    assert sid1 is not None
    assert sid2 is not None
    assert sid1 != sid2


def test_session_cannot_access_or_order_another_sessions_quotes(tmp_path):
    """Session B cannot confirm, order, or view resources belonging to Session A (returns 404)."""
    db_file = str(tmp_path / "test_m08_iso.db")
    from app.database import get_db, init_db
    init_db(db_file)
    settings = Settings(
        OFFLINE_TESTS=1,
        DATABASE_PATH=db_file,
        CHANNEL3_API_KEY="k",
        GEMINI_API_KEY="k",
        GEMINI_MODEL="m",
        PAYPAL_CLIENT_ID="id",
        PAYPAL_CLIENT_SECRET="sec",
    )
    app.dependency_overrides[get_settings] = lambda: settings

    session_a = "sess_user_alpha"
    session_b = "sess_user_beta"
    snap_id = "snap_user_a"
    quote_id = "quote_user_a"
    order_id = "ord_user_a"

    with get_db(db_file) as conn:
        conn.execute("INSERT INTO searches (id, session_id, query, status, created_at) VALUES ('s_a', ?, 'stick', 'SUCCESS', '2026-11-10T00:00:00Z')", (session_a,))
        conn.execute(
            """
            INSERT INTO product_snapshots (id, search_id, channel3_id, title, price, currency, availability, merchant_domain, raw_json, fetched_at)
            VALUES (?, 's_a', 'c_a', 'Stick', '30.00', 'USD', 'InStock', 'store.com', '{}', '2026-11-10T00:00:00Z')
            """,
            (snap_id,),
        )
        conn.execute(
            """
            INSERT INTO quotes (id, session_id, snapshot_id, quantity, unit_price, currency, total, status, expires_at, created_at)
            VALUES (?, ?, ?, 1, '30.00', 'USD', '30.00', 'QUOTED', '2026-11-10T12:00:00Z', '2026-11-10T00:00:00Z')
            """,
            (quote_id, session_a, snap_id),
        )
        conn.execute(
            """
            INSERT INTO orders (id, session_id, quote_id, status, created_at, updated_at)
            VALUES (?, ?, ?, 'ORDER_CREATED', '2026-11-10T00:00:00Z', '2026-11-10T00:00:00Z')
            """,
            (order_id, session_a, quote_id),
        )

    client_b = TestClient(app, cookies={"sid": session_b})

    # 1. Session B cannot create a quote from Session A's snapshot
    res_q = client_b.post("/api/quotes", json={"snapshot_id": snap_id, "quantity": 1})
    assert res_q.status_code == 404

    # 2. Session B cannot confirm Session A's quote
    res_c = client_b.post(f"/api/quotes/{quote_id}/confirm", json={"confirmed_total": "30.00"})
    assert res_c.status_code == 404

    # 3. Session B cannot create an order using Session A's quote
    res_o = client_b.post("/api/orders", json={"quote_id": quote_id})
    assert res_o.status_code == 404

    # 4. Session B cannot view Session A's order receipt
    res_r = client_b.get(f"/api/orders/{order_id}")
    assert res_r.status_code == 404
