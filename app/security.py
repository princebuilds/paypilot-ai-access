"""Session cookie management and rate limiting logic."""
import time
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import get_settings
from app.errors import RateLimitedError


class SessionMiddleware(BaseHTTPMiddleware):
    """Ensure every client has an anonymous, HttpOnly session cookie 'sid'."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        existing_sid = request.cookies.get("sid")
        is_new_session = False

        if existing_sid and 8 <= len(existing_sid) <= 64 and existing_sid.replace("-", "").replace("_", "").isalnum():
            session_id = existing_sid
        else:
            session_id = uuid.uuid4().hex
            is_new_session = True

        request.state.session_id = session_id
        response = await call_next(request)

        if is_new_session:
            is_secure = request.url.scheme == "https"
            response.set_cookie(
                key="sid",
                value=session_id,
                httponly=True,
                samesite="lax",
                secure=is_secure,
                max_age=86400 * 7,  # 7 days
            )

        return response


def get_session_id(request: Request) -> str:
    """Dependency retrieving the authenticated session ID from request state."""
    sid = getattr(request.state, "session_id", None)
    if not sid:
        sid = request.cookies.get("sid")
    if not sid:
        sid = uuid.uuid4().hex
        request.state.session_id = sid
    return sid


class RateLimiter:
    """In-memory rate limiter tracking IP hourly limits and daily search caps."""

    def __init__(self):
        self._ip_timestamps: Dict[str, List[float]] = defaultdict(list)
        self._daily_counts: Dict[str, int] = defaultdict(int)

    def check_rate_limit(self, client_ip: str, settings: Optional[Any] = None) -> None:
        """Check hourly limit for client IP and global daily cap."""
        active_settings = settings or get_settings()
        now = time.time()
        one_hour_ago = now - 3600.0
        today_key = time.strftime("%Y-%m-%d", time.gmtime(now))

        # Check global daily cap
        if self._daily_counts[today_key] >= active_settings.DAILY_SEARCH_CAP:
            raise RateLimitedError("Daily demonstration limit reached. Please try again tomorrow.")

        # Prune timestamps older than 1 hour for this IP
        timestamps = [t for t in self._ip_timestamps[client_ip] if t > one_hour_ago]
        self._ip_timestamps[client_ip] = timestamps

        if len(timestamps) >= active_settings.RATE_LIMIT_PER_HOUR:
            raise RateLimitedError("Many people are using this demo. Please wait a minute and try again.")

    def record_call(self, client_ip: str) -> None:
        """Record successful call against limits."""
        now = time.time()
        today_key = time.strftime("%Y-%m-%d", time.gmtime(now))
        self._ip_timestamps[client_ip].append(now)
        self._daily_counts[today_key] += 1

    def reset(self) -> None:
        """Reset internal rate limiting data (for testing)."""
        self._ip_timestamps.clear()
        self._daily_counts.clear()


rate_limiter = RateLimiter()
