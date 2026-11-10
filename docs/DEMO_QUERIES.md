# docs/DEMO_QUERIES.md: Validated Demo Queries & Real Results

Validated against the live Channel3 API on 2026-11-10.
All returned products are confirmed in-stock, priced in USD, within requested budgets, and available from real US merchant retailers.

---

### Query 1: "sturdy wooden walking stick"
- **Customer Budget:** $40.00
- **Channel3 Filter:** `filters: { "price": { "max_price": 40.0 }, "availability": ["InStock"] }`
- **Results Count:** 3
- **Products:**
  1. **Hickory Rustic Walking Stick**
     - **Channel3 ID:** `LlXW9jv`
     - **Price:** $26.01 USD
     - **Availability:** InStock
     - **Merchant Domain:** `jbtools.com`
     - **Brand:** Brazos (Craft / Specialty)
     - **Evidence highlight:** Solid hickory wood, handcrafted, rubber traction tip.
  2. **Natural Wood Walking Stick**
     - **Channel3 ID:** `7V1UUgC`
     - **Price:** $39.99 USD
     - **Availability:** InStock
     - **Merchant Domain:** `walmart.com`
     - **Brand:** RMS
     - **Evidence highlight:** Natural wood walking cane, rubber tip for balance.
  3. **Wooden Cane Walking Stick**
     - **Channel3 ID:** `k68aocH`
     - **Price:** $24.99 USD
     - **Availability:** InStock
     - **Merchant Domain:** `wayfair.com`
     - **Brand:** Charlton Home
     - **Evidence highlight:** Traditional curved handle, solid wood construction.
- **Assessment:** **KEEP**. Highly relevant, unbranded/craft products with strong verbatim evidence for grounding.

---

### Query 2: "large button corded telephone"
- **Customer Budget:** $50.00
- **Channel3 Filter:** `filters: { "price": { "max_price": 50.0 }, "availability": ["InStock"] }`
- **Results Count:** 3
- **Products:**
  1. **Landline Telephone**
     - **Channel3 ID:** `RnyntXV`
     - **Price:** $49.99 USD
     - **Availability:** InStock
     - **Merchant Domain:** `pcrichard.com`
     - **Brand:** AT&T
     - **Evidence highlight:** High-contrast buttons, audio boost, hearing aid compatible.
  2. **Corded Answering System with Large Tilt Display**
     - **Channel3 ID:** `1DPTnEb`
     - **Price:** $39.99 USD
     - **Availability:** InStock
     - **Merchant Domain:** `officedepot.com`
     - **Brand:** AT&T
     - **Evidence highlight:** Extra-large tilt display, oversized keypad numbers.
  3. **1-Line Caller ID Integrated Telephone System**
     - **Channel3 ID:** `NiaSwn6`
     - **Price:** $45.00 USD
     - **Availability:** InStock
     - **Merchant Domain:** `bestbuy.com`
     - **Brand:** Panasonic
     - **Evidence highlight:** 1-line corded base, visual ringer alert, caller ID.
- **Assessment:** **KEEP**. Ideal for accessibility demo (target audience: older adults/low vision). While AT&T and Panasonic are established consumer electronics brands, the products are generic accessibility appliances without dominant fashion trademarks.

---

### Query 3: "handheld magnifying glass with light"
- **Customer Budget:** $25.00
- **Channel3 Filter:** `filters: { "price": { "max_price": 25.0 }, "availability": ["InStock"] }`
- **Results Count:** 3
- **Products:**
  1. **5X Magnifying Glass with Light, Handheld 48 LED Light**
     - **Channel3 ID:** `5BY4XNZ`
     - **Price:** $22.99 USD
     - **Availability:** InStock
     - **Merchant Domain:** `wayfair.com`
     - **Brand:** Ebern Designs (Generic Home)
     - **Evidence highlight:** 48 LED ring light, 5X optical grade magnification.
  2. **Magnifying Glass with LED Light, Lightweight Handheld**
     - **Channel3 ID:** `dvD1BxE`
     - **Price:** $17.99 USD
     - **Availability:** InStock
     - **Merchant Domain:** `wayfair.com`
     - **Brand:** Stalwart (Generic Tools)
     - **Evidence highlight:** Dual LED illumination, lightweight ergonomic grip.
  3. **Magnifying Glass with Light, 10X 45X Handheld Glass**
     - **Channel3 ID:** `EK0KFII`
     - **Price:** $9.99 USD
     - **Availability:** InStock
     - **Merchant Domain:** `newegg.com`
     - **Brand:** Newegg.com (Retailer direct)
     - **Evidence highlight:** High-power dual lenses, 3 built-in LED lights.
- **Assessment:** **KEEP**. Perfect unbranded low-vision assistance tool under $25 budget.
