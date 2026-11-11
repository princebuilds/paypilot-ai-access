"""Server-side activity event generator built strictly from stored database records.

Governed by Hackathon money-safety and auditability rules:
- Built strictly from stored SQLite records (searches, grounding_runs, quotes, orders, payment_events).
- Never returns model-generated text.
- Never contains secrets, tokens, or credential-like values.
- Powers 'What the assistant did' panel on results and receipt views.
"""
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.database import get_db_connection


def sanitize_event_detail(text: str) -> str:
    """Ensure no secret-looking strings or auth tokens can leak into event details."""
    forbidden = ("bearer", "secret", "client_secret", "api_key", "password")
    lower = text.lower()
    for f in forbidden:
        if f in lower:
            return "[REDACTED]"
    return text


def get_activity_for_session(session_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Build chronological activity timeline for a user session strictly from DB rows."""
    path = db_path or get_settings().DATABASE_PATH
    events: List[Dict[str, Any]] = []

    with get_db_connection(path) as conn:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

        # 1. Searches and Grounding runs
        searches = conn.execute(
            """
            SELECT id, query, result_count, latency_ms, status, created_at
            FROM searches
            WHERE session_id = ?
            ORDER BY created_at ASC
            """,
            (session_id,),
        ).fetchall()

        for s in searches:
            events.append({
                "step": "channel3_search",
                "title": "Live Product Catalog Search",
                "detail": sanitize_event_detail(
                    f"Searched Channel3 catalog for '{s['query']}' — {s.get('result_count', 0)} products retrieved in {s.get('latency_ms', 0)}ms"
                ),
                "timestamp": s["created_at"],
                "source_table": "searches",
            })

            # Check matching grounding runs
            gr = conn.execute(
                """
                SELECT kept_count, removed_count, created_at
                FROM grounding_runs
                WHERE search_id = ?
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (s["id"],),
            ).fetchone()

            if gr:
                events.append({
                    "step": "grounding",
                    "title": "Evidence & Grounding Check",
                    "detail": sanitize_event_detail(
                        f"Safety grounding verified {gr['kept_count']} recommendations against product snapshots; dropped {gr['removed_count']} ungrounded or mismatched items"
                    ),
                    "timestamp": gr["created_at"],
                    "source_table": "grounding_runs",
                })

        # 2. Quotes & Confirmations
        quotes = conn.execute(
            """
            SELECT q.id, q.unit_price, q.total, q.currency, q.status, q.confirmed_at, q.created_at,
                   p.merchant_domain
            FROM quotes q
            LEFT JOIN product_snapshots p ON q.snapshot_id = p.id
            WHERE q.session_id = ?
            ORDER BY q.created_at ASC
            """,
            (session_id,),
        ).fetchall()

        for q in quotes:
            retailer = q.get("merchant_domain") or "retailer"
            events.append({
                "step": "price_lock",
                "title": "Server-Side Price Lock",
                "detail": sanitize_event_detail(
                    f"Locked price at ${q['total']} {q['currency']} from retailer {retailer} (10-minute expiry)"
                ),
                "timestamp": q["created_at"],
                "source_table": "quotes",
            })

            if q.get("confirmed_at"):
                events.append({
                    "step": "buyer_confirmation",
                    "title": "Buyer Total Confirmation",
                    "detail": sanitize_event_detail(
                        f"Customer explicitly confirmed exact checkout total of ${q['total']} {q['currency']}"
                    ),
                    "timestamp": q["confirmed_at"],
                    "source_table": "quotes",
                })

        # 3. Orders and Payment events
        orders = conn.execute(
            """
            SELECT id, paypal_order_id, status, capture_id, captured_amount, captured_currency, created_at
            FROM orders
            WHERE session_id = ?
            ORDER BY created_at ASC
            """,
            (session_id,),
        ).fetchall()

        for o in orders:
            pe_rows = conn.execute(
                """
                SELECT step, http_status, paypal_debug_id, summary, created_at
                FROM payment_events
                WHERE order_id = ?
                ORDER BY id ASC
                """,
                (o["id"],),
            ).fetchall()

            for pe in pe_rows:
                step_name = pe.get("step")
                if step_name == "CREATE_ORDER":
                    events.append({
                        "step": "paypal_order_created",
                        "title": "PayPal Sandbox Order Created",
                        "detail": sanitize_event_detail(
                            f"Created PayPal Sandbox order with plain amount (Status: HTTP {pe.get('http_status', 201)})"
                        ),
                        "timestamp": pe["created_at"],
                        "source_table": "payment_events",
                    })
                elif step_name == "CAPTURE_ORDER":
                    is_verified = (o.get("status") == "CAPTURED_VERIFIED")
                    detail_str = (
                        f"Server capture verified: order COMPLETED, capture COMPLETED, "
                        f"amount and currency (${o.get('captured_amount')} {o.get('captured_currency')}) matched, custom_id matched"
                        if is_verified
                        else f"PayPal payment capture processed (Status: HTTP {pe.get('http_status', 200)})"
                    )
                    events.append({
                        "step": "paypal_capture_verified",
                        "title": "Payment Capture & Verification",
                        "detail": sanitize_event_detail(detail_str),
                        "timestamp": pe["created_at"],
                        "source_table": "payment_events",
                    })

    # Sort strictly chronologically by ISO timestamp
    events.sort(key=lambda e: e.get("timestamp") or "")
    return events


def get_activity_for_order(order_id: str, session_id: Optional[str] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Build chronological activity timeline for a specific order and its linked quote & search."""
    path = db_path or get_settings().DATABASE_PATH
    with get_db_connection(path) as conn:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        order = conn.execute(
            "SELECT session_id FROM orders WHERE id = ?", (order_id,)
        ).fetchone()

        if not order:
            return []

        # If session_id provided, verify ownership
        if session_id and order["session_id"] != session_id:
            return []

        return get_activity_for_session(order["session_id"], db_path=path)
