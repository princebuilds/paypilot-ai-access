"""Channel3 HTTPX API client, defensive offer parsing, and snapshot persistence."""
import datetime
import json
import logging
import time
import urllib.parse
import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.config import get_settings
from app.database import get_db
from app.errors import UpstreamServiceError

logger = logging.getLogger("paypilot.channel3")

CHANNEL3_BASE_URL = "https://api.trychannel3.com/v1"
CACHE_TTL_SECONDS = 600.0  # 10 minutes cache per AGENTS.md


def parse_offer_price(offer: Dict[str, Any]) -> Tuple[str, str]:
    """Defensively extract (price, currency) from an offer dictionary.

    Raises ValueError on unrecognized price shapes.
    """
    raw_price = offer.get("price")
    raw_currency = offer.get("currency")

    price_val = None
    curr_val = raw_currency

    if isinstance(raw_price, dict):
        price_val = raw_price.get("price") or raw_price.get("amount") or raw_price.get("value")
        if not curr_val:
            curr_val = raw_price.get("currency")
    elif raw_price is not None:
        price_val = raw_price

    if price_val is None or curr_val is None:
        raise ValueError(f"Unrecognized offer price/currency structure: {offer}")

    try:
        clean_price = f"{Decimal(str(price_val)):.2f}"
    except Exception as exc:
        raise ValueError(f"Cannot parse price '{price_val}' into Decimal: {exc}") from exc

    return clean_price, str(curr_val).strip().upper()


def parse_product_offer(product: Dict[str, Any]) -> Dict[str, Any]:
    """Defensively parse and normalize a Channel3 product record."""
    pid = product.get("id") or product.get("channel3_id")
    if not pid:
        raise ValueError(f"Missing product id in Channel3 record: {product}")

    title = product.get("title")
    if not title:
        raise ValueError(f"Missing product title for id {pid}")

    offers = product.get("offers")
    if not offers or not isinstance(offers, list) or len(offers) == 0:
        raise ValueError(f"Product {pid} has no offers list")

    # Select the primary / first offer
    primary_offer = offers[0]
    if not isinstance(primary_offer, dict):
        raise ValueError(f"Primary offer for product {pid} is not a dictionary: {primary_offer}")

    price_str, currency_str = parse_offer_price(primary_offer)

    # Buy URL and merchant domain
    buy_url = primary_offer.get("url") or primary_offer.get("buy_url") or ""
    merchant_domain = primary_offer.get("domain") or ""
    if not merchant_domain and buy_url:
        try:
            parsed = urllib.parse.urlparse(buy_url)
            merchant_domain = parsed.netloc.replace("www.", "")
        except Exception:
            merchant_domain = ""

    availability = primary_offer.get("availability") or product.get("availability") or "Unknown"

    # Images
    images: List[str] = []
    raw_images = product.get("images") or []
    if isinstance(raw_images, list):
        for img in raw_images:
            if isinstance(img, str):
                images.append(img)
            elif isinstance(img, dict) and img.get("url"):
                images.append(img["url"])

    # Key features and materials
    key_features = product.get("key_features") or []
    if isinstance(key_features, str):
        key_features = [key_features]
    elif not isinstance(key_features, list):
        key_features = []

    materials = product.get("materials") or []
    if isinstance(materials, str):
        materials = [materials]
    elif not isinstance(materials, list):
        materials = []

    return {
        "channel3_id": str(pid),
        "title": str(title).strip(),
        "description": str(product.get("description") or "").strip(),
        "images": images,
        "image_url": images[0] if images else None,
        "merchant_domain": merchant_domain or "retailer.com",
        "price": price_str,
        "currency": currency_str,
        "availability": str(availability).strip(),
        "buy_url": buy_url,
        "key_features": [str(k) for k in key_features],
        "materials": [str(m) for m in materials],
        "raw_json": json.dumps(product),
    }


