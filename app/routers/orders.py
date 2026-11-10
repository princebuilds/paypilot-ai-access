"""Order creation, PayPal capture, verification, cancellation, and receipt endpoints."""
import datetime
import uuid

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.database import get_db
from app.errors import AppError, NotFoundError
from app.paypal import PayPalClient
from app.schemas import (
    OrderCancelResponse,
    OrderCaptureResponse,
    OrderCreateRequest,
    OrderCreateResponse,
    ReceiptResponse,
)
from app.security import get_session_id

router = APIRouter()


def get_paypal_client(settings: Settings = Depends(get_settings)) -> PayPalClient:
    """Dependency provider for PayPalClient."""
    return PayPalClient(settings=settings)


@router.post("/orders", response_model=OrderCreateResponse)
def create_order(
    body: OrderCreateRequest,
    session_id: str = Depends(get_session_id),
    settings: Settings = Depends(get_settings),
    paypal_client: PayPalClient = Depends(get_paypal_client),
) -> OrderCreateResponse:
    """Create internal and PayPal Sandbox order from a confirmed quote."""
    db_file = settings.DATABASE_PATH
    with get_db(db_file) as conn:
        quote = conn.execute(
            "SELECT * FROM quotes WHERE id = ?",
            (body.quote_id,),
        ).fetchone()

    if not quote:
        raise NotFoundError(f"Quote '{body.quote_id}' not found.")

    if quote["session_id"] != session_id:
        raise NotFoundError("Quote does not belong to your session.")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if now_iso > quote["expires_at"]:
        raise AppError(
            code="QUOTE_EXPIRED",
            message="This quote has expired. Please request a new price.",
            http_status=422,
        )

    if quote["status"] != "CONFIRMED":
        raise AppError(
            code="QUOTE_NOT_CONFIRMED",
            message="Quote must be confirmed by the customer before creating an order.",
            http_status=422,
        )

    order_id = f"ord_{uuid.uuid4().hex[:12]}"

    # Call PayPal Sandbox create order with internal order_id as custom_id and idempotency key
    paypal_order_id, debug_id = paypal_client.create_order(
        order_id=order_id,
        total=quote["total"],
        currency=quote["currency"],
    )

    with get_db(db_file) as conn:
        conn.execute(
            """
            INSERT INTO orders (id, session_id, quote_id, paypal_order_id, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'ORDER_CREATED', ?, ?)
            """,
            (order_id, session_id, body.quote_id, paypal_order_id, now_iso, now_iso),
        )

    return OrderCreateResponse(
        order_id=order_id,
        paypal_order_id=paypal_order_id,
        status="ORDER_CREATED",
    )


@router.post("/orders/{order_id}/capture", response_model=OrderCaptureResponse)
def capture_order(
    order_id: str,
    session_id: str = Depends(get_session_id),
    settings: Settings = Depends(get_settings),
    paypal_client: PayPalClient = Depends(get_paypal_client),
) -> OrderCaptureResponse:
    """Capture PayPal order server-side and verify all four money-safety invariants."""
    db_file = settings.DATABASE_PATH
    with get_db(db_file) as conn:
        order = conn.execute(
            """
            SELECT o.*, q.total as expected_total, q.currency as expected_currency
            FROM orders o
            JOIN quotes q ON o.quote_id = q.id
            WHERE o.id = ?
            """,
            (order_id,),
        ).fetchone()

    if not order:
        raise NotFoundError(f"Order '{order_id}' not found.")

    if order["session_id"] != session_id:
        raise NotFoundError("Order does not belong to your session.")

    # Idempotent second capture: return existing verified receipt
    if order["status"] == "CAPTURED_VERIFIED":
        return OrderCaptureResponse(
            order_id=order_id,
            status="CAPTURED_VERIFIED",
            message=order["message"] or "Payment verified.",
            receipt_url=f"/receipt.html?order={order_id}",
        )

    # Execute PayPal capture
    paypal_payload, debug_id = paypal_client.capture_order(
        internal_order_id=order_id,
        paypal_order_id=order["paypal_order_id"],
    )

    # Verify capture invariants
    status, capture_id, captured_amt, captured_curr, msg = paypal_client.verify_capture(
        internal_order_id=order_id,
        expected_total=order["expected_total"],
        expected_currency=order["expected_currency"],
        paypal_payload=paypal_payload,
    )

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_db(db_file) as conn:
        conn.execute(
            """
            UPDATE orders
            SET status = ?, capture_id = ?, captured_amount = ?, captured_currency = ?, message = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, capture_id, captured_amt, captured_curr, msg, now_iso, order_id),
        )

    return OrderCaptureResponse(
        order_id=order_id,
        status=status,
        message=msg,
        receipt_url=f"/receipt.html?order={order_id}",
    )


@router.post("/orders/{order_id}/cancel", response_model=OrderCancelResponse)
def cancel_order(
    order_id: str,
    session_id: str = Depends(get_session_id),
    settings: Settings = Depends(get_settings),
) -> OrderCancelResponse:
    """Record customer cancellation of an order."""
    db_file = settings.DATABASE_PATH
    with get_db(db_file) as conn:
        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    if not order:
        raise NotFoundError(f"Order '{order_id}' not found.")

    if order["session_id"] != session_id:
        raise NotFoundError("Order does not belong to your session.")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_db(db_file) as conn:
        conn.execute("UPDATE orders SET status = 'CANCELLED', updated_at = ? WHERE id = ?", (now_iso, order_id))

    return OrderCancelResponse(status="CANCELLED")


@router.get("/orders/{order_id}", response_model=ReceiptResponse)
def get_order_receipt(
    order_id: str,
    session_id: str = Depends(get_session_id),
    settings: Settings = Depends(get_settings),
) -> ReceiptResponse:
    """Retrieve verified receipt data for an order."""
    db_file = settings.DATABASE_PATH
    with get_db(db_file) as conn:
        row = conn.execute(
            """
            SELECT o.id as order_id, o.status, o.capture_id as paypal_capture_id,
                   o.updated_at as captured_at, o.message,
                   q.quantity, q.unit_price, q.total, q.currency,
                   p.title, p.merchant_domain, p.buy_url as retailer_url,
                   o.session_id
            FROM orders o
            JOIN quotes q ON o.quote_id = q.id
            JOIN product_snapshots p ON q.snapshot_id = p.id
            WHERE o.id = ?
            """,
            (order_id,),
        ).fetchone()

    if not row:
        raise NotFoundError(f"Order '{order_id}' not found.")

    if row["session_id"] != session_id:
        raise NotFoundError("Order does not belong to your session.")

    return ReceiptResponse(
        order_id=row["order_id"],
        status=row["status"],
        title=row["title"],
        quantity=row["quantity"],
        unit_price=row["unit_price"],
        total=row["total"],
        currency=row["currency"],
        paypal_capture_id=row["paypal_capture_id"],
        captured_at=row["captured_at"],
        merchant_domain=row["merchant_domain"],
        retailer_url=row["retailer_url"],
        sandbox=True,
        message=row["message"] or "Sandbox payment processed.",
    )
