"""Health check endpoint exposing operational booleans only."""
from typing import Optional

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.database import get_db
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return operational status booleans and safe configuration info."""
    channel3_configured = bool(settings.CHANNEL3_API_KEY and settings.CHANNEL3_API_KEY.strip())
    gemini_configured = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
    paypal_configured = bool(
        settings.PAYPAL_CLIENT_ID
        and settings.PAYPAL_CLIENT_ID.strip()
        and settings.PAYPAL_CLIENT_SECRET
        and settings.PAYPAL_CLIENT_SECRET.strip()
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

