import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


def test_health_endpoint_exposes_booleans_only(tmp_path):
    db_file = str(tmp_path / "test.db")
    app.dependency_overrides[get_settings] = lambda: Settings(
        OFFLINE_TESTS=1,
        DATABASE_PATH=db_file,
        CHANNEL3_API_KEY="test_channel3_secret_key",
        GEMINI_API_KEY="test_gemini_secret_key",
        PAYPAL_CLIENT_ID="test_paypal_id",
        PAYPAL_CLIENT_SECRET="test_paypal_secret",
        GEMINI_MODEL="test-model-alias",
    )
    client = TestClient(app)

    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()

    assert data["ok"] is True
    assert isinstance(data["channel3_configured"], bool)
    assert isinstance(data["gemini_configured"], bool)
    assert isinstance(data["paypal_configured"], bool)
    assert data["channel3_configured"] is True
    assert data["gemini_configured"] is True
    assert data["paypal_configured"] is True

    # Critical check: No secret values appear in the health response body
    raw_response = res.text
    assert "test_channel3_secret_key" not in raw_response
    assert "test_gemini_secret_key" not in raw_response
    assert "test_paypal_id" not in raw_response
    assert "test_paypal_secret" not in raw_response


def test_startup_fails_in_live_mode_with_missing_key():
    settings = Settings(
        OFFLINE_TESTS=0,
        CHANNEL3_API_KEY=None,
        GEMINI_API_KEY="key",
        GEMINI_MODEL="model",
        PAYPAL_CLIENT_ID="id",
        PAYPAL_CLIENT_SECRET="secret",
    )
    with pytest.raises(RuntimeError) as exc_info:
        settings.validate_for_startup()
    assert "CHANNEL3_API_KEY" in str(exc_info.value)