class Channel3Client:
    """HTTP client for Channel3 API with retries, timeouts, and snapshot caching."""

    def __init__(self, api_key: Optional[str] = None, settings: Optional[Any] = None):
        cfg = settings or get_settings()
        self.settings = cfg
        self.api_key = api_key or (getattr(cfg, "CHANNEL3_API_KEY", None))
        self.timeout = 15.0

    def _headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise UpstreamServiceError("Channel3 API key not configured")
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Execute request with up to 2 retries on 429 and 5xx."""
        headers = self._headers()
        retries = 2
        delay = 1.0

        for attempt in range(retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.request(method, url, headers=headers, **kwargs)
                    if resp.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                        time.sleep(delay)
                        delay *= 2
                        continue
                    if resp.status_code >= 400:
                        raise UpstreamServiceError(
                            f"Channel3 upstream returned HTTP {resp.status_code}: {resp.text[:200]}"
                        )
                    return resp
            except (httpx.TimeoutException, httpx.NetworkError) as err:
                if attempt < retries:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise UpstreamServiceError(f"Channel3 connection failed: {err}") from err

        raise UpstreamServiceError("Channel3 max retries exceeded")

    def search(
        self,
        query: str,
        session_id: str,
        max_price: Optional[float] = None,
        in_stock_only: bool = True,
        limit: int = 5,
        db_path: Optional[str] = None,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Search Channel3 inventory with 10-minute caching and snapshot persistence.

        Returns (search_id, list_of_product_snapshots).
        """
        params = {
            "query": query,
            "limit": limit,
            "max_price": max_price,
            "in_stock_only": in_stock_only,
        }
        params_str = json.dumps(params, sort_keys=True)
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        cutoff_dt = (now_dt - datetime.timedelta(seconds=CACHE_TTL_SECONDS)).isoformat()
        db_file = db_path or getattr(self.settings, "DATABASE_PATH", None)

        # 1. Check cache in database
        with get_db(db_file) as conn:
            cached_search = conn.execute(
                """
                SELECT id FROM searches
                WHERE query = ? AND params_json = ? AND status = 'SUCCESS' AND created_at >= ?
                ORDER BY created_at DESC LIMIT 1
                """,
                (query, params_str, cutoff_dt),
            ).fetchone()

            if cached_search:
                search_id = cached_search["id"]
                snapshots = conn.execute(
                    "SELECT * FROM product_snapshots WHERE search_id = ?",
                    (search_id,),
                ).fetchall()
                if snapshots:
                    logger.info("Channel3 search cache hit for query: '%s'", query)
                    return search_id, [dict(s) for s in snapshots]

        # 2. Cache miss: Execute live search
        body: Dict[str, Any] = {"query": query, "limit": limit}
        filters: Dict[str, Any] = {}
        if max_price is not None:
            filters["price"] = {"max_price": float(max_price)}
        if in_stock_only:
            filters["availability"] = ["InStock"]
        if filters:
            body["filters"] = filters

        start_time = time.time()
        search_id = uuid.uuid4().hex
        now_iso = now_dt.isoformat()

        try:
            resp = self._request_with_retry(
                "POST",
                f"{CHANNEL3_BASE_URL}/search",
                json=body,
            )
            data = resp.json()
            latency_ms = int((time.time() - start_time) * 1000)
            raw_products = data.get("products") or []

            parsed_snapshots: List[Dict[str, Any]] = []
            for raw_p in raw_products:
                try:
                    parsed = parse_product_offer(raw_p)
                    parsed["id"] = uuid.uuid4().hex
                    parsed["search_id"] = search_id
                    parsed["fetched_at"] = now_iso
                    parsed_snapshots.append(parsed)
                except ValueError as parse_err:
                    logger.warning("Dropped Channel3 product due to parse error: %s", parse_err)

            # Persist search and snapshots
            with get_db(db_file) as conn:
                conn.execute(
                    """
                    INSERT INTO searches (id, session_id, query, params_json, result_count, latency_ms, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (search_id, session_id, query, params_str, len(parsed_snapshots), latency_ms, "SUCCESS", now_iso),
                )
                for snap in parsed_snapshots:
                    conn.execute(
                        """
                        INSERT INTO product_snapshots (
                            id, search_id, channel3_id, title, description, key_features_json,
                            materials_json, image_url, merchant_domain, price, currency,
                            availability, buy_url, raw_json, fetched_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            snap["id"],
                            search_id,
                            snap["channel3_id"],
                            snap["title"],
                            snap["description"],
                            json.dumps(snap["key_features"]),
                            json.dumps(snap["materials"]),
                            snap["image_url"],
                            snap["merchant_domain"],
                            snap["price"],
                            snap["currency"],
                            snap["availability"],
                            snap["buy_url"],
                            snap["raw_json"],
                            snap["fetched_at"],
                        ),
                    )

            return search_id, parsed_snapshots

        except Exception as exc:
            latency_ms = int((time.time() - start_time) * 1000)
            with get_db(db_file) as conn:
                conn.execute(
                    """
                    INSERT INTO searches (id, session_id, query, params_json, result_count, latency_ms, status, created_at)
                    VALUES (?, ?, ?, ?, 0, ?, 'FAILED', ?)
                    """,
                    (search_id, session_id, query, params_str, latency_ms, now_iso),
                )
            if isinstance(exc, UpstreamServiceError):
                raise
            raise UpstreamServiceError(f"Channel3 search failed: {exc}") from exc

    def get_product(self, channel3_id: str, currency: str = "USD") -> Dict[str, Any]:
        """Fetch fresh product details using the free Channel3 detail endpoint."""
        url = f"{CHANNEL3_BASE_URL}/products/{channel3_id}"
        resp = self._request_with_retry("GET", url, params={"currency": currency})
        data = resp.json()
        product_data = data.get("product") or data
        return parse_product_offer(product_data)
