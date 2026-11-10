"""Integration tests for Cross-Check Matrix Row 2: Agent to Quote interaction.

Target Invariant:
- snapshot_id returned by /api/agent is valid, formatted, and queryable in product_snapshots.
- QuoteCreateRequest schema validates the snapshot_id and session isolation.
"""
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.agent import AgentService
from app.channel3 import Channel3Client
from app.config import Settings, get_settings
from app.database import get_db_connection, init_db
from app.main import app
from app.routers.agent import get_agent_service
from app.schemas import QuoteCreateRequest


@pytest.fixture
def test_env(tmp_path):
    db_file = str(tmp_path / "test_matrix_02.db")
    init_db(db_file)
    settings = Settings(
        OFFLINE_TESTS=1,
        DATABASE_PATH=db_file,
        CHANNEL3_API_KEY="test-ch3-key",
        GEMINI_API_KEY="test-gemini-key",
        GEMINI_MODEL="test-model",
        PAYPAL_CLIENT_ID="test-paypal-id",
        PAYPAL_CLIENT_SECRET="test-paypal-sec",
    )
    return settings, db_file


def test_agent_snapshot_id_valid_for_quote(test_env, monkeypatch):
    """Snapshot ID from /api/agent response is valid and ready for quote creation."""
    settings, db_file = test_env
    app.dependency_overrides[get_settings] = lambda: settings

    fixture_path = Path("tests/fixtures/channel3_search_real.json")
    real_ch3_data = json.loads(fixture_path.read_text(encoding="utf-8"))

    ch3_client = Channel3Client(settings=settings)
    monkeypatch.setattr(
        ch3_client,
        "_request_with_retry",
        lambda *args, **kwargs: MagicMock(
            status_code=200,
            json=lambda: real_ch3_data,
            headers={"date": "Tue, 10 Nov 2026 00:00:00 GMT"},
        ),
    )

    def mock_model_caller(contents, config):
        if len(contents) == 1:
            call_mock = MagicMock()
            call_mock.name = "search_products"
            call_mock.args = {"query": "sturdy walking stick", "max_price": 40.0}
            resp_mock = MagicMock()
            resp_mock.function_calls = [call_mock]
            resp_mock.text = None
            return resp_mock
        else:
            first_prod = real_ch3_data["products"][0]
            resp_mock = MagicMock()
            resp_mock.function_calls = None
            resp_mock.text = json.dumps(
                {
                    "summary": "Found walking stick.",
                    "clarifying_question": None,
                    "recommendations": [
                        {
                            "product_id": first_prod["id"],
                            "reasons": [
                                {
                                    "claim": "Solid handcrafted wood",
                                    "evidence_field": "title",
                                    "evidence_text": "Natural Wood Walking Stick",
                                }
                            ],
                        }
                    ],
                }
            )
            return resp_mock

    agent_svc = AgentService(settings=settings, channel3_client=ch3_client, model_caller=mock_model_caller)
    app.dependency_overrides[get_agent_service] = lambda: agent_svc

    client = TestClient(app)
    res = client.post(
        "/api/agent",
        json={"message": "walking stick under 40", "budget": "40.00"},
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["recommendations"]) == 1
    snapshot_id = data["recommendations"][0]["snapshot_id"]

    # Verify that the QuoteCreateRequest schema accepts this snapshot_id
    quote_req = QuoteCreateRequest(snapshot_id=snapshot_id, quantity=1, budget="40.00")
    assert quote_req.snapshot_id == snapshot_id
    assert quote_req.quantity == 1

    # Verify that calling /api/quotes with client works
    q_res = client.post("/api/quotes", json={"snapshot_id": snapshot_id, "quantity": 1, "budget": "40.00"})
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert q_data["quote_id"].startswith("quote_")
    assert q_data["status"] == "QUOTED"

    # Verify that another session calling /api/quotes with the same snapshot_id gets 404
    other_client = TestClient(app, cookies={"sid": "other_unrelated_session"})
    other_res = other_client.post("/api/quotes", json={"snapshot_id": snapshot_id, "quantity": 1})
    assert other_res.status_code == 404

    # Verify that the snapshot exists in DB and is linked to the session's search
    with get_db_connection(db_file) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.id, p.price, p.currency, p.availability, s.session_id
            FROM product_snapshots p
            JOIN searches s ON p.search_id = s.id
            WHERE p.id = ?
            """,
            (snapshot_id,),
        )
        row = cur.fetchone()
        assert row is not None
        assert row["currency"] == "USD"
        assert row["availability"] == "InStock"
