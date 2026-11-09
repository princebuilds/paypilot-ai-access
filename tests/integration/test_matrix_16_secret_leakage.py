import io
import logging
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
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

        # Check HTTP responses for secrets
        for secret in all_secrets:
            assert secret not in responses_text, f"Secret leaked in HTTP response: {secret}"

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
