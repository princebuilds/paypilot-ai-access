# MASTER BUILD PROMPT: PayPilot AI ACCESS (greenfield)

Paste everything below the line into Antigravity (Planning mode) in the workspace `C:\PAYPAL`. This replaces `ANTIGRAVITY_BUILD_PROMPT.md`. Before pasting, make sure `PROTOCOL.md`, `AGENTS.md` and `SPEC.md` are in the folder and that `scripts\static_checks.py` has been copied in (it is a fixed file I supply; you must not write your own).

---

You are my senior engineer. We are building PayPilot AI ACCESS **from scratch** for the PayPal AI Hackathon 2026. There is no earlier codebase; do not look for one. Build it in `C:\PAYPAL` as a professional, public, reproducible GitHub project (`princebuilds/paypilot-ai-access`, MIT licence, owner Prince Kumar, solo).

## 0. Rules of engagement

- Read these fully, in this order of precedence: `PROTOCOL.md`, `AGENTS.md`, `SPEC.md`, then this prompt. If they conflict, stop and ask me.
- Work every phase through the loop in `PROTOCOL.md`: plan, implement, verify, cross-check against the whole matrix, fix, re-verify, record. A gate is green only when `python -m pytest -q` and `python scripts/static_checks.py` both exit 0 and the relevant matrix rows have saved evidence.
- Nothing is "done" without real command output saved in `docs/evidence/`. Label results MOCK, LIVE or MANUAL. Say NOT RUN when you could not run it.
- Ask me instead of guessing. Keep `docs/PROGRESS.md` current and re-read it at the start of each phase.
- Never read, print or commit secrets. Never run `git push`, deploy, or make live calls without my instruction. Sandbox payments only.
- Python 3.13, Windows 11, PowerShell. If a package fails to install, report the exact error; do not swap or downgrade silently.
- If `scripts\static_checks.py` is missing, stop and tell me to copy it.

## 1. Professional repository blueprint

Create exactly the layout in `AGENTS.md` section 6. Notes:

- `app/` holds the backend; `static/` the frontend (vanilla HTML, CSS, JS, no build step); `tests/` is split into `unit/`, `integration/` and `live/`; `docs/` holds every written deliverable.
- Add `.gitattributes` with `* text=auto`. Add `SECURITY.md` (one short page: Sandbox only, never commit keys, how to report a problem).
- `pyproject.toml` holds config only (no build system):
  - `[tool.pytest.ini_options]`: `testpaths = ["tests"]`, `addopts = "-q -m 'not live'"`, a marker `live: calls real external services and needs keys`.
  - `[tool.ruff]` with a sensible default rule set.
- `requirements.txt` has runtime packages only, pinned with exact versions from `pip freeze` after install. `requirements-dev.txt` has `pytest`, `respx` and `ruff`, also pinned.
- `.gitignore` covers `.env`, `.venv/`, `__pycache__/`, `*.pyc`, `*.db`, `*.db-wal`, `*.db-shm`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`, `htmlcov/`, `.idea/`, `.vscode/`, `*.log`, and the local `_local/` folder. Commit `docs/evidence/`.
- Move the stray `PayPilot AI ACCESS Architecture and Change Plan.pdf` into `_local/` (ignored). It predates later verification and must not confuse judges.
- `.env.example` lists `CHANNEL3_API_KEY`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_ENV=sandbox`, `OFFLINE_TESTS=0`, `RATE_LIMIT_PER_HOUR=30`, `DAILY_SEARCH_CAP=1500`, with placeholder values only.
- `.github/workflows/ci.yml`: on push and pull request, `ubuntu-latest`, Python 3.13, install both requirements files, run `ruff check .`, `pytest -q`, `python scripts/static_checks.py`. CI uses no secrets and runs only MOCK tests.

## 2. Git and GitHub standards

- Branch: `main`. Small commits. Conventional Commits: `feat:`, `fix:`, `test:`, `docs:`, `chore:`, `ci:`, `refactor:`. One logical change per commit, each leaving the tests green.
- Commit after every verified step so history shows the real development timeline.
- Tags: `v0.1.0` after live Channel3 works, `v0.5.0` after a verified Sandbox capture, `v1.0.0` at submission.
- You do not push. After each phase gate, give me the exact PowerShell push commands and I will run them. After the first push, ask me to confirm GitHub Actions is green and to paste the result.
- Repository settings you must give me to apply on GitHub: description ("Accessible, voice-first AI shopping agent with grounded product recommendations and buyer-approved PayPal Sandbox checkout"), website (the Render URL, when it exists), topics (`fastapi`, `paypal`, `gemini`, `agentic-commerce`, `accessibility`, `voice`, `hackathon`), and a check that the MIT licence shows in the About panel.
- README requirements are in phase B8.

## 3. Test architecture

