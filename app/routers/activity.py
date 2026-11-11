"""Router for retrieving server-side activity events."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from app.activity import get_activity_for_order, get_activity_for_session
from app.config import Settings, get_settings
from app.security import get_session_id

router = APIRouter(prefix="/api/activity", tags=["activity"])


@router.get("", response_model=Dict[str, List[Dict[str, Any]]])
def get_activity_events(
    order_id: Optional[str] = Query(None, description="Optional order ID to fetch specific order timeline"),
    session_id: str = Depends(get_session_id),
    settings: Settings = Depends(get_settings),
) -> Dict[str, List[Dict[str, Any]]]:
    """Return chronological activity timeline generated strictly from database tables."""
    if order_id:
        events = get_activity_for_order(order_id, session_id=session_id, db_path=settings.DATABASE_PATH)
    else:
        events = get_activity_for_session(session_id, db_path=settings.DATABASE_PATH)

    return {"events": events}
