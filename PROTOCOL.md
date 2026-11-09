# PROTOCOL.md: how you work (read first, before the build prompt)

"Without mistakes" is not something anyone can promise. The standard here is: no known failing check, and every claim backed by saved evidence. Anything you could not run is reported as NOT RUN, never as passed.

## 1. The loop (applies to every phase and every fix)
PLAN  ->  IMPLEMENT  ->  VERIFY  ->  CROSS-CHECK  ->  (FIX  ->  RE-VERIFY  ->  RE-CROSS-CHECK)*  ->  RECORD  ->  NEXT

- **PLAN.** Before writing code, list the acceptance checks for this phase (from the build prompt) and the rows of the cross-check matrix (section 3) that this change can affect. Write them to `docs/PROGRESS.md`.
- **IMPLEMENT.** Smallest change that satisfies the plan. Commit when it works.
- **VERIFY (the feature itself).** Run the phase's own checks: new tests, a real curl or browser action, the live script where a human step is not needed.
- **CROSS-CHECK (everything else).** Run the full gate:
  `python -m pytest -q`
  `python scripts/static_checks.py`
  every matrix row in section 3 touched by this change, and any row you are unsure about. A change can break a feature you did not touch. The cross-check exists to catch that.
- **FIX.** If anything fails: reproduce first (write a failing test), fix the root cause, never the symptom. Do not edit a test, a check or `static_checks.py` to make it pass. Do not add try/except that hides the failure.
- **RE-VERIFY and RE-CROSS-CHECK.** After every fix, re-run steps 3 and 4 in full, not just the failing item. Add a regression test for the bug.
- **Loop limits.** If the same failure survives three fix attempts, stop. Write the root-cause analysis, what you tried and what you suspect into `docs/PROGRESS.md`, and ask me. Do not work around it, stub it or fake it.
- **RECORD.** Save evidence to `docs/evidence/phaseN_<name>.txt`: each command, its exit code and the relevant real output lines. Update `docs/PROGRESS.md`: done, passing (with evidence file names), NOT RUN, next step.
- **NEXT.** Start the next phase only when the gate is green. Re-read `AGENTS.md`, `SPEC.md` and `docs/PROGRESS.md` at the start of each phase.

A gate is green only when: `pytest` exits 0, `static_checks.py` exits 0 (warnings explained in `PROGRESS.md`), and every relevant matrix row passes with saved evidence.

## 2. Evidence rules
- Evidence is real tool output. Never summarise from memory, never paste output you did not just produce.
- Label every result MOCK, LIVE or MANUAL. Mock passes never count as live verification.
- If a command fails to run (missing key, no network, needs a human), the result is NOT RUN with the reason, and the phase's live items stay open.
- If your output and the docs disagree, believe the real output, note the discrepancy in `docs/DECISIONS.md`, and ask me if it affects a contract in `SPEC.md`.

## 3. Cross-check matrix

For each row, the check must exist as a test or a recorded manual step. T = automated test, M = manual with evidence, L = live, needs keys.

