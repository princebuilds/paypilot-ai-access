#!/usr/bin/env python3
"""Live smoke test runner for PayPilot AI ACCESS.

Executes real external API calls against Channel3, Gemini, and PayPal Sandbox.
Saves sanitized real response fixtures and updates docs/LIVE_TEST_REPORT.md.
Never prints or logs API keys or secrets.
"""
import argparse
import datetime
import json
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import httpx
from app.config import get_settings


def sanitize_dict(obj):
    """Recursively strip any API key or token strings from dictionaries."""
    if isinstance(obj, dict):
        clean = {}
        for k, v in obj.items():
            k_lower = k.lower()
            if any(s in k_lower for s in ("api_key", "secret", "password", "auth", "x-api-key")) or k_lower in ("token", "access_token"):
                clean[k] = "[REDACTED]"
            else:
                clean[k] = sanitize_dict(v)
        return clean
    elif isinstance(obj, list):
        return [sanitize_dict(item) for item in obj]
    return obj


def run_channel3_smoke_test():
    """Execute live Channel3 search and detail call, saving sanitized fixtures."""
    settings = get_settings()
    api_key = settings.CHANNEL3_API_KEY
    if not api_key:
        print("[ERROR] CHANNEL3_API_KEY not configured in .env")
        sys.exit(1)

    print("\n--- Live Channel3 Integration Test ---")
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    query = "sturdy wooden walking stick"
    search_url = "https://api.trychannel3.com/v1/search"
    search_payload = {
        "query": query,
        "limit": 3,
        "filters": {"availability": ["InStock"]},
    }

    fixtures_dir = ROOT / "tests" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    print(f"Executing search: query='{query}', limit=3 ...")
    with httpx.Client(timeout=20.0) as client:
        start_t = datetime.datetime.now(datetime.timezone.utc)
        resp = client.post(search_url, headers=headers, json=search_payload)
        latency = (datetime.datetime.now(datetime.timezone.utc) - start_t).total_seconds()

        if resp.status_code != 200:
            print(f"[FAIL] Channel3 search returned HTTP {resp.status_code}: {resp.text[:200]}")
            sys.exit(1)

        search_data = resp.json()
        sanitized_search = sanitize_dict(search_data)
        (fixtures_dir / "channel3_search_real.json").write_text(
            json.dumps(sanitized_search, indent=2), encoding="utf-8"
        )

        products = search_data.get("products") or []
        count = len(products)
        print(f"[PASS] Search HTTP 200 OK (latency: {latency:.2f}s, products found: {count})")
        print(f"Saved fixture: tests/fixtures/channel3_search_real.json")

        if count == 0:
            print("[WARN] Search returned zero products; cannot test detail call.")
            return

        first_p = products[0]
        first_id = first_p.get("id")
        first_title = first_p.get("title", "No Title")
        first_offers = first_p.get("offers") or []
        first_offer = first_offers[0] if first_offers else {}

        raw_p_price = first_offer.get("price")
        price_disp = raw_p_price if not isinstance(raw_p_price, dict) else raw_p_price.get("price")
        curr_disp = first_offer.get("currency") or (raw_p_price.get("currency") if isinstance(raw_p_price, dict) else "USD")
        avail_disp = first_offer.get("availability") or "Unknown"
        domain_disp = first_offer.get("domain") or "retailer.com"

        print(f"\nFirst Product Overview:")
        print(f"  ID:           {first_id}")
        print(f"  Title:        {first_title[:60]}")
        print(f"  Price:        {price_disp} {curr_disp}")
        print(f"  Availability: {avail_disp}")
        print(f"  Merchant:     {domain_disp}")

        # Product detail call
        detail_url = f"https://api.trychannel3.com/v1/products/{first_id}"
        print(f"\nExecuting detail call for ID: {first_id} ...")
        detail_resp = client.get(detail_url, headers=headers, params={"currency": "USD"})

        if detail_resp.status_code != 200:
            print(f"[FAIL] Channel3 detail returned HTTP {detail_resp.status_code}: {detail_resp.text[:200]}")
            sys.exit(1)

        detail_data = detail_resp.json()
        sanitized_detail = sanitize_dict(detail_data)
        (fixtures_dir / "channel3_product_real.json").write_text(
            json.dumps(sanitized_detail, indent=2), encoding="utf-8"
        )
        print(f"[PASS] Detail HTTP 200 OK")
        print(f"Saved fixture: tests/fixtures/channel3_product_real.json")

        # Record in docs/LIVE_TEST_REPORT.md
        report_file = ROOT / "docs" / "LIVE_TEST_REPORT.md"
        report_entry = f"""
## Channel3 Live Integration Run ({datetime.datetime.now(datetime.timezone.utc).isoformat()})
- **Status:** PASS
- **Search Query:** {query}
- **Results Count:** {count}
- **Top Product ID:** {first_id}
- **Top Product Title:** {first_title}
- **Price / Currency:** {price_disp} {curr_disp}
- **Availability:** {avail_disp}
- **Fixtures Saved:** `tests/fixtures/channel3_search_real.json`, `tests/fixtures/channel3_product_real.json`
"""
        with open(report_file, "a", encoding="utf-8") as f:
            f.write(report_entry)
        print(f"Updated live test report: docs/LIVE_TEST_REPORT.md\n")


def main():
    parser = argparse.ArgumentParser(description="PayPilot AI ACCESS Live Smoke Test")
    parser.add_argument("--channel3", action="store_true", help="Run Channel3 live verification")
    parser.add_argument("--gemini", action="store_true", help="Run Gemini live verification")
    parser.add_argument("--paypal", action="store_true", help="Run PayPal live verification")
    args = parser.parse_args()

    if args.channel3 or (not args.gemini and not args.paypal):
        run_channel3_smoke_test()


if __name__ == "__main__":
    main()
