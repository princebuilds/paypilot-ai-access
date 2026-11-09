"""FastAPI application factory, static file mounting, and router integration."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db
from app.errors import (
    AppError,
    app_error_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.routers import agent, health, orders, quotes
from app.security import SessionMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    settings = get_settings()
    # In live mode (OFFLINE_TESTS=0), validate configuration
    if settings.OFFLINE_TESTS == 0:
        settings.validate_for_startup()
    init_db(settings.DATABASE_PATH)
    yield


app = FastAPI(
    title="PayPilot AI ACCESS",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(SessionMiddleware)

# Exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Routers
app.include_router(health.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(quotes.router, prefix="/api")
app.include_router(orders.router, prefix="/api")

# Static files mount
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
