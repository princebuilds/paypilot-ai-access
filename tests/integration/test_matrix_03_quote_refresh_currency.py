"""Cross-Check Matrix Row 3: Quote, Channel3 refresh, and currency verification.

Target Invariant:
- Detail refresh returning non-USD or OutOfStock raises NOT_PURCHASABLE (422).
- Detail refresh returning altered price raises PRICE_CHANGED (409) with new total.
- In-stock USD offer with matching price successfully creates price-locked quote.
"""
import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.database import get_db, init_db
from app.main import app
from app.quotes import QuotesService
from app.routers.quotes import get_quotes_service


@pytest.fixture
def test_setup(tmp_path):
    db_file = str(tmp_path / "test_matrix_03.db")
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

    # Insert baseline search and product snapshot
    session_id = "sess_m03"
    search_id = "search_m03"
    snapshot_id = "snap_m03_stick"

    with get_db(db_file) as conn:
        conn.execute(
            """
            INSERT INTO searches (id, session_id, query, status, created_at)
            VALUES (?, ?, ?, 'SUCCESS', '2026-11-10T00:00:00Z')
            """,
            (search_id, session_id, "wooden cane"),
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
                "ch3_stick_01",
                "Natural Wood Walking Cane",
                "25.00",
                "USD",
                "InStock",
                "wayfair.com",
                "{}",
                "2026-11-10T00:00:00Z",
            ),
        )

    return settings, session_id, snapshot_id


def test_quote_fails_when_product_out_of_stock(test_setup, monkeypatch):
    """Refreshed product detail that is OutOfStock returns 422 NOT_PURCHASABLE."""
    settings, session_id, snapshot_id = test_setup
    quotes_svc = QuotesService(settings=settings)
    app.dependency_overrides[get_quotes_service] = lambda: quotes_svc

    # Mock Channel3 get_product returning OutOfStock
    monkeypatch.setattr(
        quotes_svc.channel3_client,
        "get_product",
        lambda channel3_id, currency="USD": {
            "channel3_id": channel3_id,
            "title": "Natural Wood Walking Cane",
            "price": "25.00",
            "currency": "USD",
            "availability": "OutOfStock",
        },
    )

    client = TestClient(app, cookies={"sid": session_id})
    res = client.post("/api/quotes", json={"snapshot_id": snapshot_id, "quantity": 1})
    assert res.status_code == 422
    data = res.json()
    assert data["error"]["code"] == "NOT_PURCHASABLE"


def test_quote_fails_when_product_non_usd(test_setup, monkeypatch):
    """Refreshed product detail that is non-USD returns 422 NOT_PURCHASABLE."""
    settings, session_id, snapshot_id = test_setup
    quotes_svc = QuotesService(settings=settings)
    app.dependency_overrides[get_quotes_service] = lambda: quotes_svc

    monkeypatch.setattr(
        quotes_svc.channel3_client,
        "get_product",
        lambda channel3_id, currency="USD": {
            "channel3_id": channel3_id,
            "title": "Natural Wood Walking Cane",
            "price": "22.00",
            "currency": "EUR",
            "availability": "InStock",
        },
    )

    client = TestClient(app, cookies={"sid": session_id})
    res = client.post("/api/quotes", json={"snapshot_id": snapshot_id, "quantity": 1})
    assert res.status_code == 422
    data = res.json()
    assert data["error"]["code"] == "NOT_PURCHASABLE"


def test_quote_fails_on_price_changed(test_setup, monkeypatch):
    """When refreshed price differs from snapshot price, returns 409 PRICE_CHANGED."""
    settings, session_id, snapshot_id = test_setup
    quotes_svc = QuotesService(settings=settings)
    app.dependency_overrides[get_quotes_service] = lambda: quotes_svc

    # Stored price is 25.00, refreshed price is 30.00
    monkeypatch.setattr(
        quotes_svc.channel3_client,
        "get_product",
        lambda channel3_id, currency="USD": {
            "channel3_id": channel3_id,
            "title": "Natural Wood Walking Cane",
            "price": "30.00",
            "currency": "USD",
            "availability": "InStock",
        },
    )

    client = TestClient(app, cookies={"sid": session_id})
    res = client.post("/api/quotes", json={"snapshot_id": snapshot_id, "quantity": 2})
    assert res.status_code == 409
    data = res.json()
    assert data["error"]["code"] == "PRICE_CHANGED"
    # Price changed to 30.00 * 2 = $60.00
    assert "$60.00" in data["error"]["message"]


def test_quote_succeeds_matching_price_usd_instock(test_setup, monkeypatch):
    """When refreshed price matches stored snapshot, 200 QUOTED response is returned."""
    settings, session_id, snapshot_id = test_setup
    quotes_svc = QuotesService(settings=settings)
    app.dependency_overrides[get_quotes_service] = lambda: quotes_svc

    monkeypatch.setattr(
        quotes_svc.channel3_client,
        "get_product",
        lambda channel3_id, currency="USD": {
            "channel3_id": channel3_id,
            "title": "Natural Wood Walking Cane",
            "price": "25.00",
            "currency": "USD",
            "availability": "InStock",
        },
    )

    client = TestClient(app, cookies={"sid": session_id})
    res = client.post("/api/quotes", json={"snapshot_id": snapshot_id, "quantity": 2, "budget": "60.00"})
    assert res.status_code == 200
    data = res.json()
    assert data["quote_id"].startswith("quote_")
    assert data["unit_price"] == "25.00"
    assert data["total"] == "50.00"
    assert data["within_budget"] is True
    assert data["status"] == "QUOTED"
