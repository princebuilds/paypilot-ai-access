# Devpost Submission: PayPilot AI ACCESS

## Project Title
**PayPilot AI ACCESS**

## Elevator Pitch
An accessible, voice-first, customer-controlled AI shopping assistant that grounds recommendations in real retailer inventory via Channel3 and executes verified checkout through PayPal Sandbox—where the AI recommends, but the customer always approves.

---

## Inspiration & Problem Statement
Digital e-commerce has made millions of products accessible at our fingertips, but modern retail websites have become overwhelming. For older adults, people with visual or physical impairments, and first-time digital shoppers, navigating nested menus, deciphering sponsored listings, comparing fine print across retailers, and enduring complex multi-step checkout funnels creates frustration, cognitive strain, and high cart abandonment.

Furthermore, autonomous AI agents are frequently marketed with "autonomous spending" capabilities, which introduces serious safety risks—such as hallucinations, unauthorized charges, or budget overruns.

We built **PayPilot AI ACCESS** to solve both challenges:
1. Make digital commerce truly accessible through natural voice navigation, screen-reader friendly design, and transparent retailer attribution.
2. Maintain an unbreakable money-safety architecture: the AI helps discover and evaluate products, but **the human customer retains 100% financial control**.

---

## What It Does
PayPilot AI ACCESS is a lightweight, accessible shopping companion:
- **Speaks and Listens:** Shoppers speak naturally using the Web Speech API or type their requests. Real-time auditory feedback announces results and state transitions.
- **Finds Real Products:** Queries live multi-merchant product catalogs via **Channel3**, retrieving verified in-stock items with real prices and retailer domains.
- **Strict Grounding:** An anti-fabrication engine cross-checks every recommendation against stored catalog snapshots. If a feature or price is not found verbatim in upstream product data, it is dropped.
- **Customer Budget Guard:** Customers define an optional budget. The server locks the selected item's price for 10 minutes and requires explicit customer approval of the exact total.
- **Verified PayPal Sandbox Checkout:** Integrates standard PayPal Orders v2. The AI never handles money. All order creations, approvals, and captures are executed and verified on the server against four strict invariants before issuing a verified receipt.
- **"What the Assistant Did" Activity Trail:** An expandable, accessible audit timeline generated server-side directly from SQLite records, showing query latency, catalog items retrieved, grounding pass rates, price locks, and verified capture events.

---

## How We Built It & How Each Tool is Used

### 1. PayPal Orders v2 (Sandbox)
- **Role:** Handles buyer-approved checkout and verified payment capture.
- **Implementation:** Standard Checkout via PayPal REST API v2 (`/v2/checkout/orders` and `/v2/checkout/orders/{id}/capture`) with `PayPal-Request-Id` for idempotency.
- **Money-Safety Invariants:**
  - The browser *never* transmits a price or amount to the backend during order creation or capture. It only transmits `quote_id`.
  - Capture is marked complete only if four criteria hold:
    1. Order status is `COMPLETED`.
    2. Capture status in `payments.captures[0]` is `COMPLETED`.
    3. Captured amount and currency match the stored price quote exactly.
    4. `custom_id` matches the internal order ID.
  - Server-side capture prevents client tampering. Every transaction logs PayPal `debug_id` in SQLite.

### 2. Channel3 API
- **Role:** Live e-commerce product search, pricing, stock availability, and retailer attribution.
- **Implementation:** Custom HTTPX client querying Channel3's `/v1/search` and free `/v1/products/{id}` detail endpoints.
- **Defensive Parsing:** Handles nested `price.price` and `price.currency` structures defensively. Real snapshots are persisted in SQLite and cached for 10 minutes to minimize API credit consumption.
- **Retailer Transparency:** Every product card explicitly states `"Sold by <retailer>"` and notes that checkout links navigate through Channel3 affiliate links.

### 3. Google Gemini API (`google-genai`)
- **Role:** Natural language intent understanding, query refinement, and tool execution.
- **Implementation:** Pinned stable model `gemini-3.5-flash-lite` utilizing manual function calling with a single bounded tool (`search_products`).
- **Prompt Injection Defense:** Product catalog data is wrapped in strict XML delimiters (`<catalog_item>`) with explicit instructions to ignore any instructions embedded within retailer copy.
- **Clarification Loop:** When a customer request is too ambiguous, Gemini asks a clarifying question rather than guessing or hallucinating recommendations.

### 4. Fast, Lightweight Stack
- **Backend:** Python 3.13, FastAPI, standard library `sqlite3` in WAL mode for persistent transactions without external database services.
- **Frontend:** Vanilla HTML5, CSS3, and JavaScript. Zero client-side frameworks or bundlers. Strict `textContent` DOM manipulation guarantees zero `innerHTML` injection vulnerabilities.
- **Accessibility:** Axe-core verified with 0 violations. Includes skip links, visible keyboard focus rings, high-contrast ratios (4.5:1+), ARIA live announcements, and 44px+ tap targets.

---

## Challenges We Overcame
1. **Model Retirement & Stability:** While testing older model names like `gemini-2.0-flash` and `gemini-2.5-*`, we discovered API retirements. We implemented a startup inspection check that validates active, stable models and pinned `gemini-3.5-flash-lite`.
2. **Channel3 Schema Variations:** Channel3 documentation exhibited slight variations between search and product detail schemas. We wrote a defensive offer parser tested against sanitized real fixtures to ensure zero runtime crashes.
3. **PayPal Capture Invariants:** In PayPal Orders v2, a captured order can show `COMPLETED` at the top level while an individual capture might still be pending or declined. We engineered strict server-side verification inspecting `purchase_units[0].payments.captures[0]` to guarantee financial integrity.
4. **Campus Network SSL Interception:** During local testing on a university Wi-Fi network, an enterprise firewall attempted deep packet inspection on Channel3 API requests. We identified the root cause via network tracing, documented the behavior, and established clean cloud deployment on Render to ensure judges experience zero interference.

---

## Accomplishments We're Proud Of
- **Zero Fabrication Guarantee:** Grounding is strictly enforced in code. If Gemini hallucinates a feature or price that is not in the stored Channel3 snapshot, our validator drops it immediately.
- **Automated Accessibility Testing:** The frontend achieved 0 accessibility violations in automated axe-core audits and supports full keyboard and screen-reader navigation.
- **Complete Test Matrix:** 97 automated tests covering unit logic, session isolation, rate limits, CSP headers, money safety, and live sanitized PayPal sandbox responses.
- **Transparent Audit Trail:** The "What the assistant did" panel gives judges and users total visibility into how decisions were made and payments were verified.

---

## What We Learned
- **Safety by Architecture:** You cannot rely on prompt engineering alone to protect customer funds. True safety requires architectural constraints where the AI lacks tools to touch financial credentials.
- **Defensive Integration:** Real-world commerce APIs change and evolve; building defensive parsers and validating live responses against strict schemas makes code resilient.

---

## What's Next for PayPilot AI ACCESS
1. **Agent-Ready Live Merchant Integration:** Expand from PayPal Sandbox to live production PayPal commerce with direct merchant inventory partners for end-to-end physical fulfillment.
2. **Multi-Region & Indian Commerce:** Integrate regional commerce protocols (such as ONDC, Blinkit, and Amazon India) with multi-currency handling for international shoppers.
3. **Multilingual Speech (Hindi `hi-IN`):** Add Hindi voice input and speech synthesis to make digital shopping accessible to non-English speaking regional communities.
