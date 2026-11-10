"""Cross-Check Matrix Row 11: Content Security Policy, PayPal SDK, and Image Safety.

Target Invariant:
- Application responds with strict Content-Security-Policy headers.
- CSP allows PayPal Standard Checkout SDK scripts, frames, and connect endpoints.
- CSP allows product images from https sources and inline data.
- Product recommendation markup in app.js provides valid alt text for images.
"""
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parent.parent.parent


def test_csp_header_present_and_configured():
    """Verify CSP header on static and API responses."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    csp = response.headers.get("Content-Security-Policy")
    assert csp is not None, "Content-Security-Policy header is missing"

    # Directives checks
    assert "default-src 'self'" in csp
    assert "https://www.paypal.com" in csp
    assert "img-src 'self' data: https:" in csp
    assert "frame-src https://*.paypal.com" in csp
    assert "object-src 'none'" in csp
    assert "base-uri 'self'" in csp

    # Check additional security headers
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_frontend_renders_images_with_alt_attributes():
    """Verify that product cards in static/app.js configure alt text for all images."""
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "img.alt =" in app_js, "Product images must have explicit alt attribute configured"
    assert "img.src =" in app_js, "Product images must configure src"


def test_config_endpoint_returns_paypal_client_id_for_sdk_loading():
    """Verify /api/config returns client ID and expected currency for SDK injection."""
    client = TestClient(app)
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "paypal_client_id" in data
    assert data["currency"] == "USD"
    assert data["sandbox"] is True
