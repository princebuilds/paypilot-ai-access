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

## Current Status
- **Current Phase:** HUMAN STEP B (Save real Channel3 key to .env & run live smoke test)
- **Gate Status:**
  - `pytest -m 'not live'`: PASS (38 passed, 1 deselected)
  - `python scripts/static_checks.py`: PASS (18 pass, 0 warn, 0 fail)
  - `ruff check .`: PASS (All checks passed)

## Acceptance Checks & Cross-Check Matrix Mapping

### Cross-Check Matrix (Protocol Section 3)
| Row | Interaction | Target Status | Evidence |
|---|---|---|---|
| 1 | Agent, grounding, database | NOT RUN | |
| 2 | Agent to quote | NOT RUN | |
| 3 | Quote, Channel3 refresh, currency | NOT RUN | |
| 4 | Quote, budget, confirm | NOT RUN | |
| 5 | Confirm to order | NOT RUN | |
| 6 | Order to PayPal payload | NOT RUN | |
| 7 | Capture, verification, receipt | NOT RUN | |
| 8 | Session isolation | NOT RUN (Target: Phase B1) | |
| 9 | Rate limit | NOT RUN (Target: Phase B1) | |
| 10 | Frontend and API contract | NOT RUN | |
| 11 | CSP, PayPal SDK, images | NOT RUN | |
| 12 | Voice and keyboard fallback | NOT RUN | |
| 13 | Startup, model pin, health | NOT RUN (Target: Phase B1) | |
| 14 | Failure honesty | NOT RUN | |
| 15 | Sandbox honesty | PASS (Static) | `docs/evidence/phaseB0_bootstrap.txt` |
| 16 | Secret leakage | NOT RUN (Target: Phase B1) | |
| 17 | Untrusted text | NOT RUN | |
| 18 | README reality | NOT RUN | |
| 19 | Hosted parity | NOT RUN | |
| 20 | Data persistence | NOT RUN | |
