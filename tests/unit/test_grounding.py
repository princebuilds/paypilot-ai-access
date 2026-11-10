"""Unit tests for grounding validator (app/grounding.py).

Verifies AGENTS.md Section 7 and SPEC.md Section 7 rules:
- Verbatim evidence check against snapshot fields.
- Absent requested feature must not be claimed / drops recommendation if ungrounded.
- Wrong price in reason claim or evidence drops recommendation.
- Product ID not in snapshots drops recommendation.
- Safe reply text fallback when summary contains invalid price claims.
"""
import json
from decimal import Decimal
from pathlib import Path

import pytest

from app.grounding import (
    build_safe_reply_text,
    extract_mentioned_prices,
    ground_recommendations,
    is_verbatim_evidence,
)
from app.schemas import RecommendationItem


@pytest.fixture
def real_walking_stick_snapshot():
    fixture_path = Path("tests/fixtures/channel3_search_real.json")
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    raw_p = data["products"][0]
    return {
        "id": "snap_stick_001",
        "channel3_id": raw_p["id"],
        "title": raw_p["title"],
        "description": raw_p["description"],
        "key_features_json": json.dumps(raw_p.get("key_features") or []),
        "materials_json": json.dumps(raw_p.get("materials") or []),
        "price": "26.01",
        "currency": "USD",
        "availability": "InStock",
        "merchant_domain": "jbtools.com",
    }


def test_extract_mentioned_prices():
    text = "This item is $26.01, discounted from $35.00, or 26.01 USD."
    prices = extract_mentioned_prices(text)
    assert Decimal("26.01") in prices
    assert Decimal("35.00") in prices


def test_verbatim_evidence_matching(real_walking_stick_snapshot):
    # Description contains "weatherproof" and title contains "Natural Wood"
    assert is_verbatim_evidence("weatherproof", real_walking_stick_snapshot, "description")
    assert is_verbatim_evidence("Natural Wood", real_walking_stick_snapshot, "title")
    # Absent feature: "large buttons" is NOT in walking stick description
    assert not is_verbatim_evidence("large buttons", real_walking_stick_snapshot, "description")
    assert not is_verbatim_evidence("rechargeable lithium battery", real_walking_stick_snapshot, "materials")


def test_absent_feature_drops_recommendation(real_walking_stick_snapshot):
    """If model invents an evidence claim not present in text, the recommendation is dropped."""
    raw_recs = [
        {
            "product_id": real_walking_stick_snapshot["channel3_id"],
            "reasons": [
                {
                    "claim": "Features extra-large high contrast buttons",
                    "evidence_field": "description",
                    "evidence_text": "extra-large high contrast buttons",  # Not in walking stick text
                }
            ],
        }
    ]
    snapshots = {real_walking_stick_snapshot["id"]: real_walking_stick_snapshot}
    surviving, drops = ground_recommendations(raw_recs, snapshots)

    assert len(surviving) == 0
    assert len(drops) > 0
    assert "not found verbatim" in drops[0]


def test_wrong_price_in_reason_drops_recommendation(real_walking_stick_snapshot):
    """If reason mentions a price that differs from snapshot price, it is dropped."""
    raw_recs = [
        {
            "product_id": real_walking_stick_snapshot["channel3_id"],
            "reasons": [
                {
                    "claim": "Great deal for only $15.00!",  # Snapshot price is $26.01
                    "evidence_field": "description",
                    "evidence_text": "handcrafted",
                }
            ],
        }
    ]
    snapshots = {real_walking_stick_snapshot["id"]: real_walking_stick_snapshot}
    surviving, drops = ground_recommendations(raw_recs, snapshots)

    assert len(surviving) == 0
    assert any("does not match snapshot price" in d for d in drops)


