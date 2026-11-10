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

## Live End-to-End Agent & Grounding Run (2026-11-10T02:51:16.452031+00:00)
- **Model:** `gemini-3.5-flash-lite`
- **Channel3 Base:** `api.trychannel3.com/v1`

### Demo Query 1: "I need a sturdy wooden walking stick under $40"
- **Budget:** $40.00
- **Search ID:** `68fcdb24d6a141d1b8e5ca77e2857769`
- **Reply Text:** Here are sturdy wooden walking sticks that fit your budget.
- **Recommendations Returned:** 3
  1. **Wooden Cane Walking Stick** ($24.99 USD, `wayfair.com`)
     - *Claim:* It has an anti-slip stopper for stability.
       *Evidence (key_features):* "Anti-slip rubber stopper for stability"
  2. **Natural Wood Walking Stick** ($39.99 USD, `walmart.com`)
     - *Claim:* It has a durable anti-skid rubber tip.
       *Evidence (key_features):* "Durable anti-skid rubber tip"
  3. **Wooden Cane Walking Stick** ($30.99 USD, `wayfair.com`)
     - *Claim:* It has an anti-slip rubber stopper.
       *Evidence (key_features):* "Anti-slip rubber stopper at the bottom"

### Demo Query 2: "I need a jar opener for weak hands under $25"
- **Budget:** $25.00
- **Search ID:** `96cbd3218cae4adfbd0f55c94558be2e`
- **Reply Text:** Here are three jar openers that fit your budget and help with weak hands.
- **Recommendations Returned:** 3
  1. **Jar Opener** ($9.89 USD, `kohls.com`)
     - *Claim:* It helps open lids smoothly.
       *Evidence (description):* "The Farberware Classic Soft Grips Jar Opener is designed to easily open stubborn jar lids and caps."
  2. **Twisting Jar Opener** ($19.99 USD, `oxo.com`)
     - *Claim:* It reduces strain on your hands.
       *Evidence (description):* "This OXO Good Grips Twisting Jar Opener with Base Pad is designed for effortless jar opening, reducing strain on your hands."
  3. **Good Grips Twisting Jar Opener** ($16.99 USD, `containerstore.com`)
     - *Claim:* It has an easy grip handle.
       *Evidence (key_features):* "Ergonomic handle for a comfortable grip"

### Demo Query 3: "I need a handheld magnifying glass with light under $25"
- **Budget:** $25.00
- **Search ID:** `c27e0ba4e9f244dabc3ef659f16070e8`
- **Reply Text:** Here are three handheld magnifying glasses with lights that fit your budget.
- **Recommendations Returned:** 3
  1. **5X Magnifying Glass with Light, Handheld 48 LED Lighted Magnifier for Reading** ($22.99 USD, `wayfair.com`)
     - *Claim:* It has a built-in light.
       *Evidence (title):* "5X Magnifying Glass with Light, Handheld 48 LED Lighted Magnifier for Reading"
  2. **Magnifying Glass with LED Light, Lightweight Handheld Lighted 4x Magnifier** ($17.99 USD, `wayfair.com`)
     - *Claim:* It has an easy to hold design.
       *Evidence (key_features):* "Lightweight design for easy portability"
  3. **Magnifying Glass with Light, 10X 45X Handheld Glass Reading Magnifier** ($9.99 USD, `newegg.com`)
     - *Claim:* It has built-in LED lighting.
       *Evidence (key_features):* "Integrated LED lighting for the 45X lens"

### Negative Test: "I need a walking stick with large buttons under $40"
- **Budget:** $40.00
- **Search ID:** `4e5dad445dcb44668985112a487aefd1`
- **Reply Text:** I could not find a confident match. Try describing it another way.
- **Recommendations Returned:** 0
- **Negative Test Invariant Check:** Claimed large buttons = `False` (Expected: False - PASS)

