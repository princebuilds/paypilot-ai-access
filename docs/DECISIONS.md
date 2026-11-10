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
