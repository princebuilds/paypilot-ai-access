"""Grounding validator for PayPilot AI ACCESS.

Grounds agent recommendations strictly against stored product snapshots.
Enforces AGENTS.md Section 7 and SPEC.md Section 7 invariants:
- Drops recommendations whose product ID is not in this request's stored snapshots.
- Drops recommendations whose evidence text is not found verbatim in snapshot fields.
- Drops recommendations whose claims contain price values differing from snapshot price.
- Logs every dropped recommendation with a clear diagnostic reason.
- Validates model reply text / summary against grounded prices and item counts.
"""
import json
import logging
import re
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from app.schemas import GroundingReason, RecommendationItem

logger = logging.getLogger("paypilot.grounding")

# Regex to extract dollar amounts: e.g. $29.99, $30, 29.99 USD, 30 dollars
PRICE_REGEX = re.compile(
    r"(?:\$\s*(\d+(?:\.\d{2})?)|(\d+(?:\.\d{2})?)\s*(?:usd|dollars?))",
    re.IGNORECASE,
)


def extract_mentioned_prices(text: str) -> List[Decimal]:
    """Extract all numeric prices mentioned in text."""
    prices: List[Decimal] = []
    if not text:
        return prices
    for match in PRICE_REGEX.finditer(text):
        num_str = match.group(1) or match.group(2)
        if num_str:
            try:
                prices.append(Decimal(num_str))
            except Exception:
                continue
    return prices


def get_field_searchable_text(snapshot: Dict[str, Any], field_name: str) -> str:
    """Extract string text for a snapshot field (handling json lists for features/materials)."""
    raw_val = snapshot.get(field_name) or snapshot.get(f"{field_name}_json")
    if raw_val is None:
        return ""
    if isinstance(raw_val, list):
        return " ".join(str(x) for x in raw_val)
    if isinstance(raw_val, str):
        # Attempt to parse as JSON if it looks like a list
        s = raw_val.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return " ".join(str(x) for x in parsed)
            except Exception:
                pass
        return raw_val
    return str(raw_val)


def is_verbatim_evidence(evidence_text: str, snapshot: Dict[str, Any], field_name: Optional[str] = None) -> bool:
    """Check if evidence_text appears verbatim in the specified snapshot field or allowed fields."""
    ev = evidence_text.strip().lower()
    if not ev:
        return False

    allowed_fields = ["title", "description", "key_features", "materials"]
    fields_to_check = [field_name] if field_name in allowed_fields else allowed_fields

    for f in fields_to_check:
        corpus = get_field_searchable_text(snapshot, f).lower()
        if ev in corpus:
            return True

    return False


def validate_reasons(
    raw_reasons: List[Dict[str, Any]],
    snapshot: Dict[str, Any],
) -> Tuple[List[GroundingReason], List[str]]:
    """Validate each reason against verbatim snapshot text and price accuracy."""
    valid_reasons: List[GroundingReason] = []
    drop_reasons: List[str] = []

    try:
        snapshot_price = Decimal(str(snapshot.get("price", "0.00")))
    except Exception:
        snapshot_price = Decimal("0.00")

    for idx, r in enumerate(raw_reasons):
        claim = str(r.get("claim", "")).strip()
        field = str(r.get("evidence_field", "description")).strip()
        ev_text = str(r.get("evidence_text", "")).strip()

        if not claim:
            drop_reasons.append(f"Reason {idx} missing claim")
            continue
        if not ev_text:
            drop_reasons.append(f"Reason {idx} missing evidence_text")
            continue

        # 1. Price check in claim or evidence
        mentioned_prices = extract_mentioned_prices(claim) + extract_mentioned_prices(ev_text)
        price_mismatch = False
        for p in mentioned_prices:
            if p != snapshot_price:
                price_mismatch = True
                drop_reasons.append(
                    f"Reason {idx} mentions price ${p} which does not match snapshot price ${snapshot_price}"
                )
                break
        if price_mismatch:
            continue

        # 2. Verbatim evidence check
        if not is_verbatim_evidence(ev_text, snapshot, field):
            drop_reasons.append(
                f"Reason {idx} evidence_text '{ev_text[:50]}' not found verbatim in snapshot {field}"
            )
            continue

        valid_reasons.append(
            GroundingReason(
                claim=claim,
                evidence_field=field if field in ("title", "description", "key_features", "materials") else "description",
                evidence_text=ev_text,
            )
        )

    return valid_reasons, drop_reasons


