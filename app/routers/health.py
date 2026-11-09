"""Health check endpoint exposing operational booleans only."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def get_health():
    return {
        "ok": True,
        "channel3_configured": False,
        "gemini_configured": False,
        "paypal_configured": False,
        "gemini_model": "placeholder",
        "last_channel3_call_at": None,
    }
