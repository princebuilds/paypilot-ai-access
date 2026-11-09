"""Order creation and capture endpoints."""
from fastapi import APIRouter, Depends

from app.errors import NotImplementedFeatureError
from app.schemas import OrderCreateRequest
from app.security import get_session_id

router = APIRouter()


@router.post("/orders")
def create_order(
    body: OrderCreateRequest,
    session_id: str = Depends(get_session_id),
):
    """Create PayPal order from quote (implemented in Phase B4)."""
    raise NotImplementedFeatureError("Order creation will be activated in Phase B4.")


@router.post("/orders/{order_id}/capture")
def capture_order(
    order_id: str,
    session_id: str = Depends(get_session_id),
):
    """Capture and verify PayPal payment (implemented in Phase B4)."""
    raise NotImplementedFeatureError("Payment capture will be activated in Phase B4.")


@router.post("/orders/{order_id}/cancel")
def cancel_order(
    order_id: str,
    session_id: str = Depends(get_session_id),
):
    """Record customer cancellation (implemented in Phase B4)."""
    raise NotImplementedFeatureError("Order cancellation will be activated in Phase B4.")


@router.get("/orders/{order_id}")
def get_order_receipt(
    order_id: str,
    session_id: str = Depends(get_session_id),
):
    """Retrieve order receipt details (implemented in Phase B4)."""
    raise NotImplementedFeatureError("Order receipt will be activated in Phase B4.")
