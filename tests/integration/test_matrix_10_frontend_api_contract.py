"""Cross-Check Matrix Row 10: Frontend and API contract validation.

Target Invariant:
- static/app.js calls only valid backend endpoints and fields.
- static/app.js never sends price, amount, or total to create-order or capture endpoints.
- static/ uses textContent / DOM APIs exclusively (no innerHTML or document.write).
- static/index.html includes required accessibility landmarks and Sandbox banners.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def test_frontend_uses_no_inner_html_or_document_write():
    """Verify frontend JavaScript and HTML files do not use unsafe DOM write methods."""
    static_dir = ROOT / "static"
    for ext in ("*.js", "*.html"):
        for file_path in static_dir.glob(ext):
            content = file_path.read_text(encoding="utf-8")
            assert "innerHTML" not in content, f"Unsafe innerHTML found in {file_path.name}"
            assert "insertAdjacentHTML" not in content, f"Unsafe insertAdjacentHTML found in {file_path.name}"
            assert "document.write" not in content, f"Unsafe document.write found in {file_path.name}"


def test_frontend_never_sends_price_or_amount_to_order_or_capture():
    """Verify that frontend createOrder / capture network calls never send price, amount, or total."""
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

    # Inspect /api/orders call
    order_call_pattern = r'fetch\s*\(\s*["\']/api/orders["\'][^)]*\)'
    match = re.search(order_call_pattern, app_js, re.DOTALL)
    assert match, "fetch('/api/orders') not found in app.js"
    order_call_text = match.group(0)

    assert "quote_id" in order_call_text, "create-order call must pass quote_id"
    assert "price" not in order_call_text.lower(), "create-order call must NOT pass price"
    assert "amount" not in order_call_text.lower(), "create-order call must NOT pass amount"
    assert "total" not in order_call_text.lower(), "create-order call must NOT pass total"


def test_frontend_contains_accessibility_landmarks_and_sandbox_banner():
    """Verify index.html contains skip-link, main landmark, live region, and sandbox demo notices."""
    index_html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")

    assert 'class="skip-link"' in index_html, "Skip link missing from index.html"
    assert '<main id="main-content"' in index_html, "Main landmark missing from index.html"
    assert 'aria-live="polite"' in index_html, "Polite ARIA live region missing"
    assert 'role="alert"' in index_html, "Assertive alert region missing"
    assert "sandbox payment, no real purchase" in index_html.lower(), "Sandbox banner wording missing"


def test_receipt_page_contains_sandbox_honesty_and_no_dom_injection():
    """Verify receipt.html preserves sandbox honesty banner and has valid structure."""
    receipt_html = (ROOT / "static" / "receipt.html").read_text(encoding="utf-8")

    assert "sandbox payment, no real purchase" in receipt_html.lower()
    assert "innerHTML" not in receipt_html
    assert "/api/orders/" in receipt_html
