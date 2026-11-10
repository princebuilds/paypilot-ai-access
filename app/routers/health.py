"""Health check endpoint exposing operational booleans only."""
from typing import Optional

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings, is_configured_secret
from app.database import get_db
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return operational status booleans and safe configuration info."""
    channel3_configured = is_configured_secret(settings.CHANNEL3_API_KEY)
    gemini_configured = is_configured_secret(settings.GEMINI_API_KEY)
    paypal_configured = (
        is_configured_secret(settings.PAYPAL_CLIENT_ID)
        and is_configured_secret(settings.PAYPAL_CLIENT_SECRET)
    )

    last_channel3_call_at: Optional[str] = None
    try:
        with get_db(settings.DATABASE_PATH) as conn:
            row = conn.execute(
                "SELECT created_at FROM searches WHERE status = 'SUCCESS' ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            if row:
                last_channel3_call_at = row["created_at"]
    except Exception:
        # Health check should not crash if database is uninitialized
        pass

    return HealthResponse(
        ok=True,
        channel3_configured=channel3_configured,
        gemini_configured=gemini_configured,
        paypal_configured=paypal_configured,
        gemini_model=settings.GEMINI_MODEL,
        last_channel3_call_at=last_channel3_call_at,
    )
