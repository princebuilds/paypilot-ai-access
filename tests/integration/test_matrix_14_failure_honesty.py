"""Cross-Check Matrix Row 14: Upstream failure honesty.

Target Invariant:
- Upstream service failure returns clear error and zero fake products.
- Never falls back to fake or seeded catalogue data silently.
- Error response conforms to SPEC.md Section 3 error envelope.
"""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.agent import AgentService
from app.channel3 import Channel3Client
from app.config import Settings, get_settings
from app.database import init_db
from app.errors import UpstreamServiceError
from app.main import app
from app.routers.agent import get_agent_service


@pytest.fixture
def test_setup(tmp_path):
    db_file = str(tmp_path / "test_matrix_14.db")
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
    return settings


def test_channel3_failure_honesty_zero_products(test_setup, monkeypatch):
    """Channel3 outage produces clear error message and never returns fake fallback data."""
    settings = test_setup
    app.dependency_overrides[get_settings] = lambda: settings

    ch3_client = Channel3Client(settings=settings)
    # Simulate Channel3 returning 500 error
    monkeypatch.setattr(
        ch3_client,
        "_request_with_retry",
        MagicMock(side_effect=UpstreamServiceError("Channel3 upstream returned HTTP 500")),
    )

    # Scripted model that tries to search
    def mock_model(contents, config):
        call_mock = MagicMock()
        call_mock.name = "search_products"
        call_mock.args = {"query": "walking stick"}
        resp = MagicMock()
        resp.function_calls = [call_mock]
        return resp

    agent_svc = AgentService(settings=settings, channel3_client=ch3_client, model_caller=mock_model)
    app.dependency_overrides[get_agent_service] = lambda: agent_svc

    client = TestClient(app)
    res = client.post("/api/agent", json={"message": "walking stick", "budget": "40.00"})
    assert res.status_code == 502
    data = res.json()
    assert data["error"]["code"] == "UPSTREAM_ERROR"
    assert "recommendations" not in data  # No fake products returned
    assert data["error"]["retryable"] is True


def test_gemini_failure_honesty(test_setup):
    """Gemini outage produces clear error message without fake recommendations."""
    settings = test_setup
    app.dependency_overrides[get_settings] = lambda: settings

    def mock_failing_gemini(contents, config):
        raise UpstreamServiceError("The assistant is not responding. Please try again.")

    agent_svc = AgentService(settings=settings, model_caller=mock_failing_gemini)
    app.dependency_overrides[get_agent_service] = lambda: agent_svc

    client = TestClient(app)
    res = client.post("/api/agent", json={"message": "walking stick", "budget": "40.00"})
    assert res.status_code == 502
    data = res.json()
    assert data["error"]["code"] == "UPSTREAM_ERROR"
    assert "assistant is not responding" in data["error"]["message"].lower()


def test_gemini_quota_error_handled_gracefully(test_setup):
    """Gemini 429 quota exhaustion produces friendly busy message without stack traces and updates health."""
    settings = test_setup
    app.dependency_overrides[get_settings] = lambda: settings

    # Simulate google.genai 429 client error
    def mock_quota_exceeded(contents, config):
        raise RuntimeError("google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. Quota exceeded for metric")

    agent_svc = AgentService(settings=settings, model_caller=mock_quota_exceeded)
    app.dependency_overrides[get_agent_service] = lambda: agent_svc

    client = TestClient(app)
    res = client.post("/api/agent", json={"message": "walking stick", "budget": "40.00"})
    assert res.status_code == 502
    data = res.json()
    assert data["error"]["code"] == "UPSTREAM_ERROR"
    assert data["error"]["message"] == "The assistant is busy, please try again."
    assert data["error"]["retryable"] is True
    # Verify no stack trace in response
    assert "traceback" not in res.text.lower()
    assert "file " not in res.text.lower()

    # Verify health endpoint exposes quota_ok: False
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert "quota_ok" in health_data
    assert health_data["quota_ok"] is False
