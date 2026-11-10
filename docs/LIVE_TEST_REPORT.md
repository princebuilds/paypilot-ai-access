# docs/LIVE_TEST_REPORT.md: PayPilot AI ACCESS Live Test Report

Status: NOT RUN (Will record real Channel3, Gemini, and PayPal Sandbox interactions during Phase B2, B3, B6).

## Channel3 Live Integration Run (2026-11-10T01:56:37.993957+00:00)
- **Status:** PASS
- **Search Query:** sturdy wooden walking stick
- **Results Count:** 3
- **Top Product ID:** 7V1UUgC
- **Top Product Title:** Natural Wood Walking Stick
- **Price / Currency:** 39.99 USD
- **Availability:** InStock
- **Fixtures Saved:** `tests/fixtures/channel3_search_real.json`, `tests/fixtures/channel3_product_real.json`

## Channel3 Live Integration Run (2026-11-10T02:15:18.002024+00:00)
- **Status:** PASS
- **Search Query:** sturdy wooden walking stick
- **Results Count:** 3
- **Top Product ID:** 7V1UUgC
- **Top Product Title:** Natural Wood Walking Stick
- **Price / Currency:** 39.99 USD
- **Availability:** InStock
- **Fixtures Saved:** `tests/fixtures/channel3_search_real.json`, `tests/fixtures/channel3_product_real.json`

## Gemini Live Function-Calling Run (2026-11-10T02:38:07.031229+00:00)
- **Status:** PASS
- **Model ID:** gemini-3.5-flash
- **Latency:** 2.36s
- **Tool Called:** `search_products`
- **Parsed Arguments:** `{"query": "sturdy wooden walking stick", "max_price": 40}`

## Gemini Live Function-Calling Run (2026-11-10T02:39:30.640172+00:00)
- **Status:** PASS
- **Model ID:** gemini-3.5-flash
- **Latency:** 4.25s
- **Tool Called:** `search_products`
- **Parsed Arguments:** `{"max_price": 40, "query": "sturdy wooden walking stick"}`
