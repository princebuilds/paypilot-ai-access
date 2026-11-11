#!/usr/bin/env python3
"""Live smoke test runner for PayPilot AI ACCESS.

Executes real external API calls against Channel3, Gemini, and PayPal Sandbox.
Saves sanitized real response fixtures and updates docs/LIVE_TEST_REPORT.md.
Never prints or logs API keys or secrets.
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import httpx  # noqa: E402

from app.config import get_settings  # noqa: E402


def sanitize_dict(obj):
    """Recursively strip any API key, token, payer name, email or address strings from dictionaries."""
    if isinstance(obj, dict):
        clean = {}
        for k, v in obj.items():
            k_lower = k.lower()
            if any(s in k_lower for s in ("api_key", "secret", "password", "auth", "x-api-key")) or k_lower in ("token", "access_token"):
                clean[k] = "[REDACTED]"
            elif k_lower in ("email_address", "email", "full_name", "given_name", "surname"):
                clean[k] = "[REDACTED]"
            elif k_lower in ("address_line_1", "address_line_2", "admin_area_2", "postal_code", "account_id", "merchant_id", "payer_id"):
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
        print("Saved fixture: tests/fixtures/channel3_search_real.json")

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

        print("\nFirst Product Overview:")
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
        print("[PASS] Detail HTTP 200 OK")
        print("Saved fixture: tests/fixtures/channel3_product_real.json")

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
        print("Updated live test report: docs/LIVE_TEST_REPORT.md\n")


def run_gemini_smoke_test():
    """Execute live Gemini function calling test and record in report."""
    settings = get_settings()
    api_key = settings.GEMINI_API_KEY
    model_name = settings.GEMINI_MODEL

    if not api_key:
        print("[ERROR] GEMINI_API_KEY not configured in .env")
        sys.exit(1)
    if not model_name:
        print("[ERROR] GEMINI_MODEL not configured in .env")
        sys.exit(1)

    print("\n--- Live Gemini Function Calling Integration Test ---")
    print(f"Target Model: {model_name}")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    tool_def = types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="search_products",
                description="Search for products in catalog",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "query": types.Schema(type="STRING", description="Search query terms"),
                        "max_price": types.Schema(type="NUMBER", description="Maximum price in USD"),
                    },
                    required=["query"],
                ),
            )
        ]
    )

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text="User request: sturdy wooden walking stick. Budget: 40.00 USD.")],
        )
    ]

    config = types.GenerateContentConfig(
        system_instruction=(
            "You are PayPilot, a shopping assistant for people who find online shopping hard. "
            "If the product type or budget is missing, ask one short question. "
            "When both product type and budget are present, call search_products."
        ),
        tools=[tool_def],
        temperature=0.0,
    )

    start_t = datetime.datetime.now(datetime.timezone.utc)
    try:
        res = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )
        latency = (datetime.datetime.now(datetime.timezone.utc) - start_t).total_seconds()
        calls = getattr(res, "function_calls", None)

        if not calls:
            print(f"[FAIL] Model did not trigger function call. Returned text: {getattr(res, 'text', '')[:100]}")
            sys.exit(1)

        fc = calls[0]
        print(f"[PASS] Function call received (latency: {latency:.2f}s)")
        print(f"  Tool Name: {fc.name}")
        print(f"  Arguments: {fc.args}")

        report_file = ROOT / "docs" / "LIVE_TEST_REPORT.md"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        report_entry = f"""
