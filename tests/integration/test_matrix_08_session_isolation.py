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