- **Layers:** `unit/` (pure logic), `integration/` (FastAPI `TestClient` plus `respx` mocks for Channel3 and PayPal, scripted fake for Gemini), `live/` (`@pytest.mark.live`, hits real services, skipped by default; run with `pytest -m live`).
- **MOCK integrity:** `tests/conftest.py` must make any real network call in a non-live test fail loudly (for example `respx` with `assert_all_mocked=True`). A mock test must never silently reach the internet.
- **Gemini is injectable.** `agent.py` takes the model-call function as a parameter so tests can script responses without network.
- **Fixtures:** record real, sanitised Channel3 and PayPal responses once during live steps and commit them under `tests/fixtures/`. Mock tests use these, not invented shapes. Until a real fixture exists, a test using a hand-made shape must be named `*_synthetic` and noted in `docs/TRACEABILITY.md`.
- **Matrix traceability:** every row of the cross-check matrix in `PROTOCOL.md` section 3 gets a file `tests/integration/test_matrix_NN_<topic>.py` (rows marked M or L in the matrix get the automated part plus a recorded manual or live step). Maintain `docs/TRACEABILITY.md`: requirement or invariant, test file, status (PASS, FAIL, NOT RUN), evidence file.
- **Invariant tests:** every invariant in `AGENTS.md` section 4 has a named test.
- **Live runner:** `scripts/live_smoke_test.py` runs the `live` tests, prints a summary, and writes `docs/LIVE_TEST_REPORT.md` with timestamps, HTTP statuses and PayPal debug IDs. It never prints keys.

## 4. Phases

Each phase ends with its gate, a `docs/PROGRESS.md` update, evidence in `docs/evidence/`, and a commit. Target times are IST.

### B0: Bootstrap (today, Nov 9, by about 15:00)
1. Confirm the workspace is `C:\PAYPAL`. Detect the Python launcher and create `.venv` (`py -3.13 -m venv .venv`). If PowerShell blocks activation, tell me to run `Set-ExecutionPolicy -Scope Process Bypass`.
2. `git init -b main`. Create all files and folders from section 1 (placeholders where needed, each with a one-line purpose). The README is a skeleton containing the required headings from B8 marked TODO; the final README is written in B8.
3. Install runtime and dev packages; pin both files.
4. Write `static/index.html` as a placeholder that already contains the Sandbox banner text so the static check can pass.
5. Run the gate. Fix anything red.
6. Commit 1: `chore: initialize project scaffold`. Commit 2: `docs: add agent instructions` (PROTOCOL, AGENTS, SPEC, MASTER_BUILD_PROMPT, scripts/static_checks.py).
7. Move `ANTIGRAVITY_BUILD_PROMPT.md` into `_local/` (it is superseded).

**HUMAN STEP F:** I create the empty GitHub repo and push using your commands. I confirm CI is green.

### B1: Platform core (today)
Build per `SPEC.md`: `config.py` (typed settings, fail fast naming the missing variable but never its value), `database.py` (DDL from section 5, WAL, idempotent init), `schemas.py`, `errors.py` (error body and handlers), `security.py` (`sid` cookie, per-IP hourly limit, daily search cap, friendly messages), routers with `health.py` working and the others returning a clear `NOT_IMPLEMENTED` error for now, and `main.py` serving `static/`. `/api/health` returns booleans only.
Tests: matrix rows 8, 9, 13, 16 (fake distinctive keys must never appear in responses, logs or `static/`), plus unit tests for config and the rate limiter.

**HUMAN STEP A:** I create `.env` by hand with the Channel3, Gemini and PayPal Sandbox values. Give me exact PowerShell steps and the dashboard names. Never ask me to paste a key into chat.

### B2: Real Channel3 (today, by about 19:00)
Implement `channel3.py` exactly as in `AGENTS.md` section 5 and `SPEC.md`: `search()` and `get_product()` via `httpx`, timeouts, up to two retries with backoff on 429 and 5xx, clear errors, a defensive offer parser, snapshots persisted, a 10-minute cache. Add `tests/live/test_live_channel3.py`.
Tests: parser unit tests, timeout, 429, malformed JSON, empty results, non-USD offers, cache behaviour.

**HUMAN STEP B:** I run `python scripts/live_smoke_test.py --channel3` and paste the output. Save the sanitised real response as `tests/fixtures/channel3_search_real.json` and the real detail response as `channel3_product_real.json`. Check the real shape against the parser and fix any mismatch. Then validate my three demo queries (`sturdy wooden walking stick under $40`, `large button corded telephone under $50`, `handheld magnifying glass with light under $25`) against real results and propose replacements for any that are branded, thin or non-USD. Write the outcome to `docs/DEMO_QUERIES.md`.
Tag `v0.1.0` when this gate is green.

### B3: Gemini agent and grounding (Nov 10, by noon)
1. With my key, list models, show me the candidates and pin a stable one in `.env.example` and `GEMINI_MODEL`. Add the startup check.
2. Implement `agent.py` (manual function-calling loop, one tool, 3 call limit, 20 second budget, structured output) and `grounding.py`, using the system instruction and schemas in `SPEC.md` section 7. Implement `POST /api/agent` with the response in `SPEC.md` section 4, the server-side summary check and template fallback.
3. Tests: unknown product ID dropped; fabricated evidence dropped; wrong price in a reason rejected; prompt-injection text in a product description changes nothing; vague request gives one clarifying question; matrix rows 1, 2 and 17.
4. Add `tests/live/test_live_gemini.py` (a real run that performs a real Channel3 search).

