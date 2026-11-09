from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.security import rate_limiter


def test_agent_endpoint_enforces_rate_limit(tmp_path):
    db_file = str(tmp_path / "test.db")
    app.dependency_overrides[get_settings] = lambda: Settings(
        OFFLINE_TESTS=1,
        DATABASE_PATH=db_file,
        RATE_LIMIT_PER_HOUR=3,
    )
    rate_limiter.reset()

    client = TestClient(app)

    # 3 calls recorded against IP
    client_ip = "testclient"
    for _ in range(3):
        rate_limiter.record_call(client_ip)

    # 4th call should hit 429
    res = client.post("/api/agent", json={"message": "hello"})
    assert res.status_code == 429
    data = res.json()
    assert data["error"]["code"] == "RATE_LIMITED"
    assert "Many people are using this demo" in data["error"]["message"]
    assert data["error"]["retryable"] is True
