"""Typed settings and fail-fast configuration validation."""
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PLACEHOLDER_TOKENS = ("_here", "placeholder", "actual")


def is_configured_secret(val: Optional[str]) -> bool:
    """Check if a secret string is properly configured and not empty or a placeholder."""
    if not val:
        return False
    s = val.strip().lower()
    if not s:
        return False
    if s.startswith("your"):
        return False
    if any(token in s for token in PLACEHOLDER_TOKENS):
        return False
    return True


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    CHANNEL3_API_KEY: Optional[str] = Field(default=None)
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    GEMINI_MODEL: Optional[str] = Field(default=None)
    PAYPAL_CLIENT_ID: Optional[str] = Field(default=None)
    PAYPAL_CLIENT_SECRET: Optional[str] = Field(default=None)
    PAYPAL_ENV: str = Field(default="sandbox")
    OFFLINE_TESTS: int = Field(default=0)
    RATE_LIMIT_PER_HOUR: int = Field(default=30)
    DAILY_SEARCH_CAP: int = Field(default=1500)
    DATABASE_PATH: str = Field(default="paypilot.db")

    def validate_for_startup(self) -> None:
        """Validate critical configuration; fail fast naming missing keys only."""
        if self.OFFLINE_TESTS == 1:
            return

        required_vars = [
            ("CHANNEL3_API_KEY", self.CHANNEL3_API_KEY),
            ("GEMINI_API_KEY", self.GEMINI_API_KEY),
            ("GEMINI_MODEL", self.GEMINI_MODEL),
            ("PAYPAL_CLIENT_ID", self.PAYPAL_CLIENT_ID),
            ("PAYPAL_CLIENT_SECRET", self.PAYPAL_CLIENT_SECRET),
        ]
        for name, val in required_vars:
            if not is_configured_secret(val):
                raise RuntimeError(f"Missing or placeholder environment variable: {name}")

        if self.GEMINI_MODEL:
            m = self.GEMINI_MODEL.strip().lower()
            if "-preview" in m or m.endswith("-latest"):
                raise RuntimeError(f"Configured GEMINI_MODEL must not be a preview or latest alias: {self.GEMINI_MODEL}")

        if self.PAYPAL_ENV.lower() != "sandbox":
            raise RuntimeError("PAYPAL_ENV must be 'sandbox'")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