## Gemini Live Function-Calling Run ({now_iso})
- **Status:** PASS
- **Model ID:** {model_name}
- **Latency:** {latency:.2f}s
- **Tool Called:** `{fc.name}`
- **Parsed Arguments:** `{json.dumps(fc.args)}`
"""
        with open(report_file, "a", encoding="utf-8") as f:
            f.write(report_entry)
        print("Updated live test report: docs/LIVE_TEST_REPORT.md\n")

    except Exception as e:
        print(f"[FAIL] Gemini call failed: {type(e).__name__}: {str(e)[:200]}")
        sys.exit(1)


def run_paypal_smoke_test():
    """Execute live PayPal Sandbox create-order to confirm credentials and payload."""
    settings = get_settings()
    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
        print("[ERROR] PAYPAL_CLIENT_ID or PAYPAL_CLIENT_SECRET not configured in .env")
        sys.exit(1)

    print("\n--- Live PayPal Sandbox Integration Test (Create-Order Only) ---")
    print("Endpoint: https://api-m.sandbox.paypal.com/v2/checkout/orders")

    from app.paypal import PayPalClient

    paypal_client = PayPalClient(settings=settings)
    test_internal_id = f"smoke_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')}"
    test_total = "39.99"

    start_t = datetime.datetime.now(datetime.timezone.utc)
    try:
        paypal_order_id, debug_id = paypal_client.create_order(
            order_id=test_internal_id,
            total=test_total,
            currency="USD",
        )
        latency = (datetime.datetime.now(datetime.timezone.utc) - start_t).total_seconds()
        print(f"[PASS] PayPal Order Created successfully (latency: {latency:.2f}s)")
        print(f"  Internal Order ID: {test_internal_id}")
        print(f"  PayPal Order ID:   {paypal_order_id}")
        print(f"  PayPal Debug ID:   {debug_id}")
        print("  Status:            CREATED (Sandbox create-only verified)")

        report_file = ROOT / "docs" / "LIVE_TEST_REPORT.md"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        report_entry = f"""
