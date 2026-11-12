# PayPilot AI ACCESS: Hackathon Submission Checklist

Use this checklist to ensure 100% compliance with all official PayPal AI Hackathon 2026 rules before submitting on Devpost.

---

## 1. Deadlines & Timing
- [ ] **Submission Deadline:** November 12, 2026 at 12:00 PM Pacific (November 13, 2026 at 1:30 AM IST).
- [ ] **Target Completion:** Complete Devpost submission before 10:00 PM IST on November 12 to provide buffer.
- [ ] **Hosted Demo Availability:** Hosted URL must stay live and functional free of charge until **December 15, 2026**.

---

## 2. Devpost Form Fields

### Basic Information
- [ ] **Project Name:** `PayPilot AI ACCESS`
- [ ] **Tagline / Elevator Pitch:**
  > An accessible, voice-first, customer-controlled AI shopping assistant that grounds recommendations in real retailer inventory via Channel3 and executes verified checkout through PayPal Sandbox—where the AI recommends, but the customer always approves.
- [ ] **Project Story:** Copy markdown content from [`docs/DEVPOST.md`](DEVPOST.md).

### Links & URLs
- [ ] **Public GitHub Repository URL:**
  `https://github.com/princebuilds/paypilot-ai-access`
- [ ] **Open Source License:**
  Confirm MIT License file is visible in GitHub repo root and About section.
- [ ] **Hosted Application URL:**
  Provide live Render app URL (e.g. `https://paypilot-ai-access.onrender.com`).
- [ ] **Demo Video URL (YouTube):**
  - [ ] Public or unlisted YouTube link.
  - [ ] Duration is strictly under 3 minutes (script targets 2:45).
  - [ ] Shows the application running live in the browser.
  - [ ] No copyrighted music or unendorsed third-party trademark claims.

### Judge Testing Information
- [ ] **Sandbox Buyer Test Account Credentials:**
  Provide the dedicated US sandbox personal test account:
  - **Email:** `sb-...@personal.example.com`
  - **Password:** `...`
- [ ] **Sample Queries for Judges:**
  1. `"sturdy wooden walking stick under $40"`
  2. `"jar opener for weak hands under $25"`
  3. `"handheld magnifying glass with light under $25"`

---

## 3. Disclosures & Mandatory Declarations
- [ ] **AI Coding Assistant Disclosure:**
  Disclose Google Antigravity IDE agent used as autonomous pair programmer, and Claude (Anthropic) used for initial architecture and protocol review.
- [ ] **Models & APIs Used:**
  - Google Gemini API (`gemini-3.5-flash-lite` via `google-genai`)
  - Channel3 E-commerce Search & Product API
  - PayPal Orders v2 Sandbox Checkout
- [ ] **Channel3 Prize Eligibility:**
  Ensure real API calls are demonstrated and documented in `docs/LIVE_TEST_REPORT.md` (mentioning Channel3 alone does not qualify).
- [ ] **Freshness & Timeline:**
  Confirm repository was built incrementally from scratch during the hackathon period (after Oct 1, 2026). Git commit history reflects all phases.

---

## 4. Code & Security Verification Gate
Before the final submission, execute the complete verification suite:
- [ ] **Static Checks:** Run `python scripts/static_checks.py` &rarr; Must output `18 checks: 18 pass, 0 warn, 0 fail`.
- [ ] **Automated Tests:** Run `pytest -m 'not live' -q` &rarr; All 97 tests must pass.
- [ ] **Linter:** Run `ruff check .` &rarr; 0 errors.
- [ ] **Secret Scan:** Confirm no API keys or personal passwords exist in tracked files or commit history:
  `git log -p | grep -E "AIza|ch3_live|E[A-Za-z0-9_\-]{70,}"` (Must return empty).
- [ ] **GitHub Actions CI:** Confirm green checkmark badge on latest commit on branch `main`.

---

## 5. Post-Submission
- [ ] Retain local `.env` and backups safely.
- [ ] Monitor Render dashboard weekly to ensure hosting credit balance remains active through December 15, 2026.
