# docs/PROGRESS.md: PayPilot AI ACCESS Progress Log

## Project Inputs (SPEC.md Section 2)
| Input | Value | Status |
|---|---|---|
| Operating system and shell | Windows 11, PowerShell | Confirmed |
| Python version installed | Python 3.13.15 | Confirmed |
| GitHub username and repo | princebuilds/paypilot-ai-access | Confirmed |
| Licence | MIT | Confirmed |
| Solo or team; Devpost rep | Solo - Prince Kumar | Confirmed |
| Render account ready | No (will set up in Phase B7) | Confirmed |
| Publish throwaway Sandbox buyer login in README | Yes (dedicated throwaway sandbox buyer account for Phase B8) | Confirmed |
| Three product requests for demo | 1. "sturdy wooden walking stick under $40"<br>2. "large button corded telephone under $50"<br>3. "handheld magnifying glass with light under $25" | Confirmed (to verify in Phase B2 with live Channel3) |

## Phase B0: Bootstrap (Done)
- Workspace confirmed: `C:\PAYPAL`.
- Virtual environment created with Python 3.13 (`.venv`).
- Initialized git repository on branch `main`.
- Clean repository structure created per blueprint (`app/`, `static/`, `tests/`, `docs/`, `scripts/`, `.github/`).
- Fixed `scripts/static_checks.py` placed and verified.
- Dependencies installed and pinned in `requirements.txt` and `requirements-dev.txt`. Transitive dependencies documented in `docs/DECISIONS.md`.
- `pyproject.toml` configured with pytest options and ruff rules.
- Superseded documents moved to `_local/`.
- Commit 1 made: `chore: initialize project scaffold` (originally 8d65a4c, rewritten to 29e26a0 for GitHub no-reply email).
- Commit 2 made: `docs: add agent instructions` (originally f355aaa, rewritten to c95fb46 for GitHub no-reply email).
- Evidence record commit: originally 696c537, rewritten to 04a6251. Note: `docs/evidence/phaseB0_bootstrap.txt` records original command run timestamps/hashes and is preserved without modification.
- Gate status: **GREEN** (pytest exits 0, static_checks exits 0 with 18 passes, ruff exits 0).
- Evidence saved: `docs/evidence/phaseB0_bootstrap.txt`.

## Phase B1: Platform core (Done)
- Built `app/config.py`: typed settings with fail-fast validation naming missing variables without printing secret values; `OFFLINE_TESTS` handling.
- Built `app/database.py`: SQLite3 with WAL mode and schema DDL creating `searches`, `product_snapshots`, `quotes`, `orders`, and `payment_events`.
- Built `app/schemas.py`: Pydantic models for error envelopes, health, agent, quotes, and orders endpoints.
- Built `app/errors.py`: `AppError` hierarchy, standardized JSON response handlers for application errors, validation errors, and safe 500s.
- Built `app/security.py`: `sid` cookie lifecycle (HttpOnly, SameSite=Lax, Secure over HTTPS), per-IP hourly rate limiter and global daily search cap.
- Built `app/routers/health.py`: `/api/health` returning operational status booleans and safe metadata only.
- Built stub routers (`app/routers/agent.py`, `app/routers/quotes.py`, `app/routers/orders.py`) returning `NOT_IMPLEMENTED`.
- Mounted `static/` at `/` in `app/main.py`.
- Fixed placeholder detection in `config.py` and `/api/health`: reject values starting with "your" or containing "_here", "placeholder", "actual".
- Unit tests added: `tests/unit/test_config.py`, `tests/unit/test_security.py`, `tests/unit/test_channel3_parser.py`.
- Integration tests added: `test_matrix_08_session_isolation.py`, `test_matrix_09_rate_limit.py`, `test_matrix_13_startup_model_health.py`, `test_matrix_16_secret_leakage.py`, `test_channel3_mock.py`.
- Gate status: **GREEN** (pytest: 38 passed, 1 deselected; static_checks: 18 pass, 0 fail; ruff: all passed).
- Evidence saved: `docs/evidence/phaseB1_platform_core.txt`.

