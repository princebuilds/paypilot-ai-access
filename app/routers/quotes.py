"""Quote generation and confirmation endpoints."""
from fastapi import APIRouter, Depends

from app.errors import NotImplementedFeatureError
from app.schemas import QuoteConfirmRequest, QuoteCreateRequest
from app.security import get_session_id

router = APIRouter()


@router.post("/quotes")
def create_quote(
    body: QuoteCreateRequest,
    session_id: str = Depends(get_session_id),
):
    """Create price-locked quote (implemented in Phase B4)."""
    raise NotImplementedFeatureError("Quote generation will be activated in Phase B4.")


@router.post("/quotes/{quote_id}/confirm")
def confirm_quote(
    quote_id: str,
    body: QuoteConfirmRequest,
    session_id: str = Depends(get_session_id),
):
    """Confirm quote total (implemented in Phase B4)."""
    raise NotImplementedFeatureError("Quote confirmation will be activated in Phase B4.")
