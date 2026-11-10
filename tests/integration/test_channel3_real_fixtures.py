import json
from pathlib import Path

from app.channel3 import parse_product_offer

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_parser_against_real_channel3_search_fixture():
    """Verify defensive parser against recorded real Channel3 search response."""
    fixture_path = FIXTURES_DIR / "channel3_search_real.json"
    assert fixture_path.exists(), "channel3_search_real.json fixture must exist"

    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    products = data.get("products") or []
    assert len(products) == 3

    for p in products:
        parsed = parse_product_offer(p)
        assert parsed["channel3_id"]
        assert parsed["title"]
        assert parsed["price"]
        assert parsed["currency"] == "USD"
        assert parsed["availability"] == "InStock"
        assert parsed["merchant_domain"]
        assert parsed["buy_url"].startswith("https://")


def test_parser_against_real_channel3_product_detail_fixture():
    """Verify defensive parser against recorded real Channel3 product detail response."""
    fixture_path = FIXTURES_DIR / "channel3_product_real.json"
    assert fixture_path.exists(), "channel3_product_real.json fixture must exist"

    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    product = data.get("product") or data

    parsed = parse_product_offer(product)
    assert parsed["channel3_id"] == "7V1UUgC"
    assert parsed["title"] == "Natural Wood Walking Stick"
    assert parsed["price"] == "39.99"
    assert parsed["currency"] == "USD"
    assert parsed["availability"] == "InStock"
    assert parsed["merchant_domain"] == "walmart.com"
    assert len(parsed["description"]) > 100
