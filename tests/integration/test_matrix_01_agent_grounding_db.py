"""Integration tests for Cross-Check Matrix Row 1: Agent, Grounding, Database.

Target Invariant:
- Every snapshot_id returned by /api/agent exists in product_snapshots table.
- Dropped recommendations are logged and excluded from response.
- Grounding uses real Channel3 fixture data.
- Vague input triggers exactly one clarifying question without searching.
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


@pytest.fixture
def test_env(tmp_path):
    db_file = str(tmp_path / "test_matrix_01.db")
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


def test_agent_grounding_db_snapshots_exist(test_env, monkeypatch):
    """Every snapshot_id in recommendations must exist in product_snapshots table."""
    settings, db_file = test_env
    app.dependency_overrides[get_settings] = lambda: settings

    # Load real Channel3 search fixture
    fixture_path = Path("tests/fixtures/channel3_search_real.json")
    real_ch3_data = json.loads(fixture_path.read_text(encoding="utf-8"))

    # Mock Channel3 search returning real fixture data
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

    # Scripted Gemini caller simulating 2-turn manual function calling
    def mock_model_caller(contents, config):
        if len(contents) == 1:
            # Turn 1: Model calls search_products
            call_mock = MagicMock()
            call_mock.name = "search_products"
            call_mock.args = {"query": "sturdy wooden walking stick", "max_price": 40.0}
            resp_mock = MagicMock()
            resp_mock.function_calls = [call_mock]
            resp_mock.text = None
            return resp_mock
        else:
            # Turn 2: Model returns structured recommendations with verbatim evidence
            first_prod = real_ch3_data["products"][0]
            resp_mock = MagicMock()
            resp_mock.function_calls = None
            resp_mock.text = json.dumps(
                {
                    "summary": "I found 1 handcrafted walking stick option for you.",
                    "clarifying_question": None,
                    "recommendations": [
                        {
                            "product_id": first_prod["id"],
                            "reasons": [
                                {
                                    "claim": "Handcrafted solid wood walking stick",
                                    "evidence_field": "title",
                                    "evidence_text": "Natural Wood Walking Stick",
                                }
                            ],
                        },
                        # Also include a fake ungrounded product that must be dropped
                        {
                            "product_id": "fake_nonexistent_id",
                            "reasons": [
                                {
                                    "claim": "Cheap stick",
                                    "evidence_field": "title",
                                    "evidence_text": "Fake",
                                }
                            ],
                        },
                    ],
                }
            )
            return resp_mock

    agent_svc = AgentService(
        settings=settings,
        channel3_client=ch3_client,
        model_caller=mock_model_caller,
    )
    app.dependency_overrides[get_agent_service] = lambda: agent_svc

    client = TestClient(app)
    res = client.post(
        "/api/agent",
        json={"message": "I need a sturdy walking stick under $40", "budget": "40.00"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["search_id"] is not None
    assert len(data["recommendations"]) == 1  # The fake product was dropped!

    rec = data["recommendations"][0]
    snapshot_id = rec["snapshot_id"]
    assert snapshot_id.startswith("snap_") or len(snapshot_id) > 5
    assert rec["channel3_id"] == real_ch3_data["products"][0]["id"]
    assert rec["price"] == "39.99"
    assert rec["currency"] == "USD"
    assert rec["purchasable"] is True

    # Invariant check: snapshot_id must exist in product_snapshots table
    with get_db_connection(db_file) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, title, price, currency FROM product_snapshots WHERE id = ?", (snapshot_id,))
        row = cur.fetchone()
        assert row is not None
        assert row["title"] == rec["title"]
        assert row["price"] == rec["price"]


def test_vague_request_triggers_clarifying_question(test_env):
    """Vague user input without product type or budget returns clarifying question without search."""
    settings, db_file = test_env
    app.dependency_overrides[get_settings] = lambda: settings

    # Model caller simulating clarifying question response (no tool call)
    def mock_clarifying_caller(contents, config):
        resp = MagicMock()
        resp.function_calls = None
        resp.text = "What type of product are you looking to buy, and what is your budget?"
        return resp

    agent_svc = AgentService(
        settings=settings,
        model_caller=mock_clarifying_caller,
    )
    app.dependency_overrides[get_agent_service] = lambda: agent_svc

    client = TestClient(app)
    res = client.post(
        "/api/agent",
        json={"message": "Help me shop"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["clarifying_question"] is not None
    assert "budget" in data["clarifying_question"].lower() or "product" in data["clarifying_question"].lower()
    assert len(data["recommendations"]) == 0
    assert data["live_data"]["channel3_calls"] == 0
