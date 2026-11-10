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


## Channel3 Live Integration Run (2026-11-10T03:27:42.760809+00:00)
- **Status:** PASS
- **Search Query:** sturdy wooden walking stick
- **Results Count:** 3
- **Top Product ID:** 7V1UUgC
- **Top Product Title:** Natural Wood Walking Stick
- **Price / Currency:** 39.99 USD
- **Availability:** InStock
- **Fixtures Saved:** `tests/fixtures/channel3_search_real.json`, `tests/fixtures/channel3_product_real.json`

## Real End-to-End Agent & Grounding Verification (2026-11-10T04:51:49.412927+00:00)
- **Model:** `gemini-3.5-flash-lite`
- **Channel3 Base:** `api.trychannel3.com/v1`
- **Mode:** Live end-to-end (`AgentService.run`) with caching

### Query: "I need a sturdy wooden walking stick under $40"
- **Budget:** $40.00
- **Search ID:** `b5d38edfb2ba41eea943a8111e7f67ee`
- **Reply Text:** Here are three wooden walking sticks that fit your budget.
- **Model Proposed Recommendations:** 3
- **Recommendations Dropped by Grounding:** 0
- **Recommendations Survived Grounding:** 3
- **Verified Recommendations & Reasons:**
  1. **Wooden Cane Walking Stick** ($24.99 USD, `wayfair.com`)
     - *Claim:* It is made of wood.
       *Evidence (title):* "Wooden Cane Walking Stick"
     - *Claim:* It has an anti-slip rubber stopper for stability.
       *Evidence (key_features):* "Anti-slip rubber stopper for stability"
  2. **Natural Wood Walking Stick** ($39.99 USD, `walmart.com`)
     - *Claim:* It is made of natural wood.
       *Evidence (title):* "Natural Wood Walking Stick"
     - *Claim:* It features a durable anti-skid rubber tip.
       *Evidence (key_features):* "Durable anti-skid rubber tip"
  3. **Wooden Cane Walking Stick** ($30.99 USD, `wayfair.com`)
     - *Claim:* It is a wooden cane.
       *Evidence (title):* "Wooden Cane Walking Stick"
     - *Claim:* It has an anti-slip rubber stopper at the bottom.
       *Evidence (key_features):* "Anti-slip rubber stopper at the bottom"

### Query: "I need a jar opener for weak hands under $25"
- **Budget:** $25.00
- **Search ID:** `acaab79198ad42a59233b241efba2ec8`
- **Reply Text:** Here are three jar openers that help with weak hands.
- **Model Proposed Recommendations:** 3
- **Recommendations Dropped by Grounding:** 0
- **Recommendations Survived Grounding:** 3
- **Verified Recommendations & Reasons:**
  1. **Jar Opener** ($9.89 USD, `kohls.com`)
     - *Claim:* It is made with a soft grip handle.
       *Evidence (description):* "It features a stainless steel construction with a soft grip handle and a spring-loaded lever mechanism that provides leveraged twisting power to smoothly remove lids."
     - *Claim:* It provides spring-loaded power to help open lids easily.
       *Evidence (key_features):* "Provides leveraged twisting and spring-loaded power to smoothly and easily open lids"
  2. **Twisting Jar Opener** ($19.99 USD, `oxo.com`)
     - *Claim:* It reduces strain on hands.
       *Evidence (description):* "This OXO Good Grips Twisting Jar Opener with Base Pad is designed for effortless jar opening, reducing strain on your hands."
     - *Claim:* It has an easy to grip handle.
       *Evidence (key_features):* "Large handle is easy to grip"
  3. **Good Grips Twisting Jar Opener** ($16.99 USD, `containerstore.com`)
     - *Claim:* It is gentle on arthritic hands.
       *Evidence (key_features):* "Large, easy-to-grip handle is gentle on even arthritic hands"
     - *Claim:* It has a non-slip silicone tray.
       *Evidence (key_features):* "Non-slip silicone tray keeps jars securely in place"

