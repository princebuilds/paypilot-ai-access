import httpx
import pytest

from app.channel3 import Channel3Client
from app.database import init_db
from app.errors import UpstreamServiceError


def test_channel3_search_timeout_raises_upstream_error(respx_mock, tmp_path):
    db_file = str(tmp_path / "test.db")
    init_db(db_file)
    respx_mock.post("https://api.trychannel3.com/v1/search").mock(
        side_effect=httpx.TimeoutException("Connection timed out")
    )
    client = Channel3Client(api_key="test_ch3_key")

    with pytest.raises(UpstreamServiceError, match="Channel3 connection failed"):
        client.search("walking stick", session_id="sess_1", db_path=db_file)


def test_channel3_search_retries_on_500(respx_mock, tmp_path):
    db_file = str(tmp_path / "test.db")
    init_db(db_file)
    # First attempt 500, second attempt 200
    route = respx_mock.post("https://api.trychannel3.com/v1/search")
    route.side_effect = [
        httpx.Response(500, text="Internal Server Error"),
        httpx.Response(
            200,
            json={
                "products": [
                    {
                        "id": "item_1",
                        "title": "Wooden Cane",
                        "offers": [{"price": "25.00", "currency": "USD", "availability": "InStock"}],
                    }
                ]
            },
        ),
    ]

    client = Channel3Client(api_key="test_ch3_key")
    search_id, results = client.search("cane", session_id="sess_2", db_path=db_file)
    assert len(results) == 1
    assert results[0]["title"] == "Wooden Cane"
    assert route.call_count == 2


def test_channel3_search_caching(respx_mock, tmp_path):
    db_file = str(tmp_path / "test.db")
    init_db(db_file)
    route = respx_mock.post("https://api.trychannel3.com/v1/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "products": [
                    {
                        "id": "stick_1",
                        "title": "Hiking Pole",
                        "offers": [{"price": "19.99", "currency": "USD", "availability": "InStock"}],
                    }
                ]
            },
        )
    )

    client = Channel3Client(api_key="test_ch3_key")
    # First search -> hits mock endpoint
    sid1, res1 = client.search("hiking", session_id="sess_3", db_path=db_file)
    assert route.call_count == 1
    assert len(res1) == 1

    # Second identical search -> served from SQLite cache, call_count remains 1
    sid2, res2 = client.search("hiking", session_id="sess_3", db_path=db_file)
    assert route.call_count == 1
    assert sid1 == sid2
    assert len(res2) == 1
    assert res2[0]["title"] == "Hiking Pole"


def test_channel3_get_product_detail(respx_mock):
    respx_mock.get("https://api.trychannel3.com/v1/products/prod_999").mock(
        return_value=httpx.Response(
            200,
            json={
                "product": {
                    "id": "prod_999",
                    "title": "Refreshed Wooden Cane",
                    "offers": [
                        {
                            "url": "https://store.example.com/p999",
                            "domain": "store.example.com",
                            "price": {"price": "29.99", "currency": "USD"},
                            "availability": "InStock",
                        }
                    ],
                }
            },
        )
    )
    client = Channel3Client(api_key="test_ch3_key")
    product = client.get_product("prod_999")
    assert product["channel3_id"] == "prod_999"
    assert product["price"] == "29.99"
    assert product["currency"] == "USD"
    assert product["merchant_domain"] == "store.example.com"
