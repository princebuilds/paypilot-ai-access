# docs/DECISIONS.md: PayPilot AI ACCESS Architectural & Technical Decisions

Record of decisions made during development, reasons, and any discrepancies noted.

## Initial Setup & Baseline
- **Date:** 2026-11-09
- **Protocol:** PROTOCOL.md adopted as the strict execution loop (Plan -> Implement -> Verify -> Cross-check -> Fix -> Re-verify -> Record -> Next).
- **Environment:** Windows 11, PowerShell, Python 3.13.15.
- **Architecture:** Greenfield build per MASTER_BUILD_PROMPT.md. Layout matching AGENTS.md section 6.
- **Transitive Runtime Dependencies:**
  The following transitive dependencies were installed by `fastapi` and `google-genai` and are recorded here per static_checks.py rule 12:
  - `cffi`: Required by `cryptography` / `google-auth`.
  - `cryptography`: Required by `google-auth` for secure token handling.
  - `httpcore2`: Required by `httpx2` / `google-genai` 3.0.0.
  - `httpx2`: Required by `google-genai` 3.0.0 for Gemini client networking.
  - `opentelemetry-api`: Sub-dependency of `fastapi` 0.162+.
  - `pycparser`: Sub-dependency of `cffi`.
  - `truststore`: Sub-dependency of `httpx2` / `google-genai` for platform trust store SSL certificates.

## Channel3 API Discoveries
- **Date:** 2026-11-10
- **Filter Structure Discrepancy:**
  The Channel3 documentation wrote `filters: price.max_price`. In actual wire execution, sending a flat key `"price.max_price"` in `filters` causes an HTTP 422 error (`extra_forbidden`). The required schema is nested dictionary:
  `{"filters": {"price": {"max_price": float_val}}}`.
- **Offer Price Structure:**
  Real API responses confirm offers represent price as an object:
  `{"price": {"price": float_val, "currency": "USD", "compare_at_price": ...}}`.
  The top-level offer dictionary has `"currency": null`. The defensive parser handles this nested shape seamlessly.

## PayPal Integration & SDK Choice
- **Date:** 2026-11-10
- **SDK Generation Choice:**
  PayPal documentation describes multiple generations: legacy checkout.js (v4), the current Standard Checkout JavaScript SDK (v5), and modern merchant toolkits.
  Current official PayPal Standard Checkout documentation:
  - Standard Checkout Integration: https://developer.paypal.com/docs/checkout/standard/integrate/
  - JavaScript SDK Reference: https://developer.paypal.com/sdk/js/reference/
  Standard Checkout officially recommends the **PayPal JavaScript SDK** loaded from `https://www.paypal.com/sdk/js` which provides `paypal.Buttons()` with server-backed actions. PayPilot AI ACCESS pins this generation:
  `https://www.paypal.com/sdk/js?client-id={PAYPAL_CLIENT_ID}&currency=USD&intent=capture&components=buttons`
- **Dynamic Client ID Injection (No Hard-coding):**
  Per AGENTS.md section 8 and SPEC.md section 8, the client ID must never be committed or hard-coded into static files (`static/index.html` or `static/app.js`). Instead, the frontend fetches the client ID at runtime from the server configuration (`GET /api/config`) and dynamically appends the SDK `<script>` tag.
- **Merchant Toolkits Excluded:**
  PayPal's Agent Toolkit and MCP server (`mcp.sandbox.paypal.com`) were evaluated and intentionally excluded because they are merchant-side tools for catalog and inventory management, whereas PayPilot is a buyer-side shopping assistant where the buyer explicitly approves payments.
- **Server-Side Money Safety Architecture:**
  - Create order accepts only `quote_id`, looks up locked price and session from database, and sends single purchase_unit without item breakdown to prevent breakdown mismatch errors.
  - Capture accepts only internal `order_id`, executes capture with idempotency key, and verifies all 4 invariants (order status COMPLETED, capture status COMPLETED, amount/currency match, custom_id match).
  - PENDING capture status is shown as pending, never completed.
  - Re-capturing an already-captured order fetches existing order details and returns verified receipt idempotently instead of failing.
- **Date:** 2026-11-10
- **Model Deprecation / Discovery:**
  Querying `client.models.list()` revealed that older models (`gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.5-flash-lite`) return HTTP 404 NOT_FOUND ("no longer available to new users").
  Candidate models supporting `generateContent` and function calling without `-preview` or `*-latest` aliases include:
  - `gemini-3.5-flash`
  - `gemini-3.5-flash-lite`
  - `gemini-3.1-flash-lite`
  - `gemini-3.6-flash`
  `gemini-3.5-flash` was verified operational with live function calling and pinned in `GEMINI_MODEL` and `.env.example`.
- **System Instruction Refinement:**
  Added the single sentence: `"When both product type and budget are present, call search_products."` to `SYSTEM_INSTRUCTION` in `app/agent.py`.
  Reason: `gemini-3.5-flash` strictly adhered to the missing budget rule by asking clarifying questions even when both were stated unless prompted that presence of both implies calling the search tool. This preserves the single clarifying question for vague requests while enabling deterministic tool calling when parameters are present.
- **Model Caller Dependency Injection:**
  `AgentService` accepts an injectable `model_caller` parameter. In non-live tests, scripted responses simulate function calling and structured outputs with zero network dependency. Real live tests execute against the pinned `gemini-3.5-flash` model via `scripts/live_smoke_test.py --gemini`.