## Phase B2: Real Channel3 Integration (Done)
- Live Channel3 search and detail API calls executed and verified via `scripts/live_smoke_test.py --channel3`.
- Raw responses sanitized and saved to `tests/fixtures/channel3_search_real.json` and `tests/fixtures/channel3_product_real.json`. Verified zero secret keys or auth headers present.
- Discovered and fixed wire schema discrepancy: Channel3 search requires nested price filter `{"price": {"max_price": float}}` rather than flat dot-notation. Recorded in `docs/DECISIONS.md`.
- Defensive offer parser tested against all real fixture products; handles nested `price.price` and `price.currency` structures.
- Verified grounding evidence fields: `title` and `description` are 100% present with rich factual details, and `materials` is present. `SPEC.md` grounding contract preserved.
- Executed and validated all 3 demo queries with real API calls and caching: results recorded in `docs/DEMO_QUERIES.md`. All 3 return in-stock, USD, under-budget products.
- Created `tests/integration/test_channel3_real_fixtures.py` verifying real fixture parsing.
- Gate status: **GREEN** (pytest: 40 passed, 1 deselected; static_checks: 18 pass, 0 fail; ruff: all passed). Evidence saved in `docs/evidence/phaseB2_channel3.txt`.
- Tag: `v0.1.0`.

## Phase B3: Gemini Agent & Grounding (Done)
- Probed Gemini models via `client.models.list()`. Older models (`gemini-2.5-*`) returned 404 retired for new users; selected and verified `gemini-3.5-flash` as active stable model with full function-calling support.
- Pinned `GEMINI_MODEL=gemini-3.5-flash` in `.env.example` and `.env`; added startup validation rejecting `-preview` and `*-latest` aliases.
- Evaluated unbranded alternatives for demo query 2 in `docs/DEMO_QUERIES.md`: replaced telephone query (AT&T, Panasonic trademark risk) with "jar opener for weak hands" ($25 budget).
- Built `app/grounding.py`:
  - Strict verbatim evidence matching across `title`, `description`, `key_features`, `materials`.
  - Drops recommendations if model claims an absent feature (tested with "large buttons" on walking sticks).
  - Drops recommendations with wrong price claims in reasons.
  - Drops unknown product IDs not in the current search's stored snapshots.
  - Safe reply text builder falling back to template sentence if summary mentions ungrounded prices.
- Built `app/agent.py`:
  - Manual function calling with single tool `search_products`.
  - Delimiter protection wrapping untrusted product catalog text.
  - Dependency-injectable `model_caller` for deterministic, zero-network unit/integration testing.
  - Clarifying question handling when user request lacks budget or product type.
- Activated `/api/agent` endpoint in `app/routers/agent.py`.
- Added unit and integration test suites:
  - `tests/unit/test_grounding.py` (8 unit tests)
  - `tests/integration/test_matrix_01_agent_grounding_db.py` (Matrix Row 1)
  - `tests/integration/test_matrix_02_agent_to_quote.py` (Matrix Row 2)
  - `tests/integration/test_matrix_17_untrusted_text.py` (Matrix Row 17)
- Live smoke test expanded in `scripts/live_smoke_test.py --gemini`: verified live tool call invocation against `gemini-3.5-flash` with recorded evidence in `docs/LIVE_TEST_REPORT.md`.
- Gate status: **GREEN** (pytest: 54 passed, 1 deselected; static_checks: 18 pass, 0 fail; ruff: all passed).
- Evidence saved: `docs/evidence/phaseB3_gemini_grounding.txt`.

## Phase B4: Quotes, Budget, PayPal Sandbox, Orders & Capture (Done)
- Built `app/quotes.py` (`QuotesService`):
  - Fetches product snapshot from session with strict session isolation.
  - Refreshes product price, currency, and availability using the free Channel3 detail endpoint.
  - Enforces USD and InStock checks; raises 422 `NOT_PURCHASABLE` if non-USD or out of stock.
  - Enforces price stability; raises 409 `PRICE_CHANGED` if upstream price differs from snapshot.
  - Enforces customer budget; raises 422 `BUDGET_EXCEEDED` if quantity * unit_price > budget.
  - Locks price with 10-minute expiry (`expires_at`), saving quotes in `QUOTED` state.
  - Quote confirmation endpoint requires exact total match; raises 422 `TOTAL_MISMATCH` if altered.
