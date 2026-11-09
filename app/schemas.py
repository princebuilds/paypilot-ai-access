"""Pydantic request and response schemas for all endpoints."""
from typing import List, Optional

from pydantic import BaseModel, Field


# --- Error Schemas ---
class ErrorDetail(BaseModel):
    """Normalized error detail body."""
    code: str
    message: str
    retryable: bool = False


class ErrorEnvelope(BaseModel):
    """Standardized error envelope per SPEC.md section 3."""
    error: ErrorDetail


# --- Health Schema ---
class HealthResponse(BaseModel):
    """Health status response."""
    ok: bool = True
    channel3_configured: bool
    gemini_configured: bool
    paypal_configured: bool
    gemini_model: Optional[str] = None
    last_channel3_call_at: Optional[str] = None


# --- Agent Schemas ---
class AgentRequest(BaseModel):
    """Input payload for /api/agent."""
    message: str = Field(min_length=1, max_length=1000)
    budget: Optional[str] = Field(default=None, pattern=r"^\d+(\.\d{2})?$")
    language: str = Field(default="en", max_length=10)


class GroundingReason(BaseModel):
    """Reason grounded in snapshot evidence."""
    claim: str
    evidence_field: str
    evidence_text: str


class RecommendationItem(BaseModel):
    """Individual recommended product card payload."""
    snapshot_id: str
    channel3_id: str
    title: str
    image_url: Optional[str] = None
    merchant_domain: str
    price: str
    currency: str = "USD"
    availability: str
    purchasable: bool = True
    not_purchasable_reason: Optional[str] = None
    buy_url: Optional[str] = None
    reasons: List[GroundingReason] = Field(default_factory=list)


class LiveDataSummary(BaseModel):
    """Metadata regarding live data source."""
    source: str = "channel3"
    fetched_at: str
    channel3_calls: int = 1


class AgentResponse(BaseModel):
    """Output payload from /api/agent."""
    search_id: str
    reply_text: str
    clarifying_question: Optional[str] = None
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    live_data: LiveDataSummary


# --- Quote Schemas ---
class QuoteCreateRequest(BaseModel):
    """Input for creating a price-locked quote."""
    snapshot_id: str
    quantity: int = Field(default=1, ge=1, le=10)
    budget: Optional[str] = Field(default=None, pattern=r"^\d+(\.\d{2})?$")


class QuoteResponse(BaseModel):
    """Price-locked quote details."""
    quote_id: str
    title: str
    unit_price: str
    currency: str = "USD"
    quantity: int
    total: str
    budget: Optional[str] = None
    within_budget: bool
    expires_at: str
    status: str = "QUOTED"


class QuoteConfirmRequest(BaseModel):
    """Input for confirming quote total."""
    confirmed_total: str = Field(pattern=r"^\d+\.\d{2}$")


class QuoteConfirmResponse(BaseModel):
    """Response from quote confirmation."""
    status: str = "CONFIRMED"


# --- Order Schemas ---
class OrderCreateRequest(BaseModel):
    """Input for creating an order."""
    quote_id: str


class OrderCreateResponse(BaseModel):
    """Response after order creation at PayPal."""
    order_id: str
    paypal_order_id: str
    status: str = "ORDER_CREATED"


class OrderCaptureResponse(BaseModel):
    """Response after server-side PayPal capture and verification."""
    order_id: str
    status: str
    message: str
    receipt_url: str


class OrderCancelResponse(BaseModel):
    """Response after customer cancels order."""
    status: str = "CANCELLED"


class ReceiptResponse(BaseModel):
    """Receipt representation for verified or failed order."""
    order_id: str
    status: str
    title: str
    quantity: int
    unit_price: str
    total: str
    currency: str = "USD"
    paypal_capture_id: Optional[str] = None
    captured_at: Optional[str] = None
    merchant_domain: str
    retailer_url: Optional[str] = None
    sandbox: bool = True
    message: str
