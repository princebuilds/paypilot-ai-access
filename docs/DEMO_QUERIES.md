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

### Query 2: "jar opener for weak hands"
- **Customer Budget:** $25.00
- **Channel3 Filter:** `filters: { "price": { "max_price": 25.0 }, "availability": ["InStock"] }`
- **Results Count:** 3
- **Products:**
  1. **Jar Opener**
     - **Channel3 ID:** `IgBk9qZ`
     - **Price:** $9.89 USD
     - **Availability:** InStock
     - **Merchant Domain:** `kohls.com`
     - **Brand:** Farberware
     - **Evidence highlight:** Easy-grip manual jar opener designed for stubborn lids and weak grip.
  2. **Good Grips Twisting Jar Opener**
     - **Channel3 ID:** `qs8hetr`
     - **Price:** $16.99 USD
     - **Availability:** InStock
     - **Merchant Domain:** `containerstore.com`
     - **Brand:** OXO
     - **Evidence highlight:** Contoured non-slip grip, leverage base holds lids securely to reduce hand strain.
  3. **Glad Bottle Jar Opener**
     - **Channel3 ID:** `gM3y6Yt`
     - **Price:** $2.99 USD
     - **Availability:** InStock
     - **Merchant Domain:** `menards.com`
     - **Brand:** Glad
     - **Evidence highlight:** Multi-size lid opener for twist-off caps and jars.
- **Assessment:** **KEEP**. Replaced the initial telephone query. Highly authentic assistive device for users with arthritis or reduced hand strength, all items priced in USD, in-stock, and under the $25 budget.

---

### Replaced Queries History

1. **Replaced: "large button corded telephone"** (Budget: $50.00)
   - Top products: AT&T Landline ($49.99), AT&T Corded Answering System ($39.99), Panasonic Integrated Telephone ($45.00).
   - Reason for replacement: High trademark risk (AT&T, Panasonic) in hackathon video submission.

2. **Rejected: "large print weekly pill organizer"** (Budget: $20.00)
   - Returned paper appointment planners (Mead, Staples) rather than medication dispensers.

3. **Rejected: "7 day pill organizer"** (Budget: $15.00)
   - Returned pet accessories (Chewy, Petco) and cosmetic boxes (T.J. Maxx).

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