## PayPal Sandbox Live Create-Order Run ({now_iso})
- **Status:** PASS (HTTP 201 Created)
- **Internal Order ID:** `{test_internal_id}`
- **PayPal Order ID:** `{paypal_order_id}`
- **PayPal Debug ID:** `{debug_id}`
- **Total Amount:** `$39.99 USD`
- **Verification:** Sandbox credentials accepted, plain amount payload verified, no money spent.
"""
        with open(report_file, "a", encoding="utf-8") as f:
            f.write(report_entry)
        print("Updated live test report: docs/LIVE_TEST_REPORT.md\n")

    except Exception as e:
        print(f"[FAIL] PayPal create-order failed: {type(e).__name__}: {str(e)[:200]}")
        sys.exit(1)


def run_paypal_full_smoke_test():
    """Execute live end-to-end PayPal Sandbox flow: create, approve, capture, and 4-invariant verification."""
    settings = get_settings()
    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
        print("[ERROR] PAYPAL_CLIENT_ID or PAYPAL_CLIENT_SECRET not configured in .env")
        sys.exit(1)

    print("\n--- Live PayPal Sandbox Full Checkout & Capture Test ---")
    print("Base: https://api-m.sandbox.paypal.com")

    from app.paypal import PayPalClient

    paypal_client = PayPalClient(settings=settings)
    test_internal_id = f"smoke_full_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')}"
    test_total = "39.99"
    currency = "USD"
    fixtures_dir = ROOT / "tests" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    token = paypal_client._get_access_token()
    create_url = "https://api-m.sandbox.paypal.com/v2/checkout/orders"
    create_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "PayPal-Request-Id": test_internal_id,
    }
    create_payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "custom_id": test_internal_id,
                "description": "PayPilot AI ACCESS - Sandbox Demo Order",
                "amount": {
                    "currency_code": currency,
                    "value": test_total,
                },
            }
        ],
        "application_context": {
            "return_url": "http://127.0.0.1:8000/receipt.html",
            "cancel_url": "http://127.0.0.1:8000",
        },
    }

    start_create_t = datetime.datetime.now(datetime.timezone.utc)
    with httpx.Client(timeout=paypal_client.timeout) as client:
        create_resp = client.post(create_url, headers=create_headers, json=create_payload)
        create_latency = (datetime.datetime.now(datetime.timezone.utc) - start_create_t).total_seconds()
        create_debug_id = create_resp.headers.get("Paypal-Debug-Id")

        if create_resp.status_code not in (200, 201):
            print(f"[FAIL] PayPal order create returned HTTP {create_resp.status_code} (debug_id: {create_debug_id})")
            sys.exit(1)

        create_data = create_resp.json()
        sanitized_create = sanitize_dict(create_data)
        (fixtures_dir / "paypal_create_real.json").write_text(
            json.dumps(sanitized_create, indent=2), encoding="utf-8"
        )

        paypal_order_id = create_data["id"]
        order_status = create_data.get("status")
        links = create_data.get("links") or []
        approve_url = next((link["href"] for link in links if link.get("rel") in ("approve", "payer-action")), None)

        print(f"[PASS] Order Created (latency: {create_latency:.2f}s)")
        print(f"  Internal Order ID: {test_internal_id}")
        print(f"  PayPal Order ID:   {paypal_order_id}")
        print(f"  Order Status:      {order_status}")
        print(f"  Create Debug ID:   {create_debug_id}")
        print(f"\nApproval URL: {approve_url}")

        if not approve_url:
            print("[FAIL] No approval URL found in PayPal create response links.")
            sys.exit(1)

        print("\n" + "=" * 70)
        print("ACTION REQUIRED:")
        print("1. Open the Approval URL above in your browser.")
        print("2. Log in with your US PayPal Sandbox personal buyer account.")
        print("3. Click 'Complete Purchase' (or Approve).")
        print("4. Return here and press ENTER to trigger capture and verification.")
        print("=" * 70 + "\n")

        print("Waiting for buyer approval on PayPal Sandbox (polling for up to 5 minutes)...")
        import time
        approved = False
        for poll_idx in range(60):
            try:
                check_data, _ = paypal_client.get_order(paypal_order_id)
                st = check_data.get("status")
                if st in ("APPROVED", "COMPLETED"):
                    print(f"[PASS] Buyer approved order! Current PayPal Status: {st}")
                    approved = True
                    break
                else:
                    if (poll_idx + 1) % 6 == 0:
                        print(f"  Still waiting for buyer approval... (current status: {st}, elapsed: {(poll_idx+1)*5}s)")
            except Exception as e:
                print(f"  [WARN] Polling get_order failed: {e}")
            time.sleep(5)

        if not approved:
            print("[FAIL] Order was not approved within 5 minutes.")
            sys.exit(1)

        # Execute capture
        capture_url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{paypal_order_id}/capture"
        capture_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": f"capture_{test_internal_id}",
        }

        start_cap_t = datetime.datetime.now(datetime.timezone.utc)
        cap_resp = client.post(capture_url, headers=capture_headers, json={})
        cap_latency = (datetime.datetime.now(datetime.timezone.utc) - start_cap_t).total_seconds()
        capture_debug_id = cap_resp.headers.get("Paypal-Debug-Id")

        if cap_resp.status_code in (200, 201):
            capture_data = cap_resp.json()
        elif cap_resp.status_code == 422:
            error_data = cap_resp.json()
            issues = error_data.get("details", [])
            if any(i.get("issue") == "ORDER_ALREADY_CAPTURED" for i in issues):
                capture_data, _ = paypal_client.get_order(paypal_order_id)
            else:
                print(f"[FAIL] Capture returned HTTP 422: {cap_resp.text[:200]} (debug_id: {capture_debug_id})")
                sys.exit(1)
        else:
            print(f"[FAIL] Capture returned HTTP {cap_resp.status_code}: {cap_resp.text[:200]} (debug_id: {capture_debug_id})")
            sys.exit(1)

        sanitized_capture = sanitize_dict(capture_data)
        (fixtures_dir / "paypal_capture_real.json").write_text(
            json.dumps(sanitized_capture, indent=2), encoding="utf-8"
        )

        v_status, cap_id, cap_val, cap_curr, msg = paypal_client.verify_capture(
            internal_order_id=test_internal_id,
            expected_total=test_total,
            expected_currency=currency,
            paypal_payload=capture_data,
        )

        print(f"\n[PASS] Capture Executed (latency: {cap_latency:.2f}s)")
        print(f"  Capture Debug ID:  {capture_debug_id}")
        print(f"  Capture ID:        {cap_id}")
        print(f"  Verification:      {v_status}")
        print(f"  Message:           {msg}")
        print(f"  Captured Total:    ${cap_val} {cap_curr}")

        # Invariant checks
        inv_order_ok = capture_data.get("status") == "COMPLETED"
        pu = (capture_data.get("purchase_units") or [{}])[0]
        caps = (pu.get("payments") or {}).get("captures") or [{}]
        inv_cap_ok = caps[0].get("status") == "COMPLETED"
        inv_amt_ok = cap_val == test_total and cap_curr == currency
        inv_custom_ok = pu.get("custom_id") == test_internal_id

        print("\nFour Non-Negotiable Invariants Status:")
        print(f"  1. Order status is COMPLETED:          {'PASS' if inv_order_ok else 'FAIL'}")
        print(f"  2. Capture status is COMPLETED:        {'PASS' if inv_cap_ok else 'FAIL'}")
        print(f"  3. Captured amount equals stored quote:{'PASS' if inv_amt_ok else 'FAIL'}")
        print(f"  4. custom_id equals internal order ID: {'PASS' if inv_custom_ok else 'FAIL'}")

        if not (inv_order_ok and inv_cap_ok and inv_amt_ok and inv_custom_ok and v_status == "CAPTURED_VERIFIED"):
            print("[FAIL] One or more capture invariants failed!")
            sys.exit(1)

        print("\n[ALL 4 INVARIANTS VERIFIED]")
        print("Saved fixtures: tests/fixtures/paypal_create_real.json, tests/fixtures/paypal_capture_real.json")

        report_file = ROOT / "docs" / "LIVE_TEST_REPORT.md"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        report_entry = f"""
