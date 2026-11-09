import pytest

from app.config import get_settings
from app.errors import RateLimitedError
from app.security import RateLimiter


def test_rate_limiter_allows_under_hourly_limit():
    limiter = RateLimiter()
    ip = "192.168.1.10"
    settings = get_settings()

    for _ in range(settings.RATE_LIMIT_PER_HOUR):
        limiter.check_rate_limit(ip)
        limiter.record_call(ip)


def test_rate_limiter_blocks_above_hourly_limit():
    limiter = RateLimiter()
    ip = "192.168.1.11"
    settings = get_settings()

    for _ in range(settings.RATE_LIMIT_PER_HOUR):
        limiter.check_rate_limit(ip)
        limiter.record_call(ip)

    with pytest.raises(RateLimitedError) as exc_info:
        limiter.check_rate_limit(ip)
    assert "Many people are using this demo" in str(exc_info.value)


def test_rate_limiter_different_ips_isolated():
    limiter = RateLimiter()
    ip1 = "10.0.0.1"
    ip2 = "10.0.0.2"
    settings = get_settings()

    for _ in range(settings.RATE_LIMIT_PER_HOUR):
        limiter.record_call(ip1)

    # ip1 should now be blocked
    with pytest.raises(RateLimitedError):
        limiter.check_rate_limit(ip1)

    # ip2 should still be allowed
    limiter.check_rate_limit(ip2)