- Built `app/paypal.py` (`PayPalClient`):
  - Targeting `https://api-m.sandbox.paypal.com` with cached OAuth bearer tokens.
  - Uses `PayPal-Request-Id` for request idempotency on create and capture.
  - Plain purchase amount payload (avoids breakdown mismatch errors).
  - Four non-negotiable capture invariants verified: order `COMPLETED`, capture `COMPLETED`, exact amount and currency match stored quote, `custom_id` matches internal order ID.
  - Maps `PENDING` capture status to pending (not completed); `DECLINED` / `PARTIALLY_COMPLETED` mapped to failed.
  - Idempotent capture: re-checks already-captured orders without failing.
  - Logs `paypal_debug_id` in `payment_events` table for all PayPal interactions.
- Built routers:
  - `app/routers/quotes.py`: `POST /api/quotes`, `POST /api/quotes/{quote_id}/confirm`.
  - `app/routers/orders.py`: `POST /api/orders`, `POST /api/orders/{order_id}/capture`, `POST /api/orders/{order_id}/cancel`, `GET /api/orders/{order_id}`.
- Recorded PayPal JS SDK standard checkout architecture decision in `docs/DECISIONS.md`.
- Added matrix tests:
  - `tests/integration/test_matrix_02_agent_to_quote.py` (Row 2: PASS)
  - `tests/integration/test_matrix_03_quote_refresh_currency.py` (Row 3: MOCK PASS, LIVE NOT RUN pending Sandbox capture)
  - `tests/integration/test_matrix_04_quote_budget_confirm.py` (Row 4: MOCK PASS, LIVE NOT RUN pending Sandbox capture)
  - `tests/integration/test_matrix_05_confirm_to_order.py` (Row 5: MOCK PASS, LIVE NOT RUN pending Sandbox capture)
  - `tests/integration/test_matrix_06_order_paypal_payload.py` (Row 6: MOCK PASS, LIVE NOT RUN pending Sandbox capture)
  - `tests/integration/test_matrix_07_capture_verification_receipt.py` (Row 7: MOCK PASS, LIVE NOT RUN pending Sandbox capture)
  - `tests/integration/test_matrix_08_session_isolation.py` (Row 8: PASS)
  - `tests/integration/test_matrix_14_failure_honesty.py` (Row 14: PASS)
  - `tests/integration/test_matrix_16_secret_leakage.py` (Row 16: PASS)
  - `tests/integration/test_matrix_20_data_persistence.py` (Row 20: PASS)
- Gate status: **GREEN** (pytest: 73 passed, 1 deselected; static_checks: 18 pass, 0 fail; ruff: all passed).
- Evidence saved: `docs/evidence/phaseB4_quotes_orders.txt`.

## Phase B5: Frontend & Accessibility (Done)
- Built `static/index.html`:
  - Accessible skip link (`#main-content`), landmark layout (`<header>`, `<main>`, `<section>`, `<footer>`).
  - Persistent Sandbox Demo notice banner.
  - Centralized ARIA live regions: `#live-announcer` (`aria-live="polite"`) and `#live-alert` (`role="alert"`).
  - Conversational hero box with assistant status dialogue.
  - Voice input with Web Speech API and accessible text fallback transcript input.
  - Recommended products grid with Channel3 metadata, product images, merchant domain, verified reasons, and evidence tags.
  - Price-locked quote presentation with exact total and confirmation step.
  - PayPal Standard Checkout container rendered only after confirmation.
- Built `static/receipt.html`:
  - Persistent Sandbox disclaimer banner.
  - Safe dynamic receipt hydration via `GET /api/orders/{order_id}` using `textContent` exclusively.
  - Status badges for `CAPTURED_VERIFIED`, `PENDING`, `FAILED`, and `CANCELLED`.
  - Transaction breakdown table, merchant domain, timestamp, and retailer outbound link.
