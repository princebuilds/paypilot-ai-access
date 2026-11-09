import pytest
import respx


@pytest.fixture(autouse=True)
def block_external_network(request):
    """Ensure non-live tests cannot make real HTTP requests."""
    if "live" in request.keywords:
        yield
        return

    with respx.mock(assert_all_mocked=True) as respx_mock:
        yield respx_mock