### Query: "I need a handheld magnifying glass with light under $25"
- **Budget:** $25.00
- **Search ID:** `3a1d3a46ab9e4cd086c8a3b6c21eb8c7`
- **Reply Text:** Here are three handheld magnifying glasses with lights that fit your budget.
- **Model Proposed Recommendations:** 3
- **Recommendations Dropped by Grounding:** 0
- **Recommendations Survived Grounding:** 3
- **Verified Recommendations & Reasons:**
  1. **5X Magnifying Glass with Light, Handheld 48 LED Lighted Magnifier for Reading** ($22.99 USD, `wayfair.com`)
     - *Claim:* It has 48 LED lights.
       *Evidence (title):* "5X Magnifying Glass with Light, Handheld 48 LED Lighted Magnifier for Reading"
     - *Claim:* It has a foldable and ergonomic handle.
       *Evidence (key_features):* "Foldable, adjustable ergonomic handle"
  2. **Magnifying Glass with LED Light, Lightweight Handheld Lighted 4x Magnifier** ($17.99 USD, `wayfair.com`)
     - *Claim:* It is a lightweight handheld magnifier.
       *Evidence (title):* "Magnifying Glass with LED Light, Lightweight Handheld Lighted 4x Magnifier"
     - *Claim:* It includes 6 energy-efficient LED lights.
       *Evidence (key_features):* "6 integrated energy-efficient LED lights"
  3. **Magnifying Glass with Light, 10X 45X Handheld Glass Reading Magnifier** ($9.99 USD, `newegg.com`)
     - *Claim:* It features dual magnification lenses.
       *Evidence (key_features):* "Dual magnification lenses: 3X and 45X"
     - *Claim:* It includes integrated LED lighting.
       *Evidence (key_features):* "Integrated LED lighting for the 45X lens"

### Query: "I need a walking stick with large buttons under $40"
- **Budget:** $40.00
- **Search ID:** `24b080e18bfb4d8292deda6cef195773`
- **Reply Text:** I could not find any walking sticks with large buttons in your budget. Here are some button products from the search results instead.
- **Model Proposed Recommendations:** 3
- **Recommendations Dropped by Grounding:** 0
- **Recommendations Survived Grounding:** 3
- **Verified Recommendations & Reasons:**
  1. **Broomstick Ride Rectangular Button** ($3.99 USD, `hottopic.com`)
     - *Claim:* It is a rectangular button.
       *Evidence (title):* "Broomstick Ride Rectangular Button"
  2. **Pride Flag Buttons** ($12.49 USD, `michaels.com`)
     - *Claim:* These are pride flag buttons.
       *Evidence (title):* "Pride Flag Buttons"
  3. **Beistle 2" Red Camouflage Military Pride Buttons, 6ct.** ($11.99 USD, `michaels.com`)
     - *Claim:* These are red camouflage military pride buttons.
       *Evidence (title):* "Beistle 2" Red Camouflage Military Pride Buttons, 6ct."


## Real End-to-End Agent & Grounding Verification (2026-11-10T06:40:46.039896+00:00)
- **Model:** `gemini-3.5-flash-lite`
- **Channel3 Base:** `api.trychannel3.com/v1`
- **Mode:** Live end-to-end (`AgentService.run`) with caching

### Query: "I need a sturdy wooden walking stick under $40"
- **Budget:** $40.00
- **Search ID:** `57e991796ac148a9ad044419296b38b7`
- **Reply Text:** I found these sturdy wooden walking sticks that match what you need.
- **Model Proposed Recommendations:** 3
- **Recommendations Dropped by Grounding:** 0
- **Recommendations Survived Grounding:** 3
- **Verified Recommendations & Reasons:**
  1. **Wooden Cane Walking Stick** ($24.99 USD, `wayfair.com`)
     - *Claim:* It is made of wood.
       *Evidence (title):* "Wooden Cane Walking Stick"
     - *Claim:* It has an anti-slip rubber stopper for stability.
       *Evidence (key_features):* "Anti-slip rubber stopper for stability"
  2. **Natural Wood Walking Stick** ($39.99 USD, `walmart.com`)
     - *Claim:* It is a natural wood walking stick.
       *Evidence (title):* "Natural Wood Walking Stick"
     - *Claim:* It is handcrafted for a rustic look and feel.
       *Evidence (key_features):* "Handcrafted rustic look and feel"
  3. **Wooden Cane Walking Stick** ($30.99 USD, `wayfair.com`)
     - *Claim:* It is a wooden cane walking stick.
       *Evidence (title):* "Wooden Cane Walking Stick"
     - *Claim:* It features a lightweight design.
       *Evidence (key_features):* "Lightweight design suitable for indoor and outdoor use"

