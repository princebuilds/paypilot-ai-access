"""PayPal Sandbox client, OAuth token caching, order creation, capture, and verification.

Governed by AGENTS.md Section 4-5 and SPEC.md Section 4-6:
- Strictly connects to Sandbox (https://api-m.sandbox.paypal.com).
- Caches OAuth token until shortly before expiry.
- PayPal-Request-Id headers for idempotent creation and capture.
- Plain amount in purchase_units (no item breakdown mismatch).
- Full 4-part capture verification (order COMPLETED, capture COMPLETED, amount/currency match, custom_id match).
- Handles PENDING status and duplicate captures idempotently.
- Logs paypal_debug_id in payment_events for auditability.
"""
import datetime
import logging
import time
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

import httpx

from app.config import Settings
from app.database import get_db
from app.errors import UpstreamServiceError

logger = logging.getLogger("paypilot.paypal")

PAYPAL_SANDBOX_BASE = "https://api-m.sandbox.paypal.com"


class PayPalClient:
    """HTTP client for PayPal Sandbox Orders v2 API."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self._cached_token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self.timeout = 20.0

    def _get_access_token(self) -> str:
        """Fetch or return cached OAuth2 client-credentials token."""
        now = time.time()
        if self._cached_token and now < (self._token_expires_at - 60):
            return self._cached_token

        if not self.client_id or not self.client_secret:
            raise UpstreamServiceError("PayPal credentials not configured")

        url = f"{PAYPAL_SANDBOX_BASE}/v1/oauth2/token"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    url,
                    auth=(self.client_id, self.client_secret),
                    data={"grant_type": "client_credentials"},
                    headers={"Accept": "application/json", "Accept-Language": "en_US"},
                )
                if resp.status_code != 200:
                    debug_id = resp.headers.get("Paypal-Debug-Id", "")
                    logger.error("PayPal token failure: HTTP %s, debug_id=%s", resp.status_code, debug_id)
                    raise UpstreamServiceError(f"PayPal authentication failed (HTTP {resp.status_code})")

                data = resp.json()
                self._cached_token = data["access_token"]
                expires_in = int(data.get("expires_in", 3600))
                self._token_expires_at = now + expires_in
                return self._cached_token
        except (httpx.TimeoutException, httpx.NetworkError) as err:
            raise UpstreamServiceError(f"PayPal connection error: {err}") from err

    def _log_event(
        self,
        order_id: str,
        step: str,
        http_status: Optional[int],
        paypal_debug_id: Optional[str],
        summary: str,
    ) -> None:
        """Log PayPal interaction event with debug_id to payment_events table."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            with get_db(self.settings.DATABASE_PATH) as conn:
                conn.execute(
                    """
                    INSERT INTO payment_events (order_id, step, http_status, paypal_debug_id, summary, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (order_id, step, http_status, paypal_debug_id, summary[:200], now_iso),
                )
        except Exception as e:
            logger.warning("Failed to log payment event: %s", e)

    def create_order(
        self,
        order_id: str,
        total: str,
        currency: str = "USD",
    ) -> Tuple[str, Optional[str]]:
        """Create a PayPal Sandbox order with custom_id and idempotency header."""
        token = self._get_access_token()
        url = f"{PAYPAL_SANDBOX_BASE}/v2/checkout/orders"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": order_id,
        }
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "custom_id": order_id,
                    "description": "PayPilot AI ACCESS - Sandbox Demo Order",
                    "amount": {
                        "currency_code": currency,
                        "value": total,
                    },
                }
            ],
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=headers, json=payload)
                debug_id = resp.headers.get("Paypal-Debug-Id")
                self._log_event(
                    order_id=order_id,
                    step="CREATE_ORDER",
                    http_status=resp.status_code,
                    paypal_debug_id=debug_id,
                    summary=f"Create order total=${total} {currency}",
                )

                if resp.status_code not in (200, 201):
                    raise UpstreamServiceError(
                        f"PayPal order creation failed (HTTP {resp.status_code}): {resp.text[:200]}"
                    )

                data = resp.json()
                paypal_order_id = data["id"]
                return paypal_order_id, debug_id
        except (httpx.TimeoutException, httpx.NetworkError) as err:
            self._log_event(order_id, "CREATE_ORDER_NET_ERR", None, None, str(err))
            raise UpstreamServiceError(f"PayPal network error: {err}") from err

    def get_order(self, paypal_order_id: str) -> Tuple[Dict[str, Any], Optional[str]]:
        """Retrieve order details from PayPal."""
        token = self._get_access_token()
        url = f"{PAYPAL_SANDBOX_BASE}/v2/checkout/orders/{paypal_order_id}"
        headers = {"Authorization": f"Bearer {token}"}

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(url, headers=headers)
            debug_id = resp.headers.get("Paypal-Debug-Id")
            if resp.status_code != 200:
                raise UpstreamServiceError(f"Failed to fetch PayPal order: HTTP {resp.status_code}")
            return resp.json(), debug_id

    def capture_order(
        self,
        internal_order_id: str,
        paypal_order_id: str,
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Capture payment for an approved PayPal order with idempotency header."""
        token = self._get_access_token()
        url = f"{PAYPAL_SANDBOX_BASE}/v2/checkout/orders/{paypal_order_id}/capture"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": f"capture_{internal_order_id}",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=headers, json={})
                debug_id = resp.headers.get("Paypal-Debug-Id")
                self._log_event(
                    order_id=internal_order_id,
                    step="CAPTURE_ORDER",
                    http_status=resp.status_code,
                    paypal_debug_id=debug_id,
                    summary=f"Capture order {paypal_order_id}",
                )

                if resp.status_code in (200, 201):
                    return resp.json(), debug_id

                # If order was already captured, fetch and verify it
                if resp.status_code == 422:
                    error_data = resp.json()
                    issues = error_data.get("details", [])
                    if any(i.get("issue") == "ORDER_ALREADY_CAPTURED" for i in issues):
                        logger.info("Order %s already captured; fetching existing order for verification", paypal_order_id)
                        return self.get_order(paypal_order_id)

                raise UpstreamServiceError(
                    f"PayPal capture failed (HTTP {resp.status_code}): {resp.text[:200]}"
                )
        except (httpx.TimeoutException, httpx.NetworkError) as err:
            self._log_event(internal_order_id, "CAPTURE_NET_ERR", None, None, str(err))
            raise UpstreamServiceError(f"PayPal capture connection error: {err}") from err

    def verify_capture(
        self,
        internal_order_id: str,
        expected_total: str,
        expected_currency: str,
        paypal_payload: Dict[str, Any],
    ) -> Tuple[str, Optional[str], Optional[str], Optional[str], str]:
        """Verify capture payload against the four non-negotiable money invariants.

        Returns (status, capture_id, captured_amount, captured_currency, message).
        Status is one of: CAPTURED_VERIFIED, PENDING, FAILED.
        """
        order_status = paypal_payload.get("status")
        purchase_units = paypal_payload.get("purchase_units") or []

        if not purchase_units:
            return "FAILED", None, None, None, "Invalid payment response: missing purchase units."

        pu = purchase_units[0]
        custom_id = pu.get("custom_id")
        payments = pu.get("payments") or {}
        captures = payments.get("captures") or []

        if not captures:
            if order_status == "COMPLETED":
                # Some PayPal GET shapes place capture directly under payments
                pass
            return "FAILED", None, None, None, "No payment capture found in PayPal order."

        capture = captures[0]
        capture_id = capture.get("id")
        capture_status = capture.get("status")
        amount_dict = capture.get("amount") or {}
        captured_value = amount_dict.get("value")
        captured_curr = amount_dict.get("currency_code")

        # 1. Custom ID check
        if custom_id != internal_order_id:
            logger.error("Capture custom_id mismatch: expected %s, got %s", internal_order_id, custom_id)
            return "FAILED", capture_id, captured_value, captured_curr, "Payment custom_id mismatch."

        # 2. Amount and Currency check
        try:
            expected_dec = Decimal(expected_total)
            captured_dec = Decimal(str(captured_value))
            if expected_dec != captured_dec or expected_currency.upper() != str(captured_curr).upper():
                logger.error(
                    "Amount mismatch: expected %s %s, got %s %s",
                    expected_total, expected_currency, captured_value, captured_curr,
                )
                return "FAILED", capture_id, captured_value, captured_curr, "Captured amount does not match quote total."
        except Exception:
            return "FAILED", capture_id, captured_value, captured_curr, "Invalid captured amount formatting."

        # 3. Status checks
        if capture_status == "PENDING":
            return (
                "PENDING",
                capture_id,
                captured_value,
                captured_curr,
                "PayPal says this payment is still pending. Do not treat it as paid.",
            )

        if order_status == "COMPLETED" and capture_status == "COMPLETED":
            return (
                "CAPTURED_VERIFIED",
                capture_id,
                captured_value,
                captured_curr,
                "Payment verified. This was a Sandbox test, so no real money moved and no order was placed with the store.",
            )

        return (
            "FAILED",
            capture_id,
            captured_value,
            captured_curr,
            "The payment did not go through. You were not charged.",
        )
