import pytest
import respx

from app.config import get_settings
from app.database import init_db
from app.main import app


@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    """Ensure FastAPI dependency overrides do not leak across tests."""
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def isolate_database_for_tests(tmp_path, monkeypatch):
    """Ensure non-live tests never write to the root paypilot.db."""
    test_db = str(tmp_path / "test_isolated.db")
    monkeypatch.setenv("DATABASE_PATH", test_db)
    get_settings.cache_clear()
    init_db(test_db)
    yield test_db
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def block_external_network(request):
    """Ensure non-live tests cannot make real HTTP requests."""
    if "live" in request.keywords:
        yield
        return

    with respx.mock(assert_all_mocked=True) as respx_mock:
        yield respx_mock