### Query: "I need a jar opener for weak hands under $25"
- **Budget:** $25.00
- **Search ID:** `1bc1f6cd613c472285b91c61a868fca4`
- **Reply Text:** I found three jar openers that fit your needs and budget.
- **Model Proposed Recommendations:** 3
- **Recommendations Dropped by Grounding:** 0
- **Recommendations Survived Grounding:** 3
- **Verified Recommendations & Reasons:**
  1. **Jar Opener** ($9.89 USD, `kohls.com`)
     - *Claim:* It is designed to easily open stubborn jar lids.
       *Evidence (description):* "The Farberware Classic Soft Grips Jar Opener is designed to easily open stubborn jar lids and caps."
  2. **Good Grips Twisting Jar Opener** ($16.99 USD, `containerstore.com`)
     - *Claim:* It is ideal for individuals with arthritis or needing extra help.
       *Evidence (description):* "making it ideal for individuals with arthritis or anyone needing a little extra help in the kitchen."
     - *Claim:* The handle is gentle on arthritic hands.
       *Evidence (key_features):* "Large, easy-to-grip handle is gentle on even arthritic hands"
  3. **Twisting Jar Opener** ($19.99 USD, `oxo.com`)
     - *Claim:* It is designed for effortless opening and reduces hand strain.
       *Evidence (description):* "This OXO Good Grips Twisting Jar Opener with Base Pad is designed for effortless jar opening, reducing strain on your hands."

### Query: "I need a handheld magnifying glass with light under $25"
- **Budget:** $25.00
- **Search ID:** `f78c387fe7144b60963c84ccdbacc415`
- **Reply Text:** I found three handheld magnifying glasses with lights that fit your budget.
- **Model Proposed Recommendations:** 3
- **Recommendations Dropped by Grounding:** 0
- **Recommendations Survived Grounding:** 3
- **Verified Recommendations & Reasons:**
  1. **5X Magnifying Glass with Light, Handheld 48 LED Lighted Magnifier for Reading** ($22.99 USD, `wayfair.com`)
     - *Claim:* It is a handheld magnifying glass with a light.
       *Evidence (title):* "5X Magnifying Glass with Light, Handheld 48 LED Lighted Magnifier for Reading"
  2. **Magnifying Glass with LED Light, Lightweight Handheld Lighted 4x Magnifier** ($17.99 USD, `wayfair.com`)
     - *Claim:* It is a lightweight handheld magnifier with an LED light.
       *Evidence (title):* "Magnifying Glass with LED Light, Lightweight Handheld Lighted 4x Magnifier"
  3. **Magnifying Glass with Light, 10X 45X Handheld Glass Reading Magnifier** ($9.99 USD, `newegg.com`)
     - *Claim:* It is a handheld reading magnifier with a light.
       *Evidence (title):* "Magnifying Glass with Light, 10X 45X Handheld Glass Reading Magnifier"

### Query: "I need a walking stick with large buttons under $40"
- **Budget:** $40.00
- **Search ID:** `d4d12ed7dca5444f925a60410931ffb4`
- **Reply Text:** I could not find a walking stick with large buttons. Try describing it another way.
- **Model Proposed Recommendations:** 0
- **Recommendations Dropped by Grounding:** 0
- **Recommendations Survived Grounding:** 0
- **No recommendations survived grounding.** (Safe rejection verified)


## Real End-to-End Agent & Grounding Verification (2026-11-10T07:04:05.539102+00:00)
- **Model:** `gemini-3.5-flash-lite`
- **Channel3 Base:** `api.trychannel3.com/v1`
- **Mode:** Live end-to-end (`AgentService.run`) with caching