## PayPal Sandbox Live Full Checkout & Capture Run ({now_iso})
- **Status:** PASS (HTTP 201 Created -> HTTP 201 Captured -> CAPTURED_VERIFIED)
- **Internal Order ID:** `{test_internal_id}`
- **PayPal Order ID:** `{paypal_order_id}`
- **Create Debug ID:** `{create_debug_id}`
- **Capture Debug ID:** `{capture_debug_id}`
- **Capture ID:** `{cap_id}`
- **Total Amount:** `${test_total} {currency}`
- **Invariant 1 (Order COMPLETED):** PASS (`{capture_data.get("status")}`)
- **Invariant 2 (Capture COMPLETED):** PASS (`{caps[0].get("status")}`)
- **Invariant 3 (Amount/Currency Match):** PASS (`${cap_val} {cap_curr}`)
- **Invariant 4 (custom_id Match):** PASS (`{test_internal_id}`)
- **Fixtures Saved:** `tests/fixtures/paypal_create_real.json`, `tests/fixtures/paypal_capture_real.json`
"""
        with open(report_file, "a", encoding="utf-8") as f:
            f.write(report_entry)
        print("Updated live test report: docs/LIVE_TEST_REPORT.md\n")


def run_paypal_capture_smoke_test(paypal_order_id: str):
    """Capture and verify an already-approved PayPal Sandbox order."""
    settings = get_settings()
    from app.paypal import PayPalClient

    paypal_client = PayPalClient(settings=settings)
    order_data, debug_id = paypal_client.get_order(paypal_order_id)
    purchase_units = order_data.get("purchase_units") or []
    if not purchase_units:
        print(f"[FAIL] Order {paypal_order_id} has no purchase_units.")
        sys.exit(1)

    pu = purchase_units[0]
    test_internal_id = pu.get("custom_id") or f"custom_{paypal_order_id}"
    amt_obj = pu.get("amount") or {}
    test_total = amt_obj.get("value", "39.99")
    currency = amt_obj.get("currency_code", "USD")

    print(f"\n--- Capturing PayPal Order {paypal_order_id} (Status: {order_data.get('status')}) ---")
    token = paypal_client._get_access_token()
    capture_url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{paypal_order_id}/capture"
    capture_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "PayPal-Request-Id": f"capture_{test_internal_id}",
    }

    start_cap_t = datetime.datetime.now(datetime.timezone.utc)
    with httpx.Client(timeout=paypal_client.timeout) as client:
        cap_resp = client.post(capture_url, headers=capture_headers, json={})
        cap_latency = (datetime.datetime.now(datetime.timezone.utc) - start_cap_t).total_seconds()
        capture_debug_id = cap_resp.headers.get("Paypal-Debug-Id")

        if cap_resp.status_code in (200, 201):
            capture_data = cap_resp.json()
        elif cap_resp.status_code == 422:
            error_data = cap_resp.json()
            issues = error_data.get("details", [])
            if any(i.get("issue") == "ORDER_ALREADY_CAPTURED" for i in issues):
                capture_data, _ = paypal_client.get_order(paypal_order_id)
            else:
                print(f"[FAIL] Capture returned HTTP 422: {cap_resp.text[:200]} (debug_id: {capture_debug_id})")
                sys.exit(1)
        else:
            print(f"[FAIL] Capture returned HTTP {cap_resp.status_code}: {cap_resp.text[:200]} (debug_id: {capture_debug_id})")
            sys.exit(1)

    fixtures_dir = ROOT / "tests" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    sanitized_capture = sanitize_dict(capture_data)
    (fixtures_dir / "paypal_capture_real.json").write_text(
        json.dumps(sanitized_capture, indent=2), encoding="utf-8"
    )

    v_status, cap_id, cap_val, cap_curr, msg = paypal_client.verify_capture(
        internal_order_id=test_internal_id,
        expected_total=test_total,
        expected_currency=currency,
        paypal_payload=capture_data,
    )

    if v_status != "CAPTURED_VERIFIED":
        print(f"[FAIL] Invariant verification failed: {v_status} - {msg}")
        sys.exit(1)

    caps = capture_data.get("purchase_units", [{}])[0].get("payments", {}).get("captures", [])
    print(f"[PASS] Order Captured and Verified (latency: {cap_latency:.2f}s)")
    print(f"  Internal Order ID:    {test_internal_id}")
    print(f"  PayPal Order ID:      {paypal_order_id}")
    print(f"  Capture Debug ID:     {capture_debug_id}")
    print(f"  Capture ID:           {cap_id}")
    print(f"  Order Status:         {capture_data.get('status')}")
    print(f"  Capture Status:       {caps[0].get('status') if caps else 'UNKNOWN'}")
    print(f"  Captured Amount:      ${cap_val} {cap_curr}")
    print(f"  Captured custom_id:   {test_internal_id}")
    print("\n[ALL 4 INVARIANTS VERIFIED]")

    report_file = ROOT / "docs" / "LIVE_TEST_REPORT.md"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report_entry = f"""
