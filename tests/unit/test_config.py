import pytest

from app.config import Settings, is_configured_secret


def test_is_configured_secret_rejects_empty_and_placeholders():
    """Verify placeholder patterns and empty strings are rejected."""
    # Empty cases
    assert is_configured_secret(None) is False
    assert is_configured_secret("") is False
    assert is_configured_secret("   ") is False

    # Placeholder patterns
    assert is_configured_secret("your_channel3_api_key_here") is False
    assert is_configured_secret("your_key") is False
    assert is_configured_secret("some_secret_here") is False
    assert is_configured_secret("replace_with_placeholder") is False
    assert is_configured_secret("put_actual_key_here") is False

    # Valid-looking keys (any format without placeholder patterns)
    assert is_configured_secret("sk-1234567890abcdef") is True
    assert is_configured_secret("valid-opaque-key-998877") is True
    assert is_configured_secret("custom-token-xyz-123") is True


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


@pytest.mark.parametrize("placeholder", [
    "your_channel3_api_key_here",
    "your_key",
    "insert_placeholder",
    "paste_key_here",
    "my_actual_token",
])
def test_config_fail_fast_rejects_placeholder(placeholder):
    """When a key has a placeholder value, fail-fast names the variable, never its value."""
    settings = Settings(
        OFFLINE_TESTS=0,
        CHANNEL3_API_KEY=placeholder,
        GEMINI_API_KEY="valid-secret-123",
        GEMINI_MODEL="valid-model-123",
        PAYPAL_CLIENT_ID="valid-id-123",
        PAYPAL_CLIENT_SECRET="valid-sec-123",
    )
    with pytest.raises(RuntimeError) as exc_info:
        settings.validate_for_startup()
    assert "CHANNEL3_API_KEY" in str(exc_info.value)
    # Never leak the placeholder string itself
    assert placeholder not in str(exc_info.value)


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