def test_unknown_product_id_drops_recommendation(real_walking_stick_snapshot):
    """Model inventing a non-existent product ID is dropped."""
    raw_recs = [
        {
            "product_id": "invented_prod_999",
            "reasons": [{"claim": "Nice wood", "evidence_field": "title", "evidence_text": "wood"}],
        }
    ]
    snapshots = {real_walking_stick_snapshot["id"]: real_walking_stick_snapshot}
    surviving, drops = ground_recommendations(raw_recs, snapshots)

    assert len(surviving) == 0
    assert any("not found in current search snapshots" in d for d in drops)


def test_valid_grounded_recommendation_survives(real_walking_stick_snapshot):
    """Verbatim evidence from real fixture passes grounding."""
    raw_recs = [
        {
            "product_id": real_walking_stick_snapshot["id"],
            "reasons": [
                {
                    "claim": "Solid handcrafted wood construction for stability",
                    "evidence_field": "title",
                    "evidence_text": "Natural Wood Walking Stick",
                }
            ],
        }
    ]
    snapshots = {real_walking_stick_snapshot["id"]: real_walking_stick_snapshot}
    surviving, drops = ground_recommendations(raw_recs, snapshots)

    assert len(surviving) == 1
    assert surviving[0].snapshot_id == "snap_stick_001"
    assert surviving[0].channel3_id == real_walking_stick_snapshot["channel3_id"]
    assert surviving[0].price == "26.01"
    assert surviving[0].purchasable is True
    assert len(surviving[0].reasons) == 1


def test_safe_reply_text_falls_back_on_wrong_price():
    item = RecommendationItem(
        snapshot_id="s1",
        channel3_id="c1",
        title="Walking Stick",
        merchant_domain="shop.com",
        price="26.01",
        currency="USD",
        availability="InStock",
        purchasable=True,
    )
    # Model summary hallucinates a cheaper price
    bad_summary = "I found this walking stick for just $10.00!"
    safe_text = build_safe_reply_text(bad_summary, [item])

    assert "$10.00" not in safe_text
    assert "The first is Walking Stick at $26.01." in safe_text


def test_safe_reply_text_preserves_valid_summary():
    item = RecommendationItem(
        snapshot_id="s1",
        channel3_id="c1",
        title="Walking Stick",
        merchant_domain="shop.com",
        price="26.01",
        currency="USD",
        availability="InStock",
        purchasable=True,
    )
    good_summary = "I found 1 option for you at $26.01."
    safe_text = build_safe_reply_text(good_summary, [item])
    assert safe_text == good_summary


def test_relevance_rule_rejects_irrelevant_product_types():
    """Verify that when a user requests a walking stick, novelty pin-back buttons are dropped."""
    button_snapshot = {
        "id": "snap_button_001",
        "channel3_id": "ch3_btn_99",
        "title": "Broomstick Ride Rectangular Button",
        "description": "Show off your love for witches with this rectangular button pin.",
        "key_features_json": json.dumps(["Metal pin back"]),
        "materials_json": json.dumps(["Metal", "Plastic"]),
        "price": "3.99",
        "currency": "USD",
        "availability": "InStock",
        "merchant_domain": "hottopic.com",
    }
    snapshots = {button_snapshot["id"]: button_snapshot}
    raw_recs = [
        {
            "product_id": "snap_button_001",
            "reasons": [
                {
                    "claim": "It is a rectangular button pin",
                    "evidence_field": "description",
                    "evidence_text": "rectangular button pin",
                }
            ],
        }
    ]

    # User explicitly requested a walking stick
    surviving, drops = ground_recommendations(
        raw_recs,
        snapshots,
        requested_query="walking stick with large buttons",
    )
    assert len(surviving) == 0
    assert len(drops) == 1
    assert "not the requested product type" in drops[0]

    # Verify reply text generates plain rejection message
    reply = build_safe_reply_text(
        model_summary="Here are button products.",
        surviving_items=surviving,
        requested_query="walking stick with large buttons",
    )
    assert "I could not find a walking stick with large buttons" in reply

