import io
import logging
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.database import init_db
from app.main import app


def test_no_secret_leakage_in_http_responses_or_logs(tmp_path):
    """Verify distinctive test keys never leak in HTTP responses, logs, or static/."""
    distinctive_ch3 = "TESTKEY_CHANNEL3_X9921_UNIQUE"
    distinctive_gem = "TESTKEY_GEMINI_Y8812_UNIQUE"
    distinctive_pp_id = "TESTKEY_PAYPAL_ID_Z7733_UNIQUE"
    distinctive_pp_sec = "TESTKEY_PAYPAL_SEC_W6644_UNIQUE"

    all_secrets = [
        distinctive_ch3,
        distinctive_gem,
        distinctive_pp_id,
        distinctive_pp_sec,
    ]

    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = logging.getLogger()
    logger.addHandler(handler)

    try:
        db_file = str(tmp_path / "test.db")
        init_db(db_file)
        app.dependency_overrides[get_settings] = lambda: Settings(
            OFFLINE_TESTS=1,
            DATABASE_PATH=db_file,
            CHANNEL3_API_KEY=distinctive_ch3,
            GEMINI_API_KEY=distinctive_gem,
            PAYPAL_CLIENT_ID=distinctive_pp_id,
            PAYPAL_CLIENT_SECRET=distinctive_pp_sec,
            GEMINI_MODEL="test-model",
        )
        client = TestClient(app)

        # Call multiple endpoints
        endpoints = [
            ("GET", "/api/health", None),
            ("GET", "/api/config", None),
            ("POST", "/api/agent", {"message": "test", "budget": "20.00"}),
            ("POST", "/api/quotes", {"snapshot_id": "snap1", "quantity": 1}),
            ("POST", "/api/orders", {"quote_id": "q1"}),
            ("GET", "/", None),
        ]

        responses_text = ""
        for method, ep, body in endpoints:
            if method == "GET":
                r = client.get(ep)
            else:
                r = client.post(ep, json=body)
            responses_text += r.text + " "

        # Check HTTP responses for true secrets (never allowed anywhere)
        for secret in [distinctive_ch3, distinctive_gem, distinctive_pp_sec]:
            assert secret not in responses_text, f"Secret leaked in HTTP response: {secret}"

        # Ensure PayPal Client ID only appears in /api/config, never elsewhere
        general_responses = ""
        for method, ep, body in endpoints:
            if ep == "/api/config":
                continue
            r = client.get(ep) if method == "GET" else client.post(ep, json=body)
            general_responses += r.text + " "
        assert distinctive_pp_id not in general_responses, "PayPal Client ID leaked in general API responses"

        # Check logs for secrets
        captured_logs = log_stream.getvalue()
        for secret in all_secrets:
            assert secret not in captured_logs, f"Secret leaked in application logs: {secret}"

        # Check static files for secrets
        static_dir = Path("static")
        if static_dir.exists():
            for p in static_dir.rglob("*"):
                if p.is_file():
                    content = p.read_text(encoding="utf-8", errors="ignore")
                    for secret in all_secrets:
                        assert secret not in content, f"Secret found in static file {p}: {secret}"

    finally:
        logger.removeHandler(handler)


def test_get_config_exposes_paypal_client_id_only_never_secrets(tmp_path):
    """Verify that GET /api/config returns only the public PayPal Client ID and never secrets."""
    db_file = str(tmp_path / "test_cfg.db")
    init_db(db_file)
    test_id = "test_paypal_client_id_12345"
    test_secret = "placeholder_paypal_secret_99999"

    app.dependency_overrides[get_settings] = lambda: Settings(
        OFFLINE_TESTS=1,
        DATABASE_PATH=db_file,
        CHANNEL3_API_KEY="test_ch3_key",
        GEMINI_API_KEY="test_gem_key",
        GEMINI_MODEL="test-model",
        PAYPAL_CLIENT_ID=test_id,
        PAYPAL_CLIENT_SECRET=test_secret,
    )

    client = TestClient(app)
    res = client.get("/api/config")
    assert res.status_code == 200
    data = res.json()

    # Exact expected keys
    assert set(data.keys()) == {"paypal_client_id", "currency", "sandbox"}
    assert data["paypal_client_id"] == test_id
    assert data["currency"] == "USD"
    assert data["sandbox"] is True

    # Critical security checks: ensure secret and other keys are never present
    res_str = res.text.lower()
    assert test_secret.lower() not in res_str
    assert "secret" not in res_str
    assert "gemini" not in res_str
    assert "channel3" not in res_str