| # | Interaction | What must hold | How |
|---|---|---|---|
| 1 | Agent, grounding, database | Every snapshot_id returned by /api/agent exists in product_snapshots for the same search and session; dropped recommendations are logged | T |
| 2 | Agent to quote | A snapshot_id from /api/agent works in /api/quotes; one from another session returns 404 | T |
| 3 | Quote, Channel3 refresh, currency | Non-USD or out-of-stock offer returns NOT_PURCHASABLE; a changed price returns PRICE_CHANGED with the new total | T, L |
| 4 | Quote, budget, confirm | Over-budget quote is blocked; confirm needs the exact total; an expired quote cannot be confirmed | T |
| 5 | Confirm to order | An unconfirmed or expired quote cannot create an order | T |
| 6 | Order to PayPal payload | The captured outgoing create-order request has amount.value equal to the quote total, currency_code USD, custom_id equal to the internal order ID, and a PayPal-Request-Id header | T |
| 7 | Capture, verification, receipt | Each PayPal outcome (COMPLETED, PENDING, DECLINED, PARTIALLY_COMPLETED, amount mismatch, currency mismatch, already captured) maps to the right state, and the receipt shows the stored amounts | T |
| 8 | Session isolation | Another session cannot read, confirm, create or capture someone else's quote or order | T |
| 9 | Rate limit | Limit applies per IP, is configurable, returns the friendly message, and does not block the live smoke test | T |
| 10 | Frontend and API contract | Every fetch in static/app.js calls an endpoint and field names that exist in SPEC.md section 4; no price or total is sent to order or capture endpoints | T (static plus TestClient) |
| 11 | CSP, PayPal SDK, images | With the Content-Security-Policy on, the page loads, PayPal buttons render, product images show, and the browser console has no CSP errors | M or Playwright |
| 12 | Voice and keyboard fallback | With speech unsupported or the microphone denied, the whole flow still works by keyboard and text | M |
| 13 | Startup, model pin, health | A missing key or an unlisted GEMINI_MODEL stops startup with a clear message; /api/health exposes booleans only | T |
| 14 | Failure honesty | With Channel3 mocked as down, the UI shows the error and zero products; no seeded data appears; with OFFLINE_TESTS=0 seeded data is unreachable | T |
| 15 | Sandbox honesty | The Sandbox banner is on every screen, and the receipt always states no real order was placed | T and M |
| 16 | Secret leakage | Start the app with distinctive fake keys (for example TESTKEY_CHANNEL3_123). They must not appear in any HTTP response, any log line, static/, or git. Test with a script that greps all of them | T |
| 17 | Untrusted text | A product title or description containing <script>, HTML, or "ignore previous instructions" renders as plain text and does not change agent behaviour | T |
| 18 | README reality | In a fresh clone and a fresh virtual environment, following only the README gets the app running and the mock tests passing | M |
| 19 | Hosted parity | The deployed app passes rows 10, 11, 13 and 15, and one full Sandbox purchase | M, L |
| 20 | Data persistence | A restart does not corrupt the database; expired quotes cannot be used after a restart | T |

## 4. Reviewer pass (before Phase 8 and again at the end)

Do this in a fresh context if your Antigravity version supports a second conversation or agent; otherwise reread the whole diff cold. Take each role in turn and write findings to `docs/REVIEW_<role>.md`:

- **Hostile hackathon judge.** Does the video flow work end to end? Which claim cannot be proven? What looks faked? What fails if a judge types something unexpected?
- **Payment and security reviewer.** Try to break each invariant in AGENTS.md section 4: tamper with a quote, replay a capture, use another session, send a huge quantity, send non-numeric budget, call endpoints out of order.
- **Accessibility reviewer.** Keyboard-only run, zoom to 200%, high contrast, screen-reader announcements, reduced motion.
- **Cold-start user.** Follow the README from nothing.

Fix every finding that is a real defect, then run the full loop again.

## 5. Final release audit
1. Fresh clone of the repository into a new folder; new virtual environment; install; run `pytest`; run `scripts/static_checks.py`.
2. Start the app; run all matrix rows again.
3. Ask me to run the live steps (Channel3, Gemini, PayPal Sandbox approval, hosted app) and paste the real outputs.
4. Write `docs/FINAL_VERIFICATION.md`: every Definition-of-Done item and matrix row with PASS, FAIL or NOT RUN, the evidence file, and for each NOT RUN exactly what I must run and how.
5. Say READY TO SUBMIT only if there are zero FAIL and every NOT RUN has been closed by me. Otherwise say NOT READY and list what blocks it.

## 6. Things you must never do
- Claim something passed without showing its output.
- Edit tests, checks or this protocol to get a green result.
- Hide an error, swallow an exception, or return fake data to keep the demo moving.
- Make live calls with credentials that are not in my .env, use a real PayPal account, push to git, or deploy without my instruction.
- Continue past a failing gate.