### Query: "I need a sturdy wooden walking stick under $40"
- **Budget:** $40.00
- **Search ID:** `46037bfb11d8440eb89e43038fae16ea`
- **Reply Text:** I found three sturdy wooden walking sticks that fit your budget.
- **Model Proposed Recommendations:** 3
- **Recommendations Dropped by Grounding:** 0
- **Recommendations Survived Grounding:** 3
- **Verified Recommendations & Reasons:**
  1. **Wooden Cane Walking Stick** ($24.99 USD, `wayfair.com`)
     - *Claim:* It provides stability with an anti-slip rubber stopper.
       *Evidence (key_features):* "Anti-slip rubber stopper for stability"
  2. **Natural Wood Walking Stick** ($39.99 USD, `walmart.com`)
     - *Claim:* It is crafted from natural wood.
       *Evidence (title):* "Natural Wood Walking Stick"
     - *Claim:* It features a durable anti-skid rubber tip.
       *Evidence (key_features):* "Durable anti-skid rubber tip"
  3. **Wooden Cane Walking Stick** ($30.99 USD, `wayfair.com`)
     - *Claim:* It is handcrafted from natural wood.
       *Evidence (key_features):* "Handcrafted from natural wood with a weatherproof clear coating"
     - *Claim:* It includes an anti-slip rubber stopper for stability.
       *Evidence (description):* "and a rubber stopper at the bottom for anti-slip stability."

### Query: "I need a jar opener for weak hands under $25"
- **Budget:** $25.00
- **Search ID:** `14befeeac69c4bf5b181a69a8e9ff124`
- **Reply Text:** Here are three jar openers that fit your budget and help with weak hands.
- **Model Proposed Recommendations:** 3
- **Recommendations Dropped by Grounding:** 0
- **Recommendations Survived Grounding:** 3
- **Verified Recommendations & Reasons:**
  1. **Jar Opener** ($9.89 USD, `kohls.com`)
     - *Claim:* It is designed to easily open stubborn jar lids.
       *Evidence (description):* "The Farberware Classic Soft Grips Jar Opener is designed to easily open stubborn jar lids and caps."
  2. **Twisting Jar Opener** ($19.99 USD, `oxo.com`)
     - *Claim:* It reduces strain on your hands and is ideal for weak or arthritic hands.
       *Evidence (description):* "This OXO Good Grips Twisting Jar Opener with Base Pad is designed for effortless jar opening, reducing strain on your hands. Its large, ergonomic T-shaped handle is easy to grip, making it ideal for individuals with arthritic hands."
  3. **Good Grips Twisting Jar Opener** ($16.99 USD, `containerstore.com`)
     - *Claim:* It features an ergonomic handle that reduces muscle strain.
       *Evidence (description):* "It features a non-slip base pad and sharp gripping jaws to securely hold jars, while the ergonomic handle is comfortable to grip and reduces muscle strain, making it ideal for individuals with arthritis or anyone needing a little extra help in the kitchen."

### Query: "I need a handheld magnifying glass with light under $25"
- **Budget:** $25.00
- **Search ID:** `515c065f78894c0d8dc461e6fc4245bc`
- **Reply Text:** I found three handheld magnifying glasses with lights within your budget.
- **Model Proposed Recommendations:** 3
- **Recommendations Dropped by Grounding:** 0
- **Recommendations Survived Grounding:** 3
- **Verified Recommendations & Reasons:**
  1. **Magnifying Glass with LED Light** ($8.98 USD, `jbtools.com`)
     - *Claim:* It is a handheld magnifier with an LED light.
       *Evidence (description):* "This is a handheld magnifying glass from Titan Tools featuring 4.4x magnification, ideal for detailed inspections, reading small text, or intricate hobby work. It includes a built-in LED light to ensure clear visibility even in dimly lit environments."
  2. **Magnifying Glass with LED Light, Lightweight Handheld Lighted 4x Magnifier** ($17.99 USD, `wayfair.com`)
     - *Claim:* It is a lightweight handheld tool with integrated LED lights.
       *Evidence (description):* "The Stalwart LED Lighted Magnifying Glass is a lightweight handheld tool designed to provide clear, magnified views of small print and detailed projects."
  3. **Magnifying Glass** ($15.99 USD, `shop.advanceautoparts.com`)
     - *Claim:* It features an LED light for enhanced visibility.
       *Evidence (description):* "The TITAN 4.4x Magnifying Glass with LED Light offers enhanced visibility for detailed work with its 4.4x magnification and non-distorting optical grade glass lens."

### Query: "I need a walking stick with large buttons under $40"
- **Budget:** $40.00
- **Search ID:** `906ebf2518624a6791c4a4a877ef930d`
- **Reply Text:** I could not find a walking stick with large buttons. Try describing it another way.
- **Model Proposed Recommendations:** 0
- **Recommendations Dropped by Grounding:** 0
- **Recommendations Survived Grounding:** 0
- **No recommendations survived grounding.** (Safe rejection verified)

