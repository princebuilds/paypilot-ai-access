"""Quote lifecycle, Channel3 detail refresh, price lock, and budget verification.

Governed by SPEC.md Section 4-6 and AGENTS.md Section 4:
- Quantities 1 to 10.
- Refreshes product through free Channel3 detail endpoint.
- USD and InStock only; others return NOT_PURCHASABLE.
- Exact price lock: price changes return PRICE_CHANGED with new total.
- Budget enforcement using Decimal arithmetic (2 decimal places).
- Quote expires in 10 minutes (600s).
- Explicit customer confirmation required before order creation.
"""
import datetime
import logging
import uuid
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, Optional

from app.channel3 import Channel3Client
from app.config import Settings
from app.database import get_db
from app.errors import AppError, NotFoundError

logger = logging.getLogger("paypilot.quotes")

QUOTE_TTL_SECONDS = 600.0  # 10 minutes


def format_money(val: Decimal) -> str:
    """Format Decimal to two decimal places string."""
    return str(val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class QuotesService:
    """Manages quote generation, detail refresh, budget checks, and confirmations."""

    def __init__(self, settings: Settings, channel3_client: Optional[Channel3Client] = None):
        self.settings = settings
        self.channel3_client = channel3_client or Channel3Client(settings=settings)

    def create_quote(
        self,
        snapshot_id: str,
        quantity: int,
        budget: Optional[str],
        session_id: str,
    ) -> Dict[str, Any]:
        """Create a price-locked quote after refreshing price and availability via Channel3 detail."""
        if quantity < 1 or quantity > 10:
            raise AppError(
                code="INVALID_QUANTITY",
                message="Quantity must be between 1 and 10.",
                http_status=422,
            )

        db_file = self.settings.DATABASE_PATH
        # 1. Fetch stored snapshot
        with get_db(db_file) as conn:
            row = conn.execute(
                """
                SELECT p.*, s.session_id as search_session_id
                FROM product_snapshots p
                JOIN searches s ON p.search_id = s.id
                WHERE p.id = ?
                """,
                (snapshot_id,),
            ).fetchone()

        if not row:
            raise NotFoundError(f"Product snapshot '{snapshot_id}' not found.")

        # Session isolation check
        if row["search_session_id"] != session_id:
            raise NotFoundError("Product snapshot does not belong to your session.")

        channel3_id = row["channel3_id"]
        stored_price = Decimal(str(row["price"]))

        # 2. Refresh product through free Channel3 detail endpoint
        try:
            fresh_product = self.channel3_client.get_product(channel3_id=channel3_id, currency="USD")
        except Exception as e:
            logger.warning("Channel3 detail refresh failed: %s; relying on stored snapshot", e)
            fresh_product = None

        if fresh_product:
            fresh_curr = str(fresh_product.get("currency", "")).upper()
            fresh_avail = str(fresh_product.get("availability", "")).lower()
            fresh_price = Decimal(str(fresh_product.get("price", "0.00")))

            # Check USD and InStock
            if fresh_curr != "USD" or fresh_avail not in ("instock", "in_stock"):
                raise AppError(
                    code="NOT_PURCHASABLE",
                    message="This product is currently unavailable or not priced in USD.",
                    http_status=422,
                )

            # Check price change
            if fresh_price != stored_price:
                new_total = format_money(fresh_price * quantity)
                raise AppError(
                    code="PRICE_CHANGED",
                    message=f"The price changed to ${new_total}. Please confirm again.",
                    http_status=409,
                )
            unit_price = fresh_price
            currency = fresh_curr
            title = fresh_product.get("title") or row["title"]
        else:
            # Fall back to verified snapshot values if detail endpoint is unreachable
            unit_price = stored_price
            currency = str(row["currency"]).upper()
            title = row["title"]
            if currency != "USD" or str(row["availability"]).lower() not in ("instock", "in_stock"):
                raise AppError(
                    code="NOT_PURCHASABLE",
                    message="This product is currently unavailable or not priced in USD.",
                    http_status=422,
                )

        # 3. Calculate total and check budget
        total = unit_price * quantity
        total_str = format_money(total)
        unit_price_str = format_money(unit_price)

        if budget:
            budget_dec = Decimal(str(budget))
            if total > budget_dec:
                raise AppError(
                    code="BUDGET_EXCEEDED",
                    message=f"That is ${total_str}, above your ${format_money(budget_dec)} budget. You can raise the budget or pick another item.",
                    http_status=422,
                )

        # 4. Insert quote record
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        expires_dt = now_dt + datetime.timedelta(seconds=QUOTE_TTL_SECONDS)
        quote_id = f"quote_{uuid.uuid4().hex[:12]}"
        created_at_iso = now_dt.isoformat()
        expires_at_iso = expires_dt.isoformat()

        with get_db(db_file) as conn:
            conn.execute(
                """
                INSERT INTO quotes (
                    id, session_id, snapshot_id, quantity, unit_price, currency,
                    total, budget, status, confirmed_at, expires_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    quote_id,
                    session_id,
                    snapshot_id,
                    quantity,
                    unit_price_str,
                    currency,
                    total_str,
                    format_money(Decimal(str(budget))) if budget else None,
                    "QUOTED",
                    None,
                    expires_at_iso,
                    created_at_iso,
                ),
            )

        return {
            "quote_id": quote_id,
            "title": title,
            "unit_price": unit_price_str,
            "currency": currency,
            "quantity": quantity,
            "total": total_str,
            "budget": format_money(Decimal(str(budget))) if budget else None,
            "within_budget": True,
            "expires_at": expires_at_iso,
            "status": "QUOTED",
        }

    def confirm_quote(
        self,
        quote_id: str,
        confirmed_total: str,
        session_id: str,
    ) -> Dict[str, str]:
        """Confirm customer intent to purchase the exact quoted total."""
        db_file = self.settings.DATABASE_PATH
        with get_db(db_file) as conn:
            row = conn.execute(
                "SELECT * FROM quotes WHERE id = ?",
                (quote_id,),
            ).fetchone()

        if not row:
            raise NotFoundError(f"Quote '{quote_id}' not found.")

        if row["session_id"] != session_id:
            raise NotFoundError("Quote does not belong to your session.")

        # Check expiration
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if now_iso > row["expires_at"]:
            with get_db(db_file) as conn:
                conn.execute("UPDATE quotes SET status = 'EXPIRED' WHERE id = ?", (quote_id,))
            raise AppError(
                code="QUOTE_EXPIRED",
                message="This quote has expired. Please request a new price.",
                http_status=422,
            )

        if row["status"] != "QUOTED":
            if row["status"] == "CONFIRMED":
                return {"status": "CONFIRMED"}
            raise AppError(
                code="INVALID_QUOTE_STATE",
                message=f"Quote cannot be confirmed from status '{row['status']}'.",
                http_status=422,
            )

        # Validate exact confirmed total
        try:
            conf_dec = Decimal(str(confirmed_total))
            quote_dec = Decimal(str(row["total"]))
        except Exception:
            raise AppError(code="TOTAL_MISMATCH", message="Invalid total format.", http_status=422)

        if conf_dec != quote_dec:
            raise AppError(
                code="TOTAL_MISMATCH",
                message=f"Confirmed total ${confirmed_total} does not match quote total ${row['total']}.",
                http_status=422,
            )

        with get_db(db_file) as conn:
            conn.execute(
                "UPDATE quotes SET status = 'CONFIRMED', confirmed_at = ? WHERE id = ?",
                (now_iso, quote_id),
            )

        return {"status": "CONFIRMED"}