### B4: Quotes, orders and PayPal (Nov 10, by evening)
Implement `quotes.py`, `paypal.py` and the quote and order routers exactly per `SPEC.md` sections 4 to 6 and `AGENTS.md` section 4. Check the current PayPal Standard Checkout docs and record which JS SDK generation you chose in `docs/DECISIONS.md`.
Tests: matrix rows 3 to 8, 14 and 20, and every invariant in `AGENTS.md` section 4. Add recorded-shape PayPal fixtures only from real Sandbox calls; until then mark synthetic tests as such.

### B5: Frontend and accessibility (Nov 10 night to Nov 11 noon)
Build `static/` per `AGENTS.md` section 8 and the states and copy in `SPEC.md` section 8: request box, microphone, editable transcript, spoken replies, product cards with evidence and live-data badge, budget and quantity, quote panel, explicit confirm step, PayPal buttons, receipt page. All dynamic text via `textContent`. A Content-Security-Policy allowing only self, the PayPal SDK and the image hosts actually seen in real results.
Tests and checks: matrix rows 10, 11, 12, 15 and 17; axe or Lighthouse run and a keyboard-only walkthrough saved to `docs/ACCESSIBILITY_TEST.md` exactly as they came out. For the browser checks (CSP, console errors) use Playwright only as a dev dependency in `requirements-dev.txt`, with the reason in `docs/DECISIONS.md`; if it cannot run, mark the row MANUAL and give me the steps.

### B6: Live end-to-end (Nov 11, afternoon)
Finish `scripts/live_smoke_test.py` (Channel3, detail, Gemini, PayPal create, approval URL, capture, verify). Write `docs/LIVE_TEST_REPORT.md`.

**HUMAN STEP C:** I approve the Sandbox payment in the browser with the buyer account, then I run the whole flow in the app myself and report what I saw. Save the real PayPal create and capture response shapes (sanitised) as fixtures and rerun the mock tests against them. Tag `v0.5.0`.

### B7: CI and deploy (Nov 11, evening)
Confirm CI is green on GitHub. Finish `render.yaml` (Python web service, start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, health check `/api/health`, all secrets `sync: false`).

**HUMAN STEP D:** I create the Render service and set the environment variables. Then run matrix row 19 and a full Sandbox purchase on the hosted URL and record the results. Warn me about the free-tier wake delay and the ephemeral SQLite disk, and note both in the README.

### B8: Documentation and submission material (Nov 12, morning)
Only from tested behaviour. Produce:
1. `README.md`, in this order: title, one-line pitch, status badges (CI), the problem and audience (no invented statistics), a screenshot or short GIF of the real running app (taken from a real run, in `docs/img/`), features, architecture diagram (Mermaid), tech stack and why, quick start (Windows PowerShell first, under ten steps), configuration table, how to test (MOCK vs LIVE explained), Live vs Mock results table linking to `docs/`, a short API reference, project layout, the Sandbox buyer test account (I confirmed it is throwaway), Limitations (demo-merchant gap, price snapshots, browser-dependent voice, ephemeral SQLite, free-tier wake delay), Security, Development timeline (from the real git log), Tools and AI disclosure (Gemini, Channel3, PayPal Sandbox, and the AI coding assistant used), Licence.
2. `docs/ARCHITECTURE.md` (from the built system, not from plans), `docs/DEVPOST.md`, `docs/DEMO_SCRIPT.md` (under 3 minutes, using the validated demo queries, stating the demo-merchant limitation on camera, no music unless licensed), `docs/SUBMISSION_CHECKLIST.md`.
3. `docs/TRACEABILITY.md` completed, and the reviewer passes in `PROTOCOL.md` section 4, written to `docs/REVIEW_*.md`, with fixes made and the full loop re-run.
4. `docs/FINAL_VERIFICATION.md` and the final release audit in `PROTOCOL.md` section 5, from a fresh clone in a new virtual environment.

**HUMAN STEP E:** I record the video, upload it as public on YouTube, finish the Devpost form, and submit by the afternoon of Nov 12 IST. Tag `v1.0.0`.

## 5. Stop conditions

Stop and ask me if: a required input or key is missing; docs and files disagree; a failure survives three fix attempts; a change would alter a contract in `SPEC.md`; something would be skipped because of time. If time runs short, cut from the bottom of the list in `AGENTS.md` section 11 and tell me. Never cut live Channel3, grounded recommendations or verified PayPal capture.

## 6. Start now

1. Reply with a short plan for B0 and the list of anything you need from me.
2. Check whether `scripts\static_checks.py` exists in the workspace. If not, tell me to copy it and wait.
3. Then run B0 through its gate and report with real output.
