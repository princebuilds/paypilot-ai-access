"""Agent interaction endpoints."""
from fastapi import APIRouter, Depends, Request

from app.config import Settings, get_settings
from app.errors import NotImplementedFeatureError
from app.schemas import AgentRequest
from app.security import get_session_id, rate_limiter

router = APIRouter()


@router.post("/agent")
def search_agent(
    request: Request,
    body: AgentRequest,
    session_id: str = Depends(get_session_id),
    settings: Settings = Depends(get_settings),
):
    """Handle conversational search requests (implemented in Phase B3)."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    rate_limiter.check_rate_limit(client_ip, settings=settings)
    raise NotImplementedFeatureError("The agent search feature will be activated in Phase B3.")
