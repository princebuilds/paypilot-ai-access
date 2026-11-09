import pytest

from app.config import Settings


def test_config_offline_mode_skips_key_validation():
    """When OFFLINE_TESTS=1, startup validation succeeds without live keys."""
    settings = Settings(OFFLINE_TESTS=1)
    settings.validate_for_startup()  # Should not raise


def test_config_fail_fast_names_missing_variable():
    """When a required key is missing, fail-fast names the exact variable, not value."""
    settings = Settings(
        OFFLINE_TESTS=0,
        CHANNEL3_API_KEY="",
        GEMINI_API_KEY="dummy",
        GEMINI_MODEL="dummy-model",
        PAYPAL_CLIENT_ID="dummy",
        PAYPAL_CLIENT_SECRET="dummy",
    )
    with pytest.raises(RuntimeError) as exc_info:
        settings.validate_for_startup()
    assert "CHANNEL3_API_KEY" in str(exc_info.value)
    # Ensure no secret value is printed
    assert "dummy" not in str(exc_info.value)


def test_config_rejects_non_sandbox_paypal_env():
    """PAYPAL_ENV must be sandbox for hackathon safety."""
    settings = Settings(
        OFFLINE_TESTS=0,
        CHANNEL3_API_KEY="test-ch3",
        GEMINI_API_KEY="test-gem",
        GEMINI_MODEL="dummy-model",
        PAYPAL_CLIENT_ID="test-id",
        PAYPAL_CLIENT_SECRET="test-sec",
        PAYPAL_ENV="live",
    )
    with pytest.raises(RuntimeError) as exc_info:
        settings.validate_for_startup()
    assert "sandbox" in str(exc_info.value).lower()
