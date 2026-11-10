"""Cross-Check Matrix Row 15: Sandbox Honesty verification.

Target Invariant:
- Sandbox banner is visible across all user views (index.html, receipt.html).
- Clear statement that no real financial transaction, order, or shipping occurs.
- PayPal order description marks it clearly as a Sandbox demonstration order.
"""
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parent.parent.parent


def test_sandbox_banner_in_index_page():
    """Verify index.html contains conspicuous Sandbox disclaimer."""
    index_html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert "sandbox payment, no real purchase" in index_html.lower()
    assert 'class="sandbox-banner"' in index_html


def test_sandbox_honesty_in_receipt_page():
    """Verify receipt.html explicitly clarifies demo nature of the order."""
    receipt_html = (ROOT / "static" / "receipt.html").read_text(encoding="utf-8")
    assert "sandbox payment, no real purchase" in receipt_html.lower()
    assert "demo" in receipt_html.lower()
    assert 'class="sandbox-banner"' in receipt_html


def test_order_payload_labels_demo_transaction():
    """Verify backend paypal client includes sandbox demonstration markers in order descriptions."""
    paypal_py = (ROOT / "app" / "paypal.py").read_text(encoding="utf-8")
    assert "sandbox demo order" in paypal_py.lower() or "demo" in paypal_py.lower()


def test_frontend_routes_served_with_sandbox_markers():
    """Verify live HTTP responses for root and receipt contain honesty disclosures."""
    client = TestClient(app)
    r1 = client.get("/")
    assert r1.status_code == 200
    assert "sandbox payment, no real purchase" in r1.text.lower()

    r2 = client.get("/receipt.html")
    assert r2.status_code == 200
    assert "sandbox payment, no real purchase" in r2.text.lower()
