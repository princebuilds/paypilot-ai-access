import pytest

from app.channel3 import parse_offer_price, parse_product_offer


def test_parse_offer_price_dict_structure():
    """Test price as dictionary with 'price' and 'currency'."""
    offer = {"price": {"price": "24.50", "currency": "USD"}}
    price, currency = parse_offer_price(offer)
    assert price == "24.50"
    assert currency == "USD"


def test_parse_offer_price_amount_key():
    """Test price as dictionary with 'amount' key."""
    offer = {"price": {"amount": 19.99, "currency": "usd"}}
    price, currency = parse_offer_price(offer)
    assert price == "19.99"
    assert currency == "USD"


def test_parse_offer_price_flat_structure():
    """Test flat price and currency fields."""
    offer = {"price": "35.00", "currency": "USD"}
    price, currency = parse_offer_price(offer)
    assert price == "35.00"
    assert currency == "USD"


def test_parse_offer_price_rejects_missing_price():
    offer = {"currency": "USD"}
    with pytest.raises(ValueError, match="Unrecognized offer price"):
        parse_offer_price(offer)


def test_parse_offer_price_rejects_missing_currency():
    offer = {"price": "15.00"}
    with pytest.raises(ValueError, match="Unrecognized offer price"):
        parse_offer_price(offer)


def test_parse_offer_price_rejects_non_numeric():
    offer = {"price": "free", "currency": "USD"}
    with pytest.raises(ValueError, match="Cannot parse price"):
        parse_offer_price(offer)


def test_parse_product_offer_success():
    product = {
        "id": "prod_12345",
        "title": "Sturdy Oak Walking Stick",
        "description": "Handcrafted oak wood cane with rubber tip.",
        "key_features": ["Solid oak", "Ergonomic handle"],
        "materials": ["Oak", "Rubber"],
        "images": ["https://images.example.com/stick1.jpg"],
        "offers": [
            {
                "url": "https://retailer.example.com/item/123",
                "domain": "retailer.example.com",
                "price": {"price": "34.99", "currency": "USD"},
                "availability": "InStock",
            }
        ],
    }
    parsed = parse_product_offer(product)
    assert parsed["channel3_id"] == "prod_12345"
    assert parsed["title"] == "Sturdy Oak Walking Stick"
    assert parsed["price"] == "34.99"
    assert parsed["currency"] == "USD"
    assert parsed["availability"] == "InStock"
    assert parsed["merchant_domain"] == "retailer.example.com"
    assert parsed["image_url"] == "https://images.example.com/stick1.jpg"
    assert "Solid oak" in parsed["key_features"]


def test_parse_product_offer_rejects_missing_title():
    product = {"id": "123", "offers": [{"price": "10.00", "currency": "USD"}]}
    with pytest.raises(ValueError, match="Missing product title"):
        parse_product_offer(product)


def test_parse_product_offer_rejects_empty_offers():
    product = {"id": "123", "title": "Test Item", "offers": []}
    with pytest.raises(ValueError, match="no offers list"):
        parse_product_offer(product)