- Built `static/styles.css`:
  - WCAG 2.1 AA compliant color palette (slate on white: 15.5:1; primary blue on white: 10.5:1).
  - High-visibility focus indicators (`outline: 3px solid #005ea6; outline-offset: 3px;`).
  - Tap targets meeting or exceeding 44px by 44px minimum touch size.
  - Fluid typography scaling safely up to 200%.
  - `prefers-reduced-motion` override suppressing animations for sensitive users.
- Built `static/app.js`:
  - Zero unsafe DOM methods (strictly uses `textContent`, `createElement`, `setAttribute`).
  - Money safety: browser NEVER sends price or amount to `/api/orders` or `/api/orders/{id}/capture`.
  - Dynamic client ID injection: fetches PayPal Client ID from `GET /api/config` and loads the PayPal SDK dynamically (no hardcoding).
  - Web Speech API integration (`SpeechRecognition`) and SpeechSynthesis TTS with toggle.
  - Focus management: programmatically moves focus to the confirmation action upon receiving a quote.
- Added Matrix Test:
  - `tests/integration/test_matrix_10_frontend_api_contract.py` (Row 10: PASS)
- Gate status: **GREEN** (pytest: 77 passed, 1 deselected; static_checks: 18 pass, 0 fail; ruff: all passed).
- Evidence saved: `docs/evidence/phaseB5_frontend.txt`.

## Current Status
- **Current Phase:** Phase B5 Complete (Awaiting User Re-entry of PayPal Sandbox Credentials for Live Create-Order Verification)
- **Gate Status:**
  - `pytest -m 'not live'`: PASS (77 passed, 1 deselected in 11.58s)
  - `python scripts/static_checks.py`: PASS (18 pass, 0 warn, 0 fail)
  - `ruff check .`: PASS (All checks passed)

## Acceptance Checks & Cross-Check Matrix Mapping

### Cross-Check Matrix (Protocol Section 3)
| Row | Interaction | Target Status | Evidence |
|---|---|---|---|
| 1 | Agent, grounding, database | PASS | `docs/evidence/phaseB3_gemini_grounding.txt` |
| 2 | Agent to quote | PASS | `docs/evidence/phaseB4_quotes_orders.txt` |
| 3 | Quote, Channel3 refresh, currency | MOCK PASS, LIVE NOT RUN | `docs/evidence/phaseB4_quotes_orders.txt` |
| 4 | Quote, budget, confirm | MOCK PASS, LIVE NOT RUN | `docs/evidence/phaseB4_quotes_orders.txt` |
| 5 | Confirm to order | MOCK PASS, LIVE NOT RUN | `docs/evidence/phaseB4_quotes_orders.txt` |
| 6 | Order to PayPal payload | MOCK PASS, LIVE NOT RUN | `docs/evidence/phaseB4_quotes_orders.txt` |
| 7 | Capture, verification, receipt | MOCK PASS, LIVE NOT RUN | `docs/evidence/phaseB4_quotes_orders.txt` |
| 8 | Session isolation | PASS | `docs/evidence/phaseB4_quotes_orders.txt` |
| 9 | Rate limit | PASS | `docs/evidence/phaseB1_platform_core.txt` |
| 10 | Frontend and API contract | PASS | `docs/evidence/phaseB5_frontend.txt` |
| 11 | CSP, PayPal SDK, images | NOT RUN | |
| 12 | Voice and keyboard fallback | NOT RUN | |
| 13 | Startup, model pin, health | PASS | `docs/evidence/phaseB1_platform_core.txt` |
| 14 | Failure honesty | PASS | `docs/evidence/phaseB4_quotes_orders.txt` |
| 15 | Sandbox honesty | PASS (Static) | `docs/evidence/phaseB0_bootstrap.txt` |
| 16 | Secret leakage | PASS | `docs/evidence/phaseB4_quotes_orders.txt` |
| 17 | Untrusted text | PASS | `docs/evidence/phaseB3_gemini_grounding.txt` |
| 18 | README reality | NOT RUN | |
| 19 | Hosted parity | NOT RUN | |
| 20 | Data persistence | PASS | `docs/evidence/phaseB4_quotes_orders.txt` |
