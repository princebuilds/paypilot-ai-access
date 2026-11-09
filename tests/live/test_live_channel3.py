import pytest

from app.channel3 import Channel3Client
from app.config import get_settings


@pytest.mark.live
def test_live_channel3_search_and_detail():
    """Verify live Channel3 search and detail endpoints with configured credentials."""
    settings = get_settings()
    if not settings.CHANNEL3_API_KEY:
        pytest.skip("CHANNEL3_API_KEY not configured in .env")

    client = Channel3Client()
    search_id, products = client.search(
        query="sturdy wooden walking stick",
        session_id="test_live_session",
        limit=3,
        in_stock_only=True,
    )
    assert search_id is not None
    assert len(products) > 0

    first_product = products[0]
    assert first_product["channel3_id"]
    assert first_product["title"]
    assert first_product["price"]

    # Detail call
    detail = client.get_product(first_product["channel3_id"])
    assert detail["channel3_id"] == first_product["channel3_id"]
    assert detail["title"]
