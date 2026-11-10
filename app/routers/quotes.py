"""Quote generation and confirmation endpoints."""
from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.quotes import QuotesService
from app.schemas import QuoteConfirmRequest, QuoteCreateRequest, QuoteResponse
from app.security import get_session_id

router = APIRouter()


def get_quotes_service(settings: Settings = Depends(get_settings)) -> QuotesService:
    """Dependency provider for QuotesService."""
    return QuotesService(settings=settings)


@router.post("/quotes", response_model=QuoteResponse)
def create_quote(
    body: QuoteCreateRequest,
    session_id: str = Depends(get_session_id),
    quotes_service: QuotesService = Depends(get_quotes_service),
) -> QuoteResponse:
    """Create price-locked quote per SPEC.md Section 4."""
    data = quotes_service.create_quote(
        snapshot_id=body.snapshot_id,
        quantity=body.quantity,
        budget=body.budget,
        session_id=session_id,
    )
    return QuoteResponse(**data)


@router.post("/quotes/{quote_id}/confirm")
def confirm_quote(
    quote_id: str,
    body: QuoteConfirmRequest,
    session_id: str = Depends(get_session_id),
    quotes_service: QuotesService = Depends(get_quotes_service),
):
    """Confirm quote total per SPEC.md Section 4."""
    return quotes_service.confirm_quote(
        quote_id=quote_id,
        confirmed_total=body.confirmed_total,
        session_id=session_id,
    )
