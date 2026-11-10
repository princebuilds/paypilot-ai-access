"""Cross-Check Matrix Row 4: Quote budget limit and exact confirmation verification.

Target Invariant:
- Quoted total exceeding customer budget is blocked (422 BUDGET_EXCEEDED).
- Confirming quote requires exact total match (422 TOTAL_MISMATCH).
- Expired quote cannot be confirmed (422 QUOTE_EXPIRED).
- Valid match transitions status to CONFIRMED.
"""
import datetime

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.database import get_db, init_db
from app.main import app
from app.quotes import QuotesService


@pytest.fixture
def test_setup(tmp_path):
    db_file = str(tmp_path / "test_matrix_04.db")
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

    session_id = "sess_m04"
    search_id = "search_m04"
    snapshot_id = "snap_m04_opener"

    with get_db(db_file) as conn:
        conn.execute(
            """
            INSERT INTO searches (id, session_id, query, status, created_at)
            VALUES (?, ?, ?, 'SUCCESS', '2026-11-10T00:00:00Z')
            """,
            (search_id, session_id, "jar opener"),
        )
        conn.execute(
            """
            INSERT INTO product_snapshots (
                id, search_id, channel3_id, title, price, currency,
                availability, merchant_domain, raw_json, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_id,
                search_id,
                "ch3_opener_01",
                "Ergonomic Jar Opener",
                "15.00",
                "USD",
                "InStock",
                "containerstore.com",
                "{}",
                "2026-11-10T00:00:00Z",
            ),
        )

    return settings, session_id, snapshot_id


def test_quote_fails_when_total_exceeds_budget(test_setup, monkeypatch):
    """Total (15.00 * 2 = 30.00) exceeding budget (25.00) returns 422 BUDGET_EXCEEDED."""
    settings, session_id, snapshot_id = test_setup
    quotes_svc = QuotesService(settings=settings)

    monkeypatch.setattr(
        quotes_svc.channel3_client,
        "get_product",
        lambda channel3_id, currency="USD": {
            "channel3_id": channel3_id,
            "title": "Ergonomic Jar Opener",
            "price": "15.00",
            "currency": "USD",
            "availability": "InStock",
        },
    )

    client = TestClient(app, cookies={"sid": session_id})
    res = client.post("/api/quotes", json={"snapshot_id": snapshot_id, "quantity": 2, "budget": "25.00"})
    assert res.status_code == 422
    data = res.json()
    assert data["error"]["code"] == "BUDGET_EXCEEDED"
    assert "above your $25.00 budget" in data["error"]["message"]


def test_confirm_fails_on_total_mismatch(test_setup, monkeypatch):
    """Customer submitting incorrect confirmation total is rejected (422 TOTAL_MISMATCH)."""
    settings, session_id, snapshot_id = test_setup
    quotes_svc = QuotesService(settings=settings)

    monkeypatch.setattr(
        quotes_svc.channel3_client,
        "get_product",
        lambda channel3_id, currency="USD": {
            "channel3_id": channel3_id,
            "title": "Ergonomic Jar Opener",
            "price": "15.00",
            "currency": "USD",
            "availability": "InStock",
        },
    )

    client = TestClient(app, cookies={"sid": session_id})
    q_res = client.post("/api/quotes", json={"snapshot_id": snapshot_id, "quantity": 1})
    quote_id = q_res.json()["quote_id"]

    # Attempt confirmation with wrong total $14.99 instead of $15.00
    c_res = client.post(f"/api/quotes/{quote_id}/confirm", json={"confirmed_total": "14.99"})
    assert c_res.status_code == 422
    assert c_res.json()["error"]["code"] == "TOTAL_MISMATCH"


def test_confirm_fails_on_expired_quote(test_setup):
    """Quote past its expires_at timestamp cannot be confirmed (422 QUOTE_EXPIRED)."""
    settings, session_id, snapshot_id = test_setup
    past_iso = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=5)).isoformat()
    quote_id = "quote_expired_01"

    with get_db(settings.DATABASE_PATH) as conn:
        conn.execute(
            """
            INSERT INTO quotes (id, session_id, snapshot_id, quantity, unit_price, currency, total, status, expires_at, created_at)
            VALUES (?, ?, ?, 1, '15.00', 'USD', '15.00', 'QUOTED', ?, ?)
            """,
            (quote_id, session_id, snapshot_id, past_iso, past_iso),
        )

    client = TestClient(app, cookies={"sid": session_id})
    c_res = client.post(f"/api/quotes/{quote_id}/confirm", json={"confirmed_total": "15.00"})
    assert c_res.status_code == 422
    assert c_res.json()["error"]["code"] == "QUOTE_EXPIRED"


def test_confirm_succeeds_exact_total(test_setup, monkeypatch):
    """Exact confirmed total transitions quote status to CONFIRMED."""
    settings, session_id, snapshot_id = test_setup
    quotes_svc = QuotesService(settings=settings)

    monkeypatch.setattr(
        quotes_svc.channel3_client,
        "get_product",
        lambda channel3_id, currency="USD": {
            "channel3_id": channel3_id,
            "title": "Ergonomic Jar Opener",
            "price": "15.00",
            "currency": "USD",
            "availability": "InStock",
        },
    )

    client = TestClient(app, cookies={"sid": session_id})
    q_res = client.post("/api/quotes", json={"snapshot_id": snapshot_id, "quantity": 1})
    quote_id = q_res.json()["quote_id"]

    c_res = client.post(f"/api/quotes/{quote_id}/confirm", json={"confirmed_total": "15.00"})
    assert c_res.status_code == 200
    assert c_res.json()["status"] == "CONFIRMED"

    with get_db(settings.DATABASE_PATH) as conn:
        row = conn.execute("SELECT status, confirmed_at FROM quotes WHERE id = ?", (quote_id,)).fetchone()
        assert row["status"] == "CONFIRMED"
        assert row["confirmed_at"] is not None