def ground_recommendations(
    raw_recommendations: List[Dict[str, Any]],
    snapshots_by_id: Dict[str, Dict[str, Any]],
) -> Tuple[List[RecommendationItem], List[str]]:
    """Filter model recommendations against stored snapshots.

    Drops any recommendation whose product ID is missing, whose evidence text is not verbatim,
    or whose reasons contain incorrect price claims.
    """
    surviving_items: List[RecommendationItem] = []
    dropped_logs: List[str] = []

    for raw_rec in raw_recommendations:
        prod_id = str(raw_rec.get("product_id", "")).strip()
        # Match by snapshot id or channel3_id
        snapshot = snapshots_by_id.get(prod_id)
        if not snapshot:
            for s in snapshots_by_id.values():
                if s.get("channel3_id") == prod_id:
                    snapshot = s
                    break

        if not snapshot:
            msg = f"Dropped recommendation: product_id '{prod_id}' not found in current search snapshots"
            logger.warning(msg)
            dropped_logs.append(msg)
            continue

        raw_reasons = raw_rec.get("reasons") or []
        valid_reasons, reason_drops = validate_reasons(raw_reasons, snapshot)

        if not valid_reasons:
            msg = f"Dropped recommendation [{snapshot.get('channel3_id')}]: 0 valid reasons survived grounding. Drops: {'; '.join(reason_drops)}"
            logger.warning(msg)
            dropped_logs.append(msg)
            continue

        # Determine purchasability: requires USD and InStock
        is_usd = str(snapshot.get("currency", "")).upper() == "USD"
        is_instock = str(snapshot.get("availability", "")).lower() in ("instock", "in_stock")
        purchasable = is_usd and is_instock
        not_purchasable_reason = None
        if not is_usd:
            not_purchasable_reason = f"Currency {snapshot.get('currency')} is not USD"
        elif not is_instock:
            not_purchasable_reason = "Product is out of stock"

        item = RecommendationItem(
            snapshot_id=snapshot.get("id", ""),
            channel3_id=snapshot.get("channel3_id", ""),
            title=snapshot.get("title", ""),
            image_url=snapshot.get("image_url"),
            merchant_domain=snapshot.get("merchant_domain", ""),
            price=str(snapshot.get("price", "0.00")),
            currency=str(snapshot.get("currency", "USD")),
            availability=str(snapshot.get("availability", "InStock")),
            purchasable=purchasable,
            not_purchasable_reason=not_purchasable_reason,
            buy_url=snapshot.get("buy_url"),
            reasons=valid_reasons,
        )
        surviving_items.append(item)

        if len(surviving_items) >= 3:
            break

    return surviving_items, dropped_logs


def build_safe_reply_text(
    model_summary: Optional[str],
    surviving_items: List[RecommendationItem],
) -> str:
    """Produce grounded reply text for voice output and UI."""
    if not surviving_items:
        return "I could not find a confident match. Try describing it another way."

    count = len(surviving_items)
    first_item = surviving_items[0]
    template_fallback = f"I found {count} options. The first is {first_item.title} at ${first_item.price}."

    if not model_summary:
        return template_fallback

    summary = model_summary.strip()
    mentioned_prices = extract_mentioned_prices(summary)
    valid_prices = {Decimal(item.price) for item in surviving_items}

    for p in mentioned_prices:
        if p not in valid_prices:
            logger.info("Falling back to template reply_text: summary mentioned ungrounded price $%s", p)
            return template_fallback

    return summary