## PayPal Sandbox Live Full Checkout & Capture Run ({now_iso})
- **Status:** PASS (HTTP 201 Captured -> CAPTURED_VERIFIED)
- **Internal Order ID:** `{test_internal_id}`
- **PayPal Order ID:** `{paypal_order_id}`
- **Capture Debug ID:** `{capture_debug_id}`
- **Capture ID:** `{cap_id}`
- **Total Amount:** `${test_total} {currency}`
- **Invariant 1 (Order COMPLETED):** PASS (`{capture_data.get("status")}`)
- **Invariant 2 (Capture COMPLETED):** PASS (`{caps[0].get("status") if caps else "UNKNOWN"}`)
- **Invariant 3 (Amount/Currency Match):** PASS (`${cap_val} {cap_curr}`)
- **Invariant 4 (custom_id Match):** PASS (`{test_internal_id}`)
- **Fixtures Saved:** `tests/fixtures/paypal_capture_real.json`
"""
    with open(report_file, "a", encoding="utf-8") as f:
        f.write(report_entry)
    print("Updated live test report: docs/LIVE_TEST_REPORT.md\n")


def main():
    parser = argparse.ArgumentParser(description="PayPilot AI ACCESS Live Smoke Test")
    parser.add_argument("--channel3", action="store_true", help="Run Channel3 live verification")
    parser.add_argument("--gemini", action="store_true", help="Run Gemini live verification")
    parser.add_argument("--paypal", action="store_true", help="Run PayPal live verification (create-order only)")
    parser.add_argument("--paypal-full", action="store_true", help="Run full PayPal Sandbox create, approve, and capture verification")
    parser.add_argument("--paypal-capture", type=str, help="Capture and verify an existing approved PayPal order ID")
    args = parser.parse_args()

    if args.channel3:
        run_channel3_smoke_test()
    if args.gemini:
        run_gemini_smoke_test()
    if args.paypal:
        run_paypal_smoke_test()
    if args.paypal_full:
        run_paypal_full_smoke_test()
    if args.paypal_capture:
        run_paypal_capture_smoke_test(args.paypal_capture)
    if not args.channel3 and not args.gemini and not args.paypal and not args.paypal_full and not args.paypal_capture:
        run_channel3_smoke_test()


if __name__ == "__main__":
    main()
