"""Agent interaction endpoints."""
from fastapi import APIRouter, Depends, Request

from app.agent import AgentService
from app.channel3 import Channel3Client
from app.config import Settings, get_settings
from app.schemas import AgentRequest, AgentResponse
from app.security import get_session_id, rate_limiter

router = APIRouter()


def get_agent_service(settings: Settings = Depends(get_settings)) -> AgentService:
    """Dependency provider for AgentService."""
    channel3_client = Channel3Client(settings=settings)
    return AgentService(settings=settings, channel3_client=channel3_client)


@router.post("/agent", response_model=AgentResponse)
def search_agent(
    request: Request,
    body: AgentRequest,
    session_id: str = Depends(get_session_id),
    settings: Settings = Depends(get_settings),
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """Handle conversational search requests per SPEC.md Section 4."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    rate_limiter.check_rate_limit(client_ip, settings=settings)

    return agent_service.process_request(
        message=body.message,
        budget=body.budget,
        session_id=session_id,
        language=body.language,
    )
