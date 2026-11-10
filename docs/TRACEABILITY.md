# docs/TRACEABILITY.md: Cross-Check Matrix Traceability

Traceability matrix linking PROTOCOL.md cross-check matrix rows to test suites and evidence files.

| Row | Interaction | Target Invariant | Test File | Status | Evidence Reference |
|---|---|---|---|---|---|
| 1 | Agent, grounding, database | Every snapshot_id returned by /api/agent exists in product_snapshots; dropped recommendations logged | tests/integration/test_matrix_01_agent_grounding_db.py | PASS | docs/evidence/phaseB3_gemini_grounding.txt |
| 2 | Agent to quote | snapshot_id works in /api/quotes; another session returns 404 | tests/integration/test_matrix_02_agent_to_quote.py | PASS | docs/evidence/phaseB3_gemini_grounding.txt |
| 3 | Quote, Channel3 refresh, currency | Non-USD/OOS returns NOT_PURCHASABLE; changed price returns PRICE_CHANGED | tests/integration/test_matrix_03_quote_refresh_currency.py | NOT RUN | |
| 4 | Quote, budget, confirm | Over-budget blocked; confirm requires exact total; expired quote cannot be confirmed | tests/integration/test_matrix_04_quote_budget_confirm.py | NOT RUN | |
| 5 | Confirm to order | Unconfirmed or expired quote cannot create order | tests/integration/test_matrix_05_confirm_to_order.py | NOT RUN | |
| 6 | Order to PayPal payload | create-order has exact quote total, USD, custom_id = internal order ID, PayPal-Request-Id | tests/integration/test_matrix_06_order_paypal_payload.py | NOT RUN | |
| 7 | Capture, verification, receipt | Status mapping (COMPLETED, PENDING, DECLINED, mismatch); receipt shows stored amounts | tests/integration/test_matrix_07_capture_verification_receipt.py | NOT RUN | |
| 8 | Session isolation | Session cannot access, confirm, create, or capture another session's resources | tests/integration/test_matrix_08_session_isolation.py | PASS | docs/evidence/phaseB1_platform_core.txt |
| 9 | Rate limit | Limit per IP, configurable, friendly message, doesn't block smoke test | tests/integration/test_matrix_09_rate_limit.py | PASS | docs/evidence/phaseB1_platform_core.txt |
| 10 | Frontend & API contract | static/app.js calls valid endpoints/fields; no price/amount sent to order/capture | tests/integration/test_matrix_10_frontend_api_contract.py | NOT RUN | |
| 11 | CSP, PayPal SDK, images | Page loads with CSP, PayPal buttons render, images show, no CSP console errors | tests/integration/test_matrix_11_csp_sdk_images.py | NOT RUN | |
| 12 | Voice & keyboard fallback | Full flow functions with keyboard and text when speech/mic denied | tests/integration/test_matrix_12_voice_keyboard_fallback.py | NOT RUN | |
| 13 | Startup, model pin, health | Missing key or unlisted model stops startup; /api/health returns booleans only | tests/integration/test_matrix_13_startup_model_health.py | PASS | docs/evidence/phaseB1_platform_core.txt |
| 14 | Failure honesty | Upstream failure shows error and zero products; no seeded data leak | tests/integration/test_matrix_14_failure_honesty.py | NOT RUN | |
| 15 | Sandbox honesty | Sandbox banner present across views; receipt clarifies no real order placed | tests/integration/test_matrix_15_sandbox_honesty.py | PASS (Static) | docs/evidence/phaseB0_bootstrap.txt |
| 16 | Secret leakage | Distinctive fake keys never leak in HTTP responses, logs, static/, or git | tests/integration/test_matrix_16_secret_leakage.py | PASS | docs/evidence/phaseB1_platform_core.txt |
| 17 | Untrusted text | HTML/script/prompt injection in product fields rendered safely as plain text | tests/integration/test_matrix_17_untrusted_text.py | PASS | docs/evidence/phaseB3_gemini_grounding.txt |
| 18 | README reality | Following README from fresh clone gets app running and tests passing | tests/integration/test_matrix_18_readme_reality.py | NOT RUN | |
| 19 | Hosted parity | Deployed app passes rows 10, 11, 13, 15 and full Sandbox checkout | tests/integration/test_matrix_19_hosted_parity.py | NOT RUN | |
| 20 | Data persistence | Restart preserves database integrity; expired quotes unusable after restart | tests/integration/test_matrix_20_data_persistence.py | NOT RUN | |
